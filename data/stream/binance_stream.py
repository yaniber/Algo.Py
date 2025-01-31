import websocket
import asyncio
import importlib
from threading import Thread
from finstore.finstore import Finstore

class WebSocketManager:
    def __init__(self, market_name, timeframe, handle_message_function=None, chunk_size=1):
        self.market_name = market_name
        self.timeframe = timeframe
        self.finstore = Finstore(market_name=market_name, timeframe=timeframe, enable_append=True)
        self.active_websockets = []
        self.websocket_threads = []
        self.handle_message_function = handle_message_function or self.default_handle_message
        self.chunk_size = chunk_size
        self.handle_message_function_str = "updated_handle_message"
        self.num_pairs_volume = 200

    def default_handle_message(self, pair, message, symbol_trade_data, anomaly_dict, finstore, current_time):
        
        raise NotImplementedError('Implement this in child class')

    async def cleanup_old_trades(self, trade_retention_ms, anomaly_retention_ms, sleep_time=60):
        
        raise NotImplementedError('Implement this in child class')

    async def periodic_reload_handle_message(self):
        try:
            while not self.stop_signal:
                self.reload_handle_message()
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            print("Reload task cancelled. Exiting gracefully.")

    def reload_handle_message(self):
        try:
            spec = importlib.util.find_spec("data.stream.custom_handle_message")
            if spec is not None:
                import data.stream.custom_handle_message
                importlib.reload(data.stream.custom_handle_message)
                module = data.stream.custom_handle_message
                if hasattr(module, self.handle_message_function_str):
                    self.handle_message_function = getattr(module, self.handle_message_function_str)
                else:
                    print("[WARNING] Module does not contain updated_handle_message function. Using default.")
            else:
                print("[WARNING] custom_handle_message module not found. Using default.")
                raise
        except Exception as e:
            print(f"[ERROR] Failed to load updated handle_message: {e}")
            self.handle_message_function = self.default_handle_message
            raise

    async def handle_message(self, ws, message):

        raise NotImplementedError('Implement this in child class')

    def on_message(self, ws, message):
        asyncio.run(self.handle_message(ws, message))

    def on_error(self, ws, error):
        print(f"On Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket closed. Reconnecting...")
        if not self.stop_signal:
            asyncio.run(self.connect_websocket(ws.url))
    
    def on_ping(self, ws, message):
        ws.send(message, websocket.ABNF.OPCODE_PONG)

    def close_all_websockets(self):
        print("Closing all WebSocket connections...")
        for ws in self.active_websockets:
            try:
                ws.close()
            except Exception as e:
                print(f"Error while closing WebSocket: {e}")
        self.active_websockets.clear()

        for thread in self.websocket_threads:
            if thread.is_alive():
                try:
                    thread.join(timeout=1)
                except Exception as e:
                    print(f"Error while joining WebSocket thread: {e}")
        self.websocket_threads.clear()

    def get_top_usdt_pairs_by_volume(self):
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

        sorted_pairs = sorted(usdt_pairs, key=lambda x: x["volume"], reverse=True)[:self.num_pairs_volume]
        return [pair["symbol"] for pair in sorted_pairs]

    async def connect_websocket(self, url):
        print(f"Connecting to URL: {url[:70]}")
        ws = websocket.WebSocketApp(
            url,
            on_message=self.on_message,
            on_close=self.on_close,
            on_ping=self.on_ping,
            on_error=self.on_error,
        )
        self.active_websockets.append(ws)

        def run_ws():
            print(f'Running the ws : {url}')
            ws.run_forever()

        thread = Thread(target=run_ws, daemon=True)
        self.websocket_threads.append(thread)
        thread.start()

        try:
            while thread.is_alive() and not self.stop_signal:
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in WebSocket connection: {e}")
        finally:
            if ws in self.active_websockets:
                self.active_websockets.remove(ws)

    async def fetch_live_data(self):

        raise NotImplementedError('Implement this in child class')

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