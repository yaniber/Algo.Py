import pandas as pd
import time
from utils.flows.fetch_calculate_insert import fetch_calculate_and_insert
from utils.calculation.indicators import calculate_ema, calculate_supertrend, calculate_spike, detect_large_gap, calculate_average_volume, calculate_exponential_regression
from utils.calculation.supertrend import faster_supertrend
from utils.calculation.slope_r2 import calculate_exponential_regression_optimized
from utils.calculation.optimized_indicators import calculate_spike_optimized, detect_large_gap_optimized, calculate_average_volume_optimized


def calculate_technical_indicators(market_name, timeframe='1d'):
    '''
    One time run function for calculating all custom indicators for a given market.
    Calculates and saves the indicator results into database.
    '''
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_ema, length=100)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_ema, length=200)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=faster_supertrend, period=7, multiplier=3)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_exponential_regression_optimized, window=90)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_exponential_regression_optimized, window=30)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_exponential_regression_optimized, window=15)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_spike_optimized, lookback_period=90, spike_threshold=0.15)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=detect_large_gap_optimized, lookback_period=90, gap_threshold=0.15)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_average_volume_optimized, lookback_period=90)

if __name__ == "__main__":
    _start = time.time()
    calculate_technical_indicators(market_name='indian_equity', timeframe='1d')
    _end_time = time.time()
    print(f"Time taken: {_end_time - _start} seconds")
