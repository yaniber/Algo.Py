'''
Issues : 
[2025-02-11 21:59:57] OHLCV data fetched.
[2025-02-11 21:59:57] Generating signals using strategy...
[2025-02-11 21:59:57] Strategy signals generated.
[2025-02-11 21:59:57] Error during deployment cycle: 'oms_instance'
'''

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
from functools import partial

# ---------------------------
# Setup persistent storage paths
# ---------------------------
DEPLOYMENTS_FILE = "active_deployments.json"
LOG_DIR = "deploy_logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ---------------------------
# Enhanced Strategy Modules
# ---------------------------
STRATEGIES = {
    # Existing strategies
    "EMA Crossover Strategy": {
        "func": "strategy.public.ema_strategy.get_ema_signals_wrapper",
        "params": {}
    },
    # New strategies can be added here
}

def dynamic_strategy_loader():
    """Dynamically load strategies with parameter inspection"""
    strategies = {}
    try:
        from strategy.public.ema_strategy import get_ema_signals_wrapper
        strategies["EMA Crossover Strategy"] = {
            "func": get_ema_signals_wrapper,
            "params": get_strategy_params(get_ema_signals_wrapper)
        }
    except ImportError:
        st.error("Could not load EMA strategy module")
    
    # Add other strategies similarly
    return strategies

# ---------------------------
# Enhanced Parameter Handling
# ---------------------------
def get_strategy_params(func):
    """Improved parameter extraction with type handling"""
    sig = inspect.signature(func)
    params = {}
    for name, param in list(sig.parameters.items())[2:]:  # Skip ohlcv_data and symbol_list
        param_info = {
            "type": param.annotation,
            "default": param.default if param.default != inspect.Parameter.empty else None
        }
        
        # Set reasonable defaults for common parameter types
        if param_info["type"] == int:
            param_info["default"] = param_info["default"] or 20
            param_info["min"] = 1
            param_info["step"] = 1
        elif param_info["type"] == float:
            param_info["default"] = param_info["default"] or 0.0
            param_info["step"] = 0.001
        elif param_info["type"] == bool:
            param_info["default"] = param_info["default"] or False
            
        params[name] = param_info
    return params

# ---------------------------
# Enhanced Asset Selection
# ---------------------------
def asset_selection_widget(market_name, timeframe):
    """Dynamic asset selection based on market type"""
    st.subheader("Asset Universe Selection")
    
    if market_name == "crypto_binance":
        pair_type = st.radio("Pair Type:", ["USDT", "BTC"], horizontal=True)
        from data.fetch.crypto_binance import fetch_symbol_list_binance
        symbols = fetch_symbol_list_binance(suffix=pair_type)
    elif market_name == "indian_equity":
        from data.fetch.indian_equity import fetch_symbol_list_indian_equity
        symbols = fetch_symbol_list_indian_equity()
    else:
        symbols = []
    
    selected = st.multiselect(
        "Select assets:", 
        options=symbols,
        default=symbols[:5]  # Select first 5 by default
    )
    return pair_type, selected

# ---------------------------
# Enhanced Scheduler Configuration
# ---------------------------
def scheduler_config_widget():
    """Improved scheduler input with timezone support"""
    st.subheader("Scheduler Configuration")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        scheduler_type = st.selectbox(
            "Schedule Type", 
            options=["Fixed Interval", "Specific Time"]
        )
    
    with col2:
        if scheduler_type == "Fixed Interval":
            interval = st.number_input(
                "Interval (minutes)", 
                min_value=1, 
                value=60,
                help="How often to run the strategy"
            )
            return {"type": "fixed_interval", "value": interval}
        else:
            tz = st.selectbox(
                "Timezone",
                options=["UTC", "Asia/Kolkata", "America/New_York"],
                index=0
            )
            exec_time = st.time_input(
                "Execution Time", 
                value=datetime.time(9, 0),
                help="Local time for daily execution"
            )
            return {"type": "specific_time", "value": exec_time, "tz": tz}

