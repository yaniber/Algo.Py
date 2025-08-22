import streamlit as st
from OMS.binance_oms import Binance
import pandas as pd
import os

# Try to import MT5 OMS, but handle gracefully if not available
try:
    from OMS.mt5_oms import MT5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    MT5 = None

# Initialize Binance OMS
def initialize_binance():
    try:
        return Binance()
    except Exception as e:
        st.error(f"Failed to initialize Binance OMS: {str(e)}")
        return None

# Initialize MT5 OMS
def initialize_mt5():
    if not MT5_AVAILABLE:
        st.error("MetaTrader5 package not installed. Please install it via 'pip install MetaTrader5'")
        return None
    
    try:
        return MT5()
    except Exception as e:
        st.error(f"Failed to initialize MT5 OMS: {str(e)}")
        st.info("Make sure MT5 credentials (MT5_LOGIN, MT5_PASSWORD, MT5_SERVER) are set in config/.env file")
        return None

# Sidebar configuration
def sidebar_controls():
    with st.sidebar:
        st.header("Exchange Configuration")
        
        # Build exchange options based on availability
        exchange_options = ["Binance"]
        if MT5_AVAILABLE:
            exchange_options.append("MetaTrader 5")
        exchange_options.append("Other Exchanges...")
        
        exchange = st.selectbox(
            "Select Exchange",
            exchange_options,
            index=0
        )
        
        if exchange == "Binance":
            market_type = st.radio(
                "Market Type",
                ["Futures", "Spot"],
                index=0
            )
        elif exchange == "MetaTrader 5":
            if MT5_AVAILABLE:
                market_type = st.radio(
                    "Market Type",
                    ["Forex", "CFDs", "Metals"],
                    index=0
                )
            else:
                st.warning("MetaTrader5 package not installed")
                market_type = None
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
                order_type = st.selectbox("Order Type", ["MARKET", "LIMIT"], key="order_type_selector")
                
            with col2:
                side = st.radio("Side", ["BUY", "SELL"], horizontal=True)
                quantity = st.number_input("Quantity", min_value=0.0, value=0.001, step=0.001)
                
            with col3:
                if order_type == "LIMIT":
                    price = st.number_input("Price", min_value=0.0, value=0.0, key="limit_price")
                    use_chaser = False
                else:
                    price = None
                    use_chaser = st.checkbox("Use Limit Order Chaser", 
                                        help="Dynamically adjust limit order price to improve fill chances")
                    
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
                    if use_chaser and order_type == "MARKET":
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

# MT5-specific functions
def mt5_order_entry(mt5_oms, market_type):
    st.subheader("📋 MT5 Order Entry")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("mt5_order_form"):
            # Symbol input with suggestions based on market type
            if market_type == "Forex":
                suggested_symbols = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD"]
                default_symbol = "EURUSD"
            elif market_type == "Metals":
                suggested_symbols = ["XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD"]
                default_symbol = "XAUUSD"
            else:  # CFDs
                suggested_symbols = ["US30", "SPX500", "NAS100", "GER30", "UK100"]
                default_symbol = "US30"
            
            col_a, col_b = st.columns([3, 1])
            with col_a:
                symbol = st.text_input("Symbol", value=default_symbol).upper()
            with col_b:
                st.selectbox("Quick Select", suggested_symbols, key="mt5_quick_symbol")
            
            # Order details
            col_side, col_type = st.columns(2)
            with col_side:
                side = st.radio("Side", ["BUY", "SELL"], horizontal=True)
            with col_type:
                order_type = st.radio("Order Type", ["MARKET", "LIMIT"], horizontal=True)
            
            # Size and price
            volume = st.number_input("Volume (Lots)", min_value=0.01, value=0.1, step=0.01, format="%.2f")
            
            price = None
            if order_type == "LIMIT":
                price = st.number_input("Price", min_value=0.0001, value=1.0, step=0.0001, format="%.4f")
            
            # Submit button
            if st.form_submit_button("🎯 Place MT5 Order", use_container_width=True):
                try:
                    success = mt5_oms.place_order(
                        symbol=symbol,
                        side=side,
                        size=volume,
                        price=price,
                        order_type=order_type
                    )
                    if success:
                        st.success(f"Order placed: {side} {volume} lots of {symbol}")
                    else:
                        st.error("Order failed - check failed orders list")
                except Exception as e:
                    st.error(f"Error placing order: {str(e)}")
    
    with col2:
        st.subheader("📊 Symbol Info")
        if st.button("Get Symbol Info"):
            try:
                # Import here to avoid issues if MT5 not available
                import MetaTrader5 as mt5
                info = mt5.symbol_info(symbol)
                if info:
                    st.metric("Spread", f"{info.spread}")
                    st.metric("Min Volume", f"{info.volume_min}")
                    st.metric("Max Volume", f"{info.volume_max}")
                    st.metric("Point", f"{info.point}")
                else:
                    st.error("Symbol not found")
            except Exception as e:
                st.error(f"Error getting symbol info: {str(e)}")

