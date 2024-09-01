import pandas as pd
from utils.decorators import result_df_decorator
import pandas_ta as ta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

@result_df_decorator(lambda length: f'ema_{length}')
def calculate_ema(df, length):
    """
    Calculate the Exponential Moving Average (EMA) for a given length.

    Parameters:
    df (pd.DataFrame): DataFrame containing OHLCV data with a 'timestamp' column.
    length (int): The length of the EMA (e.g., 10, 20, 100).

    Returns:
    pd.DataFrame: DataFrame with columns 'timestamp', 'indicator_name', 'indicator_value'.
    """
    ema = df['close'].ewm(span=length, adjust=False).mean()
    return ema

@result_df_decorator(lambda length: f'rsi_{length}')
def calculate_rsi(df, length):
    """
    Calculate the Relative Strength Index (RSI) for a given length using the 'pandas_ta' library.

    Parameters:
    df (pd.DataFrame): DataFrame containing OHLCV data with a 'timestamp' column.
    length (int): The length of the RSI (e.g., 14).

    Returns:
    pd.DataFrame: DataFrame with columns 'timestamp', 'indicator_name', 'indicator_value'.
    """
    rsi = df.ta.rsi(length=length)
    return rsi

@result_df_decorator(lambda length, atr_multiplier: f'supertrend_{length}_{atr_multiplier}')
def calculate_supertrend(df, atr_multiplier=3.0, length=10):
    """
    Calculate Supertrend for a given dataframe using ta library.

    Parameters:
    df (pd.DataFrame): DataFrame with 'high', 'low', 'close' prices.
    atr_period (int): The period for ATR calculation.
    multiplier (float): The multiplier for Supertrend.

    Returns:
    pd.Series: Supertrend values.
    """
    supertrend = ta.supertrend(high=df['high'], low=df['low'], close=df['close'], length=length, multiplier=atr_multiplier)
    column_name = f'SUPERT_{length}_{atr_multiplier}'
    return supertrend[column_name]

@result_df_decorator(lambda length: f'roc_{length}')
def calculate_roc(df, lookback_period):
    return ta.roc(df['close'], length=lookback_period)

@result_df_decorator(lambda lookback_period: f'average_volume_{lookback_period}')
def calculate_average_volume(df,lookback_period):
    df['volume_usdt'] = df['close'] * df['volume']
    return df['volume_usdt'].rolling(window=lookback_period).mean()

@result_df_decorator(lambda window: f'slope_r2_product_{window}')
def calculate_exponential_regression(df, window=90):
    # Convert the timestamp to datetime and set it as the index
    data = df.copy()
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data = data.set_index('timestamp')
    data['log_close'] = np.log(data['close'])
    slopes = []
    r2_values = []
    dates = []

    for end in range(window, len(data) + 1):
        subset = data.iloc[end-window:end]
        X = (subset.index - subset.index.min()).days.values.reshape(-1, 1)
        y = np.log(subset['close']).values

        reg = LinearRegression().fit(X, y)
        slope = reg.coef_[0]
        r2 = r2_score(y, reg.predict(X))

        slopes.append(slope)
        r2_values.append(r2)
        dates.append(subset.index[-1])

    # Create a temporary DataFrame to hold the results
    results_df = pd.DataFrame({'timestamp': dates, f'Slope_{window}': slopes, f'R2_{window}': r2_values})
    results_df.set_index('timestamp', inplace=True)

    # Join the results back to the original data
    data = data.join(results_df, how='left')
    data.reset_index(inplace=True)
    _slope_r2_product = data[f'Slope_{window}'] * data[f'R2_{window}']
    return _slope_r2_product

@result_df_decorator(lambda lookback_period, spike_threshold: f'spike_{lookback_period}_{spike_threshold}')
def calculate_spike(df, lookback_period, spike_threshold=0.5):
    """
    Calculate if there has been a spike of `spike_threshold` or more in the last `lookback_period`.

    Parameters:
    df (pd.DataFrame): DataFrame with 'open' and 'close' prices.
    lookback_period (int): The period to look back for spikes.
    spike_threshold (float): The threshold for spike detection (e.g., 0.5 for 50%).

    Returns:
    pd.Series: Series with 1 if a spike is present, 0 otherwise.
    """
    spikes = pd.Series(0, index=df.index)
    for i in range(lookback_period, len(df)):
        window = df.iloc[i-lookback_period:i]
        if any((window['close'] - window['open']) / window['open'] >= spike_threshold):
            spikes.iloc[i] = 1
        elif any((window['high'] - window['low']) / window['low'] >= spike_threshold*2):
            spikes.iloc[i] = 1
    return spikes

@result_df_decorator(lambda lookback_period, gap_threshold: f'gap_{lookback_period}_{gap_threshold}')
def detect_large_gap(df, lookback_period=90, gap_threshold=0.15):
    """
    Detect if there has been a gap up or gap down greater than the specified threshold
    in the last lookback_period days.

    Parameters:
    df (pd.DataFrame): DataFrame with 'open' and 'close' prices.
    lookback_period (int): The period to look back for gaps.
    gap_threshold (float): The threshold for gap detection (e.g., 0.15 for 15%).

    Returns:
    pd.Series: Series with 1 if a large gap is present, 0 otherwise.
    """
    gaps = pd.Series(0, index=df.index)
    for i in range(1, len(df)):
        if i >= lookback_period:
            window = df.iloc[i-lookback_period:i+1]
            gap_up = (window['open'] - window['close'].shift(1)) / window['close'].shift(1)
            gap_down = (window['open'] - window['close'].shift(1)) / window['close'].shift(1)
            
            if any(gap_up >= gap_threshold) or any(gap_down <= -gap_threshold):
                gaps.iloc[i] = 1
    
    return gaps