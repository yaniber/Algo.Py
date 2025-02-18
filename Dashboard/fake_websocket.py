import threading
import time
import random
import requests

# ------------------------------------
# 1. Get Top 200 USDT Pairs from Binance
# ------------------------------------
def get_top_usdt_pairs(num_pairs=200):
    base_url = "https://api.binance.com"
    ticker_endpoint = "/api/v3/ticker/24hr"
    response = requests.get(base_url + ticker_endpoint)
    response.raise_for_status()

    ticker_data = response.json()
    # Extract symbol and lastPrice for USDT pairs
    usdt_pairs = [
        {
            "symbol": item["symbol"],
            "lastPrice": float(item["lastPrice"])
        }
        for item in ticker_data
        if item["symbol"].endswith("USDT")
    ]
    # You can sort by quoteVolume if desired – here we sort by lastPrice, but you might change it:
    sorted_pairs = sorted(usdt_pairs, key=lambda x: x["lastPrice"], reverse=True)[:num_pairs]
    return sorted_pairs

# Get the top 200 pairs
top_pairs = get_top_usdt_pairs(200)

# ------------------------------------
# 2. Initialize Data Structures
# ------------------------------------
symbol_trade_data = {}  # Will hold historical data for each symbol
initial_prices = {}     # Baseline prices for each symbol (from Binance)
latest_prices = {}      # Latest prices (updated by simulation)

symbols = []  # List of symbols to update
for pair in top_pairs:
    symbol = pair["symbol"]
    price = pair["lastPrice"]
    symbols.append(symbol)
    initial_prices[symbol] = price
    latest_prices[symbol] = price

# ------------------------------------
# 3. Simulated WebSocket Handler
# ------------------------------------
def fake_websocket_handler():
    """
    Simulates a WebSocket data feed by updating each symbol's price every 2 seconds.
    The price updates by a small random percentage change.
    r2p_score is calculated as the percentage change from the initial price.
    """
    while True:
        timestamp = int(time.time() * 1000)  # current timestamp in ms
        for symbol in symbols:
            old_price = latest_prices[symbol]
            # Update the price with a small random change between -0.5% and +0.5%
            delta = random.uniform(-0.05, 0.05)
            new_price = old_price * (1 + delta)
            latest_prices[symbol] = new_price

            # Calculate r2p score as percentage change from the initial price
            init_price = initial_prices[symbol]
            r2p_score = ((new_price - init_price) / init_price) * 100

            # Save the new values into the symbol_trade_data dictionary
            if symbol not in symbol_trade_data:
                symbol_trade_data[symbol] = {}
            symbol_trade_data[symbol][timestamp] = {
                "close": new_price,
                "r2p_score": r2p_score
            }
        time.sleep(2)  # update interval: 2 seconds

# Run the simulation in a separate thread
websocket_thread = threading.Thread(target=fake_websocket_handler, daemon=True)
websocket_thread.start()
