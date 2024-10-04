import pandas as pd

def get_top_symbols_by_average_volume(ohlcv_data : dict, top_n : int = 500):
    """
    Identifies the top 500 stocks with the highest average volume.
    
    Args:
        ohlcv_data (dict): Dictionary where keys are stock symbols and values are OHLCV DataFrames
        top_n (int): Number of top symbols to return
    Returns:
        List of top n stock symbols by average volume
    """
    average_volumes = []

    # Calculate the average volume for each stock symbol
    for symbol, df in ohlcv_data.items():
        if 'volume' in df.columns:
            avg_volume = df['volume'].mean()
            average_volumes.append((symbol, avg_volume))

    # Convert to a DataFrame for easy sorting
    volume_df = pd.DataFrame(average_volumes, columns=['Symbol', 'AverageVolume'])

    # Sort by average volume in descending order and get the top 500
    top_n_symbols = volume_df.sort_values(by='AverageVolume', ascending=False).head(top_n)['Symbol'].tolist()

    return top_n_symbols