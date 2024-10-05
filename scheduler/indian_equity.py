from data.update.indian_equity import fill_gap
from data.fetch.indian_equity import fetch_symbol_list_indian_equity
from utils.db.fetch import fetch_entries
from executor.indian_equity_pipeline import run_pipeline
import pandas as pd
import schedule
import time
from executor.executor import execute_trades_telegram, execute_trades_zerodha
import pytz
from datetime import datetime, timedelta

def pipeline(sim_start):
    
    print("Pipeline started")
    
    symbol_list = fetch_symbol_list_indian_equity(complete_list=False)
    symbol_list_500 = fetch_symbol_list_indian_equity(complete_list=False, index_name='nifty_500')
    fill_gap(market_name='indian_equity', timeframe='1d', complete_list=False)
    
    ohlcv_data = fetch_entries(market_name='indian_equity', timeframe='1d', all_entries=False, symbol_list=symbol_list)
    
    sim_end = pd.Timestamp.now().strftime('%Y-%m-%d 00:00:00')
    fresh_buys, fresh_sells = run_pipeline(ohlcv_data, sim_start, sim_end, complete_list=False)
    
    execute_trades_telegram(fresh_buys)
    execute_trades_telegram(fresh_sells)
    
    successful_trades, failed_trades = execute_trades_zerodha(fresh_buys)
    successful_trades_sell, failed_trades_sell = execute_trades_zerodha(fresh_sells)


def Scheduler(sim_start):
    '''
    Scheduler function that runs the pipeline every day at 6 pm IST to get fresh orders and sells from pipeline.
    '''
    ist = pytz.timezone('Asia/Kolkata')
    utc = pytz.UTC

    # Desired time to run the job (17:40 IST)
    target_time_ist = datetime.now(ist).replace(hour=4, minute=30, second=0, microsecond=0)

    # Convert the target time to UTC
    target_time_utc = target_time_ist.astimezone(utc).time()

    # Schedule the job at the converted UTC time
    schedule.every().day.at(target_time_utc.strftime('%H:%M')).do(pipeline, sim_start)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    sim_start = pd.Timestamp.now() - pd.Timedelta(days=2)
    Scheduler(sim_start)