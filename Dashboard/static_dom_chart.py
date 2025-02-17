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
UPDATE_INTERVAL = 0.5
DOM_GRANULARITY = 0.05  # Price bin size in USDT
BASE_RANGE = 0.1  # Percentage price range from current price

# Thread-safe queues
trade_queue = queue.Queue()
depth_queue = queue.Queue()

def init_session_state():
    session_keys = {
        "trades": pd.DataFrame(columns=['time', 'price', 'quantity', 'direction']),
        "order_book": defaultdict(float),
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
    book = defaultdict(float)
    for p, q in data.get('b', []):
        price_level = round(float(p)/DOM_GRANULARITY)*DOM_GRANULARITY
        book[price_level] += float(q)
    for p, q in data.get('a', []):
        price_level = round(float(p)/DOM_GRANULARITY)*DOM_GRANULARITY
        book[price_level] += float(q)
    return book

def start_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(binance_websocket())

# Start WebSocket thread once
if st.session_state.ws_thread is None or not st.session_state.ws_thread.is_alive():
    st.session_state.ws_thread = threading.Thread(target=start_websocket, daemon=True)
    st.session_state.ws_thread.start()


# Control panel
with st.sidebar:
    with st.expander("⚙️ Settings", expanded=True):
        bubble_scale = st.slider("Bubble Size", 1, 20, 12)
        dom_opacity = st.slider("Order Block Opacity", 0.1, 1.0, 0.8)
        #base_range = st.slider("Price Range (%)", 0.1, 5.0, 1.0)
        theme = st.selectbox("Theme", ['Dark', 'Light'])

# Main interface
main_col = st.columns(1)[0]
with main_col:
    st.header("₿ BTC/USDT Real-Time Trading View")
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
            # Update time range
            st.session_state.time_range[1] = datetime.now()
    except queue.Empty:
        pass

    # Process depth
    try:
        while not depth_queue.empty():
            depth = process_depth_message(depth_queue.get_nowait())
            for price, volume in depth.items():
                st.session_state.order_book[price] = volume
    except queue.Empty:
        pass

    # Update display
    if time.time() - st.session_state.last_update > UPDATE_INTERVAL:
        fig = go.Figure()
        
        # Add order blocks
        if st.session_state.current_price:
            current_price = st.session_state.current_price
            price_range = current_price * BASE_RANGE / 100
            min_price = current_price - price_range
            max_price = current_price + price_range
            st.session_state.price_range = [min_price, max_price]
            
            # Get DOM levels in range
            dom_levels = sorted(
                [(p, v) for p, v in st.session_state.order_book.items() 
                 if min_price <= p <= max_price],
                key=lambda x: x[0]
            )
            
            # Create enhanced order blocks
            shapes = []
            if dom_levels:
                max_volume = max(v for _, v in dom_levels)
                for price, volume in dom_levels:
                    intensity = np.log(volume + 1) / np.log(max_volume + 1)
                    alpha = max(min(intensity * dom_opacity, 1.0), 0.3)
                    fillcolor = f'rgba(255,165,0,{alpha:.2f})'
                    
                    shapes.append({
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'y',
                        'x0': st.session_state.time_range[0],
                        'x1': st.session_state.time_range[1],
                        'y0': price - DOM_GRANULARITY/2,
                        'y1': price + DOM_GRANULARITY/2,
                        'fillcolor': fillcolor,
                        'line': {'width': 0},
                        'layer': 'below'
                    })
            
            fig.update_layout(shapes=shapes)
        
        # Add price bubbles with trend line
        if not st.session_state.trades.empty:
            df = st.session_state.trades
            
            # Add trend line
            fig.add_trace(go.Scattergl(
                x=df['time'],
                y=df['price'],
                mode='lines',
                line=dict(color='#00FF00', width=1),
                name='Price Trend'
            ))
            
            # Add trade markers
            fig.add_trace(go.Scattergl(
                x=df['time'],
                y=df['price'],
                mode='markers',
                marker=dict(
                    size=np.sqrt(df['quantity']) * bubble_scale,
                    color=np.where(df['direction'] == 'BUY', 'rgba(0,200,0,0.8)', 'rgba(255,0,0,0.8)'),
                    line=dict(width=1, color='rgba(0,0,0,0.5)')
                ),
                name='Trades'
            ))
        
        # Configure layout
        fig.update_layout(
            height=600,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='rgb(17,17,17)' if theme == 'Dark' else 'white',
            paper_bgcolor='rgb(17,17,17)' if theme == 'Dark' else 'white',
            font=dict(color='white' if theme == 'Dark' else 'black'),
            xaxis=dict(
                title='Time',
                range=st.session_state.time_range,
                rangeselector=dict(buttons=list([
                    dict(count=5, label="5m", step="minute", stepmode="backward"),
                    dict(count=1, label="1H", step="hour", stepmode="backward"),
                    dict(step="all")
                ]))
            ),
            yaxis=dict(
                title='Price (USDT)',
                range=st.session_state.price_range,
                fixedrange=False,
                tickformat=".2f"
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