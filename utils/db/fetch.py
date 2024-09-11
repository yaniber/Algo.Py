import pandas as pd
from utils.db.insert import get_db_connection
import time
from utils.decorators import cache_decorator

@cache_decorator()
def fetch_entries(market_name=None, timeframe=None, symbol_list=None, all_entries=False, infrequently_accessed_indicators=False):
    '''
    Fetches OHLCV data and technical indicators from the database.
    
    Inputs:
    market_name: str, the name of the market to fetch data for. [example: 'crypto', 'indian_equity', 'all']
    timeframe: str, the timeframe to fetch data for. [example: '1d', '1h', '15m']
    symbol_list: list, the list of symbols to fetch data for.
    all_entries: bool, whether to fetch all entries or not.
    infrequently_accessed_indicators: bool, whether to join with the technical_indicators table.

    Output:
    A dictionary of pandas DataFrames, where each key is a symbol and each value is a DataFrame of OHLCV data and technical indicators.
    {symbol: pd.DataFrame}
    '''
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    query = """
    SELECT m.market_name, s.symbol, o.timeframe, o.timestamp, o.open, o.high, o.low, o.close, o.volume
    """

    if infrequently_accessed_indicators:
        query += ", ti.indicator_name, ti.indicator_value"

    query += """
    FROM ohlcv_data o
    JOIN symbols s ON o.symbol_id = s.symbol_id
    JOIN market m ON s.market_id = m.market_id
    """

    if infrequently_accessed_indicators:
        query += """
        LEFT JOIN technical_indicators ti ON o.symbol_id = ti.symbol_id AND o.timeframe = ti.timeframe AND o.timestamp = ti.timestamp
        """

    query += " WHERE 1=1"

    params = []

    if market_name and market_name.lower() != "all":
        query += " AND m.market_name = %s"
        params.append(market_name)

    if timeframe:
        query += " AND o.timeframe = %s"
        params.append(timeframe)

    if symbol_list and not all_entries:
        query += " AND s.symbol IN ({})".format(','.join('%s' for _ in symbol_list))
        params.extend(symbol_list)

    _start_time = time.time()
    cursor.execute(query, params)
    _end_time = time.time()
    print(f"Time taken for cursor.execute: {_end_time - _start_time} seconds")
    rows = cursor.fetchall()

    data = {}
    for row in rows:
        if infrequently_accessed_indicators:
            market, symbol, timeframe, timestamp, open_, high, low, close, volume, indicator_name, indicator_value = row
        else:
            market, symbol, timeframe, timestamp, open_, high, low, close, volume = row
            indicator_name, indicator_value = 'None', 0

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

    return result

