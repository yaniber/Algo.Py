Using FinStore
==============

FinStore is the custom data layer of Algo.Py, providing a convenient way to manage and access financial data.  It's built on top of DuckDB for efficient data storage and retrieval, using Parquet files for compressed, columnar data storage.

Key Features of FinStore
------------------------

*   **Organized Data Storage:** Data is organized by market (e.g., `crypto_binance`, `indian_equity`) and timeframe (e.g., `1d`, `4h`, `1h`, `15m`). The base directory is `database/finstore`.
*   **Parquet Format:** Uses the Parquet file format for efficient storage and retrieval of large datasets.
*   **Simplified API:** Provides a simple API for reading and writing OHLCV data and technical indicators.
*   **Append Functionality:** You can add new data without overwriting old data, making it ideal for live trading and updating historical data.
*   **Caching:**  Data reads are cached for improved performance (using `diskcache`).

Exploring FinStore
-----------------

You can manually explore the FinStore data by navigating to the `database/finstore` directory. Inside, you'll find subdirectories organized by market and timeframe. Each symbol will have its own directory, containing Parquet files for `ohlcv_data.parquet` and `technical_indicators.parquet`.

Using FinStore Programmatically
---------------------------------

The `Finstore` class provides a Python API for interacting with the data.

.. code-block:: python

    from finstore.finstore import Finstore

    # Initialize FinStore
    finstore = Finstore(market_name='crypto_binance', timeframe='4h', pair='BTC')

    # Get all available symbols
    symbol_list = finstore.read.get_symbol_list()
    print(symbol_list)
    # Example Output: ['1INCHBTC', 'AAVEBTC', ... ] (list may vary)

    # Fetch data for a single symbol
    symbol, ohlcv_data = finstore.read.symbol(symbol_list[0])
    print(symbol)
    print(ohlcv_data.head()) # Displays the top 5 entries

    # Fetch merged dataframe (OHLCV + indicators)
    symbol, merged_df = finstore.read.merged_df(symbol_list[0])
    print(symbol)
    print(merged_df.head())

    # Calculate and write a technical indicator
    from utils.calculation.indicators import calculate_ema
    ohlcv_data_dict = finstore.read.symbol_list(symbol_list=symbol_list) # Get a dictionary of all the dataframes.
    finstore.write.indicator(ohlcv_data=ohlcv_data_dict, calculation_func=calculate_ema, length=20)

Contributing Strategies
-----------------------

You can contribute your own strategies to the Algo.Py platform.  Strategies are organized within the `strategy/public` directory.  To add a new strategy:

1.  **Create a New Python File:** Create a new Python file within the `strategy/public` directory (e.g., `my_new_strategy.py`).

2.  **Implement the Strategy Class:**  Define a class that inherits from `strategy.strategy_builder.StrategyBaseClass`. Your class *must* implement the `run` method. See the :ref:`strategy_development` section for detailed guidelines.

3.  **Automatic Registration:** The `strategy.strategy_registry` module automatically discovers and registers strategies in the `strategy/public` directory.  You *do not* need to manually add your strategy to a list. As long as it's in the `strategy/public` directory and inherits from `StrategyBaseClass`, it will be found.

4.  **Test Your Strategy:** Use the backtesting functionality to thoroughly test your strategy's performance.