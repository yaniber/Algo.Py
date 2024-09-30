import sqlite3
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(dotenv_path='config/.env')

# Database path from the .env file
DATABASE_PATH = os.getenv('DATABASE_PATH')
BACKUP_PATH = DATABASE_PATH + '.backup'
from utils.db.insert import get_db_connection

def check_for_gaps(market_name, timeframe):
    pass

def check_for_duplicates(market_name, timeframe):
    pass

def check_for_missing_data(market_name, timeframe):
    pass

def check_for_out_of_sync(market_name, timeframe):
    pass

def check_for_missing_technical_indicators(market_name, timeframe):
    pass

def check_technical_indicator_sync(market_name, timeframe):
    pass


def backup_database():
    # Perform backup
    # Original database connection
    conn = get_db_connection()
    # Backup database connection
    backup_conn = sqlite3.connect(BACKUP_PATH)
    with backup_conn:
        conn.backup(backup_conn)

    backup_conn.close()
    conn.close()


def recover_database():
    # Perform recovery
    # Backup database connection
    backup_conn = sqlite3.connect(BACKUP_PATH)
    # Original database connection
    conn = get_db_connection()
    with conn:
        backup_conn.backup(conn)

    backup_conn.close()
    conn.close()


if __name__ == "__main__":
    #backup_database()
    # Uncomment the following line to recover the database
    recover_database()