# ---------------------------
# Enhanced OMS Configuration
# ---------------------------
def oms_config_widget(oms_type):
    """Modular OMS configuration with validation"""
    config = {}
    
    if oms_type == "Telegram":
        col1, col2 = st.columns(2)
        with col1:
            config['token'] = st.text_input(
                "Bot Token", 
                help="Get from @BotFather",
                type="password"
            )
        with col2:
            config['chat_id'] = st.text_input(
                "Chat ID",
                help="Use @getidsbot to find"
            )
            
    elif oms_type == "Zerodha":
        config['userid'] = st.text_input("User ID")
        config['password'] = st.text_input("Password", type="password")
        config['totp'] = st.text_input("TOTP Secret", type="password")
        
    elif oms_type == "Binance":
        config['api_key'] = st.text_input("API Key", type="password")
        config['api_secret'] = st.text_input("API Secret", type="password")
        
    return config


def serialize_deployment_config(config):
    serializable = config.copy()
    # Remove non-serializable entries
    if "strategy_func" in serializable:
        # Safely get strategy name
        matching_names = [
            name for name, func in STRATEGIES.items() 
            if func == serializable["strategy_func"]
        ]
        if not serializable['strategy_name']:
            serializable["strategy_name"] = matching_names[0] if matching_names else "Unknown Strategy"
        del serializable["strategy_func"]
    if "oms_instance" in serializable:
        del serializable["oms_instance"]
    return serializable

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
            #fill_gap(
            #    market_name=market_params.get("market_name"),
            #    timeframe=market_params.get("timeframe"),
            #    complete_list=False,
            #    pair=market_params.get("pair")
            #)
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
        scheduled_job()
        schedule.every(interval).minutes.do(scheduled_job)
    elif scheduler_type == "specific_time":
        target_time = config.get("scheduler_interval", "00:00")
        append_log(deployment_id, f"Scheduling job every day at {target_time}.")
        schedule.every().day.at(target_time).do(scheduled_job)
    else:
        append_log(deployment_id, "Unknown scheduler type. Exiting deployment runner process.")
        return

    while True:
        schedule.run_pending()
        time.sleep(1)

