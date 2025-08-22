"""
MetaTrader 5 data fetching module for Algo.Py

This module provides functions to fetch OHLCV data and symbol lists from MetaTrader 5.
Works on Windows natively and on Linux via Wine.
"""

import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Try to import MetaTrader5, with Wine support for Linux environments
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False

# Load environment variables
load_dotenv(dotenv_path='config/.env')

def initialize_mt5():
    """Initialize MT5 connection"""
    if not MT5_AVAILABLE:
        print("MetaTrader5 package not available. For Linux, ensure Wine is properly configured.")
        return False
        
    try:
        # Set Wine environment if running on Linux
        if os.name != 'nt':  # Not Windows
            os.environ['WINEARCH'] = 'win64'
            os.environ['WINEPREFIX'] = '/app/.wine'
        
        # Get connection parameters from environment
        login = int(os.getenv('MT5_LOGIN', 0))
        password = os.getenv('MT5_PASSWORD')
        server = os.getenv('MT5_SERVER')
        # Default Wine path for Linux, standard path for Windows
        path = os.getenv('MT5_PATH')
        if not path and os.name != 'nt':
            path = '/app/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe'
        
        if not login or not password or not server:
            print("MT5 credentials not found in environment variables")
            return False
            
        # Initialize MT5 terminal
        if path and os.path.exists(path):
            if not mt5.initialize(path=path):
                print(f"Failed to initialize MT5 with path: {path}")
                # Try without path
                if not mt5.initialize():
                    print("Failed to initialize MT5")
                    return False
        else:
            if not mt5.initialize():
                print("Failed to initialize MT5")
                return False
        
        # Login to account
        if not mt5.login(login, password=password, server=server):
            print(f"Failed to login to MT5 account {login}")
            mt5.shutdown()
            return False
        
        wine_status = " (via Wine)" if os.name != 'nt' else ""
        print(f"Successfully connected to MT5 account: {login}{wine_status}")
        return True
        
    except Exception as e:
        print(f"Error initializing MT5: {str(e)}")
        if os.name != 'nt':
            print("Hint: For Linux, ensure Wine is properly configured and MT5 terminal is installed")
        return False

