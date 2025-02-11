import streamlit as st
import threading
import queue
import time
import schedule
import uuid
import inspect
import datetime
from datetime import datetime as dt, date
import pandas as pd
import os

# Import strategy functions
from strategy.public.ema_strategy import get_ema_signals_wrapper

# Import asset fetching functions (if needed, adjust import paths)
from finstore.finstore import Finstore

# Import OMS classes
from OMS.telegram import Telegram
from OMS.zerodha import Zerodha
# (Assume similar import for binance OMS if needed)

# Import scheduler functions from your codebase if desired (fill_gap, fetch_entries)
from data.update.crypto_binance import fill_gap
from utils.db.fetch import fetch_entries

# Global container to track active deployments
if 'deployments' not in st.session_state:
    st.session_state.deployments = {}  # dict: deployment_id -> {thread, log_queue, stop_event, config, status}

###########################
# Helper Functions & Classes
###########################

def deployment_runner(deployment_id, config, log_queue, stop_event):
    """
    This function is run in a separate thread.
    It sets up a scheduler based on the user config and runs the deployment loop.
    """
    def log(msg):
        timestamp = dt.now().strftime('%Y-%m-%d %H:%M:%S')
        log_queue.put(f"[{timestamp}] {msg}")
        print(f"[{timestamp}] {msg}")
    
    log(f"Deployment {deployment_id} started with config: {config}")
    
    # Define the job to run at scheduled times
    def scheduled_job():
        if stop_event.is_set():
            log("Stop event detected. Exiting scheduled job.")
            return
        
        log("Starting scheduled deployment cycle...")
        try:
            # Step 1: Fill gap data
            market_params = config.get("market_params", {})
            log("Calling fill_gap...")
            fill_gap(**market_params)
            log("fill_gap completed.")
            
            # Step 2: Fetch entries (OHLCV data)
            log("Fetching OHLCV data...")
            ohlcv_data = fetch_entries(**market_params)
            log("Fetched OHLCV data.")
            
            # Step 3: Generate signals using the strategy
            strategy_func = config["strategy_func"]
            strategy_params = config["strategy_params"]
            asset_universe = config["asset_universe"]
            
            # Make sure we filter ohlcv_data for selected symbols
            ohlcv_data_filtered = {sym: ohlcv_data[sym] for sym in asset_universe if sym in ohlcv_data}
            log("Generating signals using strategy...")
            entries, exits, close_data, open_data = strategy_func(ohlcv_data, asset_universe, **strategy_params)
            log("Signals generated.")
            
            # Step 4: Here you could validate signals with a TradeMonitor if needed
            # For now, we assume signals (entries, exits) are ready to be sent
            
            # Step 5: Send orders via the selected OMS
            oms = config["oms_instance"]
            log(f"Placing orders via OMS: {config['oms_type']}...")
            # This example assumes that sending orders is done via a method (e.g., send_telegram_message)
            # In a real scenario, you would prepare order details and call the proper OMS method.
            if config["oms_type"] == "Telegram":
                message = f"Deployment {deployment_id} orders:\nEntries: {entries.sum().sum()} \nExits: {exits.sum().sum()}"
                log(message)
                log(f'entries : {entries},\nexits : {exits}')
                #oms.send_telegram_message(message)
            elif config["oms_type"] == "Zerodha":
                # For zerodha, assume we prepare an orders DataFrame and call iterate_orders_df
                # This is just a placeholder
                orders_df = pd.DataFrame({
                    "symbol": list(asset_universe),
                    "Side": ["Buy"] * len(asset_universe),
                    "Size": [1]*len(asset_universe),
                    "Price": [0]*len(asset_universe)
                })
                oms.iterate_orders_df(orders_df)
            else:
                log("OMS type not recognized. Skipping order placement.")
            
            log("Deployment cycle completed.")
        except Exception as e:
            log(f"Error during deployment cycle: {str(e)}")
    
    # Schedule the job according to configuration
    scheduler_type = config.get("scheduler_type", "fixed_interval")  # or 'specific_time'
    if scheduler_type == "fixed_interval":
        interval = config.get("scheduler_interval", 60)  # in minutes
        log(f"Scheduling job every {interval} minutes.")
        scheduled_job()
        schedule.every(interval).minutes.do(scheduled_job)
    elif scheduler_type == "specific_time":
        target_time = config.get("scheduler_time", "00:00")  # in HH:MM 24hr format
        log(f"Scheduling job every day at {target_time}.")
        schedule.every().day.at(target_time).do(scheduled_job)
    else:
        log("Unknown scheduler type. Exiting deployment.")
        return
    
    # Main loop for the deployment thread
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)
    
    log("Deployment thread exiting due to stop event.")

###########################
# UI Components
###########################

st.title("📡 Strategy Deployment Dashboard")

# Sidebar or main area for creating a new deployment
st.header("New Deployment Configuration")

