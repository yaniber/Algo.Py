import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from utils.db.update import add_column_if_not_exists

# Load environment variables from .env file
load_dotenv(dotenv_path='config/.env')

# Database URL from the .env file
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def insert_market_if_not_exists(conn, market_name):
    """Insert a market into the market table if it does not exist, and return the market_id."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO market (market_name) VALUES (%s)
        ON CONFLICT (market_name) DO NOTHING;
    """, (market_name,))
    conn.commit()
    
    cursor.execute("""
        SELECT market_id FROM market WHERE market_name = %s;
    """, (market_name,))
    market_id = cursor.fetchone()[0]
    return market_id

def insert_symbol_if_not_exists(conn, symbol_name, market_id):
    """Insert a symbol into the symbols table if it does not exist, and return the symbol_id."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO symbols (symbol, market_id) VALUES (%s, %s)
        ON CONFLICT (symbol) DO NOTHING;
    """, (symbol_name, market_id))
    conn.commit()
    
    cursor.execute("""
        SELECT symbol_id FROM symbols WHERE symbol = %s;
    """, (symbol_name,))
    symbol_id = cursor.fetchone()[0]
    return symbol_id

def insert_ohlcv_data(conn, symbol_id, timeframe, df):
    """Insert OHLCV data into the ohlcv_data table."""
    cursor = conn.cursor()

    # Prepare data for insertion
    ohlcv_records = df.to_records(index=False)  # Convert DataFrame to records for PostgreSQL insertion
    ohlcv_records_list = list(ohlcv_records)

    # Dynamically generate the column names and values
    columns = ['symbol_id', 'timeframe', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
    values = [(symbol_id, timeframe, record['timestamp'], float(record['open']), float(record['high']), float(record['low']), float(record['close']), float(record['volume'])) for record in ohlcv_records_list]

    # Add any additional columns present in the DataFrame
    for col in df.columns:
        if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume']:
            # Ensure the column exists in the table
            add_column_if_not_exists('ohlcv_data', col, 'REAL')
            columns.append(col)
            for i, record in enumerate(ohlcv_records_list):
                values[i] += (float(record[col]),)

    cursor.executemany(f"""
        INSERT INTO ohlcv_data ({', '.join(columns)})
        VALUES ({', '.join(['%s'] * len(columns))})
        ON CONFLICT (symbol_id, timeframe, timestamp) DO NOTHING;
    """, values)
    conn.commit()

def insert_technical_indicators(conn, symbol_id, timeframe, df):
    """Insert technical indicators into the technical_indicators table."""
    cursor = conn.cursor()

    # Prepare data for insertion
    indicator_records = df.to_records(index=False)  # Convert DataFrame to records for PostgreSQL insertion
    indicator_records_list = list(indicator_records)

    cursor.executemany("""
        INSERT INTO technical_indicators (symbol_id, timeframe, timestamp, indicator_name, indicator_value)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (symbol_id, timeframe, timestamp, indicator_name) DO NOTHING;
    """, [(symbol_id, timeframe, record['timestamp'], record['indicator_name'], float(record['indicator_value'])) for record in indicator_records_list])
    
    conn.commit()

def insert_data(market_name, symbol_name, timeframe, df, indicators=False, indicators_df=None, frequently_accessed=False):
    """
    Main function to insert data into the database.
    
    Input:
    market_name: str 
    symbol_name: str
    timeframe: str
    df: pd.DataFrame of format: timestamp, open, high, low, close, volume
    indicators: bool : True if indicators are to be inserted, False if OHLCV data is to be inserted
    indicators_df: pd.DataFrame of format: timestamp, indicator_name, indicator_value
    frequently_accessed: bool : True if the indicator is frequently accessed
    """
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        # Ensure market exists and get market_id
        market_id = insert_market_if_not_exists(conn, market_name)
        
        # Ensure symbol exists and get symbol_id
        symbol_id = insert_symbol_if_not_exists(conn, symbol_name, market_id)
        
        if frequently_accessed:
            for col in indicators_df.columns:
                if col not in ['timestamp']:
                    add_column_if_not_exists('ohlcv_data', col, 'REAL')
            insert_ohlcv_data(conn, symbol_id, timeframe, indicators_df)
        elif indicators:
            insert_technical_indicators(conn, symbol_id, timeframe, indicators_df)
        else:
            # Insert OHLCV data for the symbol
            insert_ohlcv_data(conn, symbol_id, timeframe, df)
        
        print(f"Data for {symbol_name} in {market_name} inserted successfully.")
    except Exception as e:
        print(f"Error inserting data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Example usage
    # Replace the following with actual data fetching logic or input
    market_name = "US Equity"
    symbol_name = "AAPL"
    # Sample DataFrame creation as an example (Replace this with actual data fetching)
    df = pd.DataFrame({
        'timestamp': [1633046400000, 1633046460000],
        'open': [145.1, 145.2],
        'high': [145.5, 145.6],
        'low': [144.9, 145.0],
        'close': [145.3, 145.4],
        'volume': [1000, 2000],
    })
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Sample indicators DataFrame creation as an example (Replace this with actual data fetching)
    indicators_df = pd.DataFrame({
        'timestamp': [1633046400000, 1633046460000],
        'indicator_name': ['rsi', 'rsi'],  # Example infrequently accessed indicator
        'indicator_value': [70.5, 71.0]
    })
    indicators_df['timestamp'] = pd.to_datetime(indicators_df['timestamp'], unit='ms')
    indicators_df['timestamp'] = indicators_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Insert the data into the database
    insert_data(market_name, symbol_name, '1d', df, indicators=True, indicators_df=indicators_df)
