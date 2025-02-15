import pandas as pd
import vectorbtpro as vbt
from pandas.tseries.frequencies import to_offset
from pathlib import Path
import json
import uuid
import schedule
import time
from typing import Callable, Optional, List, Tuple, Dict, Any, Union
from threading import Thread
from datetime import datetime

from finstore.finstore import Finstore
from data.store.crypto_binance import store_crypto_binance
from data.store.indian_equity import store_indian_equity
from strategy.strategy_builder import StrategyBaseClass
from data.update.crypto_binance import fill_gap
from utils.db.fetch import fetch_entries
from executor.monitor import TradeMonitor
from strategy.strategy_registry import STRATEGY_REGISTRY

class Deployer:
    def __init__(
        self,
        backtest_uuid: Optional[str] = None,
        market_name: Optional[str] = None,
        symbol_list: Optional[List[str]] = None,
        timeframe: Optional[str] = None,
        scheduler_type: Optional[str] = None,
        scheduler_interval: Optional[str] = None,
        strategy_object: Optional[StrategyBaseClass] = None,
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
        oms_name: Optional[str] = None,
        pair: Optional[str] = None,
        oms_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.backtest_uuid = backtest_uuid
        self.market_name = market_name
        self.symbol_list = symbol_list
        self.timeframe = timeframe
        self.scheduler_type = scheduler_type
        self.scheduler_interval = scheduler_interval
        self.strategy_object = strategy_object
        self.strategy_type = strategy_type
        self.start_date = start_date
        self.end_date = end_date
        self.init_cash = init_cash
        self.fees = fees
        self.slippage = slippage
        self.size = size
        self.cash_sharing = cash_sharing
        self.allow_partial = allow_partial
        self.progress_callback = progress_callback
        self.oms_name = oms_name
        self.pair = pair
        self.oms_params = oms_params or {}
        self.oms = None

        self.oms_init()

        # Start the scheduler in a background thread
        self.scheduler_thread = Thread(target=self.scheduler_loop, daemon=True)
        self.scheduler_thread.start()

    def oms_init(self) -> None:
        """Initialize the Order Management System based on oms_name and parameters."""
        if self.oms_name == 'Telegram':
            from OMS.telegram import Telegram
            group_id = self.oms_params.get('group_id')
            self.oms = Telegram(group_id=group_id)
        elif self.oms_name == 'crypto_binance':
            from OMS.crypto_binance import BinanceOMS
            api_key = self.oms_params.get('api_key')
            api_secret = self.oms_params.get('api_secret')
            self.oms = BinanceOMS(api_key=api_key, api_secret=api_secret)
        elif self.oms_name == 'indian_equity':
            from OMS.indian_equity import EquityOMS
            broker_config = self.oms_params.get('broker_config')
            self.oms = EquityOMS(broker_config=broker_config)
        else:
            raise ValueError(f"OMS {self.oms_name} is not supported.")

    @classmethod
    def from_backtest_uuid(
        cls,
        backtest_uuid: str,
        oms_name: str,
        scheduler_type: str,
        scheduler_interval: str,
        oms_params: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> "Deployer":
        """Initialize Deployer from a backtest UUID."""
        bt_dir = Path(f"database/backtest/{backtest_uuid}")
        params_path = bt_dir / "params.json"
        
        with open(params_path, "r") as f:
            data = json.load(f)
        
        strategy_name = data["strategy_name"]
        strategy_params = data["strategy_params"]
        
        # Map strategy_name to the corresponding class
        strategy_cls = STRATEGY_REGISTRY.get(strategy_name, None).get('class', None)
        if not strategy_cls:
            raise ValueError(f"Strategy {strategy_name} not supported.")
        
        strategy_object = strategy_cls(**strategy_params)
        
        # Parse dates
        start_date = pd.Timestamp(data["start_date"])
        end_date = pd.Timestamp(data["end_date"])
        
        return cls(
            backtest_uuid=backtest_uuid,
            market_name=data["market_name"],
            symbol_list=data["symbol_list"],
            timeframe=data["timeframe"],
            scheduler_type=scheduler_type,
            scheduler_interval=scheduler_interval,
            strategy_object=strategy_object,
            strategy_type=data["strategy_type"],
            start_date=start_date,
            end_date=end_date,
            init_cash=data["init_cash"],
            fees=data["fees"],
            slippage=data["slippage"],
            size=data["size"],
            cash_sharing=data["cash_sharing"],
            allow_partial=data["allow_partial"],
            progress_callback=progress_callback,
            oms_name=oms_name,
            pair=data.get("pair"),
            oms_params=oms_params,
        )

    @classmethod
    def from_market_params(
        cls,
        market_name: str,
        symbol_list: List[str],
        timeframe: str,
        scheduler_type: str,
        scheduler_interval: str,
        strategy_object: StrategyBaseClass,
        strategy_type: str,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        init_cash: float,
        fees: float,
        slippage: float,
        size: float,
        cash_sharing: bool,
        allow_partial: bool,
        oms_name: str,
        pair: Optional[str] = None,
        oms_params: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> "Deployer":
        """Initialize Deployer with direct market parameters."""
        return cls(
            market_name=market_name,
            symbol_list=symbol_list,
            timeframe=timeframe,
            scheduler_type=scheduler_type,
            scheduler_interval=scheduler_interval,
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
            oms_name=oms_name,
            pair=pair,
            oms_params=oms_params,
        )

    def scheduler_loop(self) -> None:
        """Run the scheduler loop in a background thread."""
        if self.scheduler_type == "fixed_interval":
            interval = int(self.scheduler_interval)
            self.schedule_job()
            schedule.every(interval).minutes.do(self.schedule_job)
        elif self.scheduler_type == "specific_time":
            schedule.every().day.at(self.scheduler_interval).do(self.schedule_job)
        else:
            raise ValueError(f"Invalid scheduler type: {self.scheduler_type}")

        while True:
            schedule.run_pending()
            time.sleep(1)

    def schedule_job(self) -> None:
        """Job to be scheduled: fetch data, run strategy, generate and execute trades."""
        if self.progress_callback:
            self.progress_callback(10, "Filling data gaps")
        
        #fill_gap(
        #    market_name=self.market_name,
        #    timeframe=self.timeframe,
        #    complete_list=False,
        #    pair=self.pair
        #)
        
        if self.progress_callback:
            self.progress_callback(30, "Fetching OHLCV data")
        
        ohlcv_data = fetch_entries(
            market_name=self.market_name,
            timeframe=self.timeframe,
            symbol_list=self.symbol_list,
            all_entries=False,
            pair=self.pair
        )
        
        if self.progress_callback:
            self.progress_callback(50, "Running strategy")
        
        entries, exits, close_data, open_data = self.strategy_object.run(ohlcv_data)
        
        if self.progress_callback:
            self.progress_callback(70, "Generating fresh trades")
        
        fresh_entries, fresh_exits = self.entry_generator(entries, exits, close_data, open_data)
        
        if self.progress_callback:
            self.progress_callback(90, "Executing trades")
        
        self.executor(fresh_entries, fresh_exits)
        
        if self.progress_callback:
            self.progress_callback(100, "Job completed")

    def entry_generator(
        self,
        entries: pd.DataFrame,
        exits: pd.DataFrame,
        close_data: pd.DataFrame,
        open_data: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Identify fresh entries and exits using TradeMonitor."""
        if self.backtest_uuid:
            storage_file = f"database/backtest/{self.backtest_uuid}/past_positions.parquet"
        else:
            storage_file = f"database/backtest/{uuid.uuid4()}/past_positions.parquet"
        
        storage_dir = Path(storage_file).parent
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        trade_monitor = TradeMonitor(storage_file=storage_file)
        
        pf = vbt.Portfolio.from_signals(
            close=close_data,
            entries=entries,
            exits=exits,
            direction='longonly',
            init_cash=self.init_cash,
            cash_sharing=self.cash_sharing,
            size=self.size,
            fees=self.fees,
            slippage=self.slippage,
            allow_partial=self.allow_partial,
        )
        
        trade_history = pf.trade_history
        
        fresh_entries, fresh_exits = trade_monitor.monitor_fresh_trades(trade_history)
        return fresh_entries, fresh_exits

    def executor(self, fresh_entries: pd.DataFrame, fresh_exits: pd.DataFrame) -> None:
        """Execute trades using the configured OMS."""
        if self.oms is None:
            raise ValueError("OMS is not initialized.")
        
        self.oms.execute(fresh_entries, fresh_exits)

def dummy_progress(progress: int, status: str) -> None:
    print(f"Progress: {progress}% - {status}")


if __name__ == '__main__':
    deployer = Deployer.from_backtest_uuid(
        backtest_uuid="20250213_204749_04b493",
        oms_name='Telegram',
        scheduler_type='fixed_interval',
        scheduler_interval='1',
        oms_params={'group_id': '-4686173479'},
        progress_callback=dummy_progress,
    )

    # Keep the main thread alive
    while True:
        time.sleep(1)