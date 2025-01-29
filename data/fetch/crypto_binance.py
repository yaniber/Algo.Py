import ccxt
import pandas as pd
from datetime import datetime
import time

def fetch_ohlcv_binance(symbol, timeframe, start_date):
    exchange = ccxt.binance()
    all_ohlcv = []
    limit = 200  # Most exchanges allow a max of 500 entries per request
    since = int(start_date.timestamp() * 1000)
    while True:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            time.sleep(5)
            continue
        if not ohlcv:
            break
        all_ohlcv.extend(ohlcv)
        since = ohlcv[-1][0] + 1  # Update since to get new data from the end of the last fetch
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    if 'timestamp' not in df.columns:
        print(f"Error: 'timestamp' column missing in data for {symbol}")
    return df

def fetch_symbol_list_binance(type='spot', suffix='USDT'):
    '''
    Fetches symbol list of all matching coins from binance.
    type: 'spot' or 'futures' #change
    suffix: 'USDT' or 'BTC'
    '''
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    symbols = [market.split(':')[0] for market in markets if markets[market]['type'] == type and market.split(':')[0].endswith(f'/{suffix}')]
    return symbols