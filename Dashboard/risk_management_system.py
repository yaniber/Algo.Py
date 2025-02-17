import streamlit as st
from OMS.binance_oms import Binance
from OMS.zerodha import Zerodha
import pandas as pd
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='config/.env')

# Currency conversion setup
def get_usd_inr_rate():
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
        return response.json()['rates']['INR']
    except:
        return 74.0  # Fallback rate

USD_INR_RATE = get_usd_inr_rate()

# Initialize exchanges
def initialize_exchanges():
    exchanges = {}
    system_messages = []
    
    try:
        if os.getenv('BINANCE_API_KEY'):
            exchanges['binance'] = Binance()
        else:
            system_messages.append("⚠️ Binance not configured: Missing API keys")
    except Exception as e:
        system_messages.append(f"❌ Binance initialization failed: {str(e)}")
    
    try:
        if os.getenv('USER_ID'):
            exchanges['zerodha'] = Zerodha()
        else:
            system_messages.append("⚠️ Zerodha not configured: Missing credentials")
    except Exception as e:
        system_messages.append(f"❌ Zerodha initialization failed: {str(e)}")
    
    return exchanges, system_messages

# Portfolio calculations
def calculate_portfolio_metrics(exchanges):
    total_balance = 0
    positions = []
    broker_balances = {}

    # Binance positions
    if 'binance' in exchanges:
        try:
            binance = exchanges['binance']
            futures_balance = binance.get_futures_balance('USDT')
            total_balance += futures_balance['total']
            broker_balances['Binance'] = futures_balance['total']
            
            binance_positions = binance.view_open_futures_positions()
            if not binance_positions.empty:
                for _, row in binance_positions.iterrows():
                    mark_price = float(row['Mark Price'].replace('$', '').replace(',', ''))
                    entry_price = float(row['Entry Price'].replace('$', '').replace(',', ''))
                    size_usd = float(row['Size (USD)'].replace('$', '').replace(',', ''))
                    
                    positions.append({
                        'Exchange': 'Binance',
                        'Symbol': row['Symbol'],
                        'Size (USD)': size_usd,
                        'Entry Price': entry_price,
                        'Mark Price': mark_price,
                        'PnL (USD)': float(row['PNL (Unrealized)'].replace('$', '').replace(',', '')),
                        'Leverage': row['Leverage']
                    })
        except Exception as e:
            st.error(f"Binance data error: {str(e)}")

    # Zerodha positions & holdings
    if 'zerodha' in exchanges:
        try:
            zerodha = exchanges['zerodha']
            inr_balance = zerodha.get_available_balance()
            usd_balance = inr_balance / USD_INR_RATE
            
            zerodha_data = zerodha.get_positions()
            zerodha_positions = zerodha_data["positions"]
            zerodha_holdings = zerodha_data["holdings"]

            total_zerodha_value = usd_balance  # Start with free cash balance

            # Process Zerodha positions
            if not zerodha_positions.empty:
                for _, row in zerodha_positions.iterrows():
                    size_usd = (row['Size'] * row['Mark Price']) / USD_INR_RATE
                    total_zerodha_value += size_usd  # Add position value to total
                    positions.append({
                        'Exchange': 'Zerodha',
                        'Symbol': row['Symbol'],
                        'Size (USD)': size_usd,
                        'Entry Price': row['Entry Price'],
                        'Mark Price': row['Mark Price'],
                        'PnL (USD)': row['PnL'] / USD_INR_RATE,
                        'Leverage': 'N/A'
                    })

            # Process Zerodha holdings
            if not zerodha_holdings.empty:
                for _, row in zerodha_holdings.iterrows():
                    size_usd = (row['Size'] * row['Mark Price']) / USD_INR_RATE
                    total_zerodha_value += size_usd  # Add holding value to total
                    positions.append({
                        'Exchange': 'Zerodha (Holding)',
                        'Symbol': row['Symbol'],
                        'Size (USD)': size_usd,
                        'Entry Price': row['Entry Price'],
                        'Mark Price': row['Mark Price'],
                        'PnL (USD)': row['PnL'] / USD_INR_RATE,
                        'Leverage': 'N/A'
                    })

            # Update total balance and broker-specific balances
            total_balance += total_zerodha_value
            broker_balances['Zerodha'] = total_zerodha_value  # Now includes deployed capital

        except Exception as e:
            st.error(f"Zerodha data error: {str(e)}")

    # Convert positions to DataFrame
    positions_df = pd.DataFrame(positions)
    if not positions_df.empty:
        positions_df['% Change'] = ((positions_df['Mark Price'] - positions_df['Entry Price']) / 
                                positions_df['Entry Price']) * 100
        positions_df['Portfolio %'] = (positions_df['Size (USD)'] / total_balance) * 100
        positions_df['Alert'] = positions_df['% Change'].apply(
            lambda x: '⚠️' if x < -5 else ('🚨' if x < -10 else ''))


    return total_balance, positions_df, broker_balances

# Dashboard UI
def main():
    
    st.title("🌍 Global Risk Dashboard")
    st.markdown("---")

    # Initialize exchanges
    exchanges, system_messages = initialize_exchanges()

    # Portfolio Overview
    total_balance, positions_df, broker_balances = calculate_portfolio_metrics(exchanges)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Portfolio Value", f"${total_balance:,.2f}")

    with col2:
        day_pnl = positions_df['PnL (USD)'].sum() if not positions_df.empty else 0
        st.metric("Daily PnL", f"${day_pnl:,.2f}", 
                 delta=f"{(day_pnl/total_balance*100 if total_balance else 0):.2f}%")

    with col3:
        if day_pnl < -0.02 * total_balance:
            st.error("🚨 Extreme Drawdown Alert: >2% Daily Loss")
        elif day_pnl < -0.01 * total_balance:
            st.warning("⚠️ Drawdown Warning: >1% Daily Loss")
        else:
            st.success("✅ Portfolio Within Risk Parameters")

    st.markdown("---")

    # Broker-wise Balances (Collapsible)
    with st.expander("💰 Broker Balances (Click to Expand)"):
        for broker, balance in broker_balances.items():
            st.metric(f"{broker} Balance", f"${balance:,.2f}")

    # Positions Table
    with st.expander("📊 Detailed Position Analysis", expanded=True):
        if not positions_df.empty:
            styled_df = positions_df.style.applymap(
                lambda x: 'background-color: #ffcccc' if x < -5 else ('background-color: #ff9999' if x < -10 else ''),
                subset=['% Change']
            )
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("No open positions across all exchanges")

    # Risk Controls
    with st.expander("🔒 Emergency Risk Controls", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Kill Switch Protocol")
            selected_exchanges = st.multiselect(
                "Select exchanges to close positions:",
                ['Binance', 'Zerodha']
            )
            confirm = st.checkbox("I confirm I want to close all positions")

            if st.button("🛑 Activate Global Kill Switch", disabled=not confirm):
                try:
                    if 'Binance' in selected_exchanges and 'binance' in exchanges:
                        exchanges['binance'].close_futures_positions()
                    if 'Zerodha' in selected_exchanges and 'zerodha' in exchanges:
                        # Implement Zerodha position closing logic
                        pass
                    st.success("Kill switch executed successfully")
                except Exception as e:
                    st.error(f"Kill switch failed: {str(e)}")

        with col2:
            st.subheader("Risk Parameters")
            st.slider("Max Position Size (% of Portfolio)", 1, 100, 5)
            st.slider("Daily Loss Limit (%)", 1, 10, 2)
            st.button("🔄 Update Risk Parameters")

    # System Messages
    st.markdown("---")
    with st.expander("📢 System Status & Messages"):
        if system_messages:
            for msg in system_messages:
                if "⚠️" in msg:
                    st.warning(msg)
                elif "❌" in msg:
                    st.error(msg)
                else:
                    st.info(msg)
        else:
            st.success("✅ All systems operational")

        if st.button("🔄 Refresh System Status"):
            st.experimental_rerun()


main()
