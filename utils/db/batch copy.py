import sqlite3
import time
from queue import Queue, Empty
import threading

BATCH_SIZE = 100000  # Number of rows to batch before inserting
MAX_RETRIES = 5  # Maximum retries in case of database locking
RETRY_DELAY = 1  # Delay (in seconds) between retries

class BatchInserter:
    def __init__(self, database_path, table):
        """Initialize the BatchInserter with a connection and batch."""
        print(f"initializing batchinserter for table : {table}")
        self.current_batch = []
        self.total_inserted_rows = 0
        self.start_time = time.time()
        self.database_path = database_path
        self.table = table
        self.lock = threading.Lock()
        self.queue = Queue()
        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(target=self._process_queue)
        self.worker_thread.start()

    def _get_new_connection(self):
        """Get a new database connection with retry mechanism."""
        max_retries = 5
        retry_delay = 0.1  # Initial delay in seconds

        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.database_path)
                cursor = conn.cursor()
                cursor.execute('PRAGMA journal_mode = WAL;')  # Use WAL mode
                cursor.execute('PRAGMA synchronous = NORMAL;')  # Balance between performance and safety
                cursor.execute('PRAGMA cache_size = -2000000;')  # Increase cache size (in KB, negative value means size in bytes)
                cursor.execute('PRAGMA locking_mode = NORMAL;')  # Use NORMAL locking mode
                cursor.execute('PRAGMA temp_store = MEMORY;')
                return conn
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    print(f"Attempt {attempt + 1}/{max_retries} - Database is locked, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"Error creating a new connection: {e}")
                    raise
        raise sqlite3.OperationalError("Max retries exceeded: database is locked")

    def _insert_batch(self, batch, table, conn):
        """Insert a batch of records into the database with retry logic."""
        retries = 0
        while retries < MAX_RETRIES:
            try:
                _start_time = time.time()
                with self.lock:
                    cursor = conn.cursor()
                    if table == 'technical_indicators':
                        cursor.executemany("""
                            INSERT OR REPLACE INTO technical_indicators (symbol_id, timeframe, timestamp, indicator_name, indicator_value)
                            VALUES (?, ?, ?, ?, ?);
                        """, batch)
                    elif table == 'ohlcv_data':
                        cursor.executemany("""
                            INSERT OR IGNORE INTO ohlcv_data (symbol_id, timeframe, timestamp, open, high, low, close, volume)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """, batch)
                    conn.commit()
                _end_time = time.time()
                self.total_inserted_rows += len(batch)
                print(f"Inserted {len(batch)} rows in {_end_time - _start_time:.2f} seconds")

                if self.total_inserted_rows % 100000 == 0:
                    elapsed_time = time.time() - self.start_time
                    print(f"Inserted {self.total_inserted_rows} rows in {elapsed_time:.2f} seconds")
                    self.start_time = time.time()

                return  # If successful, break out of the retry loop

            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    retries += 1
                    print(f"Database is locked, retrying {retries}/{MAX_RETRIES}...")
                    time.sleep(RETRY_DELAY)  # Wait before retrying
                else:
                    raise e  # Re-raise non-lock related errors

        print("Max retries reached. Refreshing connection.")
        with self.lock:
            conn.close()
            conn = self._get_new_connection()

    def _process_queue(self):
        """Background thread to process the queue."""
        print('------- Starting Thread ----------')
        conn = self._get_new_connection()  # Create a new connection for this thread
        while not (self.stop_event.is_set() and self.queue.empty()):
            try:
                batch = self.queue.get(timeout=1)
                self._insert_batch(batch, self.table, conn)  # Pass the connection to the insert method
                self.queue.task_done()
            except Empty:
                continue
        conn.close()  # Close the connection when done

    def enqueue_record(self, symbol_id, timeframe, record):
        """Add record to current batch, and insert batch if batch size is reached."""
        self.current_batch.append((symbol_id, timeframe, record['timestamp'], record['indicator_name'], float(record['indicator_value'])))
        if len(self.current_batch) >= BATCH_SIZE:
            self.queue.put(self.current_batch)
            self.current_batch = []

    def chunked_dataframe(self, df, chunk_size):
        """Generator that yields chunks of the DataFrame."""
        num_records = len(df)
        for start in range(0, num_records, chunk_size):
            end = start + chunk_size
            yield df.iloc[start:end]

    def enqueue_dataframe(self, symbol_id, timeframe, df):
        """Process DataFrame in chunks and enqueue for batch insertion."""
        for chunk_df in self.chunked_dataframe(df, BATCH_SIZE):
            batch_entries = zip(
                [symbol_id] * len(chunk_df),
                [timeframe] * len(chunk_df),
                chunk_df['timestamp'],
                chunk_df['indicator_name'],
                chunk_df['indicator_value'].astype(float)
            )
            self.current_batch.extend(batch_entries)

            if len(self.current_batch) >= BATCH_SIZE:
                self.queue.put(self.current_batch)
                self.current_batch = []

        if self.current_batch:
            self.queue.put(self.current_batch)
            self.current_batch = []

    def enqueue_ohlcv_dataframe(self, symbol_id, timeframe, df):
        """Process OHLCV DataFrame in chunks and enqueue for batch insertion."""
        for chunk_df in self.chunked_dataframe(df, BATCH_SIZE):
            batch_entries = zip(
                [symbol_id] * len(chunk_df),
                [timeframe] * len(chunk_df),
                chunk_df['timestamp'],
                chunk_df['open'].astype(float),
                chunk_df['high'].astype(float),
                chunk_df['low'].astype(float),
                chunk_df['close'].astype(float),
                chunk_df['volume'].astype(float)
            )
            self.current_batch.extend(batch_entries)

            if len(self.current_batch) >= BATCH_SIZE:
                self.queue.put(self.current_batch)
                self.current_batch = []

        if self.current_batch:
            self.queue.put(self.current_batch)
            self.current_batch = []

    def get_connection(self):
        """Provide a thread-safe way to access the connection."""
        self.lock.acquire()
        return self.conn

    def release_connection(self):
        """Release the lock after using the connection."""
        self.lock.release()
    
    def stop(self):
        """Insert any remaining records and close connection."""
        print("------------ About to stop this thread.-------------")
        if self.current_batch:
            self.queue.put(self.current_batch)
        self.stop_event.set()
        self.worker_thread.join()        
        with self.lock:
            self.conn.close()
