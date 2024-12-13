import pandas as pd
from functools import wraps
import diskcache as dc
import time
import hashlib
import pickle
import inspect
import time
import functools

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
            try:
                # Filter out non-pickleable arguments
                filtered_args = tuple(arg for arg in args if is_pickleable(arg))
                filtered_kwargs = {k: v for k, v in kwargs.items() if is_pickleable(v)}
                
                # Generate cache key
                cache_key = generate_cache_key(func.__name__, filtered_args, filtered_kwargs)
                
                if cache_key in cache:
                    return cache[cache_key]

                result = func(*args, **kwargs)

                # Store result in cache with expiration and tag
                cache.set(cache_key, result, expire=expire, tag=func.__name__)

                return result
            except Exception as fault:
                print('Failed in Cache fetch.')
                raise fault
        return wrapper
    return decorator

def generate_cache_key(func_name, args, kwargs):
    """
    Generate a unique cache key based on function name and arguments.
    """
    key_structure = (func_name, args, tuple(sorted(kwargs.items())))
    return hashlib.md5(pickle.dumps(key_structure)).hexdigest()

def clear_specific_cache(func_name):
    """
    Clear cache entries for a specific function using tags.
    """
    try:
        deleted_count = cache.evict(func_name)
        print(f"Successfully cleared {deleted_count} cache entries for function: {func_name}")
        return deleted_count
    except Exception as e:
        print(f"Error clearing cache for function {func_name}: {e}")
        return 0

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

def fetch_cache_keys(func_name: str = '') -> dict:
    """
    Fetch all cache keys, optionally filtered by function name (tag).
    
    Args:
    func_name (str, optional): If provided, only fetch keys for this function.
    
    Returns:
    dict: A dictionary where keys are function names and values are lists of cache keys.
    """
    cache_keys = {}
    
    for key in cache.iterkeys():
        try:
            # Fetch the tag (function name) for this key
            _, tag = cache.get(key, expire_time=False, tag=True)
            
            if func_name == '' or tag == func_name:
                if tag not in cache_keys:
                    cache_keys[tag] = []
                cache_keys[tag].append(key)
        except KeyError:
            # Handle case where key might have been deleted
            continue
        except Exception as e:
            print(f"Error processing key {key}: {e}")
            continue
    
    return cache_keys

def retry_decorator(retries=5, backoff_factor=2, initial_delay=2, raise_exception=True):
    """
    Retry decorator with exponential backoff.
    
    Args:
    retries (int): Number of retry attempts.
    backoff_factor (int): Factor by which the delay increases.
    initial_delay (int): Initial delay in seconds.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = initial_delay
            total_sleep_time = 0

            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt == retries:
                        print(f"Failed after {retries} attempts.")
                        if raise_exception:
                            raise e
                        else:
                            return None
                    print(f"Attempt {attempt} failed: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    total_sleep_time += delay
                    delay *= backoff_factor

            print(f"Total sleep time: {total_sleep_time} seconds")
        return wrapper
    return decorator