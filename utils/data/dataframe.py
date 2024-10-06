import pandas as pd
from datetime import datetime, timedelta

def get_top_symbols_by_average_volume(ohlcv_data : dict, top_n : int = 500, year : pd.Timestamp = pd.Timestamp.now()):
    """
    Identifies the top 500 stocks with the highest average volume.
    
    Args:
        ohlcv_data (dict): Dictionary where keys are stock symbols and values are OHLCV DataFrames
        top_n (int): Number of top symbols to return
    Returns:
        List of top n stock symbols by average volume
    """
    average_volumes = []
    seen_symbols = set()
    year_before = year - pd.DateOffset(years=1)

    # Calculate the average volume and average price for each stock symbol over the past year
    for symbol, df in ohlcv_data.items():
        base_symbol = symbol.split('.')[0]  # Extract base symbol

        if base_symbol in seen_symbols:
            continue  # Skip if base symbol already processed

        if 'volume' in df.columns and 'close' in df.columns and 'timestamp' in df.columns:
            # Filter the DataFrame to include only the last year's data
            #df_last_year = df[df['timestamp'] >= year.strftime('%Y-%m-%d')]
            df_last_year = df[(year_before.strftime('%Y-%m-%d') < df['timestamp']) & (df['timestamp'] < year.strftime('%Y-%m-%d'))]

            if not df_last_year.empty:
                avg_volume = df_last_year['volume'].mean()
                avg_price = df_last_year['close'].mean()
                liquidity_metric = avg_volume * avg_price  # Liquidity metric for the past year
                average_volumes.append((symbol, liquidity_metric))
                seen_symbols.add(base_symbol)  # Mark base symbol as seen

    # Convert to a DataFrame for easy sorting
    volume_df = pd.DataFrame(average_volumes, columns=['Symbol', 'LiquidityMetric'])

    # Sort by liquidity metric in descending order and get the top n
    top_n_symbols = volume_df.sort_values(by='LiquidityMetric', ascending=False).head(top_n)['Symbol'].tolist()

    return top_n_symbols