import pytest
import psycopg2
from utils.db.initialize import (
    CREATE_MARKET_TABLE,
    CREATE_SYMBOLS_TABLE,
    CREATE_OHLCV_DATA_TABLE,
    CREATE_TECHNICAL_INDICATORS_TABLE,
    TIMESCALEDB_SETUP_OHLCV,
    TIMESCALEDB_SETUP_TECH_INDICATORS
)
from utils.db.update import get_db_connection

@pytest.fixture(scope="module")
def db_connection():
    conn = get_db_connection()
    yield conn
    conn.close()

def test_initialize_db(db_connection):
    cursor = db_connection.cursor()
    
    # Create tables
    cursor.execute(CREATE_MARKET_TABLE)
    cursor.execute(CREATE_SYMBOLS_TABLE)
    cursor.execute(CREATE_OHLCV_DATA_TABLE)
    cursor.execute(CREATE_TECHNICAL_INDICATORS_TABLE)
    db_connection.commit()
    
    # Execute TimescaleDB specific commands
    cursor.execute(TIMESCALEDB_SETUP_OHLCV)
    cursor.execute(TIMESCALEDB_SETUP_TECH_INDICATORS)
    db_connection.commit()
    
    # Check if tables were created
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name IN ('market', 'symbols', 'ohlcv_data', 'technical_indicators');
    """)
    tables = cursor.fetchall()
    assert len(tables) == 4
    
    # Clean up
    cursor.execute("DROP TABLE technical_indicators;")
    cursor.execute("DROP TABLE ohlcv_data;")
    cursor.execute("DROP TABLE symbols;")
    cursor.execute("DROP TABLE market;")
    db_connection.commit()
    cursor.close()