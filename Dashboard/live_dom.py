import streamlit as st
import pandas as pd
import numpy as np
import json
import websockets
import asyncio
import queue
import time
import plotly.graph_objects as go
from datetime import datetime
from collections import defaultdict
import threading

# Configuration
SYMBOL = 'btcusdt'
TRADE_WS_URL = f"wss://fstream.binance.com/ws/{SYMBOL}@aggTrade"
DEPTH_WS_URL = f"wss://fstream.binance.com/ws/{SYMBOL}@depth@100ms"
BUFFER_SIZE = 2000
UPDATE_INTERVAL = 0.5

# Thread-safe queues
trade_queue = queue.Queue()
depth_queue = queue.Queue()

def init_session_state():
    if "trades" not in st.session_state:
        st.session_state.trades = pd.DataFrame(columns=['time', 'price', 'quantity', 'direction'])
    if "order_book" not in st.session_state:
        st.session_state.order_book = {'bids': pd.DataFrame(columns=['price', 'quantity']),
                                      'asks': pd.DataFrame(columns=['price', 'quantity'])}
    if "last_update" not in st.session_state:
        st.session_state.last_update = time.time()

init_session_state()

async def binance_websocket():
    # Connect to both trade and depth streams
    async with websockets.connect(TRADE_WS_URL) as trade_ws, \
              websockets.connect(DEPTH_WS_URL) as depth_ws:
        
        # Create separate tasks for each stream
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
    return {
        'bids': pd.DataFrame([[float(p), float(q)] for p, q in data.get('b', [])], columns=['price', 'quantity']),
        'asks': pd.DataFrame([[float(p), float(q)] for p, q in data.get('a', [])], columns=['price', 'quantity'])
    }

def start_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(binance_websocket())

# Start WebSocket thread
if not hasattr(st.session_state, 'ws_thread'):
    st.session_state.ws_thread = threading.Thread(target=start_websocket, daemon=True)
    st.session_state.ws_thread.start()

# Dashboard Layout
st.set_page_config(
    layout="wide",
    page_title="BTC/USDT Professional Trading View",
    initial_sidebar_state="expanded"
)

# Main interface
main_col, dom_col = st.columns([4, 1])

with main_col:
    st.header("Price & Volume")
    chart_placeholder = st.empty()

with dom_col:
    st.header("Order Book Depth")
    dom_placeholder = st.empty()

# Control panel
with st.sidebar:
    with st.expander("Settings", expanded=True):
        bubble_scale = st.slider("Bubble Size", 1, 20, 10)
        dom_range = st.slider("DOM Range (%)", 0.1, 5.0, 1.0)
        theme = st.selectbox("Theme", ['Dark', 'Light'])

# Main update loop
while True:
    # Process trade messages
    while not trade_queue.empty():
        try:
            trade = process_trade_message(trade_queue.get_nowait())
            new_row = pd.DataFrame([trade])
            st.session_state.trades = pd.concat([st.session_state.trades, new_row]).iloc[-BUFFER_SIZE:]
        except queue.Empty:
            break

    # Process depth messages
    while not depth_queue.empty():
        try:
            depth = process_depth_message(depth_queue.get_nowait())
            st.session_state.order_book['bids'] = depth['bids'].sort_values('price', ascending=False)
            st.session_state.order_book['asks'] = depth['asks'].sort_values('price')
        except queue.Empty:
            break

    # Update display
    if time.time() - st.session_state.last_update > UPDATE_INTERVAL:
        # Prepare main chart
        fig = go.Figure()
        
        # Add trades if available
        if not st.session_state.trades.empty:
            df = st.session_state.trades
            fig.add_trace(go.Scattergl(
                x=df['time'],
                y=df['price'],
                mode='markers',
                marker=dict(
                    size=np.sqrt(df['quantity']) * bubble_scale,
                    color=np.where(df['direction'] == 'BUY', '#00C800', '#FF0000'),
                    opacity=0.7
                ),
                name='Trades'
            ))
        
        # Configure chart layout
        fig.update_layout(
            height=800,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='#111111' if theme == 'Dark' else '#FFFFFF',
            paper_bgcolor='#111111' if theme == 'Dark' else '#FFFFFF',
            font=dict(color='white' if theme == 'Dark' else 'black'),
            showlegend=False
        )
        
        # Update DOM display
        dom_fig = go.Figure()
        if not st.session_state.order_book['bids'].empty:
            current_price = df['price'].iloc[-1] if not df.empty else 0
            price_range = current_price * dom_range / 100
            
            bids = st.session_state.order_book['bids']
            bids = bids[bids['price'] >= (current_price - price_range)]
            dom_fig.add_trace(go.Bar(
                x=bids['quantity'],
                y=bids['price'].astype(str),
                orientation='h',
                marker_color='#00C800',
                name='Bids'
            ))
            
            asks = st.session_state.order_book['asks']
            asks = asks[asks['price'] <= (current_price + price_range)]
            dom_fig.add_trace(go.Bar(
                x=asks['quantity'],
                y=asks['price'].astype(str),
                orientation='h',
                marker_color='#FF0000',
                name='Asks'
            ))
        
        dom_fig.update_layout(
            height=800,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='#111111' if theme == 'Dark' else '#FFFFFF',
            paper_bgcolor='#111111' if theme == 'Dark' else '#FFFFFF',
            showlegend=False
        )

        # Update displays
        with main_col:
            chart_placeholder.plotly_chart(
                fig, 
                use_container_width=True,
                key=f"main_chart_{time.time()}"  # Unique key with timestamp
            )

        with dom_col:
            dom_placeholder.plotly_chart(
                dom_fig,
                use_container_width=True,
                key=f"dom_chart_{time.time()}"  # Unique key with timestamp
            )
        
        st.session_state.last_update = time.time()
    
    time.sleep(0.1)