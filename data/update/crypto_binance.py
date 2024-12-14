import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db.fetch import fetch_latest_date
from data.gather.crypto_binance import gather_ohlcv_binance
from data.store.crypto_binance import store_crypto_binance_gaps
from data.calculate.crypto_binance import update_calculated_indicators
from utils.decorators import clear_specific_cache
import pandas as pd

def fill_gap(market_name='crypto_binance', timeframe='4h', complete_list=False, index_name='nse_eq_symbols', storage_system = 'finstore', pair='BTC'):

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
    pair : str, optional
        The pair to fetch the data for. Default is 'BTC'.
    '''
    try:
        latest_date = fetch_latest_date(market_name=market_name, timeframe=timeframe, storage_system=storage_system, pair=pair)
        print(f'latest date : {latest_date}')
        clear_specific_cache('gather_ohlcv_binance')
        symbols, data = gather_ohlcv_binance(timeframe=timeframe, start_date=latest_date, type='spot', suffix=pair)
        store_crypto_binance_gaps(symbols, data, timeframe=timeframe, pair=pair)
        latest_date = fetch_latest_date(market_name=market_name, timeframe=timeframe, storage_system=storage_system, pair=pair)
        print(f'latest date after storing: {latest_date}')
        update_calculated_indicators(market_name=market_name, symbol_list=symbols, timeframe=timeframe, all_entries=False, pair=pair)
    except Exception as e:
        print(e)

    clear_specific_cache('fetch_entries')

    #clear_specific_cache('fetch_ohlcv_data', market_name=market_name, timeframe=timeframe, all_entries=complete_list)

def fill_gap_new(market_name, timeframe, complete_list=False, index_name='nse_eq_symbols', storage_system = 'finstore'):
    pass


if __name__ == '__main__':
    fill_gap(market_name='indian_equity', timeframe='1d', complete_list=False)