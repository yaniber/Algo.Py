import pandas as pd
from functools import wraps

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
