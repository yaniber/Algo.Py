import pytest
from data.store.indian_equity import store_indian_equity
from utils.db.insert import get_db_connection

def test_store_indian_equity():
    # Call the function to store data
    store_indian_equity(timeframe='1d', data_points_back=1, complete_list=False)
    
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify that data was stored in the market table
    cursor.execute("SELECT * FROM market WHERE market_name = 'indian_equity';")
    market = cursor.fetchone()
    assert market is not None, "Market 'indian_equity' should be present in the market table."
    
    # Verify that data was stored in the symbols table
    cursor.execute("SELECT * FROM symbols WHERE market_id = ?;", (market[0],))
    symbols = cursor.fetchall()
    assert len(symbols) > 0, "There should be symbols stored in the symbols table for 'indian_equity'."
    
    # Verify that data was stored in the ohlcv_data table
    cursor.execute("SELECT * FROM ohlcv_data WHERE symbol_id IN (SELECT symbol_id FROM symbols WHERE market_id = ?);", (market[0],))
    ohlcv_data = cursor.fetchall()
    assert len(ohlcv_data) > 0, "There should be OHLCV data stored in the ohlcv_data table for 'indian_equity'."
    
    # Close the database connection
    conn.close()