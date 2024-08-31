import pandas as pd
from utils.flows.indicators_calculate_insert import fetch_calculate_and_insert
from utils.calculation.ema import calculate_ema

def calculate_technical_indicators(market_name, timeframe='1d'):
    '''
    One time run function for calculating all custom indicators for a given market.
    Calculates and saves the indicator results into database.
    '''
    fetch_calculate_and_insert(market_name=market_name, timeframe=timeframe, calculation_func=calculate_ema, length=100)

if __name__ == "__main__":
    calculate_technical_indicators(market_name='indian_equity', timeframe='1d')
