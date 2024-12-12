import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db.fetch import fetch_latest_date
from data.gather.indian_equity import gather_ohlcv_indian_equity
from data.store.indian_equity import store_indian_equity_gaps
from data.calculate.indian_equity import update_calculated_indicators
from utils.decorators import clear_specific_cache
import pandas as pd

def fill_gap(market_name, timeframe, complete_list=False, index_name='nse_eq_symbols', storage_system = 'finstore'):

    '''
    Fetches the latest date from the database and gathers the ohlcv data from the NSE website.
    Stores the ohlcv data in the database.
    Clears the cache for the fetch_entries function.
    Parameters:
    ----------
    market_name : str
        The name of the market.
    timeframe : str
        The timeframe of the data.
    complete_list : bool, optional
        Whether to fetch the complete list of stocks. Default is False.
    '''
    try : 
        if storage_system == 'sqlite':
            latest_date = fetch_latest_date(market_name=market_name, timeframe=timeframe, storage_system='sqlite')
            symbols, data = gather_ohlcv_indian_equity(timeframe=timeframe, start_date=latest_date, complete_list=complete_list, index_name=index_name)
            
            store_indian_equity_gaps(symbols, data, timeframe, storage_system = 'sqlite')
            update_calculated_indicators(market_name='indian_equity', symbol_list=symbols, timeframe=timeframe, all_entries=complete_list, storage_system = 'sqlite')
        
        elif storage_system == 'finstore':
            latest_date = fetch_latest_date(market_name=market_name, timeframe=timeframe, storage_system='finstore')
            symbols, data = gather_ohlcv_indian_equity(timeframe=timeframe, start_date=latest_date, complete_list=complete_list, index_name=index_name)
            store_indian_equity_gaps(symbols, data, timeframe)
            update_calculated_indicators(market_name='indian_equity', symbol_list=symbols, timeframe=timeframe, all_entries=complete_list)
    except Exception as e:
        print(e)

    try : 
        clear_specific_cache('fetch_entries')
    except Exception as e:
        print(e)

    #clear_specific_cache('fetch_ohlcv_data', market_name=market_name, timeframe=timeframe, all_entries=complete_list)

def fill_gap_new(market_name, timeframe, complete_list=False, index_name='nse_eq_symbols', storage_system = 'finstore'):
    pass


if __name__ == '__main__':
    fill_gap(market_name='indian_equity', timeframe='1d', complete_list=False)