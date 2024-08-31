import pandas as pd
from utils.db.fetch import fetch_entries
from utils.db.insert import insert_data
from utils.calculation.ema import calculate_ema

def fetch_calculate_and_insert(market_name, timeframe, calculation_func, **calculation_kwargs):
    ohlcv_data = fetch_entries(market_name=market_name, timeframe=timeframe, all_entries=True)
    if not ohlcv_data:
        print(f"No OHLCV data found for market: {market_name} and timeframe: {timeframe}")
        return

    for symbol, df in ohlcv_data.items():
        indicator_df = calculation_func(df, **calculation_kwargs)
        insert_data(market_name=market_name, symbol_name=symbol, timeframe=timeframe, df=indicator_df, indicators=True, indicators_df=indicator_df)

    print(f"{calculation_func.__name__} calculation and insertion completed for market: {market_name} and timeframe: {timeframe}")

if __name__ == "__main__":
    fetch_calculate_and_insert(
        market_name='indian_equity',
        timeframe='1d',
        calculation_func=calculate_ema,
        length=20
    )