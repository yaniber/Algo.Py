import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path='config/.env')

# Database URL from the .env file
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def add_column_if_not_exists(table_name, column_name, column_type):
    """Add a column to a table if it does not already exist."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Check if the column already exists
    cursor.execute(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='{table_name}' AND column_name='{column_name}';
    """)
    
    if cursor.fetchone() is None:
        # Column does not exist, so add it
        cursor.execute(f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_type};
        """)
        conn.commit()
        print(f"Column '{column_name}' added to table '{table_name}'.")
    else:
        print(f"Column '{column_name}' already exists in table '{table_name}', skipping.")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    # Example usage
    add_column_if_not_exists('ohlcv_data', 'ema', 'REAL')
    add_column_if_not_exists('ohlcv_data', 'sma', 'REAL')
