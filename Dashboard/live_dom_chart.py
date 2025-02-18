'''
commited version is better but this is more accurate in terms of how orderblocks are. just very glitchy and not clean. 
'''

import streamlit as st
import pandas as pd
import numpy as np
import json
import websockets
import asyncio
import queue
import time
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import defaultdict
import threading

# Configuration
SYMBOL = 'btcusdt'
TRADE_WS_URL = f"wss://fstream.binance.com/ws/{SYMBOL}@aggTrade"
DEPTH_WS_URL = f"wss://fstream.binance.com/ws/{SYMBOL}@depth@100ms"
BUFFER_SIZE = 2000
UPDATE_INTERVAL = 2  # Reduced update frequency for stability
DOM_GRANULARITY = 0.01  # Price bin size in USDT
TIME_WINDOW = 60  # Keep 5 minutes of DOM history (seconds)

trade_queue = queue.Queue()
depth_queue = queue.Queue()

def init_session_state():
    session_keys = {
        "trades": pd.DataFrame(columns=['time', 'price', 'quantity', 'direction']),
        "dom_history": [],
        "last_update": time.time(),
        "current_price": None,
        "time_range": [datetime.now() - timedelta(minutes=1), datetime.now()],
        "price_range": [0, 0],
        "ws_thread": None
    }
    for key, val in session_keys.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()

async def binance_websocket():
    async with websockets.connect(TRADE_WS_URL) as trade_ws, \
              websockets.connect(DEPTH_WS_URL) as depth_ws:
        
        async def handle_trades():
            async for message in trade_ws:
                trade_queue.put(message)
        
        async def handle_depth():
            async for message in depth_ws:
                depth_queue.put(message)
        
        await asyncio.gather(handle_trades(), handle_depth())

def process_trade_message(msg):
    data = json.loads(msg)
    return {
        'time': datetime.fromtimestamp(data['T']/1000),
        'price': float(data['p']),
        'quantity': float(data['q']),
        'direction': 'BUY' if not data['m'] else 'SELL'
    }

def process_depth_message(msg):
    data = json.loads(msg)
    timestamp = datetime.now()
    dom_snapshot = defaultdict(float)
    
    # Process bids and asks
    for p, q in data.get('b', []):
        price = round(float(p)/DOM_GRANULARITY)*DOM_GRANULARITY
        dom_snapshot[price] += float(q)
    for p, q in data.get('a', []):
        price = round(float(p)/DOM_GRANULARITY)*DOM_GRANULARITY
        dom_snapshot[price] += float(q)
    
    return timestamp, dom_snapshot

def start_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(binance_websocket())

# Start WebSocket thread
if st.session_state.ws_thread is None or not st.session_state.ws_thread.is_alive():
    st.session_state.ws_thread = threading.Thread(target=start_websocket, daemon=True)
    st.session_state.ws_thread.start()


# Control panel
with st.sidebar:
    with st.expander("⚙️ Settings", expanded=True):
        bubble_scale = st.slider("Bubble Size", 1, 20, 12)
        #dom_opacity = st.slider("DOM Opacity", 0.1, 1.0, 0.6)
        #price_range = st.slider("Price Range (%)", 0.1, 5.0, 1.0)
        theme = st.selectbox("Theme", ['Dark', 'Light'])

price_range = 0.1
dom_opacity = 0.0001
# Main interface
main_col = st.columns(1)[0]
with main_col:
    st.header("₿ BTC/USDT Time-Anchored Order Blocks")
    chart_placeholder = st.empty()

