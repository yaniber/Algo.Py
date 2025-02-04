import streamlit as st
import pandas as pd
import inspect
import datetime
from datetime import date
import pickle
import time
from finstore.finstore import Finstore


@st.cache_resource
def get_finstore_crypto(timeframe='4h'):
    return Finstore(market_name='crypto_binance', timeframe=timeframe)

@st.cache_resource
def get_finstore_indian_equity(timeframe='1d'):
    return Finstore(market_name='indian_equity', timeframe=timeframe)

@st.cache_resource
def get_finstore(market_name , timeframe, pair=''):
    return Finstore(market_name=market_name, timeframe=timeframe, pair=pair)

# ------------------------------------
# Dummy Functions for Demonstration
# ------------------------------------

def list_strategy_modules():
    """Return available strategy modules with their parameters"""
    return {
        'EMA Crossover Strategy': get_ema_signals_wrapper,
        'RSI Strategy': dummy_rsi_strategy,
        'MACD Strategy': dummy_macd_strategy
    }

def get_signals(ohlcv_data: pd.DataFrame, 
                symbol_list: list, 
                weekday: int = 2, 
                fast_ema_period: int = 10, 
                slow_ema_period: int = 100):
    """Sample strategy function"""
    # Your actual implementation will go here
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def get_ema_signals_wrapper(ohlcv_data: pd.DataFrame, 
                symbol_list: list, 
                fast_ema_period: int = 10, 
                slow_ema_period: int = 100):
    """Sample strategy function"""
    # Your actual implementation will go here
    
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def dummy_rsi_strategy(ohlcv_data, symbol_list, rsi_period=14, oversold=30, overbought=70):
    """Dummy RSI strategy"""
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def dummy_macd_strategy(ohlcv_data, symbol_list, fast=12, slow=26, signal=9):
    """Dummy MACD strategy"""
    return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def get_available_assets(timeframe=None):
    """Return hierarchical market structure with nested universes"""
    asset_groups = {}
    
    if not timeframe:
        return {'Please select timeframe first': []}

    try:
        # Get crypto pairs
        btc_pairs = get_finstore("crypto_binance", timeframe, pair="BTC").read.get_symbol_list()
        usdt_pairs = get_finstore("crypto_binance", timeframe, pair="USDT").read.get_symbol_list()
        asset_groups['Crypto'] = {
            'BTC Pairs': list(btc_pairs) if len(btc_pairs) > 0 else ['No BTC pairs'],
            'USDT Pairs': list(usdt_pairs) if len(usdt_pairs) > 0 else ['No USDT pairs']
        }
    except Exception as e:
        asset_groups['Crypto'] = {'Error': [f'Failed to load crypto data: {str(e)}']}

    try:
        # Indian equity with sub-universes
        nse_eq = get_finstore("indian_equity", timeframe, pair="").read.get_symbol_list()
        asset_groups['Indian Market'] = {
            'NSE Equity': list(nse_eq) if len(nse_eq) > 0 else ['No NSE equities']
        }
    except Exception as e:
        asset_groups['Indian Market'] = {'Error': [f'Failed to load Indian data: {str(e)}']}

    # Add other markets
    asset_groups.update({
        'US Market': {
            'NASDAQ': ['AAPL', 'TSLA', 'GOOG'],
            'NYSE': ['IBM', 'BA']
        },
        'Commodities': {
            'Metals': ['GOLD', 'SILVER'],
            'Energy': ['OIL', 'NATURALGAS']
        }
    })
    
    return asset_groups

def process_selected_assets(selections, timeframe):
    """Convert user selections to final symbol list with nested universes"""
    all_assets = get_available_assets(timeframe)
    selected_symbols = []
    
    for selection in selections:
        clean_selection = selection.replace(" ", "")
        
        # Handle nested universe selection (e.g., "Crypto/BTC Pairs (All)")
        if '/ (All)' in clean_selection:
            market_path = clean_selection.replace(' (All)', '').split('/')
            current_level = all_assets
            try:
                for level in market_path:
                    current_level = current_level[level.strip()]
                # Flatten nested structure
                symbols = []
                for sub_level in current_level.values():
                    symbols.extend(sub_level)
                selected_symbols.extend(symbols)
            except KeyError:
                continue
        
        # Add individual symbols
        elif '(All)' not in clean_selection:
            selected_symbols.append(clean_selection)
    
    return list(set(selected_symbols))


# ------------------------------------
# Strategy Backtester Page
# ------------------------------------

