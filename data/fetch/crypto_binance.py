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
    max_retries = 5  # Increased from 3
    backoff_factor = 1

    for attempt in range(max_retries):
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
            # Always return DataFrame even if empty
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
            return df  # Return even if empty
            
        except ccxt.RateLimitExceeded:
            sleep_time = backoff_factor * (2 ** attempt)
            time.sleep(sleep_time)
        except Exception as e:
            print(f"Error on {symbol}: {str(e)}")
            return pd.DataFrame()  # Return empty DF on non-rate errors

    # After max retries return empty DataFrame instead of None
    return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

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