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

'''

import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path='config/.env')

# Access the DATABASE_PATH environment variable
database_path = os.getenv('DATABASE_PATH')

# SQL schema definitions
CREATE_MARKET_TABLE = """
CREATE TABLE IF NOT EXISTS market (
    market_id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_name TEXT NOT NULL UNIQUE
);
"""

CREATE_SYMBOLS_TABLE = """
CREATE TABLE IF NOT EXISTS symbols (
    symbol_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    market_id INTEGER,
    FOREIGN KEY (market_id) REFERENCES market (market_id)
);
"""

CREATE_OHLCV_DATA_TABLE = """
CREATE TABLE IF NOT EXISTS ohlcv_data (
    ohlcv_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol_id INTEGER,
    timeframe TEXT NOT NULL,
    timestamp DATETIME,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    FOREIGN KEY (symbol_id) REFERENCES symbols (symbol_id),
    UNIQUE (symbol_id, timeframe, timestamp)
);
"""

# Function to initialize the database
def initialize_database(db_path='database/db/ohlcv_data.db'):
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Execute schema definitions to create tables
    cursor.execute(CREATE_MARKET_TABLE)
    cursor.execute(CREATE_SYMBOLS_TABLE)
    cursor.execute(CREATE_OHLCV_DATA_TABLE)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    print("Database initialized successfully with all required tables.")

# Call the function to initialize the database when the script is run
if __name__ == "__main__":
    initialize_database()
