from data.gather.crypto_binance import gather_ohlcv_binance
from utils.db.insert import insert_data
from utils.calculation.time import calculate_start_time
from tqdm import tqdm
from finstore.finstore import Finstore

def store_crypto_binance(timeframe='1y', data_points_back=1, type='spot', suffix='USDT'):

    start_time = calculate_start_time(timeframe, data_points_back)
    timeframe = timeframe if timeframe != '1y' else '1d'
    symbols, data = gather_ohlcv_binance(timeframe=timeframe, start_date=start_time, type=type, suffix=suffix)

    finstore = Finstore(market_name='crypto_binance', timeframe=timeframe, enable_append=True)
    finstore.write.symbol_list(data_ohlcv=data)