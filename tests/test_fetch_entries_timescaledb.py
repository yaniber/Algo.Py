import pytest
import pandas as pd
import time
from utils.db.fetch import fetch_entries, clear_cache

def test_fetch_entries():
    clear_cache()  # Clear cache before starting the test
    start_time = time.time()  # Start time logging
    result = fetch_entries(market_name='indian_equity', timeframe='1d', all_entries=True)
    end_time = time.time()  # End time logging
    print(f"Time taken for fetch_entries: {end_time - start_time} seconds")
    #print(result)
    assert isinstance(result, dict)
    assert all(isinstance(df, pd.DataFrame) for df in result.values())

