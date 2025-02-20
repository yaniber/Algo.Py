<!-- File: strategy_development.md -->
# Strategy Development

Developing custom trading strategies is central to **Algo.Py**. This section explains how to create, test, and contribute your strategies.

## Contributing Strategies

1. **Create a New Python File:**  
   Place your new strategy (e.g., `my_new_strategy.py`) in the `strategy/public` directory.

2. **Implement the Strategy Class:**  
   Inherit from `StrategyBaseClass` (in `strategy/strategy_builder.py`) and implement the `run` method.

3. **Automatic Registration:**  
   Strategies in the `strategy/public` directory that inherit from `StrategyBaseClass` are automatically discovered and registered.

4. **Test Your Strategy:**  
   Use the backtesting functionality to validate performance.

## Creating a Custom Strategy

Below is an example implementation:

```python
from strategy.strategy_builder import StrategyBaseClass
import pandas as pd
from typing import Tuple, Dict

class MyCustomStrategy(StrategyBaseClass):
    def __init__(self, param1: int = 10, param2: float = 0.5):
        super().__init__(name="My Custom Strategy")
        self.param1 = param1
        self.param2 = param2

    def run(self, ohlcv_data: Dict[str, pd.DataFrame]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        entries = {}
        exits = {}
        close_prices = {}
        open_prices = {}

        for symbol, df in ohlcv_data.items():
            # Replace with your custom logic
            entries[symbol] = pd.Series(False, index=df.index)
            exits[symbol] = pd.Series(False, index=df.index)
            close_prices[symbol] = df['close']
            open_prices[symbol] = df['open']

        return (
            pd.DataFrame(entries),
            pd.DataFrame(exits),
            pd.DataFrame(close_prices),
            pd.DataFrame(open_prices),
        )
```

## Testing Strategies

- **Backtesting:** Run your strategy against historical data.
- **Live Monitoring:** Check real-time performance via the **Strategy Monitor** dashboard.

### Considerations

- **Data Integrity:** Ensure proper handling of missing values and duplicate timestamps.
- **Performance:** Optimize computations, especially for high-frequency data.
- **Avoid Overfitting:** Validate your strategy using separate hold-out data.
- **Costs & Slippage:** Simulate transaction fees and slippage.
- **Error Handling:** Implement robust error handling to avoid crashes.
