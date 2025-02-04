from data.fetch.crypto_binance import fetch_ohlcv_binance, fetch_symbol_list_binance
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import os
import sys
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def gather_ohlcv_binance(timeframe='1d', start_date=None, type='spot', suffix='USDT'):
    symbols = fetch_symbol_list_binance(type, suffix)
    
    data = {}
    with ThreadPoolExecutor(max_workers=10) as executor:  # Reduced workers
        future_to_symbol = {executor.submit(fetch_ohlcv_binance, symbol, timeframe, start_date): symbol 
                          for symbol in symbols}
        
        with tqdm(total=len(symbols), desc="Fetching symbols") as pbar:
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    # Always include symbol even if DataFrame is empty
                    data[symbol] = result
                except Exception as e:
                    data[symbol] = pd.DataFrame()  # Ensure empty entry
                pbar.update(1)

    return symbols, data
