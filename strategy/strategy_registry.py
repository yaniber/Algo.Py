'''
Usage : 
from strategy.strategy_registry import STRATEGY_REGISTRY

strategy_function = STRATEGY_REGISTRY["EMA Crossover Strategy"]
entries, exits, close_data, open_data = strategy_function.run(ohlcv_data)
'''
import importlib
import pkgutil
import inspect
from typing import Dict, Type, Any
from strategy.strategy_builder import StrategyBaseClass

# Dictionary to store { strategy_display_name -> { "class": strategy_class, "params": default_params } }
STRATEGY_REGISTRY: Dict[str, Dict[str, Any]] = {}

def discover_strategies():
    """
    Automatically discovers and registers all strategy classes from public/private directories.
    """
    strategy_modules = []

    # Scan both strategy.public and strategy.private packages
    try:
        for package in ["strategy.public"]:
            package_path = package.replace(".", "/")
            for _, module_name, _ in pkgutil.iter_modules([package_path]):
                strategy_modules.append(f"{package}.{module_name}")
    except Exception as e: 
        print(f"Error in fetching strategy modules : {e}")
        raise e

    # Import and register strategy classes
    for module_name in strategy_modules:
        try:
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, StrategyBaseClass) and obj is not StrategyBaseClass:
                    # Create an instance of the strategy to get its name
                    strategy_instance = obj()
                    
                    # Extract the strategy's custom display name
                    strategy_name = strategy_instance.display_name  # Now using display_name
                    
                    # Extract constructor parameters dynamically
                    default_params = {k: v.default for k, v in inspect.signature(obj).parameters.items() if k != "self"}

                    # Store class reference and parameters
                    STRATEGY_REGISTRY[strategy_name] = {
                        "class": obj,  # Store class
                        "params": default_params  # Extract default params
                    }
                elif obj == StrategyBaseClass:
                    pass
                elif inspect.isclass(obj):
                    print(f'Invalid Strategy Module Detected. Please check syntax again : {name}')
        except Exception as e: 
            print(f'Error in addind to STRATEGY_REGISTRY : {e}')

# Discover strategies on module import
discover_strategies()

