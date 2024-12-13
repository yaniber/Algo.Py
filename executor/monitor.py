import pandas as pd
import os
import sys
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TradeMonitor:
    
    """
    A class used to monitor trades, compare current trades to past positions, 
    and persist the past positions to disk for crash recovery.

    Attributes
    ----------
    storage_file : str
        Path to the file used for persisting the past positions.

    past_positions : pd.DataFrame
        DataFrame storing all past positions. It is loaded from disk on initialization 
        if the file exists.
    """

    def __init__(self, storage_file='database/db/past_positions.parquet'):
        
        """
        Initializes the TradeMonitor class, loading past positions from disk 
        if they exist, otherwise initializing an empty DataFrame.
        
        Parameters
        ----------
        storage_file : str, optional
            Path to the file used for storing past positions (default is 'database/db/past_positions.parquet').
        """
        
        self.storage_file = storage_file
        if os.path.exists(self.storage_file):
            self.past_positions = pd.read_parquet(self.storage_file)
        else:
            self.past_positions = pd.DataFrame()

    def monitor_fresh_trades(self, current_trade_history: pd.DataFrame):

        """
        Monitors the current trade history and identifies fresh trades 
        (buys and sells) that are not in the past positions. 

        If no past positions exist, it considers all trades in the current history as fresh.

        Parameters
        ----------
        current_trade_history : pd.DataFrame
            A DataFrame containing the current day's trade history. Must contain the 
            following columns: 'Column', 'Order Id', 'Side'.

        Returns
        -------
        tuple (pd.DataFrame, pd.DataFrame)
            A tuple containing two DataFrames:
            - fresh_buys: DataFrame of fresh "Buy" trades.
            - fresh_sells: DataFrame of fresh "Sell" trades.
        """
        fresh_buys = pd.DataFrame()
        fresh_sells = pd.DataFrame()

        if self.past_positions.empty:
            fresh_trades = current_trade_history
        else:
            fresh_trades = current_trade_history[
                ~current_trade_history.set_index(['Column', 'Order Id', 'Side']).index.isin(
                    self.past_positions.set_index(['Column', 'Order Id', 'Side']).index
                )
            ]

        self.past_positions = pd.concat([self.past_positions, fresh_trades]).drop_duplicates()

        self.past_positions.to_parquet(self.storage_file)

        fresh_buys = fresh_trades[fresh_trades['Side'] == 'Buy']
        fresh_sells = fresh_trades[fresh_trades['Side'] == 'Sell']

        return fresh_buys, fresh_sells