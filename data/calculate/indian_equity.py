import pandas as pd
from utils.flows.indicators_calculate_insert import fetch_calculate_and_insert
from utils.calculation.ema import calculate_ema

def calculate_technical_indicators(market_name, timeframe='1d'):
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_ema, length=50)

if __name__ == "__main__":
    calculate_technical_indicators(market_name='indian_equity', timeframe='1d')
