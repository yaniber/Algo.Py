import streamlit as st
import pandas as pd
import pytz
import schedule
import threading
import time
import os
from datetime import datetime
from typing import List, Dict

# ---------------------
# Mocked Pipeline Imports
# ---------------------
# Replace these with your actual imports from your codebase:
#
# from data.update.indian_equity import fill_gap
# from data.fetch.indian_equity import fetch_symbol_list_indian_equity
# from utils.db.fetch import fetch_entries
# from executor.indian_equity_pipeline import run_pipeline
# from executor.executor import (
#     execute_trades_telegram, 
#     execute_trades_zerodha, 
#     is_market_open, 
#     get_balance
# )
# from utils.notifier.telegram import send_telegram_message
# ...

# For demonstration, let's just mock the real functions:
def fill_gap(market_name: str, timeframe: str, complete_list: bool = True):
    st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] fill_gap() called")

def fetch_symbol_list_indian_equity(index_name: str):
    return ["SBIN.NS", "RELIANCE.NS", "TCS.NS", "INFY.NS"]

def fetch_entries(market_name: str, timeframe: str, all_entries: bool):
    # Return a dictionary of mock DataFrames
    # Typically you’d load from DB, but let’s just mock:
    return {
        "SBIN.NS": pd.DataFrame({
            "timestamp": pd.date_range("2023-01-01", periods=10, freq="D"),
            "open": [100]*10, "high": [105]*10, "low": [99]*10, "close": [102]*10, "volume": [1000]*10
        }),
        "RELIANCE.NS": pd.DataFrame({
            "timestamp": pd.date_range("2023-01-01", periods=10, freq="D"),
            "open": [2500]*10, "high": [2550]*10, "low": [2490]*10, "close": [2520]*10, "volume": [2000]*10
        }),
        # ...
    }

def run_pipeline(ohlcv_data, sim_start, sim_end, complete_list, symbol_list, weekday, init_cash):
    # In reality, your pipeline would produce fresh buys & sells DataFrames
    st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] run_pipeline() called")
    fresh_buys = pd.DataFrame({"symbol": ["SBIN.NS"], "side": ["BUY"], "size": [1], "price": [101]})
    fresh_sells = pd.DataFrame({"symbol": ["RELIANCE.NS"], "side": ["SELL"], "size": [1], "price": [2500]})
    return fresh_buys, fresh_sells

def is_market_open():
    # Simplified check
    return True

def execute_trades_telegram(trades_df: pd.DataFrame):
    st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] execute_trades_telegram() called")
    
def execute_trades_zerodha(trades_df: pd.DataFrame):
    st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] execute_trades_zerodha() called")
    # In a real case, you'd get success/fail from broker
    return (trades_df.to_dict("records"), [])  # (successful_trades, failed_trades)

def get_balance():
    # Mock portfolio balance
    return "Balance: ₹100,000 | Holdings: SBIN, RELIANCE"

def send_telegram_message(msg: str):
    st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Telegram Msg: {msg}")

# ---------------------
# Pipeline Functions 
# ---------------------
def pipeline_deploy(pipeline_config):
    """
    This function runs once at the scheduled time for pipeline preparation:
    1. fill_gap
    2. fetch symbol list + OHLCV
    3. run_pipeline
    4. store fresh buys and sells in parquet
    """
    st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [Pipeline] Started for strategy '{pipeline_config['strategy_name']}'")

    fill_gap(market_name='indian_equity', timeframe='1d', complete_list=True)

    try:
        symbol_list = pipeline_config['symbols'] or fetch_symbol_list_indian_equity(index_name='nse_eq_symbols')
        ohlcv_data = fetch_entries(market_name='indian_equity', timeframe='1d', all_entries=True)

        sim_start = pipeline_config['sim_start']
        sim_end   = pd.Timestamp.now().strftime('%Y-%m-%d 00:00:00')

        fresh_buys, fresh_sells = run_pipeline(
            ohlcv_data, 
            sim_start, 
            sim_end,
            complete_list=False, 
            symbol_list=symbol_list, 
            weekday=2, 
            init_cash=pipeline_config['init_cash']
        )

        # Save fresh buys/sells
        #if not fresh_buys.empty:
        #    fresh_buys.to_parquet('database/db/fresh_buys.parquet')
        #if not fresh_sells.empty:
        #    fresh_sells.to_parquet('database/db/fresh_sells.parquet')

        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [Pipeline] Completed")
    except Exception as e:
        st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [Pipeline] Error: {e}")


