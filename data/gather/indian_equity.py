from data.fetch.indian_equity import fetch_ohlcv_indian_equity, fetch_symbol_list_indian_equity
from tqdm import tqdm
from utils.decorators import cache_decorator

@cache_decorator()
def gather_ohlcv_indian_equity(timeframe='1d', start_date=None, complete_list=False):
    '''
    Gathers OHLCV data from Binance for all symbols that match the given type and suffix.

    timeframe: '1d', '1h', '15m', '5m', '1m'
    start_date: datetime object
    complete_list: True or False

    Output:
    data: dict of {symbol: df}
    '''
    symbols = fetch_symbol_list_indian_equity(complete_list)
    data = {symbol: df for symbol in tqdm(symbols) if (df := fetch_ohlcv_indian_equity(symbol, timeframe, start_date)) is not None}

    return symbols, data
