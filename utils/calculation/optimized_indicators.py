import numpy as np
from numba import njit
import pandas as pd
from utils.decorators import result_df_decorator

@njit
def calculate_spike_numba(open_prices, close_prices, high_prices, low_prices, lookback_period, spike_threshold):
    n = len(open_prices)
    spikes = np.zeros(n)  # Initialize an array of zeros for the spike results

    for i in range(lookback_period, n):
        spike_found = False
        # Check for spike in the lookback window
        for j in range(i - lookback_period, i):
            if (close_prices[j] - open_prices[j]) / open_prices[j] >= spike_threshold:
                spike_found = True
                break  # Exit early if spike is found
            elif (high_prices[j] - low_prices[j]) / low_prices[j] >= spike_threshold * 2:
                spike_found = True
                break

        if spike_found:
            spikes[i] = 1

    return spikes

# Wrapper function for easier use with pandas DataFrames
@result_df_decorator(lambda lookback_period, spike_threshold: f'spike_{lookback_period}_{spike_threshold}')
def calculate_spike_optimized(df, lookback_period, spike_threshold=0.5):
    open_prices = df['open'].values
    close_prices = df['close'].values
    high_prices = df['high'].values
    low_prices = df['low'].values
    
    # Call the Numba-accelerated function
    spike_array = calculate_spike_numba(open_prices, close_prices, high_prices, low_prices, lookback_period, spike_threshold)
    
    # Return as a pandas Series to keep the DataFrame structure
    return pd.Series(spike_array, index=df.index)


@njit
def detect_large_gap_numba(open_prices, close_prices, lookback_period, gap_threshold):
    n = len(open_prices)
    gaps = np.zeros(n)  # Initialize a result array filled with 0s

    for i in range(1, n):
        if i >= lookback_period:
            for j in range(i - lookback_period, i):
                prev_close = close_prices[j]
                curr_open = open_prices[j + 1]

                # Calculate gap up and gap down
                gap = (curr_open - prev_close) / prev_close
                
                if gap >= gap_threshold or gap <= -gap_threshold:
                    gaps[i] = 1
                    break  # Exit early if gap is found

    return gaps

# Wrapper function to work with pandas DataFrame
@result_df_decorator(lambda lookback_period, gap_threshold: f'gap_{lookback_period}_{gap_threshold}')
def detect_large_gap_optimized(df, lookback_period=90, gap_threshold=0.15):
    open_prices = df['open'].values
    close_prices = df['close'].values
    
    # Call the Numba-optimized function
    gaps_array = detect_large_gap_numba(open_prices, close_prices, lookback_period, gap_threshold)
    
    # Convert the result back into a pandas Series
    return pd.Series(gaps_array, index=df.index)


@njit
def calculate_average_volume_numba(close_prices, volumes, lookback_period):
    n = len(close_prices)
    volume_usdt = close_prices * volumes  # Calculate volume in USDT
    average_volumes = np.empty(n)  # Initialize an array to store the rolling average
    average_volumes[:] = np.nan  # Fill with NaN to handle the initial lookback period

    # Compute rolling average volume
    for i in range(lookback_period - 1, n):
        # Calculate the rolling window sum and average
        window_sum = np.sum(volume_usdt[i - lookback_period + 1:i + 1])
        average_volumes[i] = window_sum / lookback_period

    return average_volumes

# Wrapper function for pandas DataFrame usage
@result_df_decorator(lambda lookback_period: f'average_volume_{lookback_period}')
def calculate_average_volume_optimized(df, lookback_period):
    close_prices = df['close'].values
    volumes = df['volume'].values
    
    # Call the Numba-optimized function
    average_volumes_array = calculate_average_volume_numba(close_prices, volumes, lookback_period)
    
    # Return as a pandas Series to keep DataFrame compatibility
    return pd.Series(average_volumes_array, index=df.index)