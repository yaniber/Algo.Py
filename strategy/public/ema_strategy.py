import pandas as pd
pd.set_option('future.no_silent_downcasting', True)

def calculate_ema(close_data, period):
    return close_data.ewm(span=period, adjust=False).mean()

def get_ema_signals_wrapper(ohlcv_data: pd.DataFrame, 
                symbol_list: list, 
                fast_ema_period: int = 10, 
                slow_ema_period: int = 100):
    """
    Generates entry and exit signals based on EMA crossovers.
    
    Args:
        ohlcv_data (pd.DataFrame): DataFrame containing OHLCV data for the symbols.
        symbol_list (list): List of symbols to consider.
        fast_ema_period (int): Period for the fast EMA. Default is 10.
        slow_ema_period (int): Period for the slow EMA. Default is 100.
    
    Returns:
        Tuple of DataFrames: entries, exits, close_data, open_data
    """
    
    # Convert input to a dictionary of DataFrames per symbol
    ohlcv_data = {symbol: ohlcv_data[symbol] for symbol in symbol_list if symbol in ohlcv_data}
    
    # Process each symbol's DataFrame to set 'timestamp' as index and remove duplicates
    for symbol, df in ohlcv_data.items():
        if 'timestamp' in df.columns:
            df = df.reset_index(drop=True)  # Drop the current index if any
            df = df.set_index('timestamp')  # Set 'timestamp' as the new index
        ohlcv_data[symbol] = df
    
    # Remove duplicate indices
    ohlcv_data = {
        symbol: df[~df.index.duplicated(keep='first')]
        for symbol, df in ohlcv_data.items()
    }
    
    # Extract close and open prices into separate DataFrames
    close_data = pd.DataFrame({
        symbol: df['close']
        for symbol, df in ohlcv_data.items()
    })
    
    open_data = pd.DataFrame({
        symbol: df['open']
        for symbol, df in ohlcv_data.items()
    })
    
    # Calculate the fast and slow EMAs for each symbol
    fast_ema = close_data.apply(lambda col: calculate_ema(col, fast_ema_period))
    slow_ema = close_data.apply(lambda col: calculate_ema(col, slow_ema_period))
    
    # Generate entry signals (bullish crossover: fast EMA crosses above slow EMA)
    entries = (fast_ema > slow_ema) & (fast_ema.shift(1) <= slow_ema.shift(1))
    
    # Generate exit signals (bearish crossover: fast EMA crosses below slow EMA)
    exits = (fast_ema < slow_ema) & (fast_ema.shift(1) >= slow_ema.shift(1))
    
    # Fill NaN values and ensure boolean type
    entries = entries.fillna(False).astype(bool)
    exits = exits.fillna(False).astype(bool)
    
    return entries, exits, close_data, open_data