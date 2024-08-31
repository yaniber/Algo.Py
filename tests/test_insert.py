import pytest
import pandas as pd
from utils.db.insert import insert_data, get_db_connection, insert_market_if_not_exists, insert_symbol_if_not_exists

@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        'timestamp': [
            '2021-01-01 00:00:00',
            '2021-01-02 00:00:00',
            '2021-01-03 00:00:00',
            '2021-01-04 00:00:00',
            '2021-01-05 00:00:00'
        ],
        'open': [100, 101, 102, 103, 104],
        'high': [110, 111, 112, 113, 114],
        'low': [90, 91, 92, 93, 94],
        'close': [105, 106, 107, 108, 109],
        'volume': [1000, 1100, 1200, 1300, 1400]
    })

@pytest.fixture
def sample_indicators_dataframe():
    return pd.DataFrame({
        'timestamp': [
            '2021-01-01 00:00:00',
            '2021-01-02 00:00:00',
            '2021-01-03 00:00:00',
            '2021-01-04 00:00:00',
            '2021-01-05 00:00:00'
        ],
        'indicator_name': ['ema', 'ema', 'ema', 'ema', 'ema'],
        'indicator_value': [105, 106, 107, 108, 109]
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

def test_insert_data_with_indicators(sample_dataframe, sample_indicators_dataframe):
    market_name = "Test Market"
    symbol_name = "TEST"
    timeframe = "1d"
    
    insert_data(market_name, symbol_name, timeframe, sample_dataframe, indicators=True, indicators_df=sample_indicators_dataframe)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM market WHERE market_name = ?", (market_name,))
    market = cursor.fetchone()
    assert market is not None
    
    cursor.execute("SELECT * FROM symbols WHERE symbol = ?", (symbol_name,))
    symbol = cursor.fetchone()
    assert symbol is not None
    
    cursor.execute("SELECT * FROM technical_indicators WHERE symbol_id = ? AND timeframe = ?", (symbol[0], timeframe))
    technical_indicators = cursor.fetchone()
    assert technical_indicators is not None
    
    conn.close()