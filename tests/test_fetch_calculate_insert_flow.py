import pytest
from utils.flows.indicators_calculate_insert import fetch_calculate_and_insert
from utils.db.fetch import fetch_entries
from utils.calculation.ema import calculate_ema
from utils.db.insert import get_db_connection

def test_fetch_calculate_and_insert():
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
    fetch_calculate_and_insert(
        market_name='Test Market',
        timeframe='1d',
        calculation_func=calculate_ema,
        length=20
    )
    
    # Verify the results
    cursor.execute("""
        SELECT * FROM technical_indicators
        WHERE symbol_id = ? AND timeframe = '1d'
    """, (symbol_id,))
    technical_indicators = cursor.fetchall()
    
    assert len(technical_indicators) > 0, "Technical indicators should be inserted into the database."
    
    # Clean up the database
    cursor.execute("DELETE FROM technical_indicators WHERE symbol_id = ?", (symbol_id,))
    cursor.execute("DELETE FROM ohlcv_data WHERE symbol_id = ?", (symbol_id,))
    cursor.execute("DELETE FROM symbols WHERE symbol = 'TEST'")
    cursor.execute("DELETE FROM market WHERE market_name = 'Test Market'")
    conn.commit()
    conn.close()