def execute_trades_deploy():
    """
    This function executes trades if any fresh_buys/fresh_sells exist.
    """
    st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [Execute Trades] Checking market and pending trades...")
    if not is_market_open():
        send_telegram_message("Market closed. Skipping trade execution.")
        return

    buys_path = 'database/db/fresh_buys.parquet'
    sells_path = 'database/db/fresh_sells.parquet'

    if not os.path.exists(buys_path) and not os.path.exists(sells_path):
        send_telegram_message("No fresh trades to execute. Skipping.")
        return

    # Execute sells
    if os.path.exists(sells_path):
        fresh_sells = pd.read_parquet(sells_path)
        execute_trades_telegram(fresh_sells)
        success_sells, failed_sells = execute_trades_zerodha(fresh_sells)
        if failed_sells:
            pd.DataFrame(failed_sells).to_parquet('database/db/failed_sells.parquet')
        os.remove(sells_path)

    # Execute buys
    if os.path.exists(buys_path):
        fresh_buys = pd.read_parquet(buys_path)
        execute_trades_telegram(fresh_buys)
        success_buys, failed_buys = execute_trades_zerodha(fresh_buys)
        if failed_buys:
            pd.DataFrame(failed_buys).to_parquet('database/db/failed_buys.parquet')
        os.remove(buys_path)

    st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [Execute Trades] Completed")


def retry_failed_trades_deploy():
    """
    Retry any failed trades
    """
    sells_path = 'database/db/failed_sells.parquet'
    buys_path  = 'database/db/failed_buys.parquet'

    # Retry failed sells
    if os.path.exists(sells_path):
        failed_sells = pd.read_parquet(sells_path)
        execute_trades_telegram(failed_sells)
        success_sell, still_failed_sell = execute_trades_zerodha(failed_sells)
        if still_failed_sell:
            pd.DataFrame(still_failed_sell).to_parquet(sells_path)
        else:
            os.remove(sells_path)

    # Retry failed buys
    if os.path.exists(buys_path):
        failed_buys = pd.read_parquet(buys_path)
        execute_trades_telegram(failed_buys)
        success_buy, still_failed_buy = execute_trades_zerodha(failed_buys)
        if still_failed_buy:
            pd.DataFrame(still_failed_buy).to_parquet(buys_path)
        else:
            os.remove(buys_path)

    st.session_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] [Retry Failed Trades] Completed")


def balance_and_holdings_deploy():
    portfolio_message = get_balance()
    send_telegram_message(portfolio_message)

# ---------------------
# SCHEDULER & BACKGROUND
# ---------------------
def run_continuously(interval=1):
    """Run schedule.run_pending() in a background thread."""
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @staticmethod
        def run():
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run

# We need to start the background scheduler only once
if "scheduler_running" not in st.session_state:
    st.session_state.scheduler_running = False

# This will store logs of pipeline runs, trades, etc.
if "logs" not in st.session_state:
    st.session_state.logs = []

# We'll keep track of deployed strategies in session_state
# In a real scenario, you might store them in a DB
if "deployed_strategies" not in st.session_state:
    st.session_state.deployed_strategies = []

# ---------------------
# STREAMLIT UI
# ---------------------
def main():
    st.title("Live Strategy Deployment Dashboard")

    st.markdown(
        """
        This dashboard lets you:
        1. **Select or configure** a strategy and parameters.
        2. **Choose symbols** for Indian Equity (or any market).
        3. **Configure a schedule** for data fetch, pipeline run, trade execution, etc.
        4. **Deploy** the strategy with the chosen configuration.
        5. **Monitor** the deployed strategies and see logs in real time.
        """
    )

    # -------------
    # Strategy Configuration
    # -------------
    with st.expander("1. Strategy & Symbol Configuration", expanded=True):
        strategy_name = st.text_input("Strategy Name", value="My_Indian_Equity_Strategy")

        st.write("**Select Broker** (mocked in this example):")
        broker = st.selectbox("Broker:", ["Zerodha", "Fyers", "MockBroker"], index=0)

        sim_start_date = st.date_input("Simulation Start Date", value=datetime(2023,1,1).date())
        init_cash = st.number_input("Initial Cash", min_value=1000, step=1000, value=30000)

        # Strategy-specific parameters
        st.subheader("Strategy Parameters")
        fast_ema = st.number_input("fast EMA period", min_value=1, value=10)
        slow_ema = st.number_input("slow EMA period", min_value=1, value=50)

        # Symbol selection
        st.subheader("Symbol Selection")
        available_symbols = fetch_symbol_list_indian_equity("nse_eq_symbols")
        selected_symbols = st.multiselect("Pick from NSE Symbols", available_symbols, default=["SBIN.NS", "RELIANCE.NS"])

    # -------------
    # Scheduling
    # -------------
    with st.expander("2. Scheduling Configuration", expanded=True):
        st.write("**Select daily times** (HH:MM, 24-hour format) for each stage. (IST)")

        data_fetch_time = st.text_input("Data Fetch Time", value="18:00")
        pipeline_time = st.text_input("Pipeline Run Time", value="19:00")
        trade_execute_time = st.text_input("Trade Execution Time", value="09:15")
        retry_failed_time = st.text_input("Retry Failed Trades Time", value="12:00")
        balance_holdings_time = st.text_input("Balance & Holdings Time", value="17:00")

        st.caption("These times are naive or local. In production, you'd want robust timezone handling (e.g., `pytz` or `ZoneInfo`).")

    # -------------
    # Deployment
    # -------------
    with st.expander("3. Deploy & Manage", expanded=True):
        st.write("Click **Deploy** to set up scheduled tasks for this strategy.")
        
        if st.button("Deploy Strategy"):
            # Create a config object for the pipeline
            pipeline_config = {
                "strategy_name": strategy_name,
                "broker": broker,
                "sim_start": pd.Timestamp(sim_start_date),
                "init_cash": init_cash,
                "symbols": selected_symbols,
                "params": {
                    "fast_ema": fast_ema,
                    "slow_ema": slow_ema
                },
                # You could store more info as needed
            }

            # 1) Data fetch schedule
            schedule.every().day.at(data_fetch_time).do(
                lambda: fill_gap("indian_equity", "1d", True)
            ).tag(strategy_name)

            # 2) Pipeline schedule
            schedule.every().day.at(pipeline_time).do(
                lambda: pipeline_deploy(pipeline_config)
            ).tag(strategy_name)

            # 3) Execute trades schedule
            schedule.every().day.at(trade_execute_time).do(
                execute_trades_deploy
            ).tag(strategy_name)

            # 4) Retry failed trades
            schedule.every().day.at(retry_failed_time).do(
                retry_failed_trades_deploy
            ).tag(strategy_name)

            # 5) Balance & holdings
            schedule.every().day.at(balance_holdings_time).do(
                balance_and_holdings_deploy
            ).tag(strategy_name)

            # Save info about this deployment in session state
            st.session_state.deployed_strategies.append({
                "strategy_name": strategy_name,
                "broker": broker,
                "sim_start": str(sim_start_date),
                "init_cash": init_cash,
                "symbols": selected_symbols,
                "data_fetch_time": data_fetch_time,
                "pipeline_time": pipeline_time,
                "trade_execute_time": trade_execute_time,
                "retry_failed_time": retry_failed_time,
                "balance_holdings_time": balance_holdings_time,
                "deployment_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

            st.success(f"Strategy '{strategy_name}' deployed! Scheduled tasks have been created.")

        st.write("**Active Deployments:**")
        if len(st.session_state.deployed_strategies) == 0:
            st.info("No strategies deployed yet.")
        else:
            for idx, strat in enumerate(st.session_state.deployed_strategies):
                st.markdown(f"- **{idx+1}. {strat['strategy_name']}** | Broker: {strat['broker']} | Init Cash: {strat['init_cash']} | Deployed at: {strat['deployment_time']}")
                st.write(f"Symbols: {', '.join(strat['symbols'])}")
                st.write(f"Data fetch @ {strat['data_fetch_time']} | Pipeline @ {strat['pipeline_time']} | Execution @ {strat['trade_execute_time']} | Retry @ {strat['retry_failed_time']} | Balance @ {strat['balance_holdings_time']}")

                remove_button = st.button(f"Remove {strat['strategy_name']}", key=f"remove_{idx}")
                if remove_button:
                    # Clear scheduled jobs for this strategy
                    schedule.clear(strat['strategy_name'])
                    # Remove from session_state
                    st.session_state.deployed_strategies.pop(idx)
                    st.experimental_rerun()

    # -------------
    # Logs & Status
    # -------------
    with st.expander("4. Live Logs & Scheduler Status", expanded=True):
        st.write("**Scheduler Status**: ", "Running" if st.session_state.scheduler_running else "Stopped")
        if st.button("Start Scheduler") and not st.session_state.scheduler_running:
            # Start the background thread to run schedule
            st.session_state.stop_run_continuously = run_continuously()
            st.session_state.scheduler_running = True
            st.success("Scheduler started in background thread.")

        if st.button("Stop Scheduler") and st.session_state.scheduler_running:
            # Stop the background thread
            st.session_state.stop_run_continuously.set()
            st.session_state.scheduler_running = False
            st.warning("Scheduler stopped.")

        # Display logs
        st.write("**Event Logs**:")
        log_lines = st.session_state.logs[-50:]  # show last 50 logs
        if log_lines:
            st.write("\n".join(log_lines))
        else:
            st.info("No logs yet.")


if __name__ == "__main__":
    main()
