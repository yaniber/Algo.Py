from strategy.strategy_builder import StrategyBaseClass
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)
from typing import Callable, Optional, List, Tuple, Dict, Any

class EMAStrategy(StrategyBaseClass):
    """
    EMA Crossover Strategy:
    - Long entry when fast EMA crosses above slow EMA
    - Exit when fast EMA crosses below slow EMA
    """
    
    def __init__(self, fast_ema_period: int = 10, slow_ema_period: int = 100):
        """
        Initialize EMA strategy parameters.
        
        Args:
            fast_ema_period (int): Period for fast EMA calculation
            slow_ema_period (int): Period for slow EMA calculation
        """
        super().__init__(name="EMA Crossover Strategy")
        self.fast_ema_period = fast_ema_period
        self.slow_ema_period = slow_ema_period

    def run(self, ohlcv_data: Dict[str, pd.DataFrame]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Process OHLCV data and generate EMA crossover signals.
        
        Args:
            ohlcv_data (Dict[str, pd.DataFrame]): Dictionary of OHLCV DataFrames keyed by symbol
            
        Returns:
            Tuple containing:
            - entries: Boolean DataFrame of entry signals
            - exits: Boolean DataFrame of exit signals
            - close_data: DataFrame of closing prices
            - open_data: DataFrame of opening prices
        """
        entries_dict = {}
        exits_dict = {}
        close_dict = {}
        open_dict = {}

        # Process each symbol's data individually
        for symbol, df in ohlcv_data.items():
            # Clean and prepare data
            processed_df = self._preprocess_data(df)
            
            # Calculate indicators
            close_series = processed_df['close']
            fast_ema = calculate_ema(close_series, self.fast_ema_period)
            slow_ema = calculate_ema(close_series, self.slow_ema_period)
            
            # Generate signals
            entry_signals = (fast_ema > slow_ema) & (fast_ema.shift(1) <= slow_ema.shift(1))
            exit_signals = (fast_ema < slow_ema) & (fast_ema.shift(1) >= slow_ema.shift(1))
            
            # Store results
            entries_dict[symbol] = entry_signals.rename(symbol)
            exits_dict[symbol] = exit_signals.rename(symbol)
            close_dict[symbol] = close_series.rename(symbol)
            open_dict[symbol] = processed_df['open'].rename(symbol)

        # Create aligned DataFrames from individual series
        entries = pd.DataFrame(entries_dict)
        exits = pd.DataFrame(exits_dict)
        close_prices = pd.DataFrame(close_dict)
        open_prices = pd.DataFrame(open_dict)

        # Clean signal DataFrames
        entries = entries.fillna(False).astype(bool)
        exits = exits.fillna(False).astype(bool)

        return entries, exits, close_prices, open_prices

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare raw OHLCV data for analysis.
        
        Args:
            df (pd.DataFrame): Raw OHLCV data
            
        Returns:
            pd.DataFrame: Cleaned and formatted data
        """
        # Handle timestamp column
        if 'timestamp' in df.columns:
            df = df.set_index('timestamp')
            
        # Remove duplicate indices
        df = df[~df.index.duplicated(keep='first')]
        
        # Ensure required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Missing required columns: {missing}")
            
        return df


def calculate_ema(close_data: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA)
    
    Args:
        close_data (pd.Series): Series of closing prices
        period (int): EMA period
        
    Returns:
        pd.Series: EMA values
    """
    return close_data.ewm(span=period, adjust=False).mean()