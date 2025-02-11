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
import json
from dotenv import load_dotenv

# Import strategy function for EMA
from strategy.public.ema_strategy import get_ema_signals_wrapper

# Import data functions
from data.update.crypto_binance import fill_gap
from utils.db.fetch import fetch_entries

# Import OMS classes (example for Telegram and Zerodha)
from OMS.telegram import Telegram
from OMS.zerodha import Zerodha
# (Assume similar for Binance if needed)

# Global persistent dictionary to track active deployments.
# This persists as long as the server process is running.
if "ACTIVE_DEPLOYMENTS" not in globals():
    ACTIVE_DEPLOYMENTS = {}  # deployment_id -> {thread, log_queue, stop_event, config, status, created_at}

###########################
# Helper Functions & Classes
###########################

def deployment_runner(deployment_id, config, log_queue, stop_event):
    """
    Runs in a separate thread and continuously executes the deployment job based on the scheduler configuration.
    Detailed logs are sent to both the log_queue and printed to the console.
    """
    def log(msg):
        timestamp = dt.now().strftime('%Y-%m-%d %H:%M:%S')
        full_msg = f"[{timestamp}] {msg}"
        log_queue.put(full_msg)
        print(full_msg)  # Detailed log in the console

    log(f"Deployment {deployment_id} started with config: {config}")

    # Define the job to run at scheduled times
    def scheduled_job():
        if stop_event.is_set():
            log("Stop event detected. Exiting scheduled job.")
            return

        log("=== Starting scheduled deployment cycle ===")
        try:
            # Step 1: Fill gap data
            market_params = config.get("market_params", {})
            log("Calling fill_gap...")
            # fill_gap signature: fill_gap(market_name, timeframe, complete_list=False, index_name='nse_eq_symbols', storage_system='finstore', pair='BTC')
            fill_gap(
                market_name=market_params.get("market_name"),
                timeframe=market_params.get("timeframe"),
                complete_list=False,
                pair=market_params.get("pair")
            )
            log("fill_gap completed.")

            # Step 2: Fetch OHLCV data
            log("Fetching OHLCV data via fetch_entries...")
            # fetch_entries signature:
            # fetch_entries(batch_inserter, market_name, timeframe, symbol_list, all_entries, start_timestamp, batch_size, storage_system, pair)
            # Here, we pass market_name, timeframe, symbol_list, and pair.
            ohlcv_data = fetch_entries(
                market_name=market_params.get("market_name"),
                timeframe=market_params.get("timeframe"),
                symbol_list=config.get("asset_universe"),
                all_entries=False,
                pair=market_params.get("pair")
            )
            log("OHLCV data fetched.")

            # Step 3: Generate signals using the strategy function
            strategy_func = config["strategy_func"]
            strategy_params = config["strategy_params"]
            asset_universe = config["asset_universe"]

            log("Generating signals using strategy...")
            # Note: Even if ohlcv_data contains data for more symbols, we pass the entire dict to the strategy,
            # and let the strategy function filter using the asset_universe.
            entries, exits, close_data, open_data = strategy_func(ohlcv_data, asset_universe, **strategy_params)
            log("Strategy signals generated.")

            # (Optional) Step 4: Validate signals with TradeMonitor (not implemented here)
            # For now, we assume signals (entries, exits) are ready for OMS order placement.

            # Step 5: Order placement via OMS
            oms = config["oms_instance"]
            log(f"Placing orders via OMS: {config['oms_type']}...")
            if config["oms_type"] == "Telegram":
                # For Telegram, we send a summary message.
                message = (f"Deployment {deployment_id} orders summary:\n"
                           f"Entries count: {entries.sum().sum()}\n"
                           f"Exits count: {exits.sum().sum()}")
                oms.send_telegram_message(message)
                print(message)
            elif config["oms_type"] == "Zerodha":
                # For Zerodha, assume we create a dummy orders DataFrame.
                orders_df = pd.DataFrame({
                    "symbol": list(asset_universe),
                    "Side": ["Buy"] * len(asset_universe),
                    "Size": [1] * len(asset_universe),
                    "Price": [0] * len(asset_universe)
                })
                oms.iterate_orders_df(orders_df)
            else:
                log("OMS type not recognized. Skipping order placement.")

            log("=== Deployment cycle completed ===")
        except Exception as e:
            log(f"Error during deployment cycle: {str(e)}")

    # Schedule the job based on the scheduler configuration
    scheduler_type = config.get("scheduler_type", "fixed_interval")  # or 'specific_time'
    if scheduler_type == "fixed_interval":
        interval = config.get("scheduler_interval", 60)  # in minutes
        log(f"Scheduling job every {interval} minutes.")
        schedule.every(interval).minutes.do(scheduled_job)
    elif scheduler_type == "specific_time":
        target_time = config.get("scheduler_time", "00:00")  # in HH:MM 24hr format
        log(f"Scheduling job every day at {target_time}.")
        schedule.every().day.at(target_time).do(scheduled_job)
    else:
        log("Unknown scheduler type. Exiting deployment runner.")
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

