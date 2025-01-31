import asyncio
import threading
import time
import random

# Simulating WebSocket trade data
symbol_trade_data = {}

def fake_websocket_handler():
    """ Simulated WebSocket data feed updating global symbol_trade_data """
    while True:
        timestamp = int(time.time() * 1000)  # Simulate a timestamp
        new_data = {
            "BTCUSDT": random.uniform(-1, 1),
            "ETHUSDT": random.uniform(-1, 1),
            "BNBUSDT": random.uniform(-1, 1),
            "XRPUSDT": random.uniform(-1, 1),
            "ADAUSDT": random.uniform(-1, 1),
        }

        for symbol, score in new_data.items():
            if symbol not in symbol_trade_data:
                symbol_trade_data[symbol] = {}

            symbol_trade_data[symbol][timestamp] = {"r2p_score": score}

        time.sleep(60)  # Simulating new data arriving every minute

# Run the WebSocket in a separate thread
websocket_thread = threading.Thread(target=fake_websocket_handler, daemon=True)
websocket_thread.start()