def mt5_account_info(mt5_oms, market_type):
    with st.expander("💼 MT5 Account Overview"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Show Balance"):
                try:
                    balance = mt5_oms.get_available_balance()
                    account_info = mt5_oms.get_account_info()
                    if account_info:
                        st.metric("Balance", f"{balance:,.2f} {account_info.get('currency', '')}")
                        st.metric("Equity", f"{account_info.get('equity', 0):,.2f}")
                        st.metric("Margin Free", f"{account_info.get('margin_free', 0):,.2f}")
                except Exception as e:
                    st.error(f"Error getting balance: {str(e)}")
        
        with col2:
            if st.button("Show Positions"):
                try:
                    positions = mt5_oms.get_positions()
                    if not positions.empty:
                        # Display key position info
                        display_positions = positions[['symbol', 'type', 'volume', 'price_open', 'profit']].copy()
                        display_positions['type'] = display_positions['type'].map({0: 'BUY', 1: 'SELL'})
                        st.dataframe(display_positions, use_container_width=True)
                    else:
                        st.info("No open positions")
                except Exception as e:
                    st.error(f"Error getting positions: {str(e)}")
        
        with col3:
            if st.button("Show Order History"):
                st.write("Successful Orders:")
                recent_successful = mt5_oms.successful_orders[-5:] if mt5_oms.successful_orders else []
                if recent_successful:
                    for order in recent_successful:
                        st.write(f"✅ {order.get('side')} {order.get('size')} {order.get('symbol')} @ {order.get('price')}")
                else:
                    st.write("No recent successful orders")
                
                st.write("Failed Orders:")
                recent_failed = mt5_oms.failed_orders[-5:] if mt5_oms.failed_orders else []
                if recent_failed:
                    for order in recent_failed:
                        st.write(f"❌ {order.get('side')} {order.get('size')} {order.get('symbol')} - {order.get('error', 'Unknown error')}")
                else:
                    st.write("No recent failed orders")

def mt5_symbols_browser(mt5_oms, market_type):
    st.subheader("🔍 MT5 Symbols Browser")
    
    with st.expander("Browse Available Symbols", expanded=False):
        if st.button("Load Symbols"):
            try:
                symbols = mt5_oms.get_symbols()
                if symbols:
                    # Filter symbols based on market type
                    if market_type == "Forex":
                        filtered_symbols = [s for s in symbols if len(s) == 6 and any(curr in s for curr in ['USD', 'EUR', 'GBP', 'JPY'])]
                    elif market_type == "Metals":
                        filtered_symbols = [s for s in symbols if any(metal in s for metal in ['XAU', 'XAG', 'XPT', 'XPD'])]
                    else:  # CFDs
                        filtered_symbols = [s for s in symbols if any(idx in s for idx in ['US30', 'SPX', 'NAS', 'GER', 'UK100'])]
                    
                    if filtered_symbols:
                        st.write(f"Found {len(filtered_symbols)} {market_type} symbols:")
                        
                        # Display in columns for better layout
                        cols = st.columns(4)
                        for i, symbol in enumerate(filtered_symbols[:20]):  # Limit display
                            with cols[i % 4]:
                                st.write(symbol)
                        
                        if len(filtered_symbols) > 20:
                            st.info(f"... and {len(filtered_symbols) - 20} more symbols")
                    else:
                        st.warning(f"No {market_type} symbols found")
                else:
                    st.error("Failed to load symbols")
            except Exception as e:
                st.error(f"Error loading symbols: {str(e)}")

# Main app
def main():
    st.title("🚀 Custom Trading Dashboard")
    
    # Get exchange configuration
    exchange, market_type = sidebar_controls()
    
    # Initialize appropriate OMS based on selection
    if exchange == "Binance":
        oms = initialize_binance()
        if not oms:
            return
        
        # Binance-specific dashboard layout
        order_entry(oms, market_type)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            position_management(oms)
        
        with col2:
            account_info(oms, market_type)
        
        # System messages
        with st.expander("📢 System Messages"):
            if st.button("Clear Logs"):
                oms.successful_orders = []
                oms.failed_orders = []
            st.write("Recent Successful Orders:", oms.successful_orders[-3:])
            st.write("Recent Failed Orders:", oms.failed_orders[-3:])
            
    elif exchange == "MetaTrader 5":
        mt5_oms = initialize_mt5()
        if not mt5_oms:
            return
        
        # MT5-specific dashboard layout
        mt5_order_entry(mt5_oms, market_type)
        
        # MT5 symbols browser
        mt5_symbols_browser(mt5_oms, market_type)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # MT5 position overview
            st.subheader("📊 Positions & P&L")
            try:
                pnl = mt5_oms.get_pnl()
                st.metric("Total P&L", f"{pnl:,.2f}")
                
                positions = mt5_oms.get_positions()
                if not positions.empty:
                    st.dataframe(positions[['symbol', 'type', 'volume', 'price_open', 'profit']], use_container_width=True)
                else:
                    st.info("No open positions")
            except Exception as e:
                st.error(f"Error displaying positions: {str(e)}")
        
        with col2:
            mt5_account_info(mt5_oms, market_type)
        
        # System messages for MT5
        with st.expander("📢 MT5 System Messages"):
            if st.button("Clear MT5 Logs"):
                mt5_oms.successful_orders = []
                mt5_oms.failed_orders = []
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("✅ Recent Successful:")
                for order in mt5_oms.successful_orders[-3:]:
                    st.write(f"{order.get('symbol')} {order.get('side')} {order.get('size')}")
            
            with col_b:
                st.write("❌ Recent Failed:")
                for order in mt5_oms.failed_orders[-3:]:
                    st.write(f"{order.get('symbol')} - {order.get('error', 'Error')[:30]}")
    
    else:
        st.info("Please select an exchange from the sidebar to continue.")
        st.write("Supported exchanges:")
        st.write("- **Binance**: Cryptocurrency trading (Spot & Futures)")
        st.write("- **MetaTrader 5**: Forex, CFDs, and Metals trading")

main()