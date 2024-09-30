import pandas as pd
from functools import wraps
import diskcache as dc
import time
import hashlib
import pickle

# Create a cache object
cache = dc.Cache('database/db')

def result_df_decorator(indicator_name_func):
    def decorator(func):
        @wraps(func)
        def wrapper(df, *args, **kwargs):
            indicator_values = func(df, *args, **kwargs)
            indicator_name = indicator_name_func(*args, **kwargs)
            result_df = pd.DataFrame({
                'timestamp': df['timestamp'],
                'indicator_name': indicator_name,
                'indicator_value': indicator_values
            })
            return result_df
        return wrapper
    return decorator

def cache_decorator(expire=86400):  # Default expiration is 1 day
    """
    Cache decorator for caching the function output based on function's input parameters.
    Cache key is created using a hash of all an input params. 
    Only pickleable input params are considered as part of the cache key -> only rely on caching based on pickleable input params. 

    Input : 
    expire : int (seconds till expiry) : default is 1 day. 

    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            # Filter out non-pickleable objects from args and kwargs
            filtered_args = tuple(arg for arg in args if is_pickleable(arg))
            filtered_kwargs = {k: v for k, v in kwargs.items() if is_pickleable(v)}

            # Create a unique cache key based on function name and filtered arguments
            cache_key = generate_cache_key(func.__name__, filtered_args, filtered_kwargs)

            # Check if result is in cache
            if cache_key in cache:
                return cache[cache_key]

            result = func(*args, **kwargs)

            # Store result in cache with expiration
            cache.set(cache_key, result, expire=expire)

            return result
        return wrapper
    return decorator

def generate_cache_key(func_name, args, kwargs):
    """
    Generate a unique cache key based on function name and arguments.
    """
    return hashlib.md5(pickle.dumps((func_name, args, kwargs))).hexdigest()

def clear_specific_cache(func_name, *args, **kwargs):
    """
    Clear cache for specific function and arguments.
    """
    filtered_args = tuple(arg for arg in args if is_pickleable(arg))
    filtered_kwargs = {k: v for k, v in kwargs.items() if is_pickleable(v)}
    cache_key = generate_cache_key(func_name, filtered_args, filtered_kwargs)
    if cache_key in cache:
        del cache[cache_key]

def update_cache(func_name, result, expire, *args, **kwargs):
    """
    Update cache for specific function and arguments.
    """
    filtered_args = tuple(arg for arg in args if is_pickleable(arg))
    filtered_kwargs = {k: v for k, v in kwargs.items() if is_pickleable(v)}
    cache_key = generate_cache_key(func_name, filtered_args, filtered_kwargs)
    cache.set(cache_key, result, expire=expire)

def cache_period(timeframe):
    if timeframe == '1d':
        return 86400  # 1 day in seconds
    elif timeframe == '1h':
        return 3600  # 1 hour in seconds
    elif timeframe == '15m':
        return 900  # 15 minutes in seconds
    else:
        return 86400  # Default to 1 day

def is_pickleable(obj):
    try:
        pickle.dumps(obj)
        return True
    except (pickle.PicklingError, TypeError):
        return False

def clear_cache():
    """
    Clears the entire cache.
    """
    cache.clear()