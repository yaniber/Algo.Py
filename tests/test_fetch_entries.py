import pytest
import pandas as pd
import time
from utils.db.fetch import fetch_entries
from utils.decorators import clear_cache

def test_fetch_entries():
    clear_cache()
    _start_time = time.time()
    result = fetch_entries(market_name='indian_equity', timeframe='1d', all_entries=True)
    end_time = time.time()
    print(f"Time taken: {end_time - _start_time} seconds")
    assert isinstance(result, dict)
    assert all(isinstance(df, pd.DataFrame) for df in result.values())
    assert all(df.shape[1] >= 6 for df in result.values())  # Adjusted to check for at least 6 columns
    assert all('timestamp' in df.columns for df in result.values())
    assert all('open' in df.columns for df in result.values())
    assert all('high' in df.columns for df in result.values())
    assert all('low' in df.columns for df in result.values())
    assert all('close' in df.columns for df in result.values())
    assert all('volume' in df.columns for df in result.values())
    first_df = next(iter(result.values()))
    print("All columns:", first_df.columns)
