import ccxt
import pandas as pd

def fetch_ohlcv(symbol, timeframe, since):
    exchange = ccxt.binance()
    all_ohlcv = []
    limit = 200  # Most exchanges allow a max of 500 entries per request
    while True:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        if not ohlcv:
            break
        all_ohlcv.extend(ohlcv)
        since = ohlcv[-1][0] + 1  # Update since to get new data from the end of the last fetch
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    if 'timestamp' not in df.columns:
        print(f"Error: 'timestamp' column missing in data for {symbol}")
    return df