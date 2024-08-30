import pytest
from data.gather.crypto_binance import gather_ohlcv_binance
from datetime import datetime

def test_gather_ohlcv_binance():
    symbols, data = gather_ohlcv_binance(timeframe='1d', start_date=datetime(2021, 1, 1), type='spot', suffix='USDT')
    assert symbols is not None
    assert len(symbols) > 0
    assert data is not None
    assert len(data) > 0