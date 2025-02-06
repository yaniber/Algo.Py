from Dashboard.OrderflowChart.OrderFlow import OrderFlowChart
import pandas as pd
import os
import sys
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OHLC_CSV = 'data/range_ohlc.csv'
ORDERFLOW_CSV = 'data/range_candles.csv'

# Read orderflow data from CSV
orderflow_data = pd.read_csv(
ORDERFLOW_CSV,
names=['bid_size', 'price', 'ask_size', 'identifier'],
index_col=0,
parse_dates=True
)


# Read OHLC data from CSV
ohlc_data = pd.read_csv(
OHLC_CSV,
index_col=0,
parse_dates=True,
names=['open', 'high', 'low', 'close', 'identifier']
)

# Create an instance of OrderFlowChart
orderflowchart = OrderFlowChart(
orderflow_data,
ohlc_data,
identifier_col='identifier'
)

# Plot the orderflow chart
orderflowchart.plot()