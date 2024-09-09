import pytest
import pandas as pd
from utils.db.update import add_column_if_not_exists, get_db_connection
from utils.db.insert import insert_data, insert_symbol_if_not_exists, insert_market_if_not_exists
from utils.db.fetch import fetch_entries

@pytest.fixture(scope="module")
def db_connection():
    conn = get_db_connection()
    yield conn
    conn.close()

def test_add_column_and_insert_data(db_connection):
    cursor = db_connection.cursor()
    
    # Add a new column
    add_column_if_not_exists('ohlcv_data', 'new_column', 'REAL')
    
    # Check if the column was added
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='ohlcv_data' AND column_name='new_column';
    """)
    assert cursor.fetchone() is not None
    
    # Insert test data
    df = pd.DataFrame({
        'timestamp': ['2023-01-01 00:00:00', '2023-01-01 01:00:00'],
        'open': [100.0, 101.0],
        'high': [102.0, 103.0],
        'low': [99.0, 100.0],
        'close': [101.0, 102.0],
        'volume': [1000, 1500],
        'new_column': [1.1, 1.2]
    })
    
    market_name = 'Test Market'
    symbol_name = 'Test Symbol'
    timeframe = '1h'
    
    # Ensure market exists and get market_id
    market_id = insert_market_if_not_exists(db_connection, market_name)
    
    # Ensure symbol exists and get symbol_id
    symbol_id = insert_symbol_if_not_exists(db_connection, symbol_name, market_id)
    
    # Insert data
    insert_data(market_name, symbol_name, timeframe, df)
    
    # Fetch data using fetch_entries
    fetched_data = fetch_entries(market_name=market_name, timeframe=timeframe, symbol_list=[symbol_name])
    
    # Check if the data was fetched correctly
    assert symbol_name in fetched_data
    fetched_df = fetched_data[symbol_name]
    assert len(fetched_df) == 2
    
    # Clean up
    cursor.execute("ALTER TABLE ohlcv_data DROP COLUMN new_column;")
    cursor.execute("DELETE FROM ohlcv_data WHERE symbol_id=%s AND timeframe=%s;", (symbol_id, timeframe))
    db_connection.commit()
    cursor.close()
