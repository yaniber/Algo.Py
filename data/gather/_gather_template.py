"""
This is a template to start your own data source's pipeline. 

Gather is the second step in your pipeline.

Pipeline overview : 
fetch -> gather -> store -> calculate

"""

#from data.fetch.your_data_source import fetch_ohlcv_your_data_source, fetch_symbol_list_your_data_source
#from tqdm import tqdm
#from utils.decorators import cache_decorator

#@cache_decorator() -> add this if you want to cache the data (recommended)
def gather_ohlcv(timeframe='1d', start_date=None, **kwargs):
    """
    Gathers OHLCV (Open, High, Low, Close, Volume) data for all symbols from the specified data source.

    This function should be implemented to retrieve historical price and volume data
    for all available symbols from a specific data source.

    Parameters:
    timeframe (str): The timeframe of the data (e.g., '1d' for daily, '1h' for hourly).
    start_date (datetime): The start date from which to fetch the data.
    **kwargs: Additional keyword arguments specific to the data source.

    Returns:
    tuple: A tuple containing two elements:
        - list of str: A list of all symbols for which data was fetched.
        - dict: A dictionary where keys are symbols and values are pandas DataFrames
                containing the OHLCV data for each symbol. Each DataFrame should have
                the following columns:
                - timestamp (str): The timestamp of each candle in 'YYYY-MM-DD HH:MM:SS' format.
                - open (float): The opening price of the candle.
                - high (float): The highest price of the candle.
                - low (float): The lowest price of the candle.
                - close (float): The closing price of the candle.
                - volume (float): The trading volume during the candle period.

    Raises:
    NotImplementedError: This method must be implemented by the specific data source.

    Note:
    - Ensure that the 'timestamp' column in each DataFrame is in string format 'YYYY-MM-DD HH:MM:SS'.
    - All numerical columns (open, high, low, close, volume) should be of type float.
    - Handle any potential errors or exceptions specific to your data source.
    - Implement appropriate filtering or processing based on the provided parameters.
    """
    raise NotImplementedError("gather_ohlcv method must be implemented for the specific data source")