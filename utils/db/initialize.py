'''
Schema Overview

    Table Name: market
        Columns:
        market_id: INTEGER, PRIMARY KEY, AUTOINCREMENT
        market_name: TEXT, NOT NULL, UNIQUE

    Table Name: symbols
        Columns:
        symbol_id: INTEGER, PRIMARY KEY, AUTOINCREMENT
        symbol: TEXT, NOT NULL, UNIQUE
        market_id: INTEGER, FOREIGN KEY references market(market_id)

    Table Name: ohlcv_data
        Columns:
        ohlcv_id: INTEGER, PRIMARY KEY, AUTOINCREMENT
        symbol_id: INTEGER, FOREIGN KEY references symbols(symbol_id)
        timeframe: TEXT, NOT NULL
        timestamp: DATETIME
        open: REAL
        high: REAL
        low: REAL
        close: REAL
        volume: REAL
    Constraints:
    UNIQUE (symbol_id, timeframe, timestamp)

    Table Name: technical_indicators
        Columns:
        indicator_id: INTEGER, PRIMARY KEY, AUTOINCREMENT
        symbol_id: INTEGER, FOREIGN KEY references symbols(symbol_id)
        timeframe: TEXT, NOT NULL
        timestamp: DATETIME
        indicator_name: TEXT, NOT NULL
        indicator_value: REAL
    Constraints:
    UNIQUE (symbol_id, timeframe, timestamp, indicator_name)
'''

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path='config/.env')

# Access the DATABASE_URL environment variable
database_url = os.getenv('DATABASE_URL')

# SQL schema definitions
CREATE_MARKET_TABLE = """
CREATE TABLE IF NOT EXISTS market (
    market_id SERIAL PRIMARY KEY,
    market_name TEXT NOT NULL UNIQUE
);
"""

CREATE_SYMBOLS_TABLE = """
CREATE TABLE IF NOT EXISTS symbols (
    symbol_id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    market_id INTEGER,
    FOREIGN KEY (market_id) REFERENCES market (market_id) ON DELETE CASCADE
);
"""

CREATE_OHLCV_DATA_TABLE = """
CREATE TABLE IF NOT EXISTS ohlcv_data (
    symbol_id INTEGER,
    timeframe TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    FOREIGN KEY (symbol_id) REFERENCES symbols (symbol_id) ON DELETE CASCADE,
    UNIQUE (symbol_id, timeframe, timestamp)
);
"""

CREATE_TECHNICAL_INDICATORS_TABLE = """
CREATE TABLE IF NOT EXISTS technical_indicators (
    symbol_id INTEGER,
    timeframe TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    indicator_name TEXT NOT NULL,
    indicator_value REAL,
    FOREIGN KEY (symbol_id) REFERENCES symbols (symbol_id) ON DELETE CASCADE,
    UNIQUE (symbol_id, timeframe, timestamp, indicator_name)
);
"""

# SQL commands for TimescaleDB features (run separately)
TIMESCALEDB_SETUP_OHLCV = """
SELECT create_hypertable('ohlcv_data', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
ALTER TABLE ohlcv_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol_id, timeframe'
);
SELECT add_compression_policy('ohlcv_data', INTERVAL '1 day');
"""

TIMESCALEDB_SETUP_TECH_INDICATORS = """
SELECT create_hypertable('technical_indicators', 'timestamp', if_not_exists => TRUE, migrate_data => TRUE);
ALTER TABLE technical_indicators SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol_id, timeframe'
);
SELECT add_compression_policy('technical_indicators', INTERVAL '1 day');
"""

# Function to initialize the database
def initialize_database(db_url=database_url):
    # Connect to PostgreSQL database
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # Execute schema definitions to create tables
    cursor.execute(CREATE_MARKET_TABLE)
    cursor.execute(CREATE_SYMBOLS_TABLE)
    cursor.execute(CREATE_OHLCV_DATA_TABLE)
    cursor.execute(CREATE_TECHNICAL_INDICATORS_TABLE)

    # Commit table creation
    conn.commit()

    # Execute TimescaleDB specific commands separately
    cursor.execute(TIMESCALEDB_SETUP_OHLCV)
    cursor.execute(TIMESCALEDB_SETUP_TECH_INDICATORS)

    # Commit and close connection
    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialized successfully with all required tables.")

# Call the function to initialize the database when the script is run
if __name__ == "__main__":
    initialize_database()
