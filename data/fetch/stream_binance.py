import asyncio
import websockets
import json
from data.fetch.crypto_binance import fetch_symbol_list_binance
from finstore.finstore import Finstore

market_name = 'crypto_binance'
timeframe = '1m'
finstore = Finstore(market_name=market_name, timeframe=timeframe, enable_append=True)

# Stop signal
stop_signal = False

# Function to handle incoming messages
async def handle_message(pair, message):
    print(f"Received for {pair}: {message.get('k', {})}")
    finstore.stream.save_trade_data(pair, message, preset='binance_kline')

def fetch_symbol_list_binance_spoof(type='spot', suffix='BTC'):
    return ["ETHBTC", "ADABTC", "XRPBTC"] 

# WebSocket handler with a stop mechanism
async def fetch_live_data():
    global stop_signal
    base_url = "wss://stream.binance.com:9443/ws"
    symbols = fetch_symbol_list_binance(type='spot', suffix='BTC')
    symbols = [symbol.replace('/', '') for symbol in symbols]
    interval = "1m"  # Set the desired interval here
    streams = [f"{symbol.lower()}@kline_{interval}" for symbol in symbols]  # Updated to kline stream
    url = f"{base_url}/{'/'.join(streams)}"
    
    while not stop_signal:
        try:
            async with websockets.connect(url, ping_interval=180, ping_timeout=600) as websocket:
                print("Connected to Binance WebSocket")
                while not stop_signal:
                    try:
                        data = await websocket.recv()
                        message = json.loads(data)
                        symbol = message.get("s", "Unknown Pair")
                        await handle_message(symbol, message)
                    except websockets.exceptions.ConnectionClosed as e:
                        print(f"WebSocket closed: {e}")
                        break
                    except Exception as e:
                        print(f"Error: {e}")
                        break
        except Exception as e:
            print(f"Connection error: {e}")
        
        if not stop_signal:
            print("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
    
        print("Exiting WebSocket connection...")

# Adjusted entry point for environments with a running event loop
async def main():
    await fetch_live_data()


# Function to stop the WebSocket fetcher
def stop_fetching():
    global stop_signal
    stop_signal = True
    print("Stop signal sent.")

if __name__ == "__main__":
    asyncio.run(main())
