import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
from nsepython import nsefetch, nse_eq_symbols
from datetime import datetime, timedelta
from utils.decorators import cache_decorator
import pandas as pd
import requests
from io import StringIO
import time

def fetch_ohlcv_indian_equity(symbol, timeframe, start_date, end_date=datetime.now()):
    '''
    returns data from start_date to end_date for the given symbol.
    Reiterate for all symbols to get all data.
    '''
    try:
        if '.NS' not in symbol and '^' not in symbol:
            symbol = symbol + '.NS'
        data = yf.download(symbol, start=start_date, end=end_date, interval=timeframe)
        data.reset_index(inplace=True)
        data.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
        data.drop(columns=['adj_close'], inplace=True)
        data['timestamp'] = data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        return data
    except Exception as e:
        print('msg=%s, symbol=%s, error=%s', 'Error fetching data for symbol', symbol, str(e))
        return None

@cache_decorator(expire=60*60*24*30)
def fetch_symbol_list_indian_equity(complete_list=False, index_name='nse_eq_symbols'):
    '''
    Fetches the list of all symbols from the NSE website if complete_list = True
    Otherwise fetches only the top 250 stocks.
    index_name : 'all', 'nifty_50', 'nifty_midcap_100', 'nifty_smallcap_100', 'nifty_500', 'nse_eq_symbols'
    '''
    try:
        if index_name == 'nse_eq_symbols':
            return fetch_nse_eq_symbols()

        # Original functionality starts here
        # Get stock lists from indices
        nifty_50_stocks = get_index_stocks_indian_equity('NIFTY 50')
        midcap_100_stocks = get_index_stocks_indian_equity('NIFTY MIDCAP 100')
        smallcap_100_stocks = get_index_stocks_indian_equity('NIFTY SMLCAP 100')
        nifty_500_stocks = get_index_stocks_indian_equity('NIFTY 500')

        # Include the index symbols as well
        nifty_50 = ['^NSEI'] + nifty_50_stocks
        nifty_midcap_100 = ['^NSMIDCP'] + midcap_100_stocks
        nifty_smallcap_100 = ['^NSMCAP'] + smallcap_100_stocks
        nifty_500 = ['^NSE500'] + nifty_500_stocks

        # Combine all symbols
        all_symbols = nifty_50 + nifty_midcap_100 + nifty_smallcap_100

        if complete_list:
            complete_symbols_list = nse_eq_symbols()
            all_symbols = all_symbols + complete_symbols_list

        if index_name == 'nifty_50':
            return list(set(nifty_50))
        elif index_name == 'nifty_midcap_100':
            return list(set(nifty_midcap_100))
        elif index_name == 'nifty_smallcap_100':
            return list(set(nifty_smallcap_100))
        elif index_name == 'nifty_500':
            return list(set(nifty_500))

        # Remove any duplicates
        all_symbols_cleaned = []
        for symbol in all_symbols:
            if '.NS' not in symbol and '^' not in symbol:
                symbol = symbol + '.NS'
            all_symbols_cleaned.append(symbol)

        all_symbols = list(set(all_symbols_cleaned))
        return all_symbols
    except Exception as e:
        print('msg=%s, error=%s', 'Error fetching symbol list', str(e))
        raise Exception(f"Error fetching symbol list: {e}")

def get_index_stocks_indian_equity(index_name):
    '''
    Fetches the list of stocks for the given index name.
    - Used internally
    '''
    try:
        # Fetch stock symbols for the specified index
        if index_name == 'NIFTY 50':
            stocks = nsefetch('https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050')['data']
        elif index_name == 'NIFTY MIDCAP 100':
            stocks = nsefetch('https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20MIDCAP%20100')['data']
        elif index_name == 'NIFTY SMLCAP 100':
            stocks = nsefetch('https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20SMLCAP%20100')['data']
        elif index_name == 'NIFTY 500':
            stocks = nsefetch('https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500')['data']
        return [f"{stock['symbol']}.NS" for stock in stocks]
    except Exception as e:
        print('msg=%s, index_name=%s, error=%s', 'Error fetching index stocks', index_name, str(e))
        raise Exception(f"Error fetching index stocks for {index_name}: {e}")

def fetch_nse_eq_symbols(max_retries=3, delay=5):
    '''
    Fetches the list of all EQ series symbols from the NSE CSV file.
    '''
    url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            df = pd.read_csv(StringIO(response.text))
            eq_symbols = df[df[' SERIES'] == 'EQ']['SYMBOL'].tolist()
            eq_symbols = [f"{symbol}.NS" for symbol in eq_symbols]
            eq_symbols.append('^NSEI')
            return eq_symbols
        except Exception as e:
            print(f'Attempt {attempt + 1} failed. Error: {str(e)}')
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                print('msg=%s, error=%s', 'Error fetching NSE EQ symbols', str(e))
                raise Exception(f"Error fetching NSE EQ symbols: {e}")