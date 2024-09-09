from data.fetch.indian_equity import fetch_ohlcv_indian_equity, fetch_symbol_list_indian_equity
from tqdm import tqdm
import diskcache as dc
import time

# Create a cache object
cache = dc.Cache('database/db')

def gather_ohlcv_indian_equity(timeframe='1d', start_date=None, complete_list=False):
    '''
    Gathers OHLCV data from Binance for all symbols that match the given type and suffix.

    timeframe: '1d', '1h', '15m', '5m', '1m'
    start_date: datetime object
    complete_list: True or False

    Output:
    data: dict of {symbol: df}
    '''
    
    # Cache key based on function arguments
    cache_key = (timeframe, start_date, complete_list, int(time.time() // cache_period(timeframe)))

    # Check if result is in cache
    if cache_key in cache:
        return cache[cache_key]

    symbols = fetch_symbol_list_indian_equity(complete_list)
    data = {symbol: df for symbol in tqdm(symbols) if (df := fetch_ohlcv_indian_equity(symbol, timeframe, start_date)) is not None}
    
    # Store result in cache
    cache[cache_key] = (symbols, data)

    return symbols, data

def cache_period(timeframe):
    if timeframe == '1d':
        return 86400  # 1 day in seconds
    elif timeframe == '1h':
        return 3600  # 1 hour in seconds
    elif timeframe == '15m':
        return 900  # 15 minutes in seconds
    else:
        return 86400  # Default to 1 day