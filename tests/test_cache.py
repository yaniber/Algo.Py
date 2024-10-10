import pytest
import time
from utils.decorators import cache_decorator, clear_cache, fetch_cache_by_function, clear_specific_cache

@cache_decorator()
def test_function(x, y):
    return x + y

@cache_decorator(expire=1)
def test_function_with_expiry(x):
    return x * 2

def test_basic_caching():
    clear_cache()  # Start with a clean cache
    
    # First call should compute the result
    result1 = test_function(2, 3)
    assert result1 == 5
    
    # Second call should return cached result
    result2 = test_function(2, 3)
    assert result2 == 5
    
    # Different arguments should compute a new result
    result3 = test_function(3, 4)
    assert result3 == 7

def test_cache_expiry():
    clear_cache()  # Start with a clean cache
    
    # First call should compute the result
    result1 = test_function_with_expiry(5)
    assert result1 == 10
    
    # Second call should return cached result
    result2 = test_function_with_expiry(5)
    assert result2 == 10
    
    # Wait for cache to expire
    time.sleep(3)
    
    # This call should recompute the result
    result3 = test_function_with_expiry(5)
    assert result3 == 10

def test_fetch_cache_by_function():
    clear_cache()  # Start with a clean cache
    
    test_function(1, 2)
    test_function(3, 4)
    
    cached_results = fetch_cache_by_function('test_function')
    assert len(cached_results) == 2

def test_clear_specific_cache():
    clear_cache()  # Start with a clean cache
    
    test_function(1, 2)
    test_function(3, 4)
    test_function(1, 3)
    
    clear_specific_cache('test_function', x=1)
    
    cached_results = fetch_cache_by_function('test_function')
    assert len(cached_results) == 1  # Only (3, 4) should remain

if __name__ == "__main__":
    pytest.main()