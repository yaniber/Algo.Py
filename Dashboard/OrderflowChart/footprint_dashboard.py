import streamlit as st
import pandas as pd
import numpy as np
import time
import websockets
import asyncio
import json
from threading import Thread
from Dashboard.OrderflowChart.OrderFlow import OrderFlowChart

# Configuration
SYMBOL = "BTCUSDT"
TIMEFRAME = "1m"
CANDLE_LIMIT = 15  # 15 minutes history

# Initialize session state
if 'ohlc' not in st.session_state:
    st.session_state.ohlc = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'identifier'])
if 'orderflow' not in st.session_state:
    st.session_state.orderflow = pd.DataFrame(columns=['bid_size', 'price', 'ask_size', 'identifier'])
if 'current_candle' not in st.session_state:
    st.session_state.current_candle = None
if 'price_levels' not in st.session_state:
    st.session_state.price_levels = {}

def initialize_candle(timestamp):
    return {
        'open': None,
        'high': -np.inf,
        'low': np.inf,
        'close': None,
        'timestamp': timestamp,
        'bid_size': {},
        'ask_size': {}
    }

def process_trade(trade):
    price = float(trade['p'])
    qty = float(trade['q'])
    is_buyer_maker = trade['m']
    
    # Update current candle
    ts = pd.to_datetime(trade['T'], unit='ms').floor(TIMEFRAME)
    if st.session_state.current_candle is None or ts != st.session_state.current_candle['timestamp']:
        if st.session_state.current_candle is not None:
            finalize_candle(st.session_state.current_candle)
        st.session_state.current_candle = initialize_candle(ts)
    
    # Update OHLC
    current = st.session_state.current_candle
    if current['open'] is None:
        current['open'] = price
    current['high'] = max(current['high'], price)
    current['low'] = min(current['low'], price)
    current['close'] = price
    
    # Update order flow
    if is_buyer_maker:  # Seller aggressive (bid)
        current['bid_size'][price] = current['bid_size'].get(price, 0) + qty
    else:  # Buyer aggressive (ask)
        current['ask_size'][price] = current['ask_size'].get(price, 0) + qty

def finalize_candle(candle):
    # Create identifier
    identifier = str(candle['timestamp'].value)
    
    # Create OHLC entry
    ohlc_entry = {
        'open': candle['open'],
        'high': candle['high'],
        'low': candle['low'],
        'close': candle['close'],
        'identifier': identifier
    }
    
    # Create order flow entries
    orderflow_entries = []
    for price in sorted(set(candle['bid_size'].keys()).union(candle['ask_size'].keys())):
        orderflow_entries.append({
            'bid_size': candle['bid_size'].get(price, 0),
            'price': price,
            'ask_size': candle['ask_size'].get(price, 0),
            'identifier': identifier
        })
    
    # Update session state
    st.session_state.ohlc = pd.concat([st.session_state.ohlc, pd.DataFrame([ohlc_entry])])
    st.session_state.orderflow = pd.concat([st.session_state.orderflow, pd.DataFrame(orderflow_entries)])
    
    # Keep only last 15 candles
    if len(st.session_state.ohlc) > CANDLE_LIMIT:
        old_id = st.session_state.ohlc.iloc[0]['identifier']
        st.session_state.ohlc = st.session_state.ohlc.iloc[1:]
        st.session_state.orderflow = st.session_state.orderflow[st.session_state.orderflow['identifier'] != old_id]

async def binance_websocket():
    url = f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade"
    async with websockets.connect(url) as ws:
        while True:
            try:
                msg = await ws.recv()
                trade = json.loads(msg)
                process_trade(trade)
            except Exception as e:
                print(f"Error: {e}")
                break

def run_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(binance_websocket())

# Start WebSocket thread
if not st.session_state.get('ws_started', False):
    Thread(target=run_websocket, daemon=True).start()
    st.session_state.ws_started = True

# Streamlit UI
st.title("Binance BTC/USDT Live Footprint Chart")
st.markdown(f"**Real-time {TIMEFRAME} footprint chart with {CANDLE_LIMIT} candles history**")

# Create metrics columns
col1, col2, col3 = st.columns(3)
with col1:
    if not st.session_state.ohlc.empty:
        current_price = st.session_state.ohlc.iloc[-1]['close']
        st.metric("Current Price", f"{current_price:.2f}")
with col2:
    if len(st.session_state.ohlc) > 1:
        change = st.session_state.ohlc.iloc[-1]['close'] - st.session_state.ohlc.iloc[-2]['close']
        st.metric("1m Change", f"{change:.2f}")
with col3:
    if not st.session_state.orderflow.empty:
        total_volume = st.session_state.orderflow[['bid_size', 'ask_size']].sum().sum()
        st.metric("Total Volume", f"{total_volume:.2f} BTC")

# Create chart
if len(st.session_state.ohlc) >= 5:  # Wait for at least 5 candles
    try:
        ofc = OrderFlowChart(
            orderflow_data=st.session_state.orderflow,
            ohlc_data=st.session_state.ohlc,
            identifier_col='identifier'
        )
        fig = ofc.plot(return_figure=True)
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
    except Exception as e:
        st.error(f"Error generating chart: {e}")
else:
    st.info("Waiting for enough data to generate chart...")

# Data refresh note
st.markdown("*Data updates every minute. Chart may take a few seconds to render new candles.*")

# Raw data toggle
if st.checkbox("Show raw data"):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("OHLC Data")
        st.dataframe(st.session_state.ohlc)
    with col2:
        st.subheader("Order Flow Data")
        st.dataframe(st.session_state.orderflow)