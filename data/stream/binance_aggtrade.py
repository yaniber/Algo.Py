import websocket
import json
import asyncio
import importlib
from collections import defaultdict
from threading import Thread
from time import time, sleep
from utils.db.lock import generic_lock
from finstore.finstore import Finstore
from data.stream.binance_stream import WebSocketManager

class BinanceWebSocket(WebSocketManager):
    def __init__(self, market_name, timeframe, handle_message_function=None, chunk_size=1):
        super().__init__(market_name, timeframe, handle_message_function, chunk_size)
        self.market_name = market_name
        self.timeframe = timeframe
        self.finstore = Finstore(market_name=market_name, timeframe=timeframe, enable_append=True)
        self.symbol_trade_data = defaultdict(list)
        self.anomaly_dict = {}
        self.stop_signal = False
        self.active_websockets = []
        self.websocket_threads = []
        self.handle_message_function = handle_message_function or self.default_handle_message
        self.chunk_size = chunk_size
        self.handle_message_function_str = "updated_handle_message"

    def default_handle_message(self, pair, message, symbol_trade_data, anomaly_dict, finstore, current_time):
        if self.symbol_trade_data[pair]:
            previous_message = self.symbol_trade_data[pair][-1]
            if 'a' in previous_message and 'a' in message:
                if message['a'] != previous_message['a'] + 1:
                    print(f"Warning: Missed trades for {pair}. Previous 'a': {previous_message['a']}, Current 'a': {message['a']}")

        self.symbol_trade_data[pair].append(message)
        #self.finstore.stream.save_trade_data(pair, message, preset=self.timeframe)

    async def cleanup_old_trades(self, trade_retention_ms, anomaly_retention_ms, sleep_time=60):
        try:
            while not self.stop_signal:
                current_time = int(time() * 1000)
                cutoff_time = current_time - trade_retention_ms
                cutoff_time_anomaly = current_time - anomaly_retention_ms

                for symbol, trades in self.symbol_trade_data.items():
                    self.symbol_trade_data[symbol] = [trade for trade in trades if trade['T'] >= cutoff_time]

                for symbol, anomalies in self.anomaly_dict.items():
                    self.anomaly_dict[symbol] = [anomaly for anomaly in anomalies if anomaly['timestamp'] > cutoff_time_anomaly]

                await asyncio.sleep(sleep_time)
        except asyncio.CancelledError:
            print("Cleanup task cancelled. Exiting gracefully.")

    async def handle_message(self, ws, message):
        data = json.loads(message)
        if "stream" in data and "data" in data:
            stream_name = data["stream"]
            data_payload = data["data"]
            symbol = data_payload.get("s", "Unknown Pair")
            asyncio.create_task(self.handle_message_function(symbol, data_payload, self.symbol_trade_data, self.anomaly_dict, self.finstore, time()))


    async def fetch_live_data(self):
        try:
            symbols = self.get_top_usdt_pairs_by_volume()
            streams = [f"{symbol.lower()}@{self.timeframe}" for symbol in symbols]
            stream_chunks = [streams[i:i + self.chunk_size] for i in range(0, len(streams), self.chunk_size)]

            base_url = "wss://fstream.binance.com/stream?streams="
            tasks = []

            for chunk in stream_chunks:
                url = f"{base_url}{'/'.join(chunk)}"
                tasks.append(self.connect_websocket(url))

            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            print("Fetch live data task cancelled. Exiting gracefully.")

    async def run(self):
        try:
            cleanup_task = asyncio.create_task(self.cleanup_old_trades(3600000, 120000))
            fetch_data_task = asyncio.create_task(self.fetch_live_data())
            reload_task = asyncio.create_task(self.periodic_reload_handle_message())

            await asyncio.gather(cleanup_task, fetch_data_task, reload_task)
        except KeyboardInterrupt:
            print("KeyboardInterrupt detected. Exiting gracefully...")
            self.stop_signal = True
            self.close_all_websockets()
        finally:
            print("Cleaning up tasks...")
            tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

if __name__ == "__main__":
    try:
        manager = BinanceWebSocket(market_name="crypto_binance", timeframe="aggTrade")
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        print("Script terminated by user.")