# Main update loop
while True:
    # Process trades
    try:
        while not trade_queue.empty():
            trade = process_trade_message(trade_queue.get_nowait())
            new_row = pd.DataFrame([trade])
            st.session_state.trades = pd.concat([st.session_state.trades, new_row]).iloc[-BUFFER_SIZE:]
            st.session_state.current_price = trade['price']
    except queue.Empty:
        pass

    # Process depth updates
    try:
        while not depth_queue.empty():
            timestamp, dom_snapshot = process_depth_message(depth_queue.get_nowait())
            # Store DOM history with timestamp
            st.session_state.dom_history.append((timestamp, dom_snapshot))
    except queue.Empty:
        pass

    # Prune old DOM data
    cutoff = datetime.now() - timedelta(seconds=TIME_WINDOW)
    st.session_state.dom_history = [
        (ts, data) for ts, data in st.session_state.dom_history
        if ts > cutoff
    ]

    # Update display
    if time.time() - st.session_state.last_update > UPDATE_INTERVAL:
        fig = go.Figure()
        
        # Prepare DOM heatmap data
        heatmap_data = []
        if st.session_state.current_price:
            current_price = st.session_state.current_price
            price_window = current_price * price_range / 100
            min_price = current_price - price_window
            max_price = current_price + price_window
            
            # Collect relevant DOM data
            for ts, dom_snapshot in st.session_state.dom_history:
                for price, volume in dom_snapshot.items():
                    if min_price <= price <= max_price:
                        heatmap_data.append({
                            'time': ts,
                            'price': price,
                            'volume': volume
                        })

            # Create heatmap if data exists
            # Replace the heatmap_data processing and fig.add_trace with this:

            # Replace the heatmap visualization section with this:

            if heatmap_data:
                df_heat = pd.DataFrame(heatmap_data)
                
                # Filter out insignificant volumes
                volume_threshold = df_heat['volume'].quantile(0.9)  # Show top 30% volumes
                df_heat = df_heat[df_heat['volume'] > volume_threshold]
                
                if not df_heat.empty:
                    # Calculate relative strength (0-1) based on current max volume
                    max_volume = df_heat['volume'].max()
                    min_volume = df_heat['volume'].min()
                    volume_range = max_volume - min_volume if max_volume > min_volume else 1
                    
                    # Exponential scaling for opacity (emphasize strong blocks)
                    df_heat['strength'] = ((df_heat['volume'] - min_volume) / volume_range) ** 2
                    df_heat['opacity'] = df_heat['strength'].apply(
                        lambda x: min(0.2 + (0.6 * x), 0.8)  # Opacity between 0.2-0.8
                    )
                    
                    # Create dynamic color scale
                    colors = [
                        [0.0, 'rgba(255,165,0,0.1)'],
                        [0.2, 'rgba(255,165,0,0.3)'],
                        [0.5, 'rgba(255,165,0,0.6)'],
                        [1.0, 'rgba(255,165,0,0.9)']
                    ]
                    
                    fig.add_trace(go.Scattergl(
                        x=df_heat['time'],
                        y=df_heat['price'],
                        mode='markers',
                        marker=dict(
                            size=10,
                            color=df_heat['opacity'],
                            colorscale=colors,
                            cmin=0,
                            cmax=1,
                            symbol='square',
                            line_width=0,
                            opacity=0.8
                        ),
                        name='Order Blocks',
                        hoverinfo='text',
                        text=df_heat.apply(
                            lambda row: f"Price: {row['price']:.2f}<br>Strength: {row['strength']:.2f}", 
                            axis=1
                        )
                    ))

        # Add price bubbles
        if not st.session_state.trades.empty:
            df = st.session_state.trades
            fig.add_trace(go.Scattergl(
                x=df['time'],
                y=df['price'],
                mode='markers',
                marker=dict(
                    size=np.sqrt(df['quantity']) * bubble_scale,
                    color=np.where(df['direction'] == 'BUY', 'rgba(0,200,0,0.8)', 'rgba(255,0,0,0.8)'),
                    line=dict(width=1, color='rgba(0,0,0,0.5)')
                ),
                name='Trades',
                hoverinfo='text',
                text=df.apply(
                    lambda row: f"Price: {row['price']:.2f}<br>Qty: {row['quantity']:.4f} BTC", 
                    axis=1
                )
            ))

        # Configure layout
        fig.update_layout(
            height=500,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='rgb(17,17,17)' if theme == 'Dark' else 'white',
            paper_bgcolor='rgb(17,17,17)' if theme == 'Dark' else 'white',
            font=dict(color='white' if theme == 'Dark' else 'black'),
            xaxis=dict(
                title='Time',
                rangeselector=dict(buttons=list([
                    dict(count=15, label="15m", step="minute", stepmode="backward"),
                    dict(count=1, label="1H", step="hour", stepmode="backward"),
                    dict(step="all")
                ]))
            ),
            yaxis=dict(
                title='Price (USDT)',
                range=[min_price, max_price] if st.session_state.current_price else None,
                fixedrange=False,
                tickformat=".2f"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # Update chart
        with main_col:
            chart_placeholder.plotly_chart(
                fig, 
                use_container_width=True,
                key=f"main_chart_{time.time()}"
            )
        
        st.session_state.last_update = time.time()
    
    time.sleep(0.1)