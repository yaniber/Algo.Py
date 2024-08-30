import pytest
import sqlite3
from utils.db.initialize import initialize_database
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv(dotenv_path='config/.env')

# Access the DATABASE_PATH environment variable
database_path = os.getenv('DATABASE_PATH')

def test_initialize_database():
    initialize_database()
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='market';")
    market_table = cursor.fetchone()
    assert market_table is not None
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='symbols';")
    symbols_table = cursor.fetchone()
    assert symbols_table is not None
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ohlcv_data';")
    ohlcv_data_table = cursor.fetchone()
    assert ohlcv_data_table is not None
    
    conn.close()