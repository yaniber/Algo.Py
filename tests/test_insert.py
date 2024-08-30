import pytest
import pandas as pd
from utils.db.insert import insert_data, get_db_connection, insert_market_if_not_exists, insert_symbol_if_not_exists

@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        'timestamp': ['2021-01-01 00:00:00'],
        'open': [100],
        'high': [110],
        'low': [90],
        'close': [105],
        'volume': [1000]
    })

def test_insert_data(sample_dataframe):
    market_name = "Test Market"
    symbol_name = "TEST"
    timeframe = "1d"
    
    insert_data(market_name, symbol_name, timeframe, sample_dataframe)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM market WHERE market_name = ?", (market_name,))
    market = cursor.fetchone()
    assert market is not None
    
    cursor.execute("SELECT * FROM symbols WHERE symbol = ?", (symbol_name,))
    symbol = cursor.fetchone()
    assert symbol is not None
    
    cursor.execute("SELECT * FROM ohlcv_data WHERE symbol_id = ? AND timeframe = ?", (symbol[0], timeframe))
    ohlcv_data = cursor.fetchone()
    assert ohlcv_data is not None
    
    conn.close()