# Use a form to capture new deployment details.
st.header("New Deployment Configuration")
with st.form("deployment_form"):
    st.subheader("1. Strategy Module Selection")
    # For now, we include only the EMA strategy.
    strategy_option = st.selectbox("Select Strategy Module", options=["EMA Crossover Strategy"])
    st.markdown("**Strategy Parameters:**")
    fast_ema_period = st.number_input("Fast EMA Period", value=10, step=1)
    slow_ema_period = st.number_input("Slow EMA Period", value=100, step=1)

    st.subheader("2. Asset Universe Selection")
    # For simplicity, let the user input a comma-separated list of symbols.
    asset_input = st.text_input("Enter asset symbols (comma-separated)", value="BTC,ETH")
    asset_universe = [s.strip() for s in asset_input.split(",") if s.strip()]

    st.subheader("3. Market / Data Parameters")
    market_name = st.text_input("Market Name", value="crypto_binance")
    timeframe = st.selectbox("Timeframe", options=["15m", "1h", "4h"], index=0)
    pair = st.text_input("Pair (if applicable)", value="BTC")
    # Note: 'days_back' is removed because fill_gap does not require it.
    market_params = {
        "market_name": market_name,
        "timeframe": timeframe,
        "pair": pair
    }

    st.subheader("4. Broker / OMS Configuration")
    oms_type = st.selectbox("Select Broker / OMS", options=["Telegram", "Zerodha", "Binance"])
    telegram_token = ""
    telegram_group_id = ""
    user_id = ""
    password = ""
    totp_secret = ""
    if oms_type == "Telegram":
        # Token is optional; group id will be taken from env if not provided.
        telegram_token = st.text_input("Telegram Token (optional)", value="", type="password")
        telegram_group_id = st.text_input("Telegram Group ID (optional)", value="")
    elif oms_type == "Zerodha":
        user_id = st.text_input("User ID", value="")
        password = st.text_input("Password", value="", type="password")
        totp_secret = st.text_input("TOTP Secret", value="", type="password")
    # (For Binance, add similar inputs as needed.)

    st.subheader("5. Scheduler Configuration")
    scheduler_option = st.selectbox("Scheduler Type", options=["Fixed Interval", "Specific Time"])
    if scheduler_option == "Fixed Interval":
        scheduler_interval = st.number_input("Interval (minutes)", value=60, step=1)
    else:
        scheduler_time = st.text_input("Time (HH:MM in 24hr format)", value="23:00")

    submitted = st.form_submit_button("Deploy Strategy")

if submitted:
    # Prepare strategy configuration
    strategy_params = {
        "fast_ema_period": fast_ema_period,
        "slow_ema_period": slow_ema_period,
    }
    strategy_func = get_ema_signals_wrapper  # Only one strategy option for now

    # Initialize OMS based on selection
    if oms_type == "Telegram":
        # If group_id not provided, load from env JSON.
        if not telegram_group_id:
            load_dotenv(dotenv_path='config/.env')
            dict_string = os.getenv("TELEGRAM_BOT_CHANNELS")
            if dict_string:
                my_dict = json.loads(dict_string)
                telegram_group_id = my_dict.get("15m_altbtc_momentum", "")
        oms_instance = Telegram(token=telegram_token if telegram_token else None,
                                group_id=telegram_group_id if telegram_group_id else None)
    elif oms_type == "Zerodha":
        oms_instance = Zerodha(userid=user_id, password=password, totp=totp_secret)
    else:
        oms_instance = None  # Replace with Binance OMS initialization as needed

    # Prepare scheduler configuration
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

    # Save deployment info in the global ACTIVE_DEPLOYMENTS dictionary
    ACTIVE_DEPLOYMENTS[deployment_id] = {
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
if ACTIVE_DEPLOYMENTS:
    for dep_id, dep_info in ACTIVE_DEPLOYMENTS.items():
        st.subheader(f"Deployment ID: {dep_id}")
        st.markdown(f"**Created at:** {dep_info['created_at']}")
        config = dep_info["config"]
        scheduler_info = config.get("scheduler_interval", config.get("scheduler_time"))
        st.markdown(f"**Scheduler:** {scheduler_info}")
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
# Debugging / Instructions
###########################
st.markdown("---")
st.markdown("**Debugging Instructions:**")
st.markdown("- Detailed logs are printed to the console as well as shown above.")
st.markdown("- The deployment thread continues to run in the background until explicitly stopped.")
st.markdown("- These deployments persist in the global ACTIVE_DEPLOYMENTS dictionary for the lifetime of the server process.")
