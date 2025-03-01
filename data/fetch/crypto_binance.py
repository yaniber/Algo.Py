import ccxt
import pandas as pd
from datetime import datetime
import time

def fetch_ohlcv_binance(symbol, timeframe, start_date):
    """Optimized version that matches original's data inclusion behavior"""
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    since = int(start_date.timestamp() * 1000)
    all_data = []
    max_retries = 5
    backoff_factor = 1

    while True:
        ohlcv = []
        for attempt in range(max_retries):
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
                break
            except ccxt.RateLimitExceeded:
                sleep_time = backoff_factor * (2 ** attempt)
                time.sleep(sleep_time)
            except Exception as e:
                print(f"Error on {symbol}: {str(e)}")
                ohlcv = []
                break
        
        if not ohlcv:
            break

        all_data.extend(ohlcv)

        # Update 'since' to one millisecond after the last timestamp fetched.
        last_timestamp = ohlcv[-1][0]
        new_since = last_timestamp + 1
        if new_since == since:
            break
        since = new_since

    # Convert the accumulated data into a DataFrame.
    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
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