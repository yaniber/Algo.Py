from data.calculate.indian_equity import calculate_technical_indicators
from utils.db.fetch import fetch_entries

if __name__ == '__main__':
    #store_crypto_binance('1y', 1)
    #store_indian_equity('1y', 1)
    calculate_technical_indicators(market_name='indian_equity', timeframe='1d')
    result = fetch_entries(market_name='indian_equity', timeframe='1d', all_entries=True)
    print(result)
