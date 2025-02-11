import streamlit as st
import multiprocessing
import time
import schedule
import uuid
import inspect
import datetime
from datetime import datetime as dt, date
import pandas as pd
import os
import json
import signal
from dotenv import load_dotenv

# ---------------------------
# Setup persistent storage paths
# ---------------------------
DEPLOYMENTS_FILE = "active_deployments.json"
LOG_DIR = "deploy_logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ---------------------------
# Utility functions for persistence
# ---------------------------
def load_active_deployments():
    if os.path.exists(DEPLOYMENTS_FILE):
        with open(DEPLOYMENTS_FILE, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_active_deployments(deployments):
    with open(DEPLOYMENTS_FILE, "w") as f:
        json.dump(deployments, f, indent=4)

def append_log(deployment_id, msg):
    timestamp = dt.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {msg}\n"
    log_file = os.path.join(LOG_DIR, f"deployment_{deployment_id}.log")
    with open(log_file, "a") as f:
        f.write(log_line)
    print(log_line, end="")  # Also print to console

def read_log(deployment_id):
    log_file = os.path.join(LOG_DIR, f"deployment_{deployment_id}.log")
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            return f.read()
    return "No logs available."

# ---------------------------
# Available strategies dictionary
# ---------------------------
from strategy.public.ema_strategy import get_ema_signals_wrapper
STRATEGIES = {
    "EMA Crossover Strategy": get_ema_signals_wrapper
}

def get_strategy_params(func):
    """
    Returns a dictionary of parameter names and default values
    for the given strategy function, ignoring the first two parameters.
    """
    sig = inspect.signature(func)
    params = {}
    # Skip the first two parameters (ohlcv_data and symbol_list)
    for name, param in list(sig.parameters.items())[2:]:
        if param.default is not inspect.Parameter.empty:
            params[name] = param.default
        else:
            params[name] = 10 if param.annotation == int else 0.0 if param.annotation == float else ""
    return params

# ---------------------------
# Helper: Serialize deployment config for persistence
# Remove non-serializable keys.
# ---------------------------
def serialize_deployment_config(config):
    serializable = config.copy()
    # Remove non-serializable entries
    if "strategy_func" in serializable:
        # Save the name instead
        serializable["strategy_name"] = [name for name, func in STRATEGIES.items() if func == serializable["strategy_func"]][0]
        del serializable["strategy_func"]
    if "oms_instance" in serializable:
        # We only persist the OMS type and leave the instance out.
        del serializable["oms_instance"]
    return serializable

# ---------------------------
# Deployment runner function for the process
# ---------------------------
def deployment_runner_process(deployment_id, config):
    """
    This function runs in a separate process. It writes logs to a file.
    It uses schedule to run the deployment cycle periodically.
    """
    append_log(deployment_id, f"Deployment {deployment_id} started with config: {config}")

    def scheduled_job():
        append_log(deployment_id, "=== Starting scheduled deployment cycle ===")
        try:
            # Step 1: Fill gap data
            market_params = config.get("market_params", {})
            append_log(deployment_id, "Calling fill_gap...")
            from data.update.crypto_binance import fill_gap  # local import
            fill_gap(
                market_name=market_params.get("market_name"),
                timeframe=market_params.get("timeframe"),
                complete_list=False,
                pair=market_params.get("pair")
            )
            append_log(deployment_id, "fill_gap completed.")

            # Step 2: Fetch OHLCV data
            append_log(deployment_id, "Fetching OHLCV data via fetch_entries...")
            from utils.db.fetch import fetch_entries  # local import
            ohlcv_data = fetch_entries(
                market_name=market_params.get("market_name"),
                timeframe=market_params.get("timeframe"),
                symbol_list=config.get("asset_universe"),
                all_entries=False,
                pair=market_params.get("pair")
            )
            append_log(deployment_id, "OHLCV data fetched.")

            # Step 3: Generate signals using the strategy
            strategy_func = config["strategy_func"]
            strategy_params = config["strategy_params"]
            asset_universe = config["asset_universe"]

            append_log(deployment_id, "Generating signals using strategy...")
            entries, exits, close_data, open_data = strategy_func(ohlcv_data, asset_universe, **strategy_params)
            append_log(deployment_id, "Strategy signals generated.")

            # Step 4: Order placement via OMS
            oms = config["oms_instance"]
            append_log(deployment_id, f"Placing orders via OMS: {config['oms_type']}...")
            if config["oms_type"] == "Telegram":
                message = (f"Deployment {deployment_id} orders summary:\n"
                           f"Entries count: {entries.sum().sum()}\n"
                           f"Exits count: {exits.sum().sum()}")
                oms.send_telegram_message(message)
                append_log(deployment_id, f"Telegram message sent: {message}")
            elif config["oms_type"] == "Zerodha":
                orders_df = pd.DataFrame({
                    "symbol": list(asset_universe),
                    "Side": ["Buy"] * len(asset_universe),
                    "Size": [1] * len(asset_universe),
                    "Price": [0] * len(asset_universe)
                })
                oms.iterate_orders_df(orders_df)
                append_log(deployment_id, "Zerodha orders processed.")
            else:
                append_log(deployment_id, "OMS type not recognized. Skipping order placement.")

            append_log(deployment_id, "=== Deployment cycle completed ===")
        except Exception as e:
            append_log(deployment_id, f"Error during deployment cycle: {str(e)}")

    # Setup scheduling based on configuration
    scheduler_type = config.get("scheduler_type", "fixed_interval")
    if scheduler_type == "fixed_interval":
        interval = config.get("scheduler_interval", 60)
        append_log(deployment_id, f"Scheduling job every {interval} minutes.")
        schedule.every(interval).minutes.do(scheduled_job)
    elif scheduler_type == "specific_time":
        target_time = config.get("scheduler_time", "00:00")
        append_log(deployment_id, f"Scheduling job every day at {target_time}.")
        schedule.every().day.at(target_time).do(scheduled_job)
    else:
        append_log(deployment_id, "Unknown scheduler type. Exiting deployment runner process.")
        return

    while True:
        schedule.run_pending()
        time.sleep(1)

# ---------------------------
# Dashboard UI Components
# ---------------------------
st.title("📡 Strategy Deployment Dashboard")

# Load active deployments from file
active_deployments = load_active_deployments()

# ---------------------------
# New Deployment Configuration Form
# ---------------------------
st.header("New Deployment Configuration")
with st.form("deployment_form"):
    st.subheader("1. Strategy Module Selection")
    strategy_option = st.selectbox("Select Strategy Module", options=list(STRATEGIES.keys()))
    strategy_func = STRATEGIES[strategy_option]
    default_params = get_strategy_params(strategy_func)
    st.markdown("**Strategy Parameters:**")
    user_params = {}
    for param, default in default_params.items():
        if isinstance(default, int):
            user_params[param] = st.number_input(param, value=default, step=1)
        elif isinstance(default, float):
            user_params[param] = st.number_input(param, value=default, step=0.000001)
        else:
            user_params[param] = st.text_input(param, value=str(default))
    
    st.subheader("2. Asset Universe Selection")
    asset_input = st.text_input("Enter asset symbols (comma-separated)", value="BTC,ETH")
    asset_universe = [s.strip() for s in asset_input.split(",") if s.strip()]

    st.subheader("3. Market / Data Parameters")
    market_name = st.text_input("Market Name", value="crypto_binance")
    timeframe = st.selectbox("Timeframe", options=["15m", "1h", "4h"], index=0)
    pair = st.text_input("Pair (if applicable)", value="BTC")
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
        telegram_token = st.text_input("Telegram Token (optional)", value="", type="password")
        telegram_group_id = st.text_input("Telegram Group ID (optional)", value="")
    elif oms_type == "Zerodha":
        user_id = st.text_input("User ID", value="")
        password = st.text_input("Password", value="", type="password")
        totp_secret = st.text_input("TOTP Secret", value="", type="password")
    # (For Binance OMS, add inputs as needed.)

    st.subheader("5. Scheduler Configuration")
    scheduler_option = st.selectbox("Scheduler Type", options=["Fixed Interval", "Specific Time"])
    if scheduler_option == "Fixed Interval":
        scheduler_interval = st.number_input("Interval (minutes)", value=60, step=1)
        scheduler_type = "fixed_interval"
        scheduler_value = scheduler_interval
    else:
        scheduler_time = st.text_input("Time (HH:MM in 24hr format)", value="23:00")
        scheduler_type = "specific_time"
        scheduler_value = scheduler_time

    submitted = st.form_submit_button("Deploy Strategy")

if submitted:
    strategy_params = user_params
    # Initialize OMS based on selection
    if oms_type == "Telegram":
        if not telegram_group_id:
            load_dotenv(dotenv_path='config/.env')
            dict_string = os.getenv("TELEGRAM_BOT_CHANNELS")
            if dict_string:
                my_dict = json.loads(dict_string)
                telegram_group_id = my_dict.get("15m_altbtc_momentum", "")
        from OMS.telegram import Telegram
        oms_instance = Telegram(token=telegram_token if telegram_token else None,
                                group_id=telegram_group_id if telegram_group_id else None)
    elif oms_type == "Zerodha":
        from OMS.zerodha import Zerodha
        oms_instance = Zerodha(userid=user_id, password=password, totp=totp_secret)
    else:
        oms_instance = None  # For Binance, add initialization

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

    deployment_id = str(uuid.uuid4())[:8]
    process = multiprocessing.Process(target=deployment_runner_process, args=(deployment_id, deployment_config))
    process.start()

    # Save only serializable parts of deployment_config
    serializable_config = serialize_deployment_config(deployment_config)
    active_deployments[deployment_id] = {
        "pid": process.pid,
        "config": serializable_config,
        "status": "Running",
        "created_at": dt.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_active_deployments(active_deployments)
    st.success(f"Deployment {deployment_id} started successfully with PID {process.pid}.")

# ---------------------------
# Active Deployments Status
# ---------------------------
st.header("Active Deployments")
active_deployments = load_active_deployments()

if active_deployments:
    for dep_id, dep_info in list(active_deployments.items()):
        st.subheader(f"Deployment ID: {dep_id}")
        st.markdown(f"**Created at:** {dep_info.get('created_at')}")
        config = dep_info.get("config", {})
        scheduler_info = config.get("scheduler_interval", config.get("scheduler_time"))
        st.markdown(f"**Scheduler:** {scheduler_info}")
        st.markdown(f"**OMS:** {config.get('oms_type')}")
        st.markdown(f"**Process PID:** {dep_info.get('pid')}")
        log_content = read_log(dep_id)
        st.text_area("Deployment Logs", value=log_content, height=150)
        if st.button(f"Stop Deployment {dep_id}"):
            pid = dep_info.get("pid")
            try:
                os.kill(pid, signal.SIGTERM)
                st.success(f"Deployment {dep_id} stopped.")
                active_deployments.pop(dep_id)
                save_active_deployments(active_deployments)
            except Exception as e:
                st.error(f"Error stopping deployment {dep_id}: {e}")
else:
    st.info("No active deployments.")

# ---------------------------
# Debugging / Instructions
# ---------------------------
st.markdown("---")
st.markdown("**Debugging Instructions:**")
st.markdown("- Deployment processes write logs to files under the 'deploy_logs' directory.")
st.markdown("- Active deployments are stored persistently in 'active_deployments.json'.")
st.markdown("- Use the stop button to send a termination signal to the deployment process.")
st.markdown("- Logs are displayed below each deployment and printed to the console.")
