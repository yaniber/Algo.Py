import pandas as pd
from utils.flows.fetch_calculate_insert import fetch_calculate_and_insert
from utils.calculation.indicators import calculate_ema, calculate_supertrend, calculate_spike, detect_large_gap, calculate_average_volume, calculate_exponential_regression

def calculate_technical_indicators(market_name, timeframe='1d'):
    '''
    One time run function for calculating all custom indicators for a given market.
    Calculates and saves the indicator results into database.
    '''
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_ema, length=100, frequently_accessed=True)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_ema, length=200, frequently_accessed=True)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_supertrend, atr_multiplier=3.0, length=10, frequently_accessed=False)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_exponential_regression, window=90, frequently_accessed=False)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_exponential_regression, window=30, frequently_accessed=False)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_exponential_regression, window=15, frequently_accessed=False)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_spike, lookback_period=90, spike_threshold=0.15, frequently_accessed=False)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=detect_large_gap, lookback_period=90, gap_threshold=0.15, frequently_accessed=False)
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_average_volume, lookback_period=90, frequently_accessed=False)

if __name__ == "__main__":
    calculate_technical_indicators(market_name='indian_equity', timeframe='1d')
