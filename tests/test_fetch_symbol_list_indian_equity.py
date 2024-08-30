import pytest
from data.fetch.indian_equity import fetch_symbol_list_indian_equity

def test_fetch_symbol_list_indian_equity():
    symbols = fetch_symbol_list_indian_equity()
    assert symbols is not None
    assert len(symbols) > 0