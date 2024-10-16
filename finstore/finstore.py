import duckdb
import os
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import concurrent.futures
from tqdm import tqdm
import os
import sys
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Finstore:
    def __init__(self, market_name :str , timeframe : str, base_directory : str ='database/finstore', enable_append : bool = True, limit_data_lookback : int = -1):
        self.base_directory = base_directory
        self.market_name = market_name
        self.timeframe = timeframe
        self.enable_append = enable_append
        self.limit_data_lookback = limit_data_lookback
        self.read = self.Read(self)
        self.write = self.Write(self)

    class Read: 
        def __init__(self, finstore_instance):
            self.market_name = finstore_instance.market_name
            self.timeframe = finstore_instance.timeframe
            self.base_directory = finstore_instance.base_directory

        def symbol(self, symbol : str):
            
            """
            Reads the Parquet file for a given symbol and returns it as a DataFrame.

            Args:
                symbol (str): The symbol to read data for.

            Returns:
                tuple: A tuple containing the symbol and its corresponding DataFrame.
            """

            file_path = os.path.join(self.base_directory, f"market_name={self.market_name}", f"timeframe={self.timeframe}", symbol, 'ohlcv_data.parquet')
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"Parquet file not found for symbol '{symbol}' at '{file_path}'")

            conn = duckdb.connect()
            conn.execute("PRAGMA threads=4")  # Use multiple threads for parallel reading

            df = conn.execute(f"SELECT * FROM read_parquet('{file_path}')").fetchdf()
            conn.close()
            
            return symbol, df
        
        def merged_df(self, symbol : str):
            
            """
            Reads the Merged Df for ohlcv and technical indicators data files for a given symbol and returns it as a DataFrame.

            Args:
                symbol (str): The symbol to read data for.

            Returns:
                tuple: A tuple containing the symbol and its corresponding DataFrame.
            """
            
            file_path = os.path.join(self.base_directory, f"market_name={self.market_name}", f"timeframe={self.timeframe}", symbol, 'ohlcv_data.parquet')
            technical_indicators_path = os.path.join(self.base_directory, f"market_name={self.market_name}", f"timeframe={self.timeframe}", symbol, 'technical_indicators.parquet')

            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"Parquet file not found for symbol '{symbol}' at '{file_path}'")
            if not os.path.isfile(technical_indicators_path):
                raise FileNotFoundError(f"Technical indicators file not found for symbol '{symbol}' at '{technical_indicators_path}'")

            conn = duckdb.connect()
            conn.execute("PRAGMA threads=4")  # Use multiple threads for parallel reading

            df = conn.execute(f"SELECT * FROM read_parquet('{file_path}')").fetchdf()
            technical_indicators_df = conn.execute(f"SELECT * FROM read_parquet('{technical_indicators_path}')").fetchdf()
            technical_indicators_df = technical_indicators_df.drop_duplicates(subset=['timestamp', 'indicator_name'])
            technical_indicators_df = technical_indicators_df.pivot(index='timestamp', columns='indicator_name', values='indicator_value').reset_index()
            merged_df = df.merge(technical_indicators_df, on='timestamp', how='left')

            conn.close()

            return symbol, merged_df

        def symbol_list(self, symbol_list : list, merged_dataframe : bool = False):
            
            """
            Reads the Parquet files for all given symbols in parallel and returns a dictionary with the results.

            Args:
                symbol_list (list): List of symbols to read data for.

            Returns:
                dict: A dictionary with symbols as keys and their corresponding DataFrames as values.
            """
            
            results = {}
            with ProcessPoolExecutor() as executor:
                if merged_dataframe:
                    futures = {executor.submit(self.merged_df, symbol): symbol for symbol in symbol_list}
                else:
                    futures = {executor.submit(self.symbol, symbol): symbol for symbol in symbol_list}
                for future in futures:
                    symbol = futures[future]
                    try:
                        symbol, df = future.result()
                        results[symbol] = df
                    except Exception as e:
                        print(f"Error reading data for symbol {symbol}: {e}")
            
            return results
        
        def get_symbol_list(self):
            
            """
            Reads the symbol list for a given market and timeframe.

            Returns:
                list: A list of symbols.
            """

            file_path = os.path.join(self.base_directory, f"market_name={self.market_name}", f"timeframe={self.timeframe}")
            if not os.path.isdir(file_path):
                raise FileNotFoundError(f"Directory not found for market '{self.market_name}' at '{file_path}'")
            
            symbol_list = [folder for folder in os.listdir(file_path) if os.path.isdir(os.path.join(file_path, folder))]
            return symbol_list  
    
    class Write:
        """
        Writes data to the finstore.

        Args:
            appends (bool) : enable appends if file already exists, useful for adding future data or more technical indicators.

        Functions:
            symbol(self, symbol : str, data : pd.DataFrame) : writes symbol ohlcv to parquet file.
            indicator(self, ohlcv_data : dict, calculation_func : callable, **calculation_kwargs) : writes technical indicators to parquet file.
        """
        def __init__(self, finstore_instance):
            self.market_name = finstore_instance.market_name
            self.timeframe = finstore_instance.timeframe
            self.base_directory = finstore_instance.base_directory
            self.enable_append = finstore_instance.enable_append
            self.limit_data_lookback = finstore_instance.limit_data_lookback

    
        def symbol(self, symbol : str, data : pd.DataFrame):

            """
            Writes to Parquet file for a given symbol and it's ohlcv DataFrame.

            Args:
                symbol (str): The symbol to write data for.
                data (pd.Dataframe) : The ohlcv dataframe for symbol.
            """

            dir_path = os.path.join(self.base_directory, f"market_name={self.market_name}", f"timeframe={self.timeframe}", symbol)
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, 'ohlcv_data.parquet')

            if os.path.isfile(file_path) and self.enable_append:
                existing_df = pd.read_parquet(file_path)
                data = pd.concat([existing_df, data], ignore_index=True)
                data = data.drop_duplicates(subset=['timestamp'])

            data.to_parquet(file_path, index=False, compression='zstd')

        def symbol_list(self, data_ohlcv : pd.DataFrame):
            
            """
            Writes the Parquet files for all given symbols in parallel.

            Args:
                symbol_list (list): List of symbols to read data for.

            Returns:
                None
            """
            
            with ProcessPoolExecutor() as executor:
                futures = {executor.submit(self.symbol, symbol, data): symbol for symbol, data in data_ohlcv.items()}
                for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Writing symbols"):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Error writing data for symbol : {e}")

        def technical_data(self, symbol : str, indicators_df: pd.DataFrame):
            
            """
            Write technical indicators data to a parquet file.

            Args:
            symbol (str) : the symbol name you are saving technical values for.
            indicators_df (pd.Dataframe) : must be formatted using results_df decorator.
            """
            
            file_path = os.path.join(self.base_directory, f"market_name={self.market_name}", f"timeframe={self.timeframe}", symbol, 'technical_indicators.parquet')
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            indicators_df['symbol'] = symbol
            indicators_df['timeframe'] = self.timeframe
            formatted_df = indicators_df[['symbol', 'timeframe', 'timestamp', 'indicator_name', 'indicator_value']]
            formatted_df.loc[:, 'indicator_value'] = formatted_df['indicator_value'].astype(float)

            if os.path.isfile(file_path) and self.enable_append:
                existing_df = pd.read_parquet(file_path)
                formatted_df = pd.concat([existing_df, formatted_df], ignore_index=True)
                formatted_df = formatted_df.drop_duplicates(subset=['timestamp', 'indicator_name', 'symbol', 'timeframe'])
            
            formatted_df.to_parquet(file_path, index=False, compression='zstd')

        def process_indicator(self, symbol, df, calculation_func, calculation_kwargs):
            
            """
            Process data for each symbol and write technical indicators to a parquet file.
            
            Args:
            symbol (str): Symbol name.
            df (pd.DataFrame): OHLCV data DataFrame.
            calculation_func (callable): Function to calculate indicators.
            calculation_kwargs (dict): Keyword arguments for the indicator calculation function.
            """
            
            try:
                if self.limit_data_lookback > 0:
                    df = df.iloc[-self.limit_data_lookback:]
                indicators_df = calculation_func(df, **calculation_kwargs)
                self.technical_data(symbol=symbol, indicators_df=indicators_df)
            except Exception as e:
                print(f"Error calculating {calculation_func.__name__} for {symbol}: {e}")
                return

        def indicator(self, ohlcv_data, calculation_func, **calculation_kwargs):

            """
            Writes technical_indicator file for all symbols in the ohlcv_data df.

            Args:
                ohlcv_data (dict) : dictionary of format {symbol : df}
                calculation_func (function) : should be wrapped with results_df decorator. 
                calculation_kwargs : arguments for your calculation function.
            """
            
            use_multiprocessing = True
            if use_multiprocessing:
                with ProcessPoolExecutor() as executor:
                    futures = [
                        executor.submit(self.process_indicator, symbol, df, calculation_func, calculation_kwargs)
                        for symbol, df in ohlcv_data.items()
                    ]
                    for _ in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing symbols"):
                        pass  # Wait for all futures to complete
            else:
                for symbol, df in tqdm(ohlcv_data.items(), desc="Processing symbols"):
                    self.process_indicator(symbol, df, calculation_func, calculation_kwargs)

            print(f"{calculation_func.__name__} calculation and insertion completed for market: {self.market_name} and timeframe: {self.timeframe}")

