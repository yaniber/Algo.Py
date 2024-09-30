import pandas as pd
import time
from utils.flows.fetch_calculate_insert import fetch_calculate_and_insert
from utils.calculation.indicators import calculate_ema, calculate_supertrend, calculate_spike, detect_large_gap, calculate_average_volume, calculate_exponential_regression
from utils.calculation.supertrend import faster_supertrend
from utils.calculation.slope_r2 import calculate_exponential_regression_optimized
from utils.calculation.optimized_indicators import calculate_spike_optimized, detect_large_gap_optimized, calculate_average_volume_optimized
from dotenv import load_dotenv
import os
import traceback

# Load environment variables from .env file
load_dotenv(dotenv_path='config/.env')

# Access the DATABASE_PATH environment variable
database_path = os.getenv('DATABASE_PATH')

def calculate_technical_indicators(market_name, start_timestamp, all_entries, symbol_list, timeframe='1d'):
    '''
    One time run function for calculating all custom indicators for a given market.
    Calculates and saves the indicator results into database.
    '''
    try:
        fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, start_timestamp=start_timestamp, all_entries=all_entries, symbol_list=symbol_list, calculation_func=calculate_ema, length=100)
        fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, start_timestamp=start_timestamp, all_entries=all_entries, symbol_list=symbol_list, calculation_func=calculate_ema, length=200)
        fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, start_timestamp=start_timestamp, all_entries=all_entries, symbol_list=symbol_list, calculation_func=faster_supertrend, period=7, multiplier=3)
        fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, start_timestamp=start_timestamp, all_entries=all_entries, symbol_list=symbol_list, calculation_func=calculate_exponential_regression_optimized, window=90)
        fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, start_timestamp=start_timestamp, all_entries=all_entries, symbol_list=symbol_list, calculation_func=calculate_exponential_regression_optimized, window=30)
        fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, start_timestamp=start_timestamp, all_entries=all_entries, symbol_list=symbol_list, calculation_func=calculate_exponential_regression_optimized, window=15)
        fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, start_timestamp=start_timestamp, all_entries=all_entries, symbol_list=symbol_list, calculation_func=calculate_spike_optimized, lookback_period=90, spike_threshold=0.15)
        fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, start_timestamp=start_timestamp, all_entries=all_entries, symbol_list=symbol_list, calculation_func=detect_large_gap_optimized, lookback_period=90, gap_threshold=0.15)
        fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, start_timestamp=start_timestamp, all_entries=all_entries, symbol_list=symbol_list, calculation_func=calculate_average_volume_optimized, lookback_period=90)
    except Exception as e:
        print(f"Error calculating technical indicators: {e}")
        print(f"Full traceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    _start = time.time()
    calculate_technical_indicators(market_name='indian_equity', start_timestamp=None, all_entries=True, symbol_list=None, timeframe='1d')
    _end_time = time.time()
    print(f"Time taken: {_end_time - _start} seconds")