# ---------------------------
# Deployment Process Manager
# ---------------------------
class DeploymentManager:
    def __init__(self):
        self.deployments = load_active_deployments()
        self._cleanup_zombies()
        self._update_statuses()
        
    def start_deployment(self, config):
        import uuid
        deployment_id = str(uuid.uuid4())[:8]
        # Start deployment process (assume deployment_runner_process is defined elsewhere)
        import multiprocessing
        process = multiprocessing.Process(
            target=deployment_runner_process,
            args=(deployment_id, config)
        )
        process.start()
        
        # Store only serializable metadata (do not store live objects)
        serializable_config = serialize_deployment_config(config)
        self.deployments[deployment_id] = {
            "pid": process.pid,
            "config": serializable_config,
            "status": "running",
            "created": dt.now().isoformat()
        }
        save_active_deployments(self.deployments)
        return deployment_id
    
    def stop_deployment(self, deployment_id):
        try:
            pid = self.deployments[deployment_id]["pid"]
            append_log(deployment_id, f"Sending SIGTERM to process {pid}")
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                append_log(deployment_id, f"Process {pid} not found; already terminated.")
                self.deployments.pop(deployment_id)
                save_active_deployments(self.deployments)
                return True

            time.sleep(5)  # Wait for graceful shutdown

            # Try to reap the process if it's in zombie state
            try:
                waited_pid, status = os.waitpid(pid, os.WNOHANG)
                if waited_pid == 0:
                    append_log(deployment_id, f"Process {pid} still running; sending SIGKILL.")
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(2)
                    try:
                        waited_pid, status = os.waitpid(pid, os.WNOHANG)
                        if waited_pid != 0:
                            append_log(deployment_id, f"Process {pid} reaped with status {status} after SIGKILL.")
                        else:
                            append_log(deployment_id, f"Process {pid} still not reaped after SIGKILL.")
                    except Exception as ex:
                        append_log(deployment_id, f"Error waiting for process {pid} after SIGKILL: {ex}")
                else:
                    append_log(deployment_id, f"Process {pid} successfully reaped with status {status}.")
            except ChildProcessError:
                append_log(deployment_id, f"No child process exists for pid {pid}.")
            except Exception as ex:
                append_log(deployment_id, f"Error during waitpid: {ex}")

            self._cleanup_zombies()
            return True
        except Exception as e:
            append_log(deployment_id, f"Error in stop_deployment: {str(e)}")
            return False

    def _cleanup_zombies(self):
        """Remove terminated processes from deployment tracking."""
        for dep_id in list(self.deployments.keys()):
            pid = self.deployments[dep_id]["pid"]
            try:
                # os.waitpid with WNOHANG returns (0, 0) if the child hasn't been reaped,
                # otherwise, it returns (pid, status) and the child is reaped.
                waited_pid, status = os.waitpid(pid, os.WNOHANG)
                if waited_pid != 0:
                    append_log(dep_id, f"Process {pid} reaped during cleanup with status {status}.")
                    del self.deployments[dep_id]
            except ChildProcessError:
                append_log(dep_id, f"No child process exists for pid {pid} during cleanup.")
                del self.deployments[dep_id]
            except OSError:
                append_log(dep_id, f"Process {pid} no longer exists during cleanup.")
                del self.deployments[dep_id]
        save_active_deployments(self.deployments)
    
    def _update_statuses(self):
        """Check process statuses and update deployment status."""
        for dep_id, dep in list(self.deployments.items()):
            pid = dep["pid"]
            try:
                os.kill(pid, 0)  # Check if process exists
                dep["status"] = "running"
            except (OSError, ProcessLookupError):
                dep["status"] = "stopped"
        save_active_deployments(self.deployments)


# ---------------------------
# Enhanced UI Components
# ---------------------------
def deployment_status_badge(status):
    color = {
        "running": "green",
        "stopped": "red",
        "error": "orange"
    }.get(status, "gray")
    return f"<span style='color:{color};'>●</span> {status.capitalize()}"

def format_log_entry(log_line):
    if "ERROR" in log_line:
        return f"<div style='color: red;'>{log_line}</div>"
    elif "WARNING" in log_line:
        return f"<div style='color: orange;'>{log_line}</div>"
    return log_line

