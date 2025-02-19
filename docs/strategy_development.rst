
Strategy Development
=====================

This section describes how to create and test custom trading strategies using Python within the Algo.Py framework.

Creating Custom Strategies
--------------------------

All strategies are built upon the `StrategyBaseClass` located in `strategy/strategy_builder.py`.  To create a new strategy:

1.  **Inherit from `StrategyBaseClass`:**

    ```python
    from strategy.strategy_builder import StrategyBaseClass
    import pandas as pd
    from typing import Tuple, Dict, Any

    class MyCustomStrategy(StrategyBaseClass):
        def __init__(self, param1: int = 10, param2: float = 0.5):
            super().__init__(name="My Custom Strategy")  # Provide a display name
            self.param1 = param1
            self.param2 = param2
            # Add any other initialization logic here.

        def run(self, ohlcv_data: Dict[str, pd.DataFrame]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            # Your strategy logic goes here.  This is where you generate
            # entry and exit signals based on the provided OHLCV data.

            entries = {}
            exits = {}
            close_prices = {}
            open_prices = {}
            
            for symbol, df in ohlcv_data.items():
                # Process each symbol's data and generate signals
                # Replace with your actual strategy implementation
                close_prices[symbol] = df['close'] # mandatory
                open_prices[symbol] = df['open'] # mandatory
                entries[symbol] = pd.Series(False, index=df.index)  # Replace with your entry logic
                exits[symbol] = pd.Series(False, index=df.index)  # Replace with your exit logic
            
            # Return DataFrames for entries, exits, close, and open
            return pd.DataFrame(entries), pd.DataFrame(exits), pd.DataFrame(close_prices), pd.DataFrame(open_prices)
    ```

2.  **Implement the `run` Method:**

    The `run` method is the core of your strategy.  It takes a dictionary of OHLCV data (where keys are symbols and values are pandas DataFrames) as input and returns a tuple of four pandas DataFrames:

    *   **`entries`:**  A boolean DataFrame indicating entry signals.  `True` at a specific timestamp and for a specific symbol indicates an entry signal.
    *   **`exits`:** A boolean DataFrame indicating exit signals. `True` indicates an exit signal.
    *   **`close_data`:** A DataFrame containing the closing prices of each symbol.
    *   **`open_data`:** A DataFrame containing the opening prices of each symbol.

    The index of all returned DataFrames *must* be aligned.  It's recommended to use the timestamp from the input `ohlcv_data` as the index. The columns of the dataframes must be the symbols.

3.  **Define Parameters in `__init__`:**

    Define any parameters your strategy requires in the `__init__` method.  These parameters will be automatically displayed and made configurable in the backtesting and deployment dashboards.  Use type hints (e.g., `param1: int`) for proper parameter handling.

4.  **Place your strategy file:**

    Place your strategy file inside the `strategy/public` directory. The strategy registry will automatically detect the strategy file.

Testing Strategies
------------------

### Backtesting

The backtesting functionality allows you to evaluate your strategy's performance on historical data.  See the :ref:`quickstart` guide for details on how to use the backtesting dashboard.

### Live Data

You can monitor your strategy's signals on live data using the "Strategy Monitor" dashboard. This dashboard will show live generated signals.

### Important Considerations

*   **Data Handling:** Ensure your `run` method handles potential issues with the input data, such as missing values (NaNs) or duplicate timestamps.
*   **Efficiency:** Optimize your code for performance, especially if you're dealing with high-frequency data or a large number of symbols. Consider using libraries like NumPy and Numba for numerical computations.
*   **Overfitting:**  Be mindful of overfitting your strategy to historical data. Use a separate hold-out period (data not used during strategy development) to evaluate its robustness.
*   **Transaction Costs:** The backtester allows you to specify transaction fees and slippage to simulate real-world trading conditions.
*   **Edge Cases**: Consider any edge cases or data errors that you may encounter while developing your strategy.
*   **Error Handling**: Add error handling to your strategies to prevent the system from crashing.

By following these guidelines, you can create and test robust trading strategies within the Algo.Py platform.