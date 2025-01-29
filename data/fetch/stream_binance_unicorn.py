'''
What's different : using websocketApp instead of regular websockets. 
Hence there have been 0 instance of disconnection and data loss due to perfect ping pong between servers
Also have added graceful shutdown to prevent data corruption

Issues : 
- Pile up happening since the update_handle_message is awaited instead of being offloaded as a task.

Solution : 
- Try multi-processing , try putting messages in queues to be be then consumed in a multi-processing manner by another function. 
    - Remove finstore altogether , the lock might be causing issues too , we don't use it anyway
    - Spoiler : It was the bottleneck
'''

import websocket
import json
import asyncio
import importlib
from collections import defaultdict
from data.fetch.crypto_binance import fetch_symbol_list_binance
from finstore.finstore import Finstore
import time
import threading
from utils.db.lock import generic_lock

websocket_threads = []

market_name = 'crypto_binance'
timeframe = 'aggtrade'
finstore = Finstore(market_name=market_name, timeframe=timeframe, enable_append=True)

# Stop signal
stop_signal = False

# Running storage for trades in the past 10 minutes
symbol_trade_data = defaultdict(list)
anomaly_dict = {}
active_websockets = []


# Current handle_message function (default)
def default_handle_message(pair, message, symbol_trade_data, anomaly_dict, finstore, current_time):
    if symbol_trade_data[pair]:
        previous_message = symbol_trade_data[pair][-1]
        if 'a' in previous_message and 'a' in message:
            if message['a'] != previous_message['a'] + 1:
                print(f"Warning: Missed trades for {pair}. Previous 'a': {previous_message['a']}, Current 'a': {message['a']}")

    symbol_trade_data[pair].append(message)
    #finstore.stream.save_trade_data(pair, message, preset='agg_trade')

current_handle_message = default_handle_message

def reload_handle_message():
    global current_handle_message
    try:
        spec = importlib.util.find_spec("data.fetch.custom_handle_message")
        if spec is not None:
            import data.fetch.custom_handle_message
            importlib.reload(data.fetch.custom_handle_message)
            module = data.fetch.custom_handle_message
            if hasattr(module, "updated_handle_message"):
                current_handle_message = getattr(module, "updated_handle_message")
            else:
                print("[WARNING] Module does not contain updated_handle_message function. Using default.")
        else:
            print("[WARNING] custom_handle_message module not found. Using default.")
    except Exception as e:
        print(f"[ERROR] Failed to load updated handle_message: {e}")
        current_handle_message = default_handle_message

async def cleanup_old_trades():
    global stop_signal
    try:
        while not stop_signal:
            current_time = int(time.time() * 1000)
            cutoff_time = current_time - (60 * 60 * 1000)
            cutoff_time_anomaly = current_time - (2 * 60 * 1000)
            for symbol, trades in symbol_trade_data.items():
                symbol_trade_data[symbol] = [trade for trade in trades if trade['T'] >= cutoff_time]

            for symbol, anomalies in anomaly_dict.items():
                anomaly_dict[symbol] = [anomaly for anomaly in anomalies if anomaly['timestamp'] > cutoff_time_anomaly]

            await asyncio.sleep(60)
    except asyncio.CancelledError:
        print("Cleanup task cancelled. Exiting gracefully.")

async def periodic_reload_handle_message():
    global stop_signal
    try:
        while not stop_signal:
            reload_handle_message()
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("Reload task cancelled. Exiting gracefully.")

async def handle_message(ws, message):
    data = json.loads(message)
    if "stream" in data and "data" in data:
        stream_name = data["stream"]
        data_payload = data["data"]
        symbol = data_payload.get("s", "Unknown Pair")
        #await current_handle_message(symbol, data_payload, symbol_trade_data, anomaly_dict, finstore)
        asyncio.create_task(current_handle_message(symbol, data_payload, symbol_trade_data, anomaly_dict, finstore, time.time()))

def on_message(ws, message):
    asyncio.run(handle_message(ws, message))