def fetch_ohlcv_mt5(symbol, timeframe, start_date):
    """
    Fetches OHLCV (Open, High, Low, Close, Volume) data for a given symbol and timeframe from MetaTrader 5.

    Parameters:
    symbol (str): The trading symbol to fetch data for (e.g., 'EURUSD', 'XAUUSD').
    timeframe (str): The timeframe of the data (e.g., '1d', '1h', '5m', '1m').
    start_date (datetime): The start date from which to fetch the data.

    Returns:
    pandas.DataFrame: A DataFrame containing the OHLCV data with columns:
        - timestamp (str): The timestamp in 'YYYY-MM-DD HH:MM:SS' format.
        - open (float): The opening price.
        - high (float): The highest price.
        - low (float): The lowest price.
        - close (float): The closing price.
        - volume (int): The trading volume.
    """
    
    # Initialize MT5 if needed
    if not initialize_mt5():
        return pd.DataFrame()
    
    try:
        # Map timeframe strings to MT5 timeframes
        timeframe_map = {
            '1m': mt5.TIMEFRAME_M1,
            '5m': mt5.TIMEFRAME_M5,
            '15m': mt5.TIMEFRAME_M15,
            '30m': mt5.TIMEFRAME_M30,
            '1h': mt5.TIMEFRAME_H1,
            '4h': mt5.TIMEFRAME_H4,
            '1d': mt5.TIMEFRAME_D1,
            '1w': mt5.TIMEFRAME_W1,
            '1M': mt5.TIMEFRAME_MN1
        }
        
        mt5_timeframe = timeframe_map.get(timeframe)
        if mt5_timeframe is None:
            print(f"Unsupported timeframe: {timeframe}")
            return pd.DataFrame()
        
        # Check if symbol exists
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"Symbol {symbol} not found")
            return pd.DataFrame()
        
        # Enable symbol in Market Watch if not already enabled
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                print(f"Failed to enable symbol {symbol}")
                return pd.DataFrame()
        
        # Calculate number of bars to fetch (approximate)
        now = datetime.now()
        delta = now - start_date
        
        # Estimate bars based on timeframe
        bars_per_day_map = {
            '1m': 1440,
            '5m': 288,
            '15m': 96,
            '30m': 48,
            '1h': 24,
            '4h': 6,
            '1d': 1,
            '1w': 1/7,
            '1M': 1/30
        }
        
        bars_per_day = bars_per_day_map.get(timeframe, 24)
        count = max(100, int(delta.days * bars_per_day) + 100)  # Add buffer
        count = min(count, 10000)  # MT5 limit
        
        # Fetch rates
        rates = mt5.copy_rates_from(symbol, mt5_timeframe, start_date, count)
        
        if rates is None or len(rates) == 0:
            print(f"No data retrieved for {symbol}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        
        # Convert timestamp to datetime string format
        df['timestamp'] = pd.to_datetime(df['time'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Rename columns to match expected format
        df = df.rename(columns={
            'tick_volume': 'volume'  # MT5 uses tick_volume
        })
        
        # Select and order columns as expected
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
        
        # Ensure data types
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(int)
        
        # Filter data from start_date onwards
        df_filtered = df[pd.to_datetime(df['timestamp']) >= start_date].copy()
        
        print(f"Retrieved {len(df_filtered)} records for {symbol} from {start_date}")
        return df_filtered
        
    except Exception as e:
        print(f"Error fetching OHLCV data for {symbol}: {str(e)}")
        return pd.DataFrame()

def fetch_symbol_list_mt5():
    """
    Fetches a list of symbols available for trading from MetaTrader 5.

    Returns:
    list of str: A list of trading symbols available in MT5.
                 For example: ['EURUSD', 'GBPUSD', 'XAUUSD', ...]
    """
    
    # Initialize MT5 if needed
    if not initialize_mt5():
        return []
    
    try:
        # Get all symbols
        symbols = mt5.symbols_get()
        
        if symbols is None:
            print("Failed to get symbols from MT5")
            return []
        
        # Filter to visible symbols only and extract names
        symbol_list = []
        for symbol in symbols:
            if symbol.visible:
                symbol_list.append(symbol.name)
        
        print(f"Retrieved {len(symbol_list)} symbols from MT5")
        return symbol_list
        
    except Exception as e:
        print(f"Error fetching symbol list from MT5: {str(e)}")
        return []

def fetch_symbol_info_mt5(symbol):
    """
    Get detailed information about a specific symbol.
    
    Parameters:
    symbol (str): The symbol to get information for
    
    Returns:
    dict: Symbol information dictionary or None if not found
    """
    
    if not initialize_mt5():
        return None
    
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return None
        
        return symbol_info._asdict()
        
    except Exception as e:
        print(f"Error fetching symbol info for {symbol}: {str(e)}")
        return None

def get_forex_pairs():
    """Get list of forex pairs"""
    symbols = fetch_symbol_list_mt5()
    # Common forex pairs patterns
    forex_patterns = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD']
    forex_pairs = []
    
    for symbol in symbols:
        if len(symbol) == 6 and any(pattern in symbol for pattern in forex_patterns):
            forex_pairs.append(symbol)
    
    return forex_pairs

def get_metal_pairs():
    """Get list of metal/commodity pairs"""
    symbols = fetch_symbol_list_mt5()
    # Common metals/commodities
    metal_patterns = ['XAU', 'XAG', 'XPT', 'XPD', 'OIL', 'GAS', 'WTI']
    metal_pairs = []
    
    for symbol in symbols:
        if any(pattern in symbol for pattern in metal_patterns):
            metal_pairs.append(symbol)
    
    return metal_pairs

def get_indices():
    """Get list of stock indices"""
    symbols = fetch_symbol_list_mt5()
    # Common index patterns
    index_patterns = ['SPX', 'NAS', 'DOW', 'DAX', 'FTSE', 'CAC', 'NIKKEI', 'ASX']
    indices = []
    
    for symbol in symbols:
        if any(pattern in symbol for pattern in index_patterns):
            indices.append(symbol)
    
    return indices

# Aliases for backward compatibility and consistency
fetch_ohlcv = fetch_ohlcv_mt5
fetch_symbol_list = fetch_symbol_list_mt5

if __name__ == '__main__':
    # Test the functions
    print("Testing MT5 data fetching...")
    
    # Test symbol list
    symbols = fetch_symbol_list_mt5()
    print(f"Found {len(symbols)} symbols")
    if symbols:
        print(f"First 10 symbols: {symbols[:10]}")
    
    # Test OHLCV data fetch (if symbols are available)
    if symbols:
        test_symbol = symbols[0]
        start_date = datetime.now() - timedelta(days=30)
        
        print(f"\nTesting OHLCV fetch for {test_symbol}...")
        df = fetch_ohlcv_mt5(test_symbol, '1h', start_date)
        
        if not df.empty:
            print(f"Retrieved {len(df)} records")
            print(df.head())
        else:
            print("No data retrieved")
    
    # Clean up
    mt5.shutdown()