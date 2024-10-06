from utils.db.fetch import fetch_entries
from data.fetch.indian_equity import fetch_symbol_list_indian_equity
from executor.executor import get_fresh_trades
from executor.monitor import TradeMonitor
import pandas as pd
from utils.data.dataframe import get_top_symbols_by_average_volume
pd.set_option('future.no_silent_downcasting', True)

def run_pipeline(ohlcv_data : pd.DataFrame, 
                 sim_start : pd.Timestamp, 
                 sim_end : pd.Timestamp, 
                 complete_list : bool = False, 
                 symbol_list : list = [], 
                 weekday : int = 2,
                 init_cash : float = 100000):

    """
    Run the pipeline in intervals defined by sim_start and sim_end
    """
    
    #symbol_list = fetch_symbol_list_indian_equity(complete_list=complete_list)
    if symbol_list == []:
        symbol_list = get_top_symbols_by_average_volume(ohlcv_data, 1200)

    trade_monitor = TradeMonitor()
    fresh_buys, fresh_sells = get_fresh_trades(ohlcv_data, symbol_list, trade_monitor, sim_start, sim_end, weekday, init_cash)

    return fresh_buys, fresh_sells

def Scheduler():
    
    start_timestamp = pd.to_datetime('2024-09-01')
    end_timestamp = pd.to_datetime('2024-09-30')

    ohlcv_data = fetch_entries(market_name='indian_equity', timeframe='1d', all_entries=True)

    for date in pd.date_range(start=start_timestamp + pd.Timedelta(days=1), end=end_timestamp):

        date_str = date.strftime('%Y-%m-%d 00:00:00')

        trimmed_ohlcv_data = {symbol: df[df['timestamp'] <= date_str] for symbol, df in ohlcv_data.items()}

        fresh_buys, fresh_sells = run_pipeline(trimmed_ohlcv_data, start_timestamp, date)

        print(f"Date: {date}")
        if fresh_buys.empty and fresh_sells.empty:
            pass
        else:
            print(f"Fresh Buys: {fresh_buys}")
            print(f"Fresh Sells: {fresh_sells}")
        print()

if __name__ == "__main__":
    Scheduler()