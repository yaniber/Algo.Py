import pytest
from data.fetch.indian_equity import fetch_ohlcv_indian_equity
from datetime import datetime

def test_fetch_ohlcv_indian_equity():
    symbol = "RELIANCE.NS"
    timeframe = "1d"
    start_date = datetime(2021, 1, 1)
    data = fetch_ohlcv_indian_equity(symbol, timeframe, start_date)
    
    assert data is not None
    assert 'timestamp' in data.columns
    assert 'open' in data.columns
    assert 'high' in data.columns
    assert 'low' in data.columns
    assert 'close' in data.columns
    assert 'volume' in data.columns