# ---------------------------
# Main Dashboard UI
# ---------------------------
def main():
    st.title("🚀 Strategy Deployment Dashboard")
    manager = DeploymentManager()
    
    # New Deployment Form
    with st.expander("New Deployment Configuration", expanded=True):
        strategies = dynamic_strategy_loader()
        selected_strategy = st.selectbox("Strategy", options=list(strategies.keys()))
        
        if selected_strategy:
            strategy_config = strategies[selected_strategy]
            params = strategy_config["params"]
            
            # Dynamic parameter inputs
            st.subheader("Strategy Parameters")
            param_values = {}
            for param, info in params.items():
                if info["type"] == int:
                    param_values[param] = st.number_input(
                        param.replace("_", " ").title(),
                        value=info["default"],
                        min_value=info.get("min", 0),
                        step=info.get("step", 1)
                    )
                elif info["type"] == float:
                    param_values[param] = st.number_input(
                        param.replace("_", " ").title(),
                        value=info["default"],
                        step=info.get("step", 0.001)
                    )
                elif info["type"] == bool:
                    param_values[param] = st.checkbox(
                        param.replace("_", " ").title(),
                        value=info["default"]
                    )
                else:
                    param_values[param] = st.text_input(
                        param.replace("_", " ").title(),
                        value=info["default"]
                    )
            
            # Market Configuration
            st.subheader("Market Configuration")
            market_name = st.selectbox(
                "Market", 
                options=["crypto_binance", "indian_equity"]
            )
            timeframe = st.selectbox(
                "Timeframe", 
                options=["15m", "1h", "4h", "1d"]
            )
            
            # Asset Selection
            pair , asset_universe = asset_selection_widget(market_name, timeframe)
            
            # OMS Configuration
            st.subheader("Order Management")
            oms_type = st.selectbox(
                "OMS Type", 
                options=["Telegram", "Zerodha", "Binance"]
            )
            oms_config = oms_config_widget(oms_type)
            telegram_group_id = oms_config['chat_id']
            if oms_type == "Telegram":
                if not telegram_group_id:
                    load_dotenv(dotenv_path='config/.env')
                    dict_string = os.getenv("TELEGRAM_BOT_CHANNELS")
                    if dict_string:
                        my_dict = json.loads(dict_string)
                        telegram_group_id = my_dict.get("15m_altbtc_momentum", "")
                from OMS.telegram import Telegram
                oms_instance = Telegram(group_id=telegram_group_id if telegram_group_id else None)
            
            # Scheduler Configuration
            scheduler = scheduler_config_widget()
            
            if st.button("Deploy Strategy"):
                if not asset_universe:
                    st.error("Please select at least one asset")
                    return
                
                try:
                    config = {
                        "strategy": selected_strategy,
                        "strategy_name" : 'EMA Crossover Strategy',
                        "strategy_func" : strategy_config['func'],
                        "oms_instance": oms_instance,
                        "oms_type" : oms_type,
                        "strategy_params" : param_values,
                        "params": param_values,
                        "market": {
                            "name": market_name,
                            "timeframe": timeframe
                        },
                        "assets": asset_universe,
                        "asset_universe": asset_universe,
                        "oms": {
                            "type": oms_type,
                            "config": oms_config
                        },
                        "scheduler": scheduler,
                        "scheduler_type" : scheduler['type'],
                        "scheduler_interval" : scheduler['value'],
                        "market_params" : {
                            "market_name" : market_name,
                            "timeframe" : timeframe,
                            "pair" : pair,
                            "asset_universe" : asset_universe 
                        }
                    }
                    
                    deployment_id = manager.start_deployment(config)
                    st.success(f"Deployment {deployment_id} started successfully!")
                
                except Exception as e:
                    st.error(f"Deployment failed: {str(e)}")

    # Active Deployments
    st.header("Active Deployments")
    
    if not manager.deployments:
        st.info("No active deployments")
        return
    
    # In the Active Deployments section
    for dep_id, dep in list(manager.deployments.items()):
        with st.container():
            cols = st.columns([1, 2, 1, 1])
            with cols[0]:
                st.markdown(f"**{dep_id}**")
                status = dep.get("status", "unknown")
                color = {"running": "🟢", "stopped": "🔴", "error": "🟠"}.get(status, "⚪")
                st.markdown(f"{color} **{status.title()}**")
            
            with cols[1]:
                st.caption(f"Strategy: {dep['config'].get('strategy_name', 'Unknown')}")
                st.caption(f"Market: {dep['config']['market_params']['market_name']}")
            
            with cols[2]:
                if st.button("📋 Logs", key=f"logs_{dep_id}"):
                    st.session_state[f"show_logs_{dep_id}"] = not st.session_state.get(f"show_logs_{dep_id}", False)
            
            with cols[3]:
                if st.button("⏹ Stop", key=f"stop_{dep_id}"):
                    manager.stop_deployment(dep_id)
            
            if st.session_state.get(f"show_logs_{dep_id}"):
                log_content = read_log(dep_id)
                st.download_button(
                    label="Download Full Log",
                    data=log_content,
                    file_name=f"{dep_id}_logs.txt"
                )
                st.code("\n".join(log_content.split("\n")[-50:]))  # Show last 50 lines
    
    # After Active Deployments header
    if st.button("🧹 Clear Stopped Deployments"):
        manager._cleanup_zombies()
        st.rerun()

if __name__ == "__main__":
    main()