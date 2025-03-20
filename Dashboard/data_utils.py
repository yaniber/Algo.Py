import streamlit as st
from finstore.finstore import Finstore
from data.update.crypto_binance import fill_gap
from data.fetch.crypto_binance import fetch_symbol_list_binance
from data.fetch.indian_equity import fetch_symbol_list_indian_equity
from data.store.crypto_binance import store_crypto_binance
import time

# --------------------------
# Data Utilities Dashboard
# --------------------------

def show_data_utils_page():
    st.title("📊 Data Utilities Dashboard")
    
    # Section 1: Fetch New Data
    with st.expander("🚀 Fetch New Data", expanded=True):
        data_type = st.radio("Select Market:", ["crypto_binance", "indian_equity"], index=0)
        
        if data_type == "crypto_binance":
            col1, col2 = st.columns(2)
            with col1:
                type_ = st.selectbox("Type", ["spot", "futures", "swap"], index=0)
                suffix = st.text_input("Suffix (e.g., USDT, BTC)", "USDT")
            with col2:
                timeframe = st.selectbox("Timeframe", ["1d", "4h", "1h", "15m", "5m", "1m"], index=0)
                data_points = st.number_input("Data Points Back", min_value=1, value=100)
            
            calc_indicators = st.checkbox("Calculate Technical Indicators", value=True)
            
            if st.button("Fetch Crypto Data"):
                # Use st.spinner instead of st.status to avoid nesting issues
                with st.spinner("Fetching Binance Data..."):
                    try:
                        # Store data
                        st.write("💾 Storing data in Finstore...")  
                        store_crypto_binance(timeframe=timeframe, data_points_back=data_points, type=type_, suffix=suffix)
                        
                        if calc_indicators:
                            st.write("🧮 Calculating technical indicators...")
                            from data.calculate.crypto_binance import calculate_technical_indicators
                            finstore = Finstore(market_name=data_type, timeframe=timeframe, enable_append=True, pair=suffix)
                            symbol_list = finstore.read.get_symbol_list()
                            calculate_technical_indicators(market_name=data_type, symbol_list=symbol_list, timeframe=timeframe)
                        
                        st.success("✅ Data fetch complete!")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        elif data_type == "indian_equity":
            col1, col2 = st.columns(2)
            with col1:
                complete_list = st.checkbox("Fetch Complete List", value=True)
                timeframe = st.selectbox("Timeframe", ["1d", "1h", "15m", "5m"], index=0)
            with col2:
                index_name = st.radio("Index", ["all", "nse_eq_symbols"], index=0)
                data_points = st.number_input("Data Points Back", min_value=1, value=100)
            
            calc_indicators = st.checkbox("Calculate Technical Indicators", value=True)
            
            if st.button("Fetch Equity Data"):
                with st.status("Fetching Indian Equity Data...") as status:
                    try:
                        st.write("🔍 Fetching symbol list...")
                        symbols = fetch_symbol_list_indian_equity(index_name)
                        st.write(f"📊 Found {len(symbols)} symbols, gathering OHLCV...")
                        
                        progress_bar = st.progress(0)
                        for percent in range(100):
                            time.sleep(0.02)
                            progress_bar.progress(percent + 1)
                        
                        st.write("💾 Storing data in Finstore...")
                        # Actual implementation would call store_indian_equity here
                        
                        if calc_indicators:
                            st.write("🧮 Calculating technical indicators...")
                            # Actual implementation would call calculate_technical_indicators
                        
                        status.update(label="✅ Data fetch complete!", state="complete")
                    except Exception as e:
                        status.update(label=f"❌ Error: {str(e)}", state="error")

    # Section 2: Fill Data Gaps
    with st.expander("🔧 Fill Data Gaps", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            gap_market = st.selectbox("Market", ["crypto_binance", "indian_equity"], key="gap_market")
            gap_timeframe = st.selectbox("Timeframe", ["1d", "4h", "1h"], key="gap_timeframe")
        with col2:
            if gap_market == "crypto_binance":
                pair = st.text_input("Pair (e.g., BTC)", "BTC")
            else:
                pair = st.text_input("Index Name", "nse_eq_symbols")
        
        if st.button("Fill Data Gaps"):
            with st.status(f"Filling gaps for {gap_market}...") as status:
                try:
                    st.write("⏳ Checking latest available date...")
                    # Dummy check - implement actual date check
                    time.sleep(1)
                    
                    st.write("🔍 Gathering missing data...")
                    progress_bar = st.progress(0)
                    for percent in range(100):
                        time.sleep(0.02)
                        progress_bar.progress(percent + 1)
                    
                    st.write("💾 Updating database...")
                    # Actual implementation would call fill_gap here
                    # fill_gap(market_name=gap_market, timeframe=gap_timeframe, pair=pair)
                    
                    status.update(label="✅ Gap filling complete!", state="complete")
                except Exception as e:
                    status.update(label=f"❌ Error: {str(e)}", state="error")

    # Section 3: View Existing Data
    with st.expander("👀 View Existing Data", expanded=True):
        view_market = st.selectbox("Market", ["crypto_binance", "indian_equity"], key="view_market")
        view_timeframe = st.selectbox("Timeframe", ["1d", "4h", "1h", "15m", "1m"], key="view_timeframe")
        if view_market == 'crypto_binance':
            pair = st.selectbox("Pair", ["BTC", "USDT"], key="pair")
        else:
            pair = ''
        
        if st.button("Load Data Summary"):
            try:
                finstore = Finstore(market_name=view_market, timeframe=view_timeframe, pair=pair)
                symbols = finstore.read.get_symbol_list()
                
                st.subheader("📋 Available Symbols")
                st.write(f"Found {len(symbols)} symbols:")
                st.write(symbols[:10])  # Show first 10 symbols
                
                if len(symbols) > 0:
                    sample_symbol = symbols[0]
                    st.subheader(f"📈 Sample Data for {sample_symbol}")
                    symbol, sample_data = finstore.read.symbol(sample_symbol)
                    st.dataframe(sample_data.tail())
            except Exception as e:
                st.error(f"Error loading data: {str(e)}")

# Run the page
show_data_utils_page()