import pandas as pd
from utils.flows.fetch_calculate_insert import fetch_calculate_and_insert, fetch_calculate_and_insert_with_batching
from utils.calculation.indicators import calculate_ema, calculate_supertrend, calculate_spike, detect_large_gap, calculate_average_volume, calculate_exponential_regression

def calculate_technical_indicators(market_name, timeframe='1d'):
    """
    Optimized function to calculate and insert technical indicators in batches.
    """
    calculations = [
        {'calculation_func': calculate_ema, 'calculation_kwargs': {'length': 100}, 'frequently_accessed': True},
        {'calculation_func': calculate_ema, 'calculation_kwargs': {'length': 200}, 'frequently_accessed': True},
        {'calculation_func': calculate_supertrend, 'calculation_kwargs': {'atr_multiplier': 3.0, 'length': 10}, 'frequently_accessed': True},
        {'calculation_func': calculate_exponential_regression, 'calculation_kwargs': {'window': 90}, 'frequently_accessed': True},
        {'calculation_func': calculate_exponential_regression, 'calculation_kwargs': {'window': 30}, 'frequently_accessed': True},
        {'calculation_func': calculate_exponential_regression, 'calculation_kwargs': {'window': 15}, 'frequently_accessed': True},
        {'calculation_func': calculate_spike, 'calculation_kwargs': {'lookback_period': 90, 'spike_threshold': 0.15}, 'frequently_accessed': True},
        {'calculation_func': detect_large_gap, 'calculation_kwargs': {'lookback_period': 90, 'gap_threshold': 0.15}, 'frequently_accessed': True},
        {'calculation_func': calculate_average_volume, 'calculation_kwargs': {'lookback_period': 90}, 'frequently_accessed': True},
    ]

    # Fetch data once and calculate all indicators in batch
    fetch_calculate_and_insert_with_batching(market_name, timeframe, calculations)


if __name__ == "__main__":
    calculate_technical_indicators("indian_equity", "1d")