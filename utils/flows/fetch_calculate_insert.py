import os
import pandas as pd
from utils.db.fetch import fetch_entries, fetch_ohlcv_data
from utils.db.insert import insert_data, get_db_connection
from utils.calculation.indicators import calculate_ema
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import concurrent.futures
from dotenv import load_dotenv
from utils.db.batch import BatchInserter
from utils.decorators import cache_decorator

load_dotenv(dotenv_path='config/.env')
database_path = os.getenv('DATABASE_PATH')


def process_symbol(batch_inserter, symbol, df, market_name, timeframe, calculation_func, calculation_kwargs):
    """
    This function processes data for each symbol and inserts it into the database.
    It is designed to be run in parallel (multiprocessing).
    
    Args:
    symbol (str): Symbol name.
    df (pd.DataFrame): OHLCV data DataFrame.
    market_name (str): Market name.
    timeframe (str): Timeframe (e.g., '1d', '1h').
    calculation_func (callable): Function to calculate indicators.
    calculation_kwargs (dict): Keyword arguments for the indicator calculation function.
    """
    
    # Perform indicator calculations
    try:
        indicator_df = calculation_func(df, **calculation_kwargs) 
    except Exception as e:
        print(f"Error calculating {calculation_func.__name__}: {e}")
        return
    # Insert the data into the database
    insert_data(batch_inserter, market_name=market_name, symbol_name=symbol, timeframe=timeframe, df=indicator_df, indicators=True, indicators_df=indicator_df)

def fetch_calculate_and_insert(market_name, timeframe, start_timestamp, all_entries, symbol_list, calculation_func, **calculation_kwargs):
    '''
    Runs the input calculate function across the given market & timeframe and inserts the result into database.
    Multi processes the calculation function for each symbol.

    Input:
    market_name: str [Example : 'indian_equity']
    timeframe: str [Example : '1d']
    calculation_func: function [Example : calculate_ema]
    calculation_kwargs: dict [Example : length=50]
    '''
    
    batch_inserter = BatchInserter(database_path=database_path, table='technical_indicators')
    #ohlcv_data = fetch_entries(batch_inserter, market_name=market_name, timeframe=timeframe, start_timestamp=start_timestamp, all_entries=True)
    ohlcv_data = fetch_ohlcv_data(batch_inserter=batch_inserter, market_name=market_name, timeframe=timeframe, start_timestamp=start_timestamp, symbol_list=symbol_list, all_entries=all_entries)
    if not ohlcv_data:
        print(f"No OHLCV data found for market: {market_name} and timeframe: {timeframe}")
        return

    use_multiprocessing = os.getenv('USE_MULTIPROCESSING', 'True').lower() == 'true'
    use_multiprocessing = False
    if use_multiprocessing:
        with ProcessPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(process_symbol, symbol, df, market_name, timeframe, calculation_func, calculation_kwargs)
                for symbol, df in ohlcv_data.items()
            ]
            for _ in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing symbols"):
                pass  # Wait for all futures to complete
    else:
        for symbol, df in tqdm(ohlcv_data.items(), desc="Processing symbols"):
            process_symbol(batch_inserter, symbol, df, market_name, timeframe, calculation_func, calculation_kwargs)
        batch_inserter.stop()

    print(f"{calculation_func.__name__} calculation and insertion completed for market: {market_name} and timeframe: {timeframe}")

if __name__ == "__main__":
    fetch_calculate_and_insert(
        market_name='indian_equity',
        timeframe='1d',
        calculation_func=calculate_ema,
        length=20
    )