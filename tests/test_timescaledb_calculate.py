import pytest
import pandas as pd
from utils.db.insert import get_db_connection, insert_data

@pytest.fixture(scope="module")
def db_connection():
    conn = get_db_connection()
    yield conn
    conn.close()

def test_insert_frequently_accessed_indicator(db_connection):
    # Create test data
    market_name = "Test Market"
    symbol_name = "TEST"
    timeframe = "1d"
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
    
    # Insert data
    insert_data(market_name, symbol_name, timeframe, df)
    
    # Verify data insertion
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT * FROM ohlcv_data WHERE symbol_id = (
            SELECT symbol_id FROM symbols WHERE symbol = %s
        );
    """, (symbol_name,))
    rows = cursor.fetchall()
    assert len(rows) == 2
    
    # Clean up
    cursor.execute("DELETE FROM ohlcv_data WHERE symbol_id = (SELECT symbol_id FROM symbols WHERE symbol = %s);", (symbol_name,))
    cursor.execute("DELETE FROM symbols WHERE symbol = %s;", (symbol_name,))
    cursor.execute("DELETE FROM market WHERE market_name = %s;", (market_name,))
    db_connection.commit()
    cursor.close()
