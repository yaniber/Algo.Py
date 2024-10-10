import pandas as pd
from functools import wraps
import diskcache as dc
import time
import hashlib
import pickle
import inspect

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
        # Get the function's signature
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key that includes the function name and all parameters
            key_parts = [func.__name__]

            # Add positional arguments with their parameter names
            key_parts.extend(f"{param_names[i]}={arg}" for i, arg in enumerate(args))

            # Add keyword arguments
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

            cache_key = "/".join(key_parts)

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
    key_structure = (func_name, args, tuple(sorted(kwargs.items())))
    return hashlib.md5(pickle.dumps(key_structure)).hexdigest()

def clear_specific_cache(func_name, **param_filters):
    """
    Clear cache entries for a specific function.
    If param_filters are provided, only clear entries matching those filters.
    If no param_filters are provided, clear all entries for the function.
    """
    keys_to_delete = []
    
    for key in cache.iterkeys():
        key_str = str(key)
        parts = key_str.split('/')
        
        if parts[0] != func_name:
            continue
        
        if not param_filters:
            # If no filters are provided, add all keys for this function
            keys_to_delete.append(key)
        else:
            # Extract parameters from the key
            params = dict(part.split('=') for part in parts[1:] if '=' in part)
            
            # Check if all provided filters match
            if all(params.get(k) == str(v) for k, v in param_filters.items()):
                keys_to_delete.append(key)

    # Delete the identified keys
    deleted_count = 0
    for key in keys_to_delete:
        try:
            if cache.delete(key):
                deleted_count += 1
            else:
                print(f"Key not found or couldn't be deleted: {key}")
        except KeyError:
            # Key not found, just skip it
            print(f"Key not found: {key}")
            pass
        except Exception as e:
            print(f"Error deleting key {key}: {e}")

    return deleted_count  # Return number of successfully deleted keys

def update_cache(func_name, result, expire, **param_filters):
    """
    Update cache for a specific function entry based on partial parameters.
    """
    for key in cache.iterkeys():
        key_str = str(key)
        parts = key_str.split('/')
        
        if parts[0] != func_name:
            continue
        
        # Extract parameters from the key
        params = dict(part.split('=') for part in parts[1:] if '=' in part)
        
        # Check if all provided filters match
        if all(params.get(k) == str(v) for k, v in param_filters.items()):
            cache.set(key, result, expire=expire)
            return True  # Successfully updated
    
    return False  # No matching entry found

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

def fetch_cache_keys(func_name : str = None) -> dict:
    """
    Fetch all cache keys, optionally filtered by function name.
    
    Args:
    func_name (str, optional): If provided, only fetch keys for this function.
    
    Returns:
    dict: A dictionary where keys are function names and values are lists of cache keys.
    """
    cache_keys = {}
    
    for key in cache.iterkeys():
        key_str = str(key)
        parts = key_str.split('/')
        
        if not parts:
            continue
        
        current_func_name = parts[0]
        
        if func_name is None or current_func_name == func_name:
            if current_func_name not in cache_keys:
                cache_keys[current_func_name] = []
            cache_keys[current_func_name].append(key_str)
    
    return cache_keys