with st.form("deployment_form"):
    st.subheader("1. Strategy Module Selection")
    # For now, we only include the EMA strategy (feel free to expand to others)
    strategy_option = st.selectbox("Select Strategy Module", options=["EMA Crossover Strategy"])
    
    # Based on the strategy, show relevant parameters; here we use EMA parameters
    st.markdown("**Strategy Parameters:**")
    fast_ema_period = st.number_input("Fast EMA Period", value=10, step=1)
    slow_ema_period = st.number_input("Slow EMA Period", value=100, step=1)
    
    st.subheader("2. Asset Universe Selection")
    # For simplicity, let the user enter a comma-separated list of symbols
    asset_input = st.text_input("Enter asset symbols (comma-separated)", value="BTC,ETH")
    asset_universe = [s.strip() for s in asset_input.split(",") if s.strip()]
    
    st.subheader("3. Market / Data Parameters")
    market_name = st.text_input("Market Name", value="crypto_binance")
    timeframe = st.selectbox("Timeframe", options=["15m", "1h", "4h"], index=0)
    pair = st.text_input("Pair (if applicable)", value="BTC")
    days_back = st.number_input("Backtest days (for data fetch)", value=4, step=1)
    
    # Prepare market params to pass to fill_gap and fetch_entries
    market_params = {
        "market_name": market_name,
        "timeframe": timeframe,
        "pair": pair,
        #"all_entries": True,  # assuming this flag is needed; adjust as necessary
        #"days_back": days_back  # if needed by your functions
    }
    
    st.subheader("4. Broker / OMS Configuration")
    oms_type = st.selectbox("Select Broker / OMS", options=["Telegram", "Zerodha", "Binance"])
    if oms_type == "Telegram":
        telegram_token = st.text_input("Telegram Token", value="", type="password")
        telegram_group_id = st.text_input("Telegram Group ID", value="")
    elif oms_type == "Zerodha":
        user_id = st.text_input("User ID", value="")
        password = st.text_input("Password", value="", type="password")
        totp_secret = st.text_input("TOTP Secret", value="", type="password")
    # (Add similar inputs for Binance if needed)
    
    st.subheader("5. Scheduler Configuration")
    scheduler_option = st.selectbox("Scheduler Type", options=["Fixed Interval", "Specific Time"])
    if scheduler_option == "Fixed Interval":
        scheduler_interval = st.number_input("Interval (minutes)", value=60, step=1)
    else:
        scheduler_time = st.text_input("Time (HH:MM in 24hr format)", value="23:00")
    
    # Submit form button
    submitted = st.form_submit_button("Deploy Strategy")
    
if submitted:
    # Prepare strategy config
    strategy_params = {
        "fast_ema_period": fast_ema_period,
        "slow_ema_period": slow_ema_period,
    }
    # Get the strategy function – in this case, EMA
    strategy_func = get_ema_signals_wrapper
    
    # Initialize OMS based on selection
    if oms_type == "Telegram":
        # Use provided token/group_id if given, otherwise let the class load from .env
        #oms_instance = Telegram(token=telegram_token if telegram_token else None,
        #                        group_id=telegram_group_id if telegram_group_id else None)
        oms_instance = Telegram()
    elif oms_type == "Zerodha":
        oms_instance = Zerodha(userid=user_id, password=password, totp=totp_secret)
    else:
        oms_instance = None  # Replace with Binance OMS initialization as needed
    
    # Prepare scheduler config
    if scheduler_option == "Fixed Interval":
        scheduler_type = "fixed_interval"
        scheduler_value = scheduler_interval
    else:
        scheduler_type = "specific_time"
        scheduler_value = scheduler_time
    
    deployment_config = {
        "strategy_func": strategy_func,
        "strategy_params": strategy_params,
        "asset_universe": asset_universe,
        "market_params": market_params,
        "oms_type": oms_type,
        "oms_instance": oms_instance,
        "scheduler_type": scheduler_type,
    }
    if scheduler_type == "fixed_interval":
        deployment_config["scheduler_interval"] = scheduler_value
    else:
        deployment_config["scheduler_time"] = scheduler_value
    
    # Create a log queue and stop event for this deployment
    log_queue = queue.Queue()
    stop_event = threading.Event()
    deployment_id = str(uuid.uuid4())[:8]
    
    # Start the deployment in a separate daemon thread
    deployment_thread = threading.Thread(
        target=deployment_runner,
        args=(deployment_id, deployment_config, log_queue, stop_event),
        daemon=True
    )
    deployment_thread.start()
    
    # Save deployment info in session_state
    st.session_state.deployments[deployment_id] = {
        "thread": deployment_thread,
        "log_queue": log_queue,
        "stop_event": stop_event,
        "config": deployment_config,
        "status": "Running",
        "created_at": dt.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    st.success(f"Deployment {deployment_id} started successfully.")

###########################
# Deployment Status Section
###########################
st.header("Active Deployments")

if st.session_state.deployments:
    for dep_id, dep_info in st.session_state.deployments.items():
        st.subheader(f"Deployment ID: {dep_id}")
        st.markdown(f"**Created at:** {dep_info['created_at']}")
        config = dep_info["config"]
        st.markdown(f"**Scheduler:** {'Every ' + str(config.get('scheduler_interval', config.get('scheduler_time')))}")
        st.markdown(f"**OMS:** {config.get('oms_type')}")
        
        # Display log messages from the deployment's log_queue
        log_msgs = []
        while not dep_info["log_queue"].empty():
            log_msgs.append(dep_info["log_queue"].get())
        if log_msgs:
            st.text_area("Deployment Logs", value="\n".join(log_msgs), height=150)
        else:
            st.info("No new logs.")
        
        # Button to stop the deployment
        if st.button(f"Stop Deployment {dep_id}"):
            dep_info["stop_event"].set()
            st.success(f"Deployment {dep_id} stopped.")
else:
    st.info("No active deployments.")

###########################
# Notes / Debug Instructions
###########################
st.markdown("---")
st.markdown("**Debugging Instructions:**")
st.markdown("- Detailed debug messages are printed to the deployment log.")
st.markdown("- Check the logs above to see each stage of the deployment cycle.")
st.markdown("- The deployment thread runs in the background; stopping it will halt further scheduled executions.")

