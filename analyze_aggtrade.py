import matplotlib.pyplot as plt
import time
import pandas as pd
import requests

def fetch_binance_trades(symbol, start_time, end_time):
    """
    Fetch Binance trades within a time range.
    
    Args:
        symbol (str): Symbol pair (e.g., 'IQUSDT').
        start_time (int): Start time in milliseconds since epoch.
        end_time (int): End time in milliseconds since epoch.

    Returns:
        pd.DataFrame: DataFrame with trade data.
    """
    url = "https://api.binance.com/api/v3/aggTrades"
    all_trades = []

    while start_time < end_time:
        params = {
            "symbol": symbol,
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1000,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        all_trades.extend(data)
        if not data:
            break
        start_time = data[-1]["T"] + 1  # Update start_time to the last trade's timestamp + 1ms

    df = pd.DataFrame(all_trades)
    df['timestamp'] = pd.to_datetime(df['T'], unit='ms')
    return df

def visualize_trades(df, window_size=20, speed=0.5):
    """
    Visualize trades dynamically at runtime.

    Args:
        df (pd.DataFrame): Trade data with 'a' (trade ID), 'p' (price), 'q' (quantity).
        window_size (int): Number of trades to show at a time.
        speed (float): Delay between updates in seconds.
    """
    # Normalize quantity for bubble size
    df['bubble_size'] = 50 + 450 * (df['q'] - df['q'].min()) / (df['q'].max() - df['q'].min())
    df = df.sort_values('a').reset_index(drop=True)

    # Initialize interactive mode
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlabel('Trade ID')
    ax.set_ylabel('Price')
    ax.set_title('Real-Time Trade Visualization')

    for i in range(len(df)):
        start_idx = max(0, i - window_size + 1)
        end_idx = i + 1
        current_data = df.iloc[start_idx:end_idx]

        ax.clear()
        ax.scatter(
            current_data['a'],
            current_data['p'],
            s=current_data['bubble_size'],
            alpha=0.6,
            edgecolors="w",
        )
        ax.set_xlim(df['a'].min() - 1, df['a'].max() + 1)
        ax.set_ylim(df['p'].min() - 0.001, df['p'].max() + 0.001)
        ax.set_title(f"Trade ID: {df['a'].iloc[i]} - Real-Time Visualization")
        ax.set_xlabel('Trade ID')
        ax.set_ylabel('Price')

        plt.pause(speed)

    plt.ioff()
    plt.show()

# Fetch trades
start_time = int(pd.Timestamp('2025-01-09T23:50:00').timestamp() * 1000)
end_time = int(pd.Timestamp('2025-01-10T00:14:00').timestamp() * 1000)
df = fetch_binance_trades("IQUSDT", start_time, end_time)

# Ensure numeric types for 'q' and 'p'
df['q'] = pd.to_numeric(df['q'])
df['p'] = pd.to_numeric(df['p'])

# Visualize trades dynamically
visualize_trades(df, window_size=30, speed=0.2)

