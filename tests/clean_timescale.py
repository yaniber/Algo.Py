import os
import psycopg2

# Load DATABASE_URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

def connect_to_db():
    """
    Creates a new database connection using DATABASE_URL.
    """
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def drop_hypertables():
    """
    Drops all hypertables in the database.
    """
    conn = connect_to_db()
    cursor = conn.cursor()

    # Drop hypertables
    DROP_OHLCV_DATA_HYPERTABLE = "SELECT drop_chunks('ohlcv_data', cascade_to_materializations => true);"
    DROP_TECHNICAL_INDICATORS_HYPERTABLE = "SELECT drop_chunks('technical_indicators', cascade_to_materializations => true);"

    cursor.execute(DROP_OHLCV_DATA_HYPERTABLE)
    cursor.execute(DROP_TECHNICAL_INDICATORS_HYPERTABLE)

    conn.commit()
    conn.close()
    print("All hypertables dropped successfully.")

def drop_tables():
    """
    Drops all tables in the database.
    """
    conn = connect_to_db()
    cursor = conn.cursor()

    # Drop tables
    DROP_OHLCV_DATA_TABLE = "DROP TABLE IF EXISTS ohlcv_data CASCADE;"
    DROP_TECHNICAL_INDICATORS_TABLE = "DROP TABLE IF EXISTS technical_indicators CASCADE;"
    DROP_SYMBOLS_TABLE = "DROP TABLE IF EXISTS symbols CASCADE;"
    DROP_MARKET_TABLE = "DROP TABLE IF EXISTS market CASCADE;"

    cursor.execute(DROP_OHLCV_DATA_TABLE)
    cursor.execute(DROP_TECHNICAL_INDICATORS_TABLE)
    cursor.execute(DROP_SYMBOLS_TABLE)
    cursor.execute(DROP_MARKET_TABLE)

    conn.commit()
    conn.close()
    print("All tables dropped successfully.")

def drop_database():
    """
    Drops the database.
    """
    # Parse the DATABASE_URL to get the database name
    db_name = DATABASE_URL.split('/')[-1]

    # Connect to the default 'postgres' database to drop the target database
    default_conn = psycopg2.connect(DATABASE_URL.replace(db_name, 'postgres'))
    default_conn.autocommit = True
    cursor = default_conn.cursor()

    # Terminate all connections to the target database
    cursor.execute(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{db_name}'
          AND pid <> pg_backend_pid();
    """)

    # Drop the database
    cursor.execute(f"DROP DATABASE IF EXISTS {db_name};")

    default_conn.close()
    print(f"Database '{db_name}' dropped successfully.")

if __name__ == "__main__":
    #drop_hypertables()
    drop_tables()
    drop_database()