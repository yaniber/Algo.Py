import sqlite3
import time
import random
from datetime import datetime, timedelta
import gc
from utils.db.batch import BatchInserter  # Import BatchInserter
import pandas as pd
import numpy as np

# Database file
DATABASE_FILE = 'database/db/perf_test.db'

def create_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Configure database before creating tables
    configure_database(cursor)
    
    # Define table creation SQL statements
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
    
    CREATE_TECHNICAL_INDICATORS_TABLE = """
    CREATE TABLE IF NOT EXISTS technical_indicators (
        indicator_id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol_id INTEGER,
        timeframe TEXT NOT NULL,
        timestamp DATETIME,
        indicator_name TEXT NOT NULL,
        indicator_value REAL,
        FOREIGN KEY (symbol_id) REFERENCES symbols (symbol_id),
        UNIQUE (symbol_id, timeframe, timestamp, indicator_name)
    );
    """
    
    # Create tables
    cursor.execute(CREATE_MARKET_TABLE)
    cursor.execute(CREATE_SYMBOLS_TABLE)
    cursor.execute(CREATE_OHLCV_DATA_TABLE)
    cursor.execute(CREATE_TECHNICAL_INDICATORS_TABLE)
    
    conn.commit()
    conn.close()
    print("Database and tables created successfully.")

def configure_database(cursor):
    # Adjust PRAGMA settings
    cursor.execute('PRAGMA journal_mode = OFF;')
    cursor.execute('PRAGMA synchronous = 0;')
    cursor.execute('PRAGMA cache_size = 1000000;')  # give it a GB
    cursor.execute('PRAGMA locking_mode = EXCLUSIVE;')
    cursor.execute('PRAGMA temp_store = MEMORY;')

def populate_markets_and_symbols():
    """
    Populates the 'market' and 'symbols' tables with sample data.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    configure_database(cursor)
    
    markets = ['NYSE', 'NASDAQ', 'AMEX', 'LSE', 'JPX']
    symbols = [f'SYM{i}' for i in range(1, 101)]  # SYM1 to SYM100
    
    cursor.execute('BEGIN TRANSACTION')
    
    # Insert markets
    market_ids = {}
    for market_name in markets:
        cursor.execute("INSERT OR IGNORE INTO market (market_name) VALUES (?)", (market_name,))
        cursor.execute("SELECT market_id FROM market WHERE market_name = ?", (market_name,))
        market_id = cursor.fetchone()[0]
        market_ids[market_name] = market_id
    
    # Insert symbols, randomly assigning them to markets
    for symbol in symbols:
        market_name = random.choice(markets)
        market_id = market_ids[market_name]
        cursor.execute("INSERT OR IGNORE INTO symbols (symbol, market_id) VALUES (?, ?)", (symbol, market_id))
    
    conn.commit()
    conn.close()
    print("Markets and symbols populated successfully.")

def insert_ohlcv_data():
    conn_start = time.time()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    conn_time = time.time() - conn_start

    configure_database(cursor)

    # Get symbol_ids
    cursor.execute("SELECT symbol_id FROM symbols")
    symbol_ids = [row[0] for row in cursor.fetchall()]

    # Data generation parameters
    timeframes = ['1m', '5m', '15m', '1h', '1d']
    total_rows = 500000
    batch_size = 100000
    inserted_rows = 0
    data_batch = []
    current_timestamp = datetime(2020, 1, 1)
    delta = timedelta(seconds=1)
    total_gen_time = timedelta(seconds=0)
    total_insert_time = timedelta(seconds=0)
    total_loop_time = timedelta(seconds=0)
    total_gc_time = timedelta(seconds=0)

    cursor.execute('BEGIN TRANSACTION')
    print("Starting insertion into 'ohlcv_data' table...")
    start_time = time.time()
    time_per_100 = start_time

    while inserted_rows < total_rows:
        loop_start = time.time()
        remaining_rows = total_rows - inserted_rows
        current_batch_size = min(batch_size, remaining_rows)

        # Data generation timing
        data_gen_start = time.time()
        for _ in range(current_batch_size):
            symbol_id = random.choice(symbol_ids)
            timeframe = random.choice(timeframes)
            timestamp = current_timestamp.strftime('%Y-%m-%d %H:%M:%S')
            open_price = random.uniform(100, 200)
            high_price = open_price + random.uniform(0, 10)
            low_price = open_price - random.uniform(0, 10)
            close_price = random.uniform(low_price, high_price)
            volume = random.uniform(1000, 10000)
            data_batch.append((
                symbol_id,
                timeframe,
                timestamp,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            ))
            current_timestamp += delta
        data_gen_time = time.time() - data_gen_start
        total_gen_time += timedelta(seconds=data_gen_time)  # Convert to timedelta

        # Data insertion timing
        insert_start = time.time()
        cursor.executemany("""
            INSERT INTO ohlcv_data (symbol_id, timeframe, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data_batch)
        insert_time = time.time() - insert_start
        total_insert_time += timedelta(seconds=insert_time)  # Convert to timedelta

        inserted_rows += len(data_batch)
        data_batch = []

        # Garbage collection timing
        gc_start = time.time()
        gc.collect()
        gc_time = time.time() - gc_start
        total_gc_time += timedelta(seconds=gc_time)

        loop_time = time.time() - loop_start
        total_loop_time += timedelta(seconds=loop_time)

        
        if inserted_rows % 100000 == 0 or inserted_rows == total_rows:
            elapsed_time = time.time() - time_per_100
            print(f"Inserted {inserted_rows}/{total_rows} rows into 'ohlcv_data' in {elapsed_time:.2f} seconds (Data Gen: {data_gen_time:.2f}s, Insert: {insert_time:.2f}s, Loop: {loop_time:.2f}s, GC: {gc_time:.2f}s)")
            time_per_100 = time.time()

    commit_start = time.time()
    conn.commit()
    commit_time = time.time() - commit_start

    total_time = time.time() - start_time
    print(f"Inserted total {inserted_rows} rows into 'ohlcv_data' in {total_time} seconds (Conn: {conn_time}s, Data Gen: {total_gen_time}, Insert: {total_insert_time}, Loop: {total_loop_time}, GC: {total_gc_time}, Commit: {commit_time}s)")
    conn.close()

def insert_technical_indicators():
    """
    Inserts 20 million rows into the 'technical_indicators' table and measures performance.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Get symbol_ids
    cursor.execute("SELECT symbol_id FROM symbols")
    symbol_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Data generation parameters
    timeframes = ['1m', '5m', '15m', '1h', '1d']
    indicator_names = ['SMA', 'EMA', 'RSI', 'MACD', 'BollingerBands']
    total_rows = 20000000
    num_rows_per_combination = total_rows // (len(symbol_ids) * len(timeframes) * len(indicator_names))
    
    batch_inserter = BatchInserter(DATABASE_FILE)  # Initialize BatchInserter
    inserted_rows = 0
    start_time = time.time()
    total_gen_time = timedelta(seconds=0)
    
    print("Starting insertion into 'technical_indicators' table...")
    
    for symbol_id in symbol_ids:
        for timeframe in timeframes:
            for indicator_name in indicator_names:
                current_timestamp = datetime(2020, 1, 1)
                delta = timedelta(minutes=1)
                for _ in range(num_rows_per_combination):
                    data_gen_start = time.time()
                    record = {
                        'timestamp': current_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'indicator_name': indicator_name,
                        'indicator_value': random.uniform(0, 100)
                    }
                    batch_inserter.enqueue_record(symbol_id, timeframe, record)
                    current_timestamp += delta
                    data_gen_time = time.time() - data_gen_start
                    total_gen_time += timedelta(seconds=data_gen_time)  # Convert to timedelta
                    inserted_rows += 1
                    if inserted_rows % 1000000 == 0:
                        elapsed_time = time.time() - start_time
                        print(f"Enqueued {inserted_rows}/{total_rows} rows into 'technical_indicators' in {elapsed_time} seconds (Data Gen: {total_gen_time}s)")

    # Signal the BatchInserter to stop and wait for it to finish
    batch_inserter.stop()
    
    total_time = time.time() - start_time
    print(f"Enqueued total {inserted_rows} rows into 'technical_indicators' in {total_time} seconds (Data Gen: {total_gen_time}s)")

def insert_technical_indicators_from_dataframe():
    """
    Inserts 20 million rows into the 'technical_indicators' table using DataFrame and measures performance.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Get symbol_ids
    cursor.execute("SELECT symbol_id FROM symbols")
    symbol_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Data generation parameters
    timeframes = ['1m', '5m', '15m', '1h', '1d']
    indicator_names = ['SMA', 'EMA', 'RSI', 'MACD', 'BollingerBands']
    total_rows = 20000000
    num_rows_per_combination = total_rows // (len(symbol_ids) * len(timeframes) * len(indicator_names))
    
    batch_inserter = BatchInserter(DATABASE_FILE)  # Initialize BatchInserter
    start_time = time.time()
    total_gen_time = timedelta(seconds=0)
    
    print("Starting insertion into 'technical_indicators' table using DataFrame...")
    
    for symbol_id in symbol_ids:
        for timeframe in timeframes:
            for indicator_name in indicator_names:
                current_timestamp = datetime(2020, 1, 1)
                delta = timedelta(minutes=1)
                
                # Vectorized data generation
                data_gen_start = time.time()
                timestamps = [current_timestamp + i * delta for i in range(num_rows_per_combination)]
                indicator_values = np.random.uniform(0, 100, num_rows_per_combination)
                
                df = pd.DataFrame({
                    'timestamp': [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps],
                    'indicator_name': [indicator_name] * num_rows_per_combination,
                    'indicator_value': indicator_values
                })

                data_gen_time = time.time() - data_gen_start
                total_gen_time += timedelta(seconds=data_gen_time)  # Convert to timedelta
                
                batch_inserter.enqueue_dataframe(symbol_id, timeframe, df)
    
    # Signal the BatchInserter to stop and wait for it to finish
    batch_inserter.stop()
    
    total_time = time.time() - start_time
    print(f"Enqueued total {total_rows} rows into 'technical_indicators' using DataFrame in {total_time} seconds (Data Gen: {total_gen_time}s)")

def main():
    # Step 1: Create database and tables
    create_database()
    
    # Step 2: Populate markets and symbols
    populate_markets_and_symbols()
    
    # Step 3: Insert 50 million rows into 'ohlcv_data' table
    insert_ohlcv_data()
    
    # Step 4: Perform performance test on 'technical_indicators' table
    #insert_technical_indicators()
    
    # Step 5: Perform performance test on 'technical_indicators' table using DataFrame
    insert_technical_indicators_from_dataframe()

if __name__ == "__main__":
    main()