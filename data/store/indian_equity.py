from data.gather.indian_equity import gather_ohlcv_indian_equity
from utils.db.insert import insert_data
from utils.calculation.time import calculate_start_time
from tqdm import tqdm


def store_indian_equity(timeframe='1y', data_points_back=1, complete_list=False):

    start_time = calculate_start_time(timeframe, data_points_back)
    timeframe = timeframe if timeframe != '1y' else '1d'
    symbols, data = gather_ohlcv_indian_equity(timeframe=timeframe, start_date=start_time, complete_list=complete_list)

    for symbol in tqdm(symbols):
        try:
            insert_data(market_name='indian_equity', symbol_name=symbol, timeframe=timeframe, df=data[symbol])
        except Exception as e:
            print(f"Error storing {symbol}: {e}")
            continue