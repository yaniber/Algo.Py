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
    def __init__(self, market_name :str , timeframe : str, base_directory : str ='database/finstore'):
        self.base_directory = base_directory
        self.market_name = market_name
        self.timeframe = timeframe
    
    def read_parquet_for_symbol(self, symbol : str):
        
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
    
    def read_merged_df_for_symbol(self, symbol : str):
        
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

    def read_symbol_list(self, symbol_list : list, merged_dataframe : bool = False):
        
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
                futures = {executor.submit(self.read_merged_df_for_symbol, symbol): symbol for symbol in symbol_list}
            else:
                futures = {executor.submit(self.read_parquet_for_symbol, symbol): symbol for symbol in symbol_list}
            for future in futures:
                symbol = futures[future]
                try:
                    symbol, df = future.result()
                    results[symbol] = df
                except Exception as e:
                    print(f"Error reading data for symbol {symbol}: {e}")
        
        return results
    
    def save_symbol_data(self, symbol : str, data : pd.DataFrame):

        dir_path = os.path.join(self.base_directory, f"market_name={self.market_name}", f"timeframe={self.timeframe}", symbol)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, 'ohlcv_data.parquet')

        data.to_parquet(file_path, index=False, compression='zstd')


    def save_technical_data(self, symbol : str, indicators_df: pd.DataFrame, enable_appends : bool = True):
        
        """
        Write technical indicators data to a parquet file.

        Args:
        symbol (str) : the symbol name you are saving technical values for.
        indicators_df (pd.Dataframe) : must be formatted using results_df decorator.
        enable_appends (bool) : enable appends if file already exists, useful for adding future data or more technical indicators.
        """
        
        file_path = os.path.join(self.base_directory, f"market_name={self.market_name}", f"timeframe={self.timeframe}", symbol, 'technical_indicators.parquet')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        indicators_df['symbol'] = symbol
        indicators_df['timeframe'] = self.timeframe
        formatted_df = indicators_df[['symbol', 'timeframe', 'timestamp', 'indicator_name', 'indicator_value']]
        formatted_df.loc[:, 'indicator_value'] = formatted_df['indicator_value'].astype(float)

        if os.path.isfile(file_path) and enable_appends:
            existing_df = pd.read_parquet(file_path)
            formatted_df = pd.concat([existing_df, formatted_df], ignore_index=True)
        
        formatted_df.to_parquet(file_path, index=False)

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
            indicators_df = calculation_func(df, **calculation_kwargs) 
        except Exception as e:
            print(f"Error calculating {calculation_func.__name__} for {symbol}: {e}")
            return
        self.save_technical_data(symbol_name=symbol, indicators_df=indicators_df)

    def calculate_and_save_indicator(self, ohlcv_data, calculation_func, **calculation_kwargs):
        
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

