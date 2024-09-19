"""
This is a template for a store function.
You need to implement the gather function and the fetch functions in order for this to work.

Pipeline overview:
fetch -> gather -> store -> calculate
"""

### Required Imports

from data.gather._gather_template import gather_ohlcv
from utils.db.insert import insert_data
from utils.calculation.time import calculate_start_time
from tqdm import tqdm
from utils.db.batch import BatchInserter
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv(dotenv_path='config/.env')

# Access the DATABASE_PATH environment variable
database_path = os.getenv('DATABASE_PATH')


def store_your_data_source(timeframe='1y', data_points_back=1, complete_list=False):

    """
    Stores OHLCV data for a specific data source into the database.

    This function implements the following steps:
    1. Calculates the start time based on the given timeframe and number of data points.
    2. Calls the gather_ohlcv function to retrieve symbols and their corresponding OHLCV data.
    3. Initializes a BatchInserter for efficient database insertion.
    4. Iterates through each symbol, inserting its data into the database.
    5. Handles exceptions during insertion and reports errors.
    6. Closes the BatchInserter after all insertions are complete.

    The function expects the gather_ohlcv function to return:
    - A list of symbols
    - A dictionary where keys are symbols and values are pandas DataFrames containing OHLCV data ex = {'AAPL': df, 'GOOGL': df}

    It then uses the insert_data function to store each symbol's data, utilizing the BatchInserter
    for improved performance.

    Parameters:
    timeframe (str): The timeframe for the data (e.g., '1d', '1h', '1y'). Default is '1y'.
    data_points_back (int): Number of data points to fetch back in time. Default is 1.
    complete_list (bool): Whether to fetch the complete list of symbols. Default is False.

    Note:
    - The 'your_market_name' in insert_data should be replaced with the actual market name.
    - Ensure that the gather_ohlcv function is properly implemented to provide the expected data format.
    - The BatchInserter is used to optimize database insertions for large datasets.
    """
    
    start_time = calculate_start_time(timeframe, data_points_back)
    timeframe = timeframe if timeframe != '1y' else '1d'
    symbols, data = gather_ohlcv(timeframe=timeframe, start_date=start_time, complete_list=complete_list)
    batch_inserter = BatchInserter(database_path=database_path, table='ohlcv_data')

    for symbol in tqdm(symbols):
        try:
            insert_data(batch_inserter=batch_inserter, market_name='your_market_name', symbol_name=symbol, timeframe=timeframe, df=data[symbol])
        except Exception as e:
            print(f"Error storing {symbol}: {e}")
            continue
    batch_inserter.stop()