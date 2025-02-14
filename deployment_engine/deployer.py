import pandas as pd
import vectorbtpro as vbt
from pandas.tseries.frequencies import to_offset
from pathlib import Path
import json
import uuid
from typing import Callable, Optional, List, Tuple, Dict, Any

from finstore.finstore import Finstore
from data.store.crypto_binance import store_crypto_binance
from data.store.indian_equity import store_indian_equity
from strategy.strategy_builder import StrategyBaseClass


from typing import List, Callable, Optional
import pandas as pd


import schedule
import time
from data.update.crypto_binance import fill_gap
from utils.db.fetch import fetch_entries
from executor.monitor import TradeMonitor

class Deployer:
    def __init__(self, backtest_uuid: Optional[str] = None,
                 market_name: Optional[str] = None,
                 symbol_list: Optional[List[str]] = None,
                 timeframe: Optional[str] = None,
                 scheduler_type: Optional[str] = None,
                 scheduler_interval : Optional[str] = None,
                 strategy_object: Optional['StrategyBaseClass'] = None,
                 strategy_type: Optional[str] = None,
                 start_date: Optional[pd.Timestamp] = None,
                 end_date: Optional[pd.Timestamp] = None,
                 init_cash: Optional[float] = None,
                 fees: Optional[float] = None,
                 slippage: Optional[float] = None,
                 size: Optional[float] = None,
                 cash_sharing: Optional[bool] = None,
                 allow_partial: Optional[bool] = None,
                 progress_callback: Optional[Callable[[int, str], None]] = None,
                 oms_name: str = None,
                 pair: Optional[str] = None) -> None:
        """
        General initializer but not meant to be used directly.
        Use classmethods to initialize the object.
        """
        '''
        All params are must have , except : 
        progress_callback, oms_name, pair
        '''
        self.backtest_uuid = backtest_uuid # uuid that has following files in its dir : backtest_results/uuid/ : params.json , portfolio.pkl, trades.parquet, preferable also store the trademonitor here.
        self.market_name = market_name # could be indian_equity or crypto_binance
        self.symbol_list = symbol_list # list of strings of symbols
        self.timeframe = timeframe
        self.scheduler_type = scheduler_type # 2 types fixed_interval and specific_time
        self.scheduler_interval = scheduler_interval # if fixed_interval then int in minutes , else specific tie of day in UTC ??
        self.strategy_object = strategy_object # strategy object initialized with params , which has a run function to return entries , etc
        self.strategy_type = strategy_type # multi or single , prsenf in params.json
        self.start_date = start_date # pd timestamp
        self.end_date = end_date # pd timestamp
        self.init_cash = init_cash # int
        self.fees = fees # float
        self.slippage = slippage
        self.size = size # size of every position , valuepercent : 0,1 for 10 concurrent positions at a time
        self.cash_sharing = cash_sharing # True to share cash across assets
        self.allow_partial = allow_partial # True for crypto
        self.progress_callback = progress_callback # function that has int, str as input params
        self.pair = pair # BTC or USDT in case of crypto , optional otherwise
        self.oms_name = oms_name # Telegram , crypto_binance, indian_equity
        self.oms_init()
        self.scheduler()


    @classmethod
    def from_backtest_uuid(cls, backtest_uuid: str, oms_name : str) -> "Deployer":
        """
        Initialize Deployer using only the backtest UUID.
        """

        bt_dir = Path(f"backtest_results/{backtest_uuid}")
    
        with open(bt_dir / "params.json") as f:
            data = json.load(f)
        
        market_name = data.get("market_name")
        symbol_list = data.get("symbol_list")

        if not oms_name:
            oms_name = market_name


        # TODO : get all other relevant param to initialize cls with
        
        return cls(backtest_uuid=backtest_uuid, oms_name=oms_name,... all other params)

    @classmethod
    def from_market_params(cls, market_name: str,
                           symbol_list: List[str],
                           timeframe: str,
                           strategy_object: 'StrategyBaseClass',
                           strategy_type: str,
                           start_date: pd.Timestamp,
                           end_date: pd.Timestamp,
                           init_cash: float,
                           fees: float,
                           slippage: float,
                           size: float,
                           cash_sharing: bool,
                           allow_partial: bool,
                           progress_callback: Callable[[int, str], None],
                           pair: Optional[str] = None) -> "Deployer":
        """
        Initialize Deployer with market parameters.
        """
        return cls(market_name=market_name,
                   symbol_list=symbol_list,
                   timeframe=timeframe,
                   strategy_object=strategy_object,
                   strategy_type=strategy_type,
                   start_date=start_date,
                   end_date=end_date,
                   init_cash=init_cash,
                   fees=fees,
                   slippage=slippage,
                   size=size,
                   cash_sharing=cash_sharing,
                   allow_partial=allow_partial,
                   progress_callback=progress_callback,
                   pair=pair)
        # TODO : add all other params here too. 
    
    def backtested_deployment(self):
        bt_dir = Path(f"backtest_results/{self.backtest_uuid}")
    
        with open(bt_dir / "params.json") as f:
            data = json.load(f)
    

    def schedule_job(self):

        fill_gap(
            market_name=self.market_name,
            timeframe=self.timeframe,
            complete_list=False,
            pair=self.pair
        )

        ohlcv_data = fetch_entries(
            market_name=self.market_name,
            timeframe=self.timeframe,
            symbol_list=self.symbol_list,
            all_entries=False,
            pair=self.pair
        )

        entries, exits, close_data, open_data = self.strategy_object.run(ohlcv_data)

        fresh_entries, fresh_exits = self.entry_generator(entries, exits, close_data, open_data, self.backtest_uuid)

        self.executor(fresh_entries, fresh_exits)

    def entry_generator(self,entries, exits, close_data, open_data, deployment_id):
        
        trade_monitor = TradeMonitor(storage_file=f'database/db/{deployment_id}.parquet')
        
        pf = vbt.Portfolio.from_signals(
            close=close_data,
            entries=entries,
            exits=exits,
            direction='longonly',
            init_cash=self.init_cash,
            cash_sharing=True,
            size=self.size,
            size_type="valuepercent",
            fees=self.fees,
            slippage=self.slippage,
            allow_partial=False,
            size_granularity=1.0,
            sim_start=self.sim_start,
            sim_end=self.sim_end,
        )

        trade_history = pf.trade_history

        fresh_buys, fresh_sells = trade_monitor.monitor_fresh_trades(trade_history)

        return fresh_buys, fresh_sells

    def executor(self, fresh_entries, fresh_exits):

        if self.oms_name == 'Telegram':
            message = (f"fresh_entries : {fresh_entries}\n"
                        f"fresh_exits : {fresh_exits}")
            self.oms.send_telegram_message(message)

    def oms_init(self, oms_params):

        if self.oms_name == 'Telegram': 
            from OMS.telegram import Telegram
            telegram_group_id = oms_params.get('group_id', None)
            oms_instance = Telegram(group_id=telegram_group_id if telegram_group_id else None)
            self.oms = oms_instance

    def scheduler(self):
        # TODO : Determine if this needs to be executed in a daemon , background thread or not. 
        if self.scheduler_type == "fixed_interval":
            # TODO : properly convert scheduler_interval for both these cases. 
            schedule.every(int(self.scheduler_interval)).minutes.do(self.schedule_job)
        elif self.scheduler_type == "specific_time":
            schedule.every().day.at(self.scheduler_interval).do(self.schedule_job)
        else:
            print("Unknown scheduler type. Exiting deployment runner process.")
            return

        while True:
            schedule.run_pending()
            time.sleep(1)

            




if __name__ == '__main__':
    from backtest_engine.backtester import Backtester
    from strategy.public.EmaStrat import EMAStrategy
    import pandas as pd

    def dummy_progress(progress: int, status: str) -> None:
            print(f"Progress: {progress}% - {status}")

    # Initialize strategy with parameters
    ema_strategy = EMAStrategy(
        fast_ema_period=10,
        slow_ema_period=100
    )

    deployer1 = Deployer.from_backtest_uuid(backtest_uuid="123e4567-e89b-12d3-a456-426614174000", oms_name='Telegram', strategy_object=ema_strategy, progress_callback=dummy_progress)
    print(deployer1.backtest_uuid)  # Output: 123e4567-e89b-12d3-a456-426614174000
