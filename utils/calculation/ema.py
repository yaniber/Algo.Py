import pandas as pd
from utils.decorators import result_df_decorator

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
