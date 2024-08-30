import pytest
from data.store.crypto_binance import store_crypto_binance
from utils.db.insert import get_db_connection

def test_store_crypto_binance():
    # Call the function to store data
    store_crypto_binance(timeframe='1d', data_points_back=1, type='spot', suffix='USDT')
    
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify that data was stored in the market table
    cursor.execute("SELECT * FROM market WHERE market_name = 'crypto';")
    market = cursor.fetchone()
    assert market is not None, "Market 'crypto' should be present in the market table."
    
    # Verify that data was stored in the symbols table
    cursor.execute("SELECT * FROM symbols WHERE market_id = ?;", (market[0],))
    symbols = cursor.fetchall()
    assert len(symbols) > 0, "There should be symbols stored in the symbols table for 'crypto'."
    
    # Verify that data was stored in the ohlcv_data table
    cursor.execute("SELECT * FROM ohlcv_data WHERE symbol_id IN (SELECT symbol_id FROM symbols WHERE market_id = ?);", (market[0],))
    ohlcv_data = cursor.fetchall()
    assert len(ohlcv_data) > 0, "There should be OHLCV data stored in the ohlcv_data table for 'crypto'."
    
    # Close the database connection
    conn.close()