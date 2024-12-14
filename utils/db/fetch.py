import pandas as pd
import sys 
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db.insert import get_db_connection
from finstore.finstore import Finstore
import time
from utils.decorators import cache_decorator
from tqdm import tqdm

def fetch_in_batches(cursor, query, params, batch_size, last_id=None):
    with tqdm(desc="Fetching batches") as pbar:
        while True:
            paginated_query = query
            current_params = params.copy()  # Create a copy of the original params
            if last_id is not None:
                paginated_query += f" AND o.ohlcv_id > ?"
                current_params.append(last_id)
            paginated_query += f" ORDER BY o.ohlcv_id LIMIT {batch_size}"
            cursor.execute(paginated_query, current_params)
            rows = cursor.fetchall()
            if not rows:
                break
            yield rows
            last_id = rows[-1][0]  # Assuming the first column is the unique ID
            pbar.update(len(rows))

#@cache_decorator(expire=60*60*24*30)
def fetch_entries(batch_inserter=None, market_name=None, timeframe=None, symbol_list=None, all_entries=False, start_timestamp=None, batch_size=500000, storage_system='finstore', pair=''):
    '''
    Fetches OHLCV data and technical indicators from the database.
    
    Inputs:
    market_name: str, the name of the market to fetch data for. [example: 'crypto', 'indian_equity', 'all']
    timeframe: str, the timeframe to fetch data for. [example: '1d', '1h', '15m']
    symbol_list: list, the list of symbols to fetch data for.
    all_entries: bool, whether to fetch all entries or not.
    start_timestamp: str, the start timestamp to fetch data from. format : 'YYYY-MM-DD HH:MM:SS'
    batch_size: int, the number of rows to fetch in each batch.

    Output:
    A dictionary of pandas DataFrames, where each key is a symbol and each value is a DataFrame of OHLCV data and technical indicators.
    {symbol: pd.DataFrame}
    '''

    if storage_system == 'sqlite':
        if batch_inserter:
            conn = batch_inserter.conn
        else:
            conn = get_db_connection()
        if not conn:
            return None

        cursor = conn.cursor()

        query = """
        SELECT o.ohlcv_id, m.market_name, s.symbol, o.timeframe, o.timestamp, o.open, o.high, o.low, o.close, o.volume,
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
        
        if start_timestamp:
            query += " AND o.timestamp >= ?"
            params.append(start_timestamp)

        result = {}

        last_id = None
        for rows in fetch_in_batches(cursor, query, params, batch_size, last_id):
            data = {}
            for row in rows:
                id_, market, symbol, timeframe, timestamp, open_, high, low, close, volume, indicator_name, indicator_value = row
                if symbol not in data:
                    data[symbol] = []
                data[symbol].append([timestamp, open_, high, low, close, volume, indicator_name or 'None', indicator_value or 0])

            # Convert to DataFrame and pivot indicators
            for symbol, entries in data.items():
                df = pd.DataFrame(entries, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'indicator_name', 'indicator_value'])
                df_pivot = df.pivot_table(index=['timestamp', 'open', 'high', 'low', 'close', 'volume'], columns='indicator_name', values='indicator_value', fill_value=0).reset_index()
                if symbol in result:
                    result[symbol] = pd.concat([result[symbol], df_pivot])
                else:
                    result[symbol] = df_pivot

        if not batch_inserter:
            conn.close()

        return result
    
    elif storage_system == 'finstore':
        finstore = Finstore(market_name=market_name, timeframe=timeframe, enable_append=True, pair=pair)
        symbols = finstore.read.get_symbol_list()
        merged_dataframe = finstore.read.symbol_list(symbol_list=symbols, merged_dataframe=True)
        return merged_dataframe

#@cache_decorator(expire=60*60*24*30)
def fetch_ohlcv_data(batch_inserter=None, market_name=None, timeframe=None, symbol_list=None, all_entries=False, start_timestamp=None, batch_size=500000):
    '''
    Fetches OHLCV data and technical indicators from the database.
    
    Inputs:
    market_name: str, the name of the market to fetch data for. [example: 'crypto', 'indian_equity', 'all']
    timeframe: str, the timeframe to fetch data for. [example: '1d', '1h', '15m']
    symbol_list: list, the list of symbols to fetch data for.
    all_entries: bool, whether to fetch all entries or not.
    start_timestamp: str, the start timestamp to fetch data from. format : 'YYYY-MM-DD HH:MM:SS'
    batch_size: int, the number of rows to fetch in each batch.

    Output:
    A dictionary of pandas DataFrames, where each key is a symbol and each value is a DataFrame of OHLCV data and technical indicators.
    {symbol: pd.DataFrame}
    '''

    if batch_inserter:
        conn = batch_inserter.conn
    else:
        conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()

    query = """
    SELECT o.ohlcv_id, m.market_name, s.symbol, o.timeframe, o.timestamp, o.open, o.high, o.low, o.close, o.volume
    FROM ohlcv_data o
    JOIN symbols s ON o.symbol_id = s.symbol_id
    JOIN market m ON s.market_id = m.market_id
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
    
    if start_timestamp:
        query += " AND o.timestamp >= ?"
        params.append(start_timestamp)

    result = {}

    last_id = None
    for rows in fetch_in_batches(cursor, query, params, batch_size, last_id):
        data = {}
        for row in rows:
            id_, market, symbol, timeframe, timestamp, open_, high, low, close, volume = row
            if symbol not in data:
                data[symbol] = []
            data[symbol].append([timestamp, open_, high, low, close, volume])

        # Convert to DataFrame and pivot indicators
        for symbol, entries in data.items():
            df = pd.DataFrame(entries, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            result[symbol] = df

    if not batch_inserter:
        conn.close()

    return result

def fetch_ohlcv_data_for_symbol(symbol, market_name, timeframe, period=500):
    '''
    Fetch the last `period` OHLCV data points from the database for the given symbol and timeframe.

    Args:
    - symbol (str): The symbol to fetch data for.
    - market_name (str): The market name (e.g., 'indian_equity').
    - timeframe (str): The timeframe for the OHLCV data (e.g., '1d').
    - period (int): The number of most recent data points to fetch (default: 500).

    Returns:
    - DataFrame: The OHLCV data for the given symbol.
    '''
    
    query = f'''
        SELECT o.timestamp, o.open, o.high, o.low, o.close, o.volume
        FROM ohlcv_data o
        JOIN symbols s ON o.symbol_id = s.symbol_id
        JOIN market m ON s.market_id = m.market_id
        WHERE s.symbol = ? AND m.market_name = ? AND o.timeframe = ?
        ORDER BY o.timestamp DESC
        LIMIT ?
    '''
    params = (symbol, market_name, timeframe, period)
    
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # Sort data by timestamp ascending order
    df = df.sort_values(by='timestamp')
    return df

def fetch_latest_date(market_name=None, timeframe=None, storage_system = 'finstore', pair=''):
    '''
    Fetches the latest date for a given market and timeframe.
    
    Inputs:
    market_name: str, the name of the market to fetch data for. [example: 'crypto', 'indian_equity', 'all']
    timeframe: str, the timeframe to fetch data for. [example: '1d', '1h', '15m']
    symbol_list: list, the list of symbols to fetch data for.

    Output:
    date: str, the latest date for the given market and timeframe.
    '''

    if storage_system == 'sqlite':
        conn = get_db_connection()
        if not conn:
            return None

        cursor = conn.cursor()

        cursor.execute("""
        SELECT market_id
        FROM market
        WHERE market_name = ?
        """, (market_name,))

        market_id = cursor.fetchone()[0]

        cursor.execute("""
        SELECT MAX(symbol_id)
        FROM symbols
        WHERE market_id = ?
        """, (market_id,))

        symbol_id = cursor.fetchone()[0]

        cursor.execute("""
        SELECT MIN(max_timestamp) FROM (
            SELECT MAX(timestamp) as max_timestamp
            FROM ohlcv_data
            WHERE timeframe = ?
            GROUP BY symbol_id
        ) subquery
        """, (timeframe,))
        
        timestamp = cursor.fetchone()[0]
        timestamp = pd.to_datetime(timestamp)
        conn.close()

        return timestamp
    
    elif storage_system == 'finstore':

        finstore = Finstore(market_name=market_name, timeframe=timeframe, enable_append=True, pair=pair)
        symbols = finstore.read.get_symbol_list()
        ohlcv_data = finstore.read.symbol_list(symbol_list=symbols)
    
        latest_timestamps = {}
        for symbol, df in ohlcv_data.items():
            if not df.empty:
                latest_timestamps[symbol] = df['timestamp'].max()

        latest_timestamps_series = pd.Series(latest_timestamps)
        min_latest_timestamp = latest_timestamps_series.min()

        return pd.to_datetime(min_latest_timestamp)


def fetch_latest_technical_indicator_timestamp(symbol_id, timeframe):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(timestamp) FROM technical_indicators
        WHERE symbol_id = ? AND timeframe = ?
    """, (symbol_id, timeframe))
    latest_timestamp = cursor.fetchone()[0]
    conn.close()
    return latest_timestamp