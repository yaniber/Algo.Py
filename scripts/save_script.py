import sys
import os

# Add the parent directory of the root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.store.crypto_binance import store_crypto_binance
from data.store.indian_equity import store_indian_equity
from utils.decorators import clear_cache, fetch_cache_keys, clear_specific_cache  # Import clear_cache function
from utils.db.initialize import initialize_database
from data.fetch.indian_equity import fetch_symbol_list_indian_equity


def manage_cache():
    print("1. Clear cache")
    print("2. Fetch cache keys")
    print("3. Clear specific cache")
    choice = input("Enter the number corresponding to your choice: ")

    if choice == '1':
        clear_cache()
        print("Cache cleared successfully.")
    elif choice == '2':
        print("Enter the function name (blank to fetch all):")
        func_name = input("Function name: ")
        print(fetch_cache_keys(func_name))
    elif choice == '3':
        print("Enter the function name:")
        func_name = input("Function name: ")
        clear_specific_cache(func_name)
    else:
        print("Invalid choice. Please choose 1, 2 or 3.")
    sys.exit(0)

if __name__ == '__main__':
    # Ask user for input
    print("Please choose the data type to save:")
    print("1. crypto-binance")
    print("2. equity-india")
    print("3. Initialize database")
    print("4. Manage cache")
    data_type_choice = input("Enter the number corresponding to your choice: ")

    if data_type_choice == '1':
        data_type = 'crypto-binance'
        type = input("Enter the type (e.g., spot, futures): ")
        suffix = input("Enter the suffix (e.g., USDT, BTC): ")
    elif data_type_choice == '2':
        data_type = 'equity-india'
        complete_list_input = input("Fetch complete list? (y/n): ")
        complete_list = complete_list_input.lower() == 'y'
        
        # Add option to choose index_name
        print("Choose the index:")
        print("1. all")
        print("2. nse_eq_symbols")
        index_choice = input("Enter the number corresponding to your choice (default is 'all'): ")
        
        if index_choice == '2':
            index_name = 'nse_eq_symbols'
        else:
            index_name = 'all'
        
        # Add option to calculate technical indicators
        calc_indicators = input("Calculate technical indicators? (y/n): ").lower() == 'y'
    elif data_type_choice == '3':
        initialize_database()
        sys.exit(0)
    elif data_type_choice == '4':
        manage_cache()
    else:
        print("Invalid choice. Please choose 1, 2 or 3.")
        sys.exit(1)

    timeframe = input("Enter the timeframe (e.g., 1y, 1d, 1h, 1m): ")
    data_points = int(input("Enter the number of data points: "))

    # Save data based on user input
    if data_type == 'crypto-binance':
        store_crypto_binance(timeframe, data_points, type, suffix)
    elif data_type == 'equity-india':
        store_indian_equity(timeframe, data_points, complete_list, index_name)
        symbol_list = fetch_symbol_list_indian_equity(index_name='nse_eq_symbols')
        
        if calc_indicators:
            from data.calculate.indian_equity import calculate_technical_indicators
            start_timestamp = None  # You may want to add logic to determine the start timestamp
            all_entries = True if index_name == 'all' else False
            timeframe = timeframe if timeframe != '1y' else '1d'
            calculate_technical_indicators('indian_equity', start_timestamp, all_entries, symbol_list, timeframe)
    else:
        print("Invalid data type. Please choose 'crypto-binance' or 'equity-india'.")
