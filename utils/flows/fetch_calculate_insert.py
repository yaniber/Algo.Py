import os
import pandas as pd
from utils.db.fetch import fetch_entries
from utils.db.insert import insert_data, add_column_if_not_exists
from utils.calculation.indicators import calculate_ema
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import concurrent.futures
from dotenv import load_dotenv

load_dotenv(dotenv_path='config/.env')

def process_symbol(symbol, df, market_name, timeframe, calculation_func, calculation_kwargs, frequently_accessed):
    indicator_df = calculation_func(df, frequently_accessed, **calculation_kwargs)
    insert_data(market_name=market_name, symbol_name=symbol, timeframe=timeframe, df=indicator_df, indicators=True, indicators_df=indicator_df, frequently_accessed=frequently_accessed)

def process_symbol_batch(symbol, df, market_name, timeframe, calculations):
    for calc in calculations:
        calculation_func = calc['calculation_func']
        frequently_accessed = calc.get('frequently_accessed', False)
        calculation_kwargs = calc.get('calculation_kwargs', {})
        indicator_df = calculation_func(df, frequently_accessed, **calculation_kwargs)
        insert_data(market_name=market_name, symbol_name=symbol, timeframe=timeframe, df=indicator_df, indicators=True, indicators_df=indicator_df, frequently_accessed=frequently_accessed)

def fetch_calculate_and_insert(market_name, timeframe, frequently_accessed, calculation_func, **calculation_kwargs):
    '''
    Runs the input calculate function across the given market & timeframe and inserts the result into database.
    Multi processes the calculation function for each symbol.

    Input:
    market_name: str [Example : 'indian_equity']
    timeframe: str [Example : '1d']
    calculation_func: function [Example : calculate_ema]
    frequently_accessed: bool [True if the indicator is frequently accessed]
    calculation_kwargs: dict [Example : length=50]
    '''
    ohlcv_data = fetch_entries(market_name=market_name, timeframe=timeframe, all_entries=True)
    if not ohlcv_data:
        print(f"No OHLCV data found for market: {market_name} and timeframe: {timeframe}")
        return

    use_multiprocessing = os.getenv('USE_MULTIPROCESSING', 'True').lower() == 'true'

    if use_multiprocessing:
        with ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(process_symbol, symbol, df, market_name, timeframe, calculation_func, calculation_kwargs, frequently_accessed)
                for symbol, df in ohlcv_data.items()
            ]
            for _ in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing symbols"):
                pass  # Wait for all futures to complete
    else:
        for symbol, df in tqdm(ohlcv_data.items(), desc="Processing symbols"):
            process_symbol(symbol, df, market_name, timeframe, calculation_func, calculation_kwargs, frequently_accessed)

    print(f"{calculation_func.__name__} calculation and insertion completed for market: {market_name} and timeframe: {timeframe}")

def fetch_calculate_and_insert_with_batching(market_name, timeframe, calculations):
    """
    Fetch data once, then calculate all indicators for efficiency.
    """
    ohlcv_data = fetch_entries(market_name=market_name, timeframe=timeframe, all_entries=True)
    if not ohlcv_data:
        print(f"No OHLCV data found for market: {market_name} and timeframe: {timeframe}")
        return

    use_multiprocessing = os.getenv('USE_MULTIPROCESSING', 'True').lower() == 'true'

    if use_multiprocessing:
        with ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(process_symbol_batch, symbol, df, market_name, timeframe, calculations)
                for symbol, df in ohlcv_data.items()
            ]
            for _ in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing symbols"):
                pass  # Wait for all futures to complete
    else:
        for symbol, df in tqdm(ohlcv_data.items(), desc="Processing symbols"):
            process_symbol_batch(symbol, df, market_name, timeframe, calculations)

    print(f"Batch calculation and insertion completed for market: {market_name} and timeframe: {timeframe}")

if __name__ == "__main__":
    fetch_calculate_and_insert(
        market_name='indian_equity',
        timeframe='1d',
        calculation_func=calculate_ema,
        length=20
    )