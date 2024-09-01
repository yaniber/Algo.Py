import pandas as pd
from utils.db.insert import get_db_connection
import time
import diskcache as dc

# Create a cache object
cache = dc.Cache('database/db')

def fetch_entries(market_name=None, timeframe=None, symbol_list=None, all_entries=False):
    '''
    Fetches OHLCV data and technical indicators from the database.
    
    Inputs:
    market_name: str, the name of the market to fetch data for. [example: 'crypto', 'indian_equity', 'all']
    timeframe: str, the timeframe to fetch data for. [example: '1d', '1h', '15m']
    symbol_list: list, the list of symbols to fetch data for.
    all_entries: bool, whether to fetch all entries or not.

    Output:
    A dictionary of pandas DataFrames, where each key is a symbol and each value is a DataFrame of OHLCV data and technical indicators.
    {symbol: pd.DataFrame}
    '''
    # Cache key based on function arguments
    cache_key = (market_name, timeframe, tuple(symbol_list) if symbol_list else None, all_entries, int(time.time() // cache_period(timeframe)))

    # Check if result is in cache
    if cache_key in cache:
        return cache[cache_key]

    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    query = """
    SELECT m.market_name, s.symbol, o.timeframe, o.timestamp, o.open, o.high, o.low, o.close, o.volume,
           ti.indicator_name, ti.indicator_value
    FROM ohlcv_data o
    JOIN symbols s ON o.symbol_id = s.symbol_id
    JOIN market m ON s.market_id = m.market_id
    LEFT JOIN technical_indicators ti ON o.symbol_id = ti.symbol_id AND o.timeframe = ti.timeframe AND o.timestamp = ti.timestamp
    WHERE 1=1
    """

    params = []

    if market_name and market_name.lower() != "all":
        query += " AND m.market_name = ?"
        params.append(market_name)

    if timeframe:
        query += " AND o.timeframe = ?"
        params.append(timeframe)

    if symbol_list and not all_entries:
        query += " AND s.symbol IN ({})".format(','.join('?' for _ in symbol_list))
        params.extend(symbol_list)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    data = {}
    for row in rows:
        market, symbol, timeframe, timestamp, open_, high, low, close, volume, indicator_name, indicator_value = row
        if symbol not in data:
            data[symbol] = []
        # Append the row with a default value for indicator_name and indicator_value if they are None
        data[symbol].append([timestamp, open_, high, low, close, volume, indicator_name or 'None', indicator_value or 0])

    # Convert to DataFrame and pivot indicators
    result = {}
    for symbol, entries in data.items():
        df = pd.DataFrame(entries, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'indicator_name', 'indicator_value'])
        df_pivot = df.pivot_table(index=['timestamp', 'open', 'high', 'low', 'close', 'volume'], columns='indicator_name', values='indicator_value', fill_value=0).reset_index()
        result[symbol] = df_pivot

    conn.close()

    # Store result in cache
    cache[cache_key] = result

    # or Store result in cache with expiration time
    #cache.set(cache_key, result, expire=cache_period(timeframe))

    return result

def cache_period(timeframe):
    if timeframe == '1d':
        return 86400  # 1 day in seconds
    elif timeframe == '1h':
        return 3600  # 1 hour in seconds
    elif timeframe == '15m':
        return 900  # 15 minutes in seconds
    else:
        return 86400  # Default to 1 day

def clear_cache():
    """
    Clears the entire cache.
    """
    cache.clear()
