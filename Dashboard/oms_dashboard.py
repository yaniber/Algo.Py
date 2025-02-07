import streamlit as st
from OMS.binance_oms import Binance
import pandas as pd
import os

# Initialize Binance OMS
def initialize_binance():
    try:
        return Binance()
    except Exception as e:
        st.error(f"Failed to initialize Binance OMS: {str(e)}")
        return None

# Page configuration
st.set_page_config(
    page_title="Custom Trading Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar configuration
def sidebar_controls():
    with st.sidebar:
        st.header("Exchange Configuration")
        exchange = st.selectbox(
            "Select Exchange",
            ["Binance", "Other Exchanges..."],
            index=0
        )
        
        if exchange == "Binance":
            market_type = st.radio(
                "Market Type",
                ["Futures", "Spot"],
                index=0
            )
        else:
            market_type = None
            
        return exchange, market_type

# Main order form with limit order chaser
def order_entry(binance_oms, market_type):
    with st.expander("📝 Order Entry", expanded=True):
        with st.form("order_form"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                symbol = st.text_input("Symbol", "BTCUSDT").upper()
                order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"])
                
            with col2:
                side = st.radio("Side", ["BUY", "SELL"], horizontal=True)
                quantity = st.number_input("Quantity", min_value=0.0, value=0.001, step=0.001)
                
            with col3:
                if order_type == "LIMIT":
                    price = st.number_input("Price", min_value=0.0, value=0.0)
                    use_chaser = st.checkbox("Use Limit Order Chaser", 
                                           help="Dynamically adjust limit order price to improve fill chances")
                else:
                    price = None
                    use_chaser = False
                    
                if market_type == "Futures":
                    quantity_type = st.radio("Quantity Type", ["CONTRACTS", "USD"], horizontal=True)
                else:
                    quantity_type = None
                    
            with col4:
                if market_type == "Futures":
                    leverage = st.number_input("Leverage", min_value=1, max_value=125, value=20)
                else:
                    leverage = None
                    
                st.write("")  # Spacer
                submit_order = st.form_submit_button("📤 Place Order")
            
            if submit_order:
                try:
                    if use_chaser and order_type == "LIMIT":
                        # Use limit order chaser
                        chaser_params = {
                            'symbol': symbol,
                            'side': side,
                            'size': quantity,
                            'max_retries': 20,
                            'interval': 0.5,
                            'reduceOnly': False
                        }
                        if market_type == "Futures":
                            result = binance_oms.limit_order_chaser_async(**chaser_params)
                        else:
                            # For spot markets (would need spot implementation in OMS)
                            result = binance_oms.limit_order_chaser_async(**chaser_params)
                        
                        st.success("Limit order chaser activated!")
                        st.write("Tracking order execution...")
                    else:
                        # Regular order placement
                        if market_type == "Futures":
                            result = binance_oms.place_futures_order(
                                symbol=symbol,
                                side=side,
                                quantity=quantity,
                                price=price if order_type == "LIMIT" else None,
                                order_type=order_type,
                                quantity_type=quantity_type
                            )
                            if leverage:
                                binance_oms.change_leverage(symbol, leverage)
                        else:
                            result = binance_oms.place_order(
                                symbol=symbol,
                                side=side,
                                size=quantity,
                                price=price if order_type == "LIMIT" else None,
                                order_type=order_type
                            )
                        
                        if result:
                            st.success("Order placed successfully!")
                            st.json(result)
                        else:
                            st.error("Failed to place order")
                        
                except Exception as e:
                    st.error(f"Order failed: {str(e)}")

# Position management
def position_management(binance_oms):
    with st.expander("📊 Position Management"):
        if st.button("🔄 Refresh Positions"):
            positions = binance_oms.view_open_futures_positions()
            if not positions.empty:
                st.dataframe(positions.style.highlight_max(axis=0), use_container_width=True)
            else:
                st.info("No open positions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.form("close_position_form"):
                symbol_to_close = st.text_input("Symbol to Close", "BTCUSDT").upper()
                close_percentage = st.slider("Close Percentage", 0, 100, 100)
                use_chaser = st.checkbox("Use Limit Order Chaser")
                
                if st.form_submit_button("🚪 Close Position"):
                    try:
                        result = binance_oms.close_futures_positions(
                            symbol=symbol_to_close,
                            percentage=close_percentage,
                            use_chaser=use_chaser
                        )
                        if result:
                            st.success(f"Closing {close_percentage}% of {symbol_to_close} position")
                    except Exception as e:
                        st.error(f"Failed to close position: {str(e)}")
        
        with col2:
            with st.form("leverage_form"):
                leverage_symbol = st.text_input("Symbol for Leverage", "BTCUSDT").upper()
                new_leverage = st.slider("New Leverage", 1, 125, 20)
                
                if st.form_submit_button("⚖️ Change Leverage"):
                    try:
                        result = binance_oms.change_leverage(leverage_symbol, new_leverage)
                        if result:
                            st.success(f"Leverage changed to {new_leverage}x for {leverage_symbol}")
                    except Exception as e:
                        st.error(f"Leverage change failed: {str(e)}")

# Account information
def account_info(binance_oms, market_type):
    with st.expander("💼 Account Overview"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Show Balance"):
                if market_type == "Futures":
                    balance = binance_oms.get_futures_balance("USDT")
                    if balance:
                        st.metric("Futures USDT Balance", 
                                f"{balance['available']:,.2f} / {balance['total']:,.2f}",
                                help="Available / Total Balance")
                else:
                    balance = binance_oms.get_available_balance("USDT")
                    if balance:
                        st.metric("Spot USDT Balance", f"{float(balance['free']):,.2f}")
        
        with col2:
            if st.button("Show Positions"):
                if market_type == "Futures":
                    positions = binance_oms.view_open_futures_positions()
                    if not positions.empty:
                        st.dataframe(positions.style.highlight_max(axis=0), use_container_width=True)
                    else:
                        st.info("No open futures positions")
                else:
                    st.info("Position tracking only available for Futures")
        
        with col3:
            if st.button("Show Order History"):
                st.write("Successful Orders:")
                st.write(binance_oms.successful_orders[-5:])
                st.write("Failed Orders:")
                st.write(binance_oms.failed_orders[-5:])

# Main app
def main():
    st.title("🚀 Custom Trading Dashboard")
    
    # Initialize Binance OMS
    binance_oms = initialize_binance()
    if not binance_oms:
        return
    
    # Get exchange configuration
    exchange, market_type = sidebar_controls()
    
    # Dashboard layout
    order_entry(binance_oms, market_type)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        position_management(binance_oms)
    
    with col2:
        account_info(binance_oms, market_type)  # Pass market_type here
    
    # System messages
    with st.expander("📢 System Messages"):
        if st.button("Clear Logs"):
            binance_oms.successful_orders = []
            binance_oms.failed_orders = []
        st.write("Recent Successful Orders:", binance_oms.successful_orders[-3:])
        st.write("Recent Failed Orders:", binance_oms.failed_orders[-3:])

if __name__ == "__main__":
    main()