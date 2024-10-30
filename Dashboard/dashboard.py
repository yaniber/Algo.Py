import os
import sys
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from OMS.oms import OMS
from OMS.zerodha import Zerodha


import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh
import time

zerodha = Zerodha()
# Set Streamlit page config
st.set_page_config(
    page_title="Trading Dashboard",
    layout="wide",
)

# Sidebar
st.sidebar.title("Trading Dashboard")
st.sidebar.write("Use this dashboard to monitor your trading activity and strategies.")

# Function placeholders to simulate data fetching (replace with your actual data fetching logic)
def fetch_balance():
    bal = zerodha.get_available_balance()
    return int(bal)
    #return np.random.randint(9000, 11000)  # Simulated random balance for demonstration

def fetch_open_positions():
    data = {
        'Symbol': ['AAPL', 'TSLA'],
        'Quantity': [50, 20],
        'Price': [150, 700],
        'PnL': [100, -50]
    }
    return pd.DataFrame(data)

def fetch_past_positions():
    data = {
        'Symbol': ['MSFT', 'GOOGL', 'AMZN'],
        'Quantity': [30, 10, 5],
        'Price': [250, 2700, 3300],
        'PnL': [200, -100, 150]
    }
    return pd.DataFrame(data)

def fetch_fresh_buys():
    data = {
        'Time': ['10:05', '10:10', '10:15'],
        'Symbol': ['AAPL', 'NFLX', 'GOOGL'],
        'Quantity': [10, 5, 15],
        'Price': [150, 500, 2700]
    }
    return pd.DataFrame(data)

def fetch_fresh_sells():
    data = {
        'Time': ['10:07', '10:12', '10:18'],
        'Symbol': ['TSLA', 'MSFT', 'AMZN'],
        'Quantity': [7, 10, 3],
        'Price': [700, 250, 3300]
    }
    return pd.DataFrame(data)

# Display balance in an empty container
balance_container = st.empty()

def display_balance():
    balance = fetch_balance()
    balance_container.metric("Account Balance", f"₹{balance}")

# Display open positions
st.header("Open Positions")
open_positions_df = fetch_open_positions()
st.table(open_positions_df)

# Display past positions in a collapsible scrollable container
st.header("Past Positions")
with st.expander("Show/Hide Past Positions"):
    past_positions_df = fetch_past_positions()
    st.dataframe(past_positions_df, height=300)

# Display fresh buys table in an empty container
fresh_buys_container = st.empty()
def display_fresh_buys():
    fresh_buys_df = fetch_fresh_buys()
    fresh_buys_container.dataframe(fresh_buys_df)

# Display fresh sells table in an empty container
fresh_sells_container = st.empty()
def display_fresh_sells():
    fresh_sells_df = fetch_fresh_sells()
    fresh_sells_container.dataframe(fresh_sells_df)

# Plotting a graph (e.g., PnL over time)
st.header("PnL Over Time")
def plot_pnl_graph():
    time_series = pd.date_range(start='2023-10-01', periods=100, freq='T')
    pnl_series = np.random.randn(100).cumsum()  # Simulated PnL data
    
    fig = go.Figure(
        go.Scatter(
            x=time_series,
            y=pnl_series,
            mode='lines',
            name='PnL'
        )
    )
    fig.update_layout(
        title="PnL Over Time",
        xaxis_title="Time",
        yaxis_title="PnL",
    )
    st.plotly_chart(fig, use_container_width=True)

plot_pnl_graph()

# Initial display
display_balance()
display_fresh_buys()
display_fresh_sells()

# Auto-refresh specific components
refresh_interval = 600  # Refresh every 5 seconds

while True:
    time.sleep(refresh_interval)  # Wait for the interval
    display_balance()  # Only refresh the balance component
    display_fresh_buys()  # Refresh fresh buys
    display_fresh_sells()  # Refresh fresh sells