def show_backtester_page():
    st.title("Strategy Backtester 🔧")
    
    # 1. Strategy Module Selection
    with st.expander("📦 Strategy Module Selection", expanded=True):
        strategy_modules = list_strategy_modules()
        selected_module = st.selectbox(
            "Select Strategy Module",
            options=list(strategy_modules.keys())
        )
    
    # 2. Asset Selection with nested universes
    with st.expander("🌍 Asset Selection", expanded=True):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # Timeframe selection
            timeframe = st.selectbox(
                "⏳ Timeframe:",
                options=["1D", "4H", "1H", "15m", "5m", "1m"],
                index=0
            )
        
        with col2:
            asset_groups = get_available_assets(timeframe)
            all_options = []

            # Build nested options
            for market, submarkets in asset_groups.items():
                # Add market-level universe
                all_options.append(f"{market}/ (All)")
                
                for submarket, symbols in submarkets.items():
                    # Add submarket-level universe
                    all_options.append(f" {market}/{submarket} (All)")
                    
                    # Add individual symbols
                    for sym in symbols:
                        all_options.append(f"  {sym}")

            # Multi-select with hierarchical indentation
            selected = st.multiselect(
                "Select assets/universe:",
                options=all_options,
                default=[],
                format_func=lambda x: x.replace('/', ' ➔ '),
                help="Select entire universes or individual assets"
            )

            # Process selections
            final_symbols = process_selected_assets(selected, timeframe)
    
    # Display selected symbols
    if final_symbols:
        st.info(f"Selected {len(final_symbols)} assets: {', '.join(final_symbols[:3])}..."
              f" (Timeframe: {timeframe})")
    else:
        st.error("Please select at least one asset universe or individual asset")

    
    # 3. Strategy Parameters
    with st.expander("⚙️ Strategy Parameters", expanded=True):
        strategy_func = strategy_modules[selected_module]
        sig = inspect.signature(strategy_func)
        params = {}
        
        # Skip first two parameters (ohlcv_data and symbol_list)
        for param in list(sig.parameters.values())[2:]:
            # Create input widgets based on parameter type
            if param.annotation == int:
                val = st.number_input(
                    param.name,
                    value=param.default if param.default != inspect.Parameter.empty else 0,
                    step=1
                )
            elif param.annotation == float:
                val = st.number_input(
                    param.name,
                    value=param.default if param.default != inspect.Parameter.empty else 0.0,
                    step=0.1
                )
            else:
                val = st.text_input(
                    param.name,
                    value=str(param.default) if param.default != inspect.Parameter.empty else ""
                )
            params[param.name] = val
    
    # 4. Backtest Configuration
    with st.expander("📅 Backtest Settings", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=date(2023, 1, 1)
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=date(2024, 1, 1)
            )
        
        init_cash = st.number_input("Initial Capital", value=100000)
        fees = st.number_input("Trading Fees (%)", value=0.1)
        slippage = st.number_input("Slippage (%)", value=0.05)
    
    # 5. Run Backtest
    if st.button("🚀 Run Backtest"):
        if not final_symbols:
            st.error("Please select at least one asset!")
            return
        
        # Mock progress and execution
        with st.spinner("Running backtest..."):
            progress_bar = st.progress(0)
            
            # Simulate strategy execution
            for i in range(3):
                time.sleep(0.5)
                progress_bar.progress((i + 1) * 25)
            
            # Dummy data for demonstration
            mock_results = pd.DataFrame({
                'Metric': ['Total Return', 'Sharpe Ratio', 'Max Drawdown'],
                'Value': ['+125.4%', '2.34', '-23.5%']
            })
            
            # Mock portfolio object
            mock_portfolio = {
                'config': params,
                'results': mock_results
            }
            
            # Save mock portfolio
            with open(f"backtest_{datetime.datetime.now().isoformat()}.pkl", "wb") as f:
                pickle.dump(mock_portfolio, f)
            
            progress_bar.empty()
            
            # Display results
            st.success("Backtest completed!")
            
            # Show basic metrics
            st.subheader("📊 Performance Summary")
            st.dataframe(mock_results)
            
            # Show mock equity curve
            st.subheader("📈 Equity Curve")
            num_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1
            mock_equity = pd.DataFrame({
                'Date': pd.date_range(start=start_date, end=end_date),
                'Value': [100000 + i*1000 for i in range(num_days)]
            })
            st.line_chart(mock_equity.set_index('Date'))
            
            # Show save location
            st.info("Portfolio object saved to local storage")

# Run the page
show_backtester_page()