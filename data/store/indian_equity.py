from data.gather.indian_equity import gather_ohlcv_indian_equity
from utils.db.insert import insert_data
from utils.calculation.time import calculate_start_time
from tqdm import tqdm
from utils.db.batch import BatchInserter
from finstore.finstore import Finstore
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv(dotenv_path='config/.env')

# Access the DATABASE_PATH environment variable
database_path = os.getenv('DATABASE_PATH')


def store_indian_equity(timeframe='1y', data_points_back=1, complete_list=False, index_name='nse_eq_symbols', storage_system = 'finstore'):

    start_time = calculate_start_time(timeframe, data_points_back)
    timeframe = timeframe if timeframe != '1y' else '1d'
    symbols, data = gather_ohlcv_indian_equity(timeframe=timeframe, start_date=start_time, complete_list=complete_list, index_name=index_name)
    
    if storage_system == 'sqlite':
        batch_inserter = BatchInserter(database_path=database_path, table='ohlcv_data')

        for symbol in tqdm(symbols):
            try:
                insert_data(batch_inserter=batch_inserter, market_name='indian_equity', symbol_name=symbol, timeframe=timeframe, df=data[symbol])
            except Exception as e:
                print(f"Error storing {symbol}: {e}")
                continue
        batch_inserter.stop()
    elif storage_system == 'finstore':
        finstore = Finstore(market_name='indian_equity', timeframe='1d', enable_append=True)
        finstore.write.symbol_list(data_ohlcv=data)


def store_indian_equity_gaps(symbols, data, timeframe, storage_system = 'finstore'):

    if storage_system == 'sqlite':
        batch_inserter = BatchInserter(database_path=database_path, table='ohlcv_data')

        for symbol in tqdm(symbols):
            try:
                insert_data(batch_inserter=batch_inserter, market_name='indian_equity', symbol_name=symbol, timeframe=timeframe, df=data[symbol])
            except Exception as e:
                print(f"Error storing {symbol}: {e}")
                continue
        batch_inserter.stop()
    
    elif storage_system == 'finstore':
        finstore = Finstore(market_name='indian_equity', timeframe='1d', enable_append=True)
        finstore.write.symbol_list(data_ohlcv=data)

if __name__ == "__main__":
    store_indian_equity(timeframe='1y', data_points_back=10, complete_list=False)