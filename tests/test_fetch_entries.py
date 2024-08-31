import pytest
import pandas as pd
from utils.db.fetch import fetch_entries

def test_fetch_entries():
    result = fetch_entries(market_name='Test Market', timeframe='1d', symbol_list=['TEST'], all_entries=False)
    print(result)
    assert isinstance(result, dict)
    assert all(isinstance(df, pd.DataFrame) for df in result.values())
    assert len(result) == 1
    assert all(df.shape[0] > 0 for df in result.values())
    assert all(df.shape[1] >= 6 for df in result.values())  # Adjusted to check for at least 6 columns
    assert all('timestamp' in df.columns for df in result.values())
    assert all('open' in df.columns for df in result.values())
    assert all('high' in df.columns for df in result.values())
    assert all('low' in df.columns for df in result.values())
    assert all('close' in df.columns for df in result.values())
    assert all('volume' in df.columns for df in result.values())
    assert all('ema' in df.columns for df in result.values())
    for symbol, df in result.items():
        print(f"Open prices for {symbol}:")
        print(df['open'])
    # Check for at least one technical indicator column
    assert all(any(col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume'] for col in df.columns) for df in result.values())
