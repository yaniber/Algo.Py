import os
import pandas as pd
from utils.db.fetch import fetch_entries
from utils.db.insert import insert_data
from utils.calculation.indicators import calculate_ema
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import concurrent.futures
from dotenv import load_dotenv

load_dotenv(dotenv_path='config/.env')

def process_symbol(symbol, df, market_name, timeframe, calculation_func, calculation_kwargs):
    indicator_df = calculation_func(df, **calculation_kwargs)
    insert_data(market_name=market_name, symbol_name=symbol, timeframe=timeframe, df=indicator_df, indicators=True, indicators_df=indicator_df)

def fetch_calculate_and_insert(market_name, timeframe, calculation_func, **calculation_kwargs):
    '''
    Runs the input calculate function across the given market & timeframe and inserts the result into database.
    Multi processes the calculation function for each symbol.

    Input:
    market_name: str [Example : 'indian_equity']
    timeframe: str [Example : '1d']
    calculation_func: function [Example : calculate_ema]
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
                executor.submit(process_symbol, symbol, df, market_name, timeframe, calculation_func, calculation_kwargs)
                for symbol, df in ohlcv_data.items()
            ]
            for _ in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing symbols"):
                pass  # Wait for all futures to complete
    else:
        for symbol, df in tqdm(ohlcv_data.items(), desc="Processing symbols"):
            process_symbol(symbol, df, market_name, timeframe, calculation_func, calculation_kwargs)

    print(f"{calculation_func.__name__} calculation and insertion completed for market: {market_name} and timeframe: {timeframe}")

if __name__ == "__main__":
    fetch_calculate_and_insert(
        market_name='indian_equity',
        timeframe='1d',
        calculation_func=calculate_ema,
        length=20
    )