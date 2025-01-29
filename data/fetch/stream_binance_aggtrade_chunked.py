'''
What's different ? V1 in improvements , unicorn is the next best version. 
IT chunks the streams so that 300 streams don't happen in a single websocket connection instead they are equally divided.
'''
import asyncio
import websockets
import json
from data.fetch.crypto_binance import fetch_symbol_list_binance
from finstore.finstore import Finstore
from collections import defaultdict, deque
import time
import importlib
import numpy as np

market_name = 'crypto_binance'
timeframe = 'aggtrade'
finstore = Finstore(market_name=market_name, timeframe=timeframe, enable_append=True)

# Stop signal
stop_signal = False

# Running storage for trades in the past 10 minutes
symbol_trade_data = defaultdict(list)
anomaly_dict = {}

# Current handle_message function (default)
async def default_handle_message(pair, message, symbol_trade_data, anomaly_dict, finstore):
    #print(f"Received for {pair}: {message}")

    # Save the trade data for the past 10 minutes
    if symbol_trade_data[pair]:
        previous_message = symbol_trade_data[pair][-1]
        if 'a' in previous_message and 'a' in message:
            if message['a'] != previous_message['a'] + 1:
                print(f"Warning: Missed trades for {pair}. Previous 'a': {previous_message['a']}, Current 'a': {message['a']}")

    symbol_trade_data[pair].append(message)

    # Save the trade data using finstore
    finstore.stream.save_trade_data(pair, message, preset='agg_trade')

# Assign default handle_message
current_handle_message = default_handle_message

def reload_handle_message():
    global current_handle_message
    try:
        spec = importlib.util.find_spec("data.fetch.custom_handle_message")
        if spec is not None:
            import data.fetch.custom_handle_message
            importlib.reload(data.fetch.custom_handle_message)  # Force reload
            module = data.fetch.custom_handle_message
            if hasattr(module, "updated_handle_message"):
                current_handle_message = getattr(module, "updated_handle_message")
                #print("[INFO] Updated handle_message function loaded successfully.")
            else:
                print("[WARNING] Module does not contain updated_handle_message function. Using default.")
        else:
            print("[WARNING] custom_handle_message module not found. Using default.")
    except Exception as e:
        print(f"[ERROR] Failed to load updated handle_message: {e}")
        current_handle_message = default_handle_message


# Function to clean up old trades
async def cleanup_old_trades():
    while not stop_signal:
        current_time = int(time.time() * 1000)  # Current time in ms
        cutoff_time = current_time - (10 * 60 * 1000)  # 10 minutes ago
        for symbol, trades in symbol_trade_data.items():
            symbol_trade_data[symbol] = [trade for trade in trades if trade['T'] >= cutoff_time]

        for pair in list(anomaly_dict.keys()):
            anomaly_dict[pair] = [anomaly for anomaly in anomaly_dict[pair] if anomaly['timestamp'] > cutoff_time]

        await asyncio.sleep(60)  # Clean up every minute

# Function to handle incoming messages
async def handle_message(pair, message):
    await current_handle_message(pair, message, symbol_trade_data, anomaly_dict, finstore)

def fetch_symbol_list_binance_spoof(type='spot', suffix='BTC'):
    return ["ETHBTC", "ADABTC", "XRPBTC"]

def get_top_usdt_pairs_by_volume():
    import requests
    base_url = "https://api.binance.com"
    ticker_endpoint = "/api/v3/ticker/24hr"

    # Fetch data from Binance API
    response = requests.get(base_url + ticker_endpoint)
    response.raise_for_status()  # Raise an exception for HTTP errors

    # Parse JSON response
    ticker_data = response.json()

    # Filter for USDT pairs and gather relevant information
    usdt_pairs = [
        {
            "symbol": item["symbol"],
            "volume": float(item["quoteVolume"])
        }
        for item in ticker_data
        if item["symbol"].endswith("USDT")
    ]

    # Sort by volume and get the top 100
    sorted_pairs = sorted(usdt_pairs, key=lambda x: x["volume"], reverse=True)[:300]

    # Extract only the symbols
    top_100_symbols = [pair["symbol"] for pair in sorted_pairs]

    return top_100_symbols

# Function to create WebSocket connections for chunks
async def fetch_live_data_for_chunk(streams_chunk):
    global stop_signal
    base_url = "wss://fstream.binance.com/stream?streams="
    url = f"{base_url}{'/'.join(streams_chunk)}"

    retry_attempts = 0
    max_retries = 5
    backoff_delay = 5

    while not stop_signal:
        try:
            async with websockets.connect(url, ping_interval=180, ping_timeout=600) as websocket:
                print(f"Connected to WebSocket for chunk: {streams_chunk[:5]}...")  # Display first 5 streams for clarity
                while not stop_signal:
                    try:
                        data = await websocket.recv()
                        message = json.loads(data)
                        if "stream" in message and "data" in message:
                            stream_name = message["stream"]
                            data_payload = message["data"]
                            symbol = data_payload.get("s", "Unknown Pair")
                            await handle_message(symbol, data_payload)
                    except websockets.exceptions.ConnectionClosed as e:
                        print(f"WebSocket closed: {e}")
                        break
                    except Exception as e:
                        print(f"Error: {e}")
                        break
        except Exception as e:
            print(f"Connection error: {e}")
            retry_attempts += 1
        
        if not stop_signal:
            delay = backoff_delay * (2 ** retry_attempts)
            print(f"Reconnecting in {delay} seconds...")
            await asyncio.sleep(delay)
    
    print("Exiting WebSocket connection for chunk...")

# WebSocket handler with chunking
async def fetch_live_data():
    global stop_signal
    symbols = get_top_usdt_pairs_by_volume()
    streams = [f"{symbol.lower()}@aggTrade" for symbol in symbols]

    # Chunking logic
    chunk_size = 50  # Maximum streams per WebSocket connection
    stream_chunks = [streams[i:i + chunk_size] for i in range(0, len(streams), chunk_size)]

    # Run WebSocket connections for all chunks concurrently
    tasks = [fetch_live_data_for_chunk(chunk) for chunk in stream_chunks]
    await asyncio.gather(*tasks)

# Adjusted entry point for environments with a running event loop
async def main():
    cleanup_task = asyncio.create_task(cleanup_old_trades())
    fetch_data_task = asyncio.create_task(fetch_live_data())
    # Periodically check for updates to handle_message
    async def periodic_reload():
        while not stop_signal:
            reload_handle_message()
            await asyncio.sleep(10)  # Check for updates every 10 seconds

    reload_task = asyncio.create_task(periodic_reload())

    await asyncio.gather(cleanup_task, fetch_data_task, reload_task)

# Function to stop the WebSocket fetcher
def stop_fetching():
    global stop_signal
    stop_signal = True
    print("Stop signal sent.")

if __name__ == "__main__":
    asyncio.run(main())
