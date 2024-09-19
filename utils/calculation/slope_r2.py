import numpy as np
import pandas as pd
from numba import njit , prange
#import vectorbtpro as vbt
from utils.decorators import result_df_decorator

@njit
def calculate_slope_r2(x, y):
    n = len(x)
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_xx = np.sum(x * x)
    
    denominator = (n * sum_xx - sum_x * sum_x)
    if denominator == 0 or n==0:
        return np.nan, np.nan  # Return NaN if division by zero would occur
    
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    
    y_pred = slope * x + intercept
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    ss_res = np.sum((y - y_pred) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    
    return slope, r2

@njit
def calculate_slope_r2_rolling(log_close, window):
    n = len(log_close)
    slopes = np.empty(n)
    r2_values = np.empty(n)
    slopes[:] = np.nan
    r2_values[:] = np.nan
    
    for i in range(window - 1, n):
        y = log_close[i-window+1:i+1]
        x = np.arange(window)
        slope, r2 = calculate_slope_r2(x, y)
        slopes[i] = slope
        r2_values[i] = r2
    
    return slopes, r2_values

@result_df_decorator(lambda window: f'slope_r2_product_{window}')
def calculate_exponential_regression_optimized(df, window=90):
    log_close = np.log(df['close'].values)
    slopes, r2_values = calculate_slope_r2_rolling(log_close, window)
    
    slope_r2_product = slopes * r2_values
    return pd.Series(slope_r2_product, index=df.index)

""" # If you want to use vectorbtpro for even more performance, you can use this alternative implementation:
@result_df_decorator(lambda window: f'slope_r2_product_{window}')
def calculate_exponential_regression_vbt(df, window=90):
    log_close = np.log(df['close'].values)
    
    @njit
    def slope_r2_func_nb(close):
        x = np.arange(len(close))
        slope, r2 = calculate_slope_r2(x, close)
        return slope * r2
    
    slope_r2_product = vbt.generic.nb.rolling_apply_nb(
        log_close,
        window,
        slope_r2_func_nb
    )
    
    return pd.Series(slope_r2_product, index=df.index) """

