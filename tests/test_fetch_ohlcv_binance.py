import pytest
from data.fetch.crypto_binance import fetch_ohlcv_binance
from datetime import datetime

def test_fetch_ohlcv_binance():
    symbol = "BTC/USDT"
    timeframe = "1d"
    start_date = datetime(2021, 1, 1)
    data = fetch_ohlcv_binance(symbol, timeframe, start_date)
    
    assert data is not None
    assert 'timestamp' in data.columns
    assert 'open' in data.columns
    assert 'high' in data.columns
    assert 'low' in data.columns
    assert 'close' in data.columns
    assert 'volume' in data.columns