def on_ping(ws, message):
    #print(f"Received ping: {message}")
    ws.send(message, websocket.ABNF.OPCODE_PONG)
    #print(f"Sent pong: {message}")

def on_error(ws, error):
    print(f"On Error: {error}")

def on_close(ws, close_status_code, close_msg):
    global stop_signal
    print("WebSocket closed. Reconnecting...")
    if not stop_signal:
        asyncio.run(connect_websocket(ws.url))

def close_all_websockets():
    global active_websockets
    print("Closing all WebSocket connections...")
    for ws in active_websockets:
        try:
            ws.close()  # Gracefully close the WebSocket
        except Exception as e:
            print(f"Error while closing WebSocket: {e}")
    active_websockets.clear()

    # Stop all WebSocket threads
    for thread in websocket_threads:
        if thread.is_alive():
            try:
                thread.join(timeout=1)  # Wait for the thread to terminate
            except Exception as e:
                print(f"Error while joining WebSocket thread: {e}")
    websocket_threads.clear()

def get_top_usdt_pairs_by_volume():
    import requests
    base_url = "https://api.binance.com"
    ticker_endpoint = "/api/v3/ticker/24hr"

    response = requests.get(base_url + ticker_endpoint)
    response.raise_for_status()

    ticker_data = response.json()
    usdt_pairs = [
        {
            "symbol": item["symbol"],
            "volume": float(item["quoteVolume"])
        }
        for item in ticker_data
        if item["symbol"].endswith("USDT")
    ]

    sorted_pairs = sorted(usdt_pairs, key=lambda x: x["volume"], reverse=True)[:50]
    return [pair["symbol"] for pair in sorted_pairs]

async def connect_websocket(url):
    global active_websockets, stop_signal, websocket_threads
    print(f'Connecting to url : {url[:70]}')
    ws = websocket.WebSocketApp(
        url,
        on_message=on_message,
        on_close=on_close,
        on_ping=on_ping,
        on_error=on_error,
    )
    active_websockets.append(ws)

    def run_ws():
        ws.run_forever()

    thread = threading.Thread(target=run_ws, daemon=True)
    websocket_threads.append(thread)
    thread.start()

    try:
        while thread.is_alive() and not stop_signal:
            await asyncio.sleep(0.1)
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
    finally:
        if ws in active_websockets:
            active_websockets.remove(ws)

async def fetch_live_data():
    global stop_signal
    try:
        symbols = get_top_usdt_pairs_by_volume()
        symbols.append('tfuelusdt')
        #symbols = fetch_symbol_list_binance(type='spot', suffix='BTC')
        #usdt_symbols = fetch_symbol_list_binance(type='spot', suffix='USDT')
        #symbols = symbols + usdt_symbols
        #symbols = [symbol.replace('/', '') for symbol in symbols]
        
        streams = [f"{symbol.lower()}@aggTrade" for symbol in symbols]

        chunk_size = 1
        stream_chunks = [streams[i:i + chunk_size] for i in range(0, len(streams), chunk_size)]

        base_url = "wss://fstream.binance.com/stream?streams="
        tasks = []

        for chunk in stream_chunks:
            url = f"{base_url}{'/'.join(chunk)}"
            tasks.append(connect_websocket(url))

        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        print("Fetch live data task cancelled. Exiting gracefully.")

async def main():
    global stop_signal
    try:
        cleanup_task = asyncio.create_task(cleanup_old_trades())
        fetch_data_task = asyncio.create_task(fetch_live_data())
        reload_task = asyncio.create_task(periodic_reload_handle_message())

        await asyncio.gather(cleanup_task, fetch_data_task, reload_task)
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Exiting gracefully...")
        stop_signal = True
        close_all_websockets()
    finally:
        print("Cleaning up tasks...")
        tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
        for task in tasks:
            print('cancelling a task........')
            task.cancel()
            try:
                await task  # Awaiting the task allows it to exit gracefully.
            except asyncio.CancelledError:
                pass  # Suppress expected cancellation errors.
        print("All asyncio tasks cleaned up.")
        #with generic_lock:
        #    print('Finstore gracefully exits.')

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Script terminated by user.")
