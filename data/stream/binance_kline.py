from data.stream.binance_aggtrade import BinanceWebSocket
import asyncio
import json
from time import time
from data.fetch.crypto_binance import fetch_symbol_list_binance
from OMS.binance_oms import Binance

class KlineWebSocket(BinanceWebSocket):
    def __init__(self, market_name, timeframe, chunk_size=1):
        super().__init__(market_name, timeframe=timeframe, chunk_size=chunk_size)
        self.symbol_trade_data = {}
        self.handle_message_function_str = "kline_handle_message"
        self.top_pairs_dict = {}
        self.binance_client = Binance()
        self.num_pairs_volume = 10
    
    async def default_handle_message(self, pair, message, symbol_trade_data, top_pairs_dict, finstore, current_time):
        print(f"Kline data for {pair}: {message}")
    

    
    async def cleanup_old_trades(self, trade_retention_ms, anomaly_retention_ms, sleep_time=60):
        try:
            while not self.stop_signal:
                current_time = int(time() * 1000)
                cutoff_time = current_time - trade_retention_ms
                cutoff_time_anomaly = current_time - anomaly_retention_ms

                for symbol, trades in self.symbol_trade_data.items():
                    # Remove trades whose 'T' value is less than the cutoff time
                    self.symbol_trade_data[symbol] = {
                        trade_id: trade
                        for trade_id, trade in trades.items()
                        if trade['T'] >= cutoff_time
                    }

                #for symbol, anomalies in self.top_pairs_dict.items():
                #    self.top_pairs_dict[symbol] = [anomaly for anomaly in anomalies if anomaly['timestamp'] > cutoff_time_anomaly]

                await asyncio.sleep(sleep_time)
        except asyncio.CancelledError:
            print("Cleanup task cancelled. Exiting gracefully.")
    
    async def handle_message(self, ws, message):
        try:
            data = json.loads(message)
            data = data.get('data').get('k')
            pair = data.get('s')
            asyncio.create_task(self.handle_message_function(pair, data, self.symbol_trade_data, self.top_pairs_dict, self.finstore, time(), self.binance_client))
        except Exception as fault:
            import traceback
            print(traceback.print_exc())

    def on_message(self, ws, message):
        asyncio.run(self.handle_message(ws, message))
    
    async def fetch_live_klines(self):
        # Fetch symbols and initiate kline websocket streams
        #symbols = self.get_top_usdt_pairs_by_volume()
        usdt_symbols = fetch_symbol_list_binance(type='swap', suffix='USDT')
        symbols = [symbol.replace('/', '') for symbol in usdt_symbols]
        symbols = list(set(symbols))[-1*self.num_pairs_volume:]
        if ('BTCUSDT' not in symbols) or 'btcusdt' not in symbols:
            symbols.append('BTCUSDT')
        print(len(symbols))
        streams = [f"{symbol.lower()}@kline_1m" for symbol in symbols]
        stream_chunks = [streams[i:i + self.chunk_size] for i in range(0, len(streams), self.chunk_size)]

        base_url = "wss://fstream.binance.com/stream?streams="
        tasks = []

        for chunk in stream_chunks:
            url = f"{base_url}{'/'.join(chunk)}"
            tasks.append(self.connect_websocket(url))

        await asyncio.gather(*tasks)
    
    async def run(self):
        try:
            cleanup_task = asyncio.create_task(self.cleanup_old_trades(90*60*1000, 5*60*1000))
            fetch_data_task = asyncio.create_task(self.fetch_live_klines())
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
    manager = KlineWebSocket(market_name="crypto_binance", timeframe="kline_1m")
    asyncio.run(manager.run())

