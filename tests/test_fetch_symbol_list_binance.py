import pytest
from data.fetch.crypto_binance import fetch_symbol_list_binance

def test_fetch_symbol_list_binance():
    symbols = fetch_symbol_list_binance()
    assert symbols is not None
    assert len(symbols) > 0