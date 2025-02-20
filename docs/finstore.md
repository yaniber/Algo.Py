<!-- File: finstore.md -->
# FinStore

**FinStore** is the custom data layer for **Algo.Py**—optimized for fast data storage, retrieval, and incremental updates using DuckDB and Parquet.

## Key Features

- **Organized Data Storage:** Data is structured by market (e.g., `crypto_binance`, `indian_equity`) and timeframe (e.g., 1d, 4h). Files are stored in the `database/finstore` directory.
- **Efficient Storage:** Uses Parquet for compressed, columnar storage.
- **Simplified API:** A straightforward API (`Finstore`) for reading/writing OHLCV data and technical indicators.
- **Incremental Updates:** Add new data without overwriting existing files.
- **Caching:** Integrated caching (using `diskcache`) improves performance.

## Exploring FinStore

Browse the `database/finstore` directory to see data organized by market and timeframe. Each symbol’s folder contains files like `ohlcv_data.parquet` and `technical_indicators.parquet`.

## Using FinStore Programmatically

```python
from finstore.finstore import Finstore

# Initialize FinStore
finstore = Finstore(market_name='crypto_binance', timeframe='4h', pair='BTC')

# Get available symbols
symbol_list = finstore.read.get_symbol_list()
print(symbol_list)

# Fetch data for one symbol
symbol, ohlcv_data = finstore.read.symbol(symbol_list[0])
print(symbol)
print(ohlcv_data.head())

# Get merged dataframe (OHLCV + indicators)
symbol, merged_df = finstore.read.merged_df(symbol_list[0])
print(symbol)
print(merged_df.head())

# Calculate and write a technical indicator (e.g., EMA)
from utils.calculation.indicators import calculate_ema
ohlcv_data_dict = finstore.read.symbol_list(symbol_list=symbol_list)
finstore.write.indicator(ohlcv_data=ohlcv_data_dict, calculation_func=calculate_ema, length=20)
```

## Extending FinStore

Feel free to extend FinStore’s functionality to support additional data sources or technical indicators.
