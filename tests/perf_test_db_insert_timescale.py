import os
import psycopg
import multiprocessing
import time
import random
from datetime import datetime, timedelta

# Load DATABASE_URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

def connect_to_db():
    """
    Creates a new database connection using DATABASE_URL.
    """
    conn = psycopg.connect(DATABASE_URL)
    return conn

def create_database():
    """
    Connects to TimescaleDB and creates the required tables and hypertables.
    """
    conn = connect_to_db()
    cursor = conn.cursor()

    # Enable required extensions
    cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
    cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")  # If needed

    # Create tables
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
        FOREIGN KEY (market_id) REFERENCES market (market_id)
    );
    """

    CREATE_OHLCV_DATA_TABLE = """
    CREATE TABLE IF NOT EXISTS ohlcv_data (
        symbol_id INTEGER,
        timeframe TEXT NOT NULL,
        timestamp TIMESTAMPTZ NOT NULL,
        open NUMERIC,
        high NUMERIC,
        low NUMERIC,
        close NUMERIC,
        volume NUMERIC,
        FOREIGN KEY (symbol_id) REFERENCES symbols (symbol_id)
    );
    """

    CREATE_TECHNICAL_INDICATORS_TABLE = """
    CREATE TABLE IF NOT EXISTS technical_indicators (
        symbol_id INTEGER,
        timeframe TEXT NOT NULL,
        timestamp TIMESTAMPTZ NOT NULL,
        indicator_name TEXT NOT NULL,
        indicator_value NUMERIC,
        FOREIGN KEY (symbol_id) REFERENCES symbols (symbol_id)
    );
    """

    cursor.execute(CREATE_MARKET_TABLE)
    cursor.execute(CREATE_SYMBOLS_TABLE)
    cursor.execute(CREATE_OHLCV_DATA_TABLE)
    cursor.execute(CREATE_TECHNICAL_INDICATORS_TABLE)

    # Create hypertables
    cursor.execute("SELECT create_hypertable('ohlcv_data', 'timestamp', if_not_exists => TRUE);")
    cursor.execute("SELECT create_hypertable('technical_indicators', 'timestamp', if_not_exists => TRUE);")

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timeframe ON ohlcv_data (symbol_id, timeframe);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_technical_symbol_timeframe ON technical_indicators (symbol_id, timeframe);")

    conn.commit()
    conn.close()
    print("Database and tables created successfully.")

def populate_markets_and_symbols():
    """
    Populates the 'market' and 'symbols' tables with sample data.
    """
    conn = connect_to_db()
    cursor = conn.cursor()

    markets = ['NYSE', 'NASDAQ', 'AMEX', 'LSE', 'JPX']
    symbols = [f'SYM{i}' for i in range(1, 101)]  # SYM1 to SYM100

    # Insert markets
    market_ids = {}
    for market_name in markets:
        cursor.execute("INSERT INTO market (market_name) VALUES (%s) RETURNING market_id;", (market_name,))
        market_id = cursor.fetchone()[0]
        market_ids[market_name] = market_id

    # Insert symbols, randomly assigning them to markets
    symbol_data = [(symbol, market_ids[random.choice(markets)]) for symbol in symbols]

    insert_query = "INSERT INTO symbols (symbol, market_id) VALUES (%s, %s)"
    cursor.executemany(insert_query, symbol_data)

    conn.commit()
    conn.close()
    print("Markets and symbols populated successfully.")

def insert_ohlcv_data():
    """
    Inserts 50 million rows into the 'ohlcv_data' table using parallel processing.
    """
    total_rows = 50000000
    num_processes = 8  # Adjust based on available cores
    rows_per_process = total_rows // num_processes

    processes = []
    for process_id in range(num_processes):
        p = multiprocessing.Process(target=insert_ohlcv_data_chunk, args=(rows_per_process, process_id))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

def insert_ohlcv_data_chunk(rows_to_insert, process_id):
    """
    Inserts a chunk of data into the 'ohlcv_data' table.
    """
    conn = connect_to_db()
    cursor = conn.cursor()

    # Get symbol_ids
    cursor.execute("SELECT symbol_id FROM symbols")
    symbol_ids = [row[0] for row in cursor.fetchall()]

    # Data generation parameters
    timeframes = ['1m', '5m', '15m', '1h', '1d']
    batch_size = 100000  # Adjust based on memory
    inserted_rows = 0
    current_timestamp = datetime(2020, 1, 1) + timedelta(days=process_id)
    delta = timedelta(minutes=1)  # Adjust as needed

    print(f"Process {process_id} starting insertion into 'ohlcv_data' table...")
    start_time = time.time()

    while inserted_rows < rows_to_insert:
        remaining_rows = rows_to_insert - inserted_rows
        current_batch_size = min(batch_size, remaining_rows)

        # Data generation
        data_gen_start_time = time.time()
        data_batch = []
        for _ in range(current_batch_size):
            symbol_id = random.choice(symbol_ids)
            timeframe = random.choice(timeframes)
            timestamp = current_timestamp
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
        data_gen_end_time = time.time()

        # Batch insert using COPY
        insert_start_time = time.time()
        with cursor.copy("COPY ohlcv_data (symbol_id, timeframe, timestamp, open, high, low, close, volume) FROM STDIN") as copy:
            for row in data_batch:
                copy.write_row(row)
        conn.commit()
        insert_end_time = time.time()

        inserted_rows += current_batch_size

        if inserted_rows % 100000 == 0 or inserted_rows == rows_to_insert:
            elapsed_time = insert_end_time - insert_start_time
            print(f"Process {process_id} inserted {inserted_rows}/{rows_to_insert} rows in {elapsed_time:.2f} seconds (excluding data generation time)")
            start_time = time.time()

    conn.close()

def insert_technical_indicators():
    """
    Inserts 200 million rows into the 'technical_indicators' table using parallel processing.
    """
    total_rows = 200000000
    num_processes = 8  # Adjust based on available cores
    rows_per_process = total_rows // num_processes

    processes = []
    for process_id in range(num_processes):
        p = multiprocessing.Process(target=insert_technical_indicators_chunk, args=(rows_per_process, process_id))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

def insert_technical_indicators_chunk(rows_to_insert, process_id):
    """
    Inserts a chunk of data into the 'technical_indicators' table.
    """
    conn = connect_to_db()
    cursor = conn.cursor()

    # Get symbol_ids
    cursor.execute("SELECT symbol_id FROM symbols")
    symbol_ids = [row[0] for row in cursor.fetchall()]

    # Data generation parameters
    timeframes = ['1m', '5m', '15m', '1h', '1d']
    indicator_names = ['SMA', 'EMA', 'RSI', 'MACD', 'BollingerBands']
    batch_size = 100000
    inserted_rows = 0
    current_timestamp = datetime(2020, 1, 1) + timedelta(days=process_id)
    delta = timedelta(minutes=1)  # Adjust as needed

    print(f"Process {process_id} starting insertion into 'technical_indicators' table...")
    start_time = time.time()

    while inserted_rows < rows_to_insert:
        remaining_rows = rows_to_insert - inserted_rows
        current_batch_size = min(batch_size, remaining_rows)

        # Data generation
        data_gen_start_time = time.time()
        data_batch = []
        for _ in range(current_batch_size):
            symbol_id = random.choice(symbol_ids)
            timeframe = random.choice(timeframes)
            timestamp = current_timestamp
            for indicator_name in indicator_names:
                indicator_value = random.uniform(0, 100)
                data_batch.append((
                    symbol_id,
                    timeframe,
                    timestamp,
                    indicator_name,
                    indicator_value
                ))
            current_timestamp += delta
        data_gen_end_time = time.time()

        # Batch insert using COPY
        insert_start_time = time.time()
        with cursor.copy("COPY technical_indicators (symbol_id, timeframe, timestamp, indicator_name, indicator_value) FROM STDIN") as copy:
            for row in data_batch:
                copy.write_row(row)
        conn.commit()
        insert_end_time = time.time()

        inserted_rows += current_batch_size

        if inserted_rows % 100000 == 0 or inserted_rows == rows_to_insert:
            elapsed_time = insert_end_time - insert_start_time
            print(f"Process {process_id} inserted {inserted_rows}/{rows_to_insert} rows in {elapsed_time:.2f} seconds (excluding data generation time)")
            start_time = time.time()

    conn.close()

def main():
    # Step 1: Create database and tables
    create_database()

    # Step 2: Populate markets and symbols
    populate_markets_and_symbols()

    # Step 3: Insert 50 million rows into 'ohlcv_data' table
    insert_ohlcv_data()

    # Step 4: Perform performance test on 'technical_indicators' table
    insert_technical_indicators()

if __name__ == "__main__":
    main()
