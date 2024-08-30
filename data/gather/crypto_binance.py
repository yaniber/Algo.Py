from fetch import fetch_ohlcv_binance, fetch_symbol_list_binance
from datetime import datetime, timedelta

import os
import sys
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def gather_ohlcv_binance(timeframe='1d', start_date=None, type='spot', suffix='USDT'):
    '''
    Gathers OHLCV data from Binance for all symbols that match the given type and suffix.

    timeframe: '1d', '1h', '15m', '5m', '1m'
    start_date: datetime object
    type: 'spot' or 'futures' #change
    suffix: 'USDT' or 'BTC'

    Output:
    data: dict of {symbol: df}
    '''
    symbols = fetch_symbol_list_binance(type, suffix)
    data = {symbol: df for symbol in symbols if (df := fetch_ohlcv_binance(symbol, timeframe, start_date)) is not None}
    return data
