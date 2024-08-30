import pytest
from data.gather.indian_equity import gather_ohlcv_indian_equity
from datetime import datetime

def test_gather_ohlcv_indian_equity():
    symbols, data = gather_ohlcv_indian_equity(timeframe='1d', start_date=datetime(2021, 1, 1), complete_list=False)
    assert symbols is not None
    assert len(symbols) > 0
    assert data is not None
    assert len(data) > 0