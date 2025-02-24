from strategy.strategy_builder import StrategyBaseClass
import pandas as pd
from typing import Dict, Tuple

class OutsideBarReversalStrategy(StrategyBaseClass):
    """
    Outside Bar Reversal Strategy (Long-only):
    - Bullish entry when outside bar closes below previous low with bearish candle
    - Exit when close price hits 1.5x ATR stop loss or 3x ATR take profit
    """
    
    def __init__(self, atr_period: int = 14):
        super().__init__(name="Outside Bar Reversal Strategy")
        self.atr_period = atr_period

    def run(self, ohlcv_data: Dict[str, pd.DataFrame]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        entries_dict = {}
        exits_dict = {}
        close_dict = {}
        open_dict = {}

        for symbol, df in ohlcv_data.items():
            processed_df = self._preprocess_data(df)
            processed_df['atr'] = self._calculate_atr(processed_df)
            
            # Generate entry signals
            long_entries = self._calculate_entries(processed_df)
            
            # Generate exit signals
            exit_signals = self._calculate_exits(processed_df, long_entries)
            
            # Store results
            entries_dict[symbol] = long_entries.rename(symbol)
            exits_dict[symbol] = exit_signals.rename(symbol)
            close_dict[symbol] = processed_df['close'].rename(symbol)
            open_dict[symbol] = processed_df['open'].rename(symbol)

        # Create aligned DataFrames
        entries = pd.DataFrame(entries_dict).fillna(False).astype(bool)
        exits = pd.DataFrame(exits_dict).fillna(False).astype(bool)
        close_prices = pd.DataFrame(close_dict)
        open_prices = pd.DataFrame(open_dict)

        return entries, exits, close_prices, open_prices

    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate OHLCV data"""
        if 'timestamp' in df.columns:
            df = df.set_index('timestamp')
        df.index = pd.to_datetime(df.index)
        df = df[~df.index.duplicated(keep='first')].sort_index()
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if missing := [col for col in required_cols if col not in df.columns]:
            raise ValueError(f"Missing required columns: {missing}")
        return df

    def _calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate ATR using simple moving average"""
        df['prev_close'] = df['close'].shift(1)
        
        tr = pd.DataFrame({
            'high_low': df['high'] - df['low'],
            'high_prevclose': (df['high'] - df['prev_close']).abs(),
            'low_prevclose': (df['low'] - df['prev_close']).abs()
        }).max(axis=1)
        
        return tr.rolling(window=self.atr_period).mean()

    def _calculate_entries(self, df: pd.DataFrame) -> pd.Series:
        """Identify long entry signals"""
        prev_high = df['high'].shift(1)
        prev_low = df['low'].shift(1)
        
        return (
            (df['high'] > prev_high) & 
            (df['low'] < prev_low) & 
            (df['close'] < prev_low) & 
            (df['open'] > df['close'])
        )

    def _calculate_exits(self, df: pd.DataFrame, long_entries: pd.Series) -> pd.Series:
        """Calculate exits using static SL/TP based on entry price and entry-time ATR"""
        exit_signals = pd.Series(False, index=df.index)
        entry_points = df.index[long_entries]

        for entry_time in entry_points:
            try:
                entry_pos = df.index.get_loc(entry_time)
                if entry_pos + 1 >= len(df):
                    continue
            except KeyError:
                continue

            # Get static values AT ENTRY TIME
            entry_atr = df.iloc[entry_pos]['atr']
            entry_price = df.iloc[entry_pos + 1]['open']  # Next bar's open
            
            # Calculate fixed thresholds
            stop_loss = entry_price - 1.5 * entry_atr
            take_profit = entry_price + 3 * entry_atr

            # Look ahead for exit conditions
            for exit_pos in range(entry_pos + 1, len(df)):
                current_close = df.iloc[exit_pos]['close']
                
                # Check exit conditions
                if current_close <= stop_loss:
                    exit_signals.iloc[exit_pos] = True
                    break
                if current_close >= take_profit:
                    exit_signals.iloc[exit_pos] = True
                    break

        return exit_signals