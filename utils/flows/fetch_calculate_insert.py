import os
import pandas as pd
from utils.db.fetch import fetch_entries, fetch_ohlcv_data, fetch_ohlcv_data_for_symbol
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
    start_timestamp: str [Example : '2024-01-01 00:00:00']
    all_entries: bool [Example : True]
    symbol_list: list [Example : ['SBIN', 'HDFC']]
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

def update_technical_indicators(market_name, symbol_list, timeframe, calculation_func, data_lookback_period=500, **calculation_kwargs):
    '''
    Update the technical indicators for the given market, symbols, and timeframe.

    Args:
    - market_name (str): The market name (e.g., 'indian_equity').
    - symbol_list (list): List of symbols to update indicators for (e.g., ['SBIN', 'HDFC']).
    - timeframe (str): The timeframe for OHLCV data (e.g., '1d').
    - calculation_func (function): The function to calculate the technical indicator (e.g., faster_supertrend).
    - data_lookback_period (int): Number of past data points to consider for recalculating the indicators (default: 500).
    - calculation_kwargs (dict): Any additional keyword arguments for the indicator calculation function.
    '''
    
    batch_inserter = BatchInserter(database_path=database_path, table='technical_indicators')
    
    for symbol in tqdm(symbol_list, desc="Updating technical indicators"):
        # Fetch the last 'period' data points for the given symbol and timeframe
        df = fetch_ohlcv_data_for_symbol(symbol, market_name, timeframe, data_lookback_period)
        
        if df is None or df.empty:
            print(f"No OHLCV data found for {symbol} in {market_name} and {timeframe}")
            continue

        # Perform indicator calculation
        try:
            indicator_df = calculation_func(df, **calculation_kwargs) 
        except Exception as e:
            print(f"Error calculating {calculation_func.__name__} for {symbol}: {e}")
            continue
        
        # Insert or update the calculated indicators in the technical_indicators table
        insert_data(batch_inserter, market_name=market_name, symbol_name=symbol, timeframe=timeframe, df=indicator_df, indicators=True, indicators_df=indicator_df)

    batch_inserter.stop()
    print(f"{calculation_func.__name__} update completed for market: {market_name}, timeframe: {timeframe}")


if __name__ == "__main__":
    fetch_calculate_and_insert(
        market_name='indian_equity',
        timeframe='1d',
        calculation_func=calculate_ema,
        length=20
    )