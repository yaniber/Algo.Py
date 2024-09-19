"""
This is a template to start your own data source's pipeline. 

Fetch is the entry point for your pipeline. 
I've tried to keep it as generic as possible to accomodate most of the data sources.

Pipeline overview : 
fetch -> gather -> store -> calculate

"""

# import ccxt
# import pandas as pd
# from datetime import datetime
# import libraries if required to fetch data from your data source

def fetch_ohlcv(symbol, timeframe, start_date):
    """
    Fetches OHLCV (Open, High, Low, Close, Volume) data for a given symbol and timeframe.

    This function should be implemented to retrieve historical price and volume data
    from a specific data source (e.g., an exchange API, database, or data provider).

    Parameters:
    symbol (str): The trading symbol to fetch data for (e.g., 'BTC/USDT').
    timeframe (str): The timeframe of the data (e.g., '1d' for daily, '1h' for hourly).
    start_date (datetime): The start date from which to fetch the data.

    Returns:
    pandas.DataFrame: A DataFrame containing the OHLCV data with the following columns:
        - timestamp (str): The timestamp of each candle in 'YYYY-MM-DD HH:MM:SS' format.
        - open (float): The opening price of the candle.
        - high (float): The highest price of the candle.
        - low (float): The lowest price of the candle.
        - close (float): The closing price of the candle.
        - volume (float): The trading volume during the candle period.

    The DataFrame should be sorted by timestamp in ascending order.

    Raises:
    NotImplementedError: This method must be implemented by the specific data source.

    Note:
    - Ensure that the 'timestamp' column is in string format 'YYYY-MM-DD HH:MM:SS'.
    - All numerical columns (open, high, low, close, volume) should be of type float.
    - Handle any potential errors or exceptions specific to your data source.
    """
    raise NotImplementedError("fetch_ohlcv method must be implemented for the specific data source")

def fetch_symbol_list():
    """
    Fetches a list of symbols available for trading from the data source.

    This function should be implemented to retrieve a list of available trading symbols
    from a specific data source (e.g., an exchange API, database, or data provider).

    Returns:
    list of str: A list of trading symbols. Each symbol should be a string representing
                 a tradable asset or pair. For example:
                 ['BTC/USDT', 'ETH/USDT', 'XRP/USDT', ...]

    The exact format of the symbols may vary depending on the data source, but they should
    be consistent with the format expected by the fetch_ohlcv function.

    Additional information:
    - The returned list should only include symbols that are actually available for trading
      and for which data can be fetched.
    - If the data source distinguishes between different types of markets (e.g., spot, futures),
      this function should return symbols for the relevant market type.
    - If applicable, the function should filter symbols based on the base currency or quote currency
      that is of interest (e.g., only USDT pairs).
    - The list should be free of duplicates.
    - The order of the symbols in the list is not significant unless specified by the data source.

    Raises:
    NotImplementedError: This method must be implemented by the specific data source.

    """
    raise NotImplementedError("fetch_symbol_list method must be implemented for the specific data source")