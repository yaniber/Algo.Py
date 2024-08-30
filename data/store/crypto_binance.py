from data.gather.crypto_binance import gather_ohlcv_binance
from utils.db.insert import insert_data
from utils.calculation.time import calculate_start_time
from tqdm import tqdm


def store_crypto_binance(timeframe='1y', data_points_back=1, type='spot', suffix='USDT'):

    start_time = calculate_start_time(timeframe, data_points_back)
    timeframe = timeframe if timeframe != '1y' else '1d'
    symbols, data = gather_ohlcv_binance(timeframe=timeframe, start_date=start_time, type=type, suffix=suffix)

    for symbol in tqdm(symbols):
        try:
            insert_data(market_name='crypto', symbol_name=symbol, timeframe=timeframe, df=data[symbol])
        except Exception as e:
            print(f"Error storing {symbol}: {e}")
            continue