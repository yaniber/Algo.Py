import pytest
from data.calculate.indian_equity import calculate_technical_indicators
from utils.db.insert import get_db_connection
from utils.db.fetch import fetch_entries
import time

def test_calculate_technical_indicators():
    # Ensure the database is in a known state before the test
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert test data into the database
    cursor.execute("INSERT OR IGNORE INTO market (market_name) VALUES ('Test Market')")
    cursor.execute("INSERT OR IGNORE INTO symbols (symbol, market_id) VALUES ('TEST', (SELECT market_id FROM market WHERE market_name = 'Test Market'))")
    symbol_id = cursor.execute("SELECT symbol_id FROM symbols WHERE symbol = 'TEST'").fetchone()[0]
    
    ohlcv_data = [
        ('2021-01-01 00:00:00', 100, 110, 90, 105, 1000),
        ('2021-01-02 00:00:00', 101, 111, 91, 106, 1100),
        ('2021-01-03 00:00:00', 102, 112, 92, 107, 1200),
        ('2021-01-04 00:00:00', 103, 113, 93, 108, 1300),
        ('2021-01-05 00:00:00', 104, 114, 94, 109, 1400)
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO ohlcv_data (symbol_id, timeframe, timestamp, open, high, low, close, volume)
        VALUES (?, '1d', ?, ?, ?, ?, ?, ?)
    """, [(symbol_id, *row) for row in ohlcv_data])
    
    conn.commit()
    
    # Run the function to be tested
    calculate_technical_indicators(market_name='Test Market', timeframe='1d')
    
    # Check if there are any entries for slope_r2_product_90
    cursor.execute("SELECT timestamp, indicator_name FROM technical_indicators WHERE indicator_name = 'slope_r2_product_90' AND symbol_id = ?", (symbol_id,))
    slope_r2_entries = cursor.fetchall()
    assert len(slope_r2_entries) > 0, "There should be entries for slope_r2_product_90."

    # Check the type of timestamp in the fetched entries
    #for entry in slope_r2_entries:
    #    timestamp, slope_r2_value = entry
    #    assert isinstance(timestamp, str), "Timestamp should be of type string."
    #    assert isinstance(slope_r2_value, float), "slope_r2_product_90 should be of type float."

    # Use fetch_entries to get both OHLCV data and technical indicators
    result = fetch_entries(market_name='Test Market', timeframe='1d', symbol_list=['TEST'], all_entries=False)
    
    assert 'TEST' in result, "Symbol 'TEST' should be in the result."
    df = result['TEST']
    
    # Verify the technical indicators were inserted
    assert not df.empty, "DataFrame should not be empty."
    time.sleep(15)
    
    # Verify field types
    assert df['timestamp'].dtype == 'object'  # timestamp should be string
    assert df['open'].dtype == 'float64'  # open should be float
    assert df['high'].dtype == 'float64'  # high should be float
    assert df['low'].dtype == 'float64'  # low should be float
    assert df['close'].dtype == 'float64'  # close should be float
    assert df['volume'].dtype == 'float64'  # volume should be float
    for col in df.columns:
        if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume']:
            assert df[col].dtype == 'float64'  # technical indicators should be float
    
    # Clean up the database
    cursor.execute("DELETE FROM technical_indicators WHERE symbol_id = ?", (symbol_id,))
    cursor.execute("DELETE FROM ohlcv_data WHERE symbol_id = ?", (symbol_id,))
    cursor.execute("DELETE FROM symbols WHERE symbol = 'TEST'")
    cursor.execute("DELETE FROM market WHERE market_name = 'Test Market'")
    conn.commit()
    conn.close()

