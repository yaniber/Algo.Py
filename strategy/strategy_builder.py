import pandas as pd
from typing import Tuple, Dict, Any

class StrategyBaseClass:
    """
    Base class for all trading strategies. Child classes must implement the run method.
    """

    def __init__(self) -> None:
        """
        Initialize strategy parameters. Child classes should set their parameters as instance variables.
        """
        pass

    @property
    def params(self) -> Dict[str, Any]:
        """
        Returns a dictionary of the strategy's parameters, excluding private variables.
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    def run(self, ohlcv_data: Dict[str, pd.DataFrame]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Process the OHLCV data and generate entry/exit signals.

        Args:
            ohlcv_data (Dict[str, pd.DataFrame]): Dictionary of DataFrames containing OHLCV data for each symbol

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]: A tuple containing:
                - entries (pd.DataFrame): Boolean DataFrame indicating entry signals (columns=symbols)
                - exits (pd.DataFrame): Boolean DataFrame indicating exit signals (columns=symbols)
                - close_data (pd.DataFrame): DataFrame of closing prices (columns=symbols)
                - open_data (pd.DataFrame): DataFrame of opening prices (columns=symbols)
        """
        raise NotImplementedError("run method must be implemented by subclass.")