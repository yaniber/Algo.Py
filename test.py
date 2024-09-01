from data.calculate.indian_equity import calculate_technical_indicators
from data.store.indian_equity import store_indian_equity
from utils.calculation.indicators import calculate_supertrend
from utils.flows.fetch_calculate_insert import fetch_calculate_and_insert  
from utils.db.fetch import fetch_entries, clear_cache

if __name__ == '__main__':
    #store_crypto_binance('1y', 1)
    #store_indian_equity('1y', 10)
    #calculate_technical_indicators(market_name='indian_equity', timeframe='1d')
    #result = fetch_entries(market_name='indian_equity', timeframe='1d', all_entries=True)
    #print(result['MRPL.NS'])
    #fetch_calculate_and_insert(market_name='indian_equity', timeframe='1d', calculation_func=calculate_supertrend, atr_multiplier=3.0, length=10)
    clear_cache()