import streamlit as st
import pandas as pd
import importlib
import inspect
import datetime
import json
import uuid
import pytz
import os
from pathlib import Path
from croniter import croniter
import threading

# Persistence setup
PERSISTENCE_FILE = Path("deployments.json")
IST = pytz.timezone('Asia/Kolkata')

def load_deployments():
    if PERSISTENCE_FILE.exists():
        with open(PERSISTENCE_FILE) as f:
            return json.load(f)
    return []

def save_deployments(deployments):
    with open(PERSISTENCE_FILE, 'w') as f:
        json.dump(deployments, f, default=str)

# Initialize session state
if 'deployments' not in st.session_state:
    st.session_state.deployments = load_deployments()

def get_schedule_options(strategy_type):
    """Return schedule config options based on strategy type"""
    options = {
        'indian_equity': {
            'data_fetch': {'type': 'fixed', 'default': '18:00'},
            'pipeline': {'type': 'fixed', 'default': '19:00'},
            'execution': {'type': 'fixed', 'default': '09:15'},
            'retry': {'type': 'fixed', 'default': '12:00'},
            'balance': {'type': 'fixed', 'default': '17:00'}
        },
        'crypto_momentum': {
            '4h_bot': {'type': 'cron', 'default': '0 23 * * *'},  # Daily at 23:00 IST (17:30 UTC)
            '15m_bot': {'type': 'interval', 'default': 120},  # Minutes
            '5m_bot': {'type': 'interval', 'default': 40}     # Minutes
        }
    }
    return options.get(strategy_type, {})

def calculate_next_run(schedule_config):
    now = datetime.datetime.now(IST)
    
    if schedule_config['type'] == 'fixed':
        scheduled_time = datetime.datetime.strptime(schedule_config['value'], '%H:%M').time()
        next_run = datetime.datetime.combine(now.date(), scheduled_time)
        if next_run < now:
            next_run += datetime.timedelta(days=1)
        return next_run.astimezone(IST)
    
    elif schedule_config['type'] == 'interval':
        return now + datetime.timedelta(minutes=schedule_config['value'])
    
    elif schedule_config['type'] == 'cron':
        base = now - datetime.timedelta(seconds=1)
        iter = croniter(schedule_config['value'], base)
        return iter.get_next(datetime.datetime).astimezone(IST)
    
    return now

def strategy_params_input(strategy_func):
    """Generate dynamic inputs for strategy parameters"""
    params = {}
    sig = inspect.signature(strategy_func)
    
    # Skip system parameters
    system_params = ['ohlcv_data', 'sim_start', 'sim_end', 'complete_list', 
                    'symbol_list', 'weekday', 'init_cash']
    
    for param in sig.parameters.values():
        if param.name in system_params:
            continue
            
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
                step=0.01
            )
        elif param.annotation == bool:
            val = st.checkbox(
                param.name,
                value=param.default if param.default != inspect.Parameter.empty else False
            )
        else:
            val = st.text_input(
                param.name,
                value=str(param.default) if param.default != inspect.Parameter.empty else ""
            )
        
        params[param.name] = val
    
    return params

def deployment_form():
    """Form for creating new deployments"""
    with st.form("new_deployment"):
        st.subheader("🚀 New Strategy Deployment")
        
        # Strategy selection
        strategy_type = st.selectbox(
            "Strategy Type",
            options=['indian_equity', 'crypto_momentum'],
            format_func=lambda x: "Indian Equity" if x == 'indian_equity' else "Crypto Momentum"
        )
        
        # Strategy module selection
        strategy_module = st.text_input(
            "Strategy Module Path",
            value="executor.indian_equity_pipeline.run_pipeline" if strategy_type == 'indian_equity' 
                  else "scheduler.binance_bots._4h_momentum_bot"
        )
        
        # Schedule configuration
        schedule_options = get_schedule_options(strategy_type)
        schedule_configs = {}
        
        st.subheader("Schedule Configuration")
        for task, config in schedule_options.items():
            col1, col2 = st.columns(2)
            with col1:
                schedule_type = st.selectbox(
                    f"{task} Schedule Type",
                    options=['fixed', 'interval', 'cron'],
                    index=['fixed', 'interval', 'cron'].index(config['type']),
                    key=f"{task}_type"
                )
            with col2:
                if schedule_type == 'fixed':
                    value = st.text_input(
                        f"{task} Time (HH:MM)",
                        value=config['default'],
                        key=f"{task}_fixed"
                    )
                elif schedule_type == 'interval':
                    value = st.number_input(
                        f"{task} Interval (minutes)",
                        value=config['default'],
                        key=f"{task}_interval"
                    )
                else:
                    value = st.text_input(
                        f"{task} Cron Expression",
                        value=config['default'],
                        key=f"{task}_cron"
                    )
            
            schedule_configs[task] = {'type': schedule_type, 'value': value}
        
        # Deploy button
        if st.form_submit_button("Deploy Strategy"):
            try:
                module_path, func_name = strategy_module.rsplit('.', 1)
                module = importlib.import_module(module_path)
                strategy_func = getattr(module, func_name)
                
                new_deployment = {
                    'id': str(uuid.uuid4()),
                    'strategy_type': strategy_type,
                    'strategy_module': strategy_module,
                    'schedule_configs': schedule_configs,
                    'next_runs': {task: calculate_next_run(config) 
                                 for task, config in schedule_configs.items()},
                    'status': 'active',
                    'logs': [],
                    'created_at': datetime.datetime.now(IST).isoformat()
                }
                
                st.session_state.deployments.append(new_deployment)
                save_deployments(st.session_state.deployments)
                st.success("Strategy deployed successfully!")
            
            except Exception as e:
                st.error(f"Error deploying strategy: {str(e)}")

def update_deployment_status():
    """Update next run times and execute scheduled jobs"""
    now = datetime.datetime.now(IST)
    
    for deployment in st.session_state.deployments:
        if deployment['status'] != 'active':
            continue
        
        for task, config in deployment['schedule_configs'].items():
            if pd.to_datetime(deployment['next_runs'][task]) < now:
                try:
                    # Execute the task
                    module_path, func_name = deployment['strategy_module'].rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    func = getattr(module, func_name)
                    
                    # Run in background thread
                    thread = threading.Thread(target=func)
                    thread.start()
                    
                    # Update logs
                    log_msg = f"{now} - {task} executed successfully"
                    deployment['logs'].append(log_msg)
                    
                except Exception as e:
                    error_msg = f"{now} - {task} failed: {str(e)}"
                    deployment['logs'].append(error_msg)
                
                # Update next run time
                deployment['next_runs'][task] = calculate_next_run(config).isoformat()
        
    save_deployments(st.session_state.deployments)

def deployment_card(deployment):
    """Display individual deployment card with controls"""
    with st.expander(f"📈 {deployment['strategy_module']} - {deployment['id'][:8]}"):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
                **Type:** {deployment['strategy_type'].replace('_', ' ').title()}  
                **Status:** {deployment['status'].capitalize()}  
                **Created:** {pd.to_datetime(deployment['created_at']).strftime('%d %b %Y %H:%M')}
            """)
            
            st.markdown("**Next Scheduled Runs:**")
            for task, next_run in deployment['next_runs'].items():
                st.write(f"{task}: {pd.to_datetime(next_run).strftime('%d %b %Y %H:%M %Z')}")

        with col2:
            if st.button("⏹️ Stop", key=f"stop_{deployment['id']}"):
                deployment['status'] = 'stopped'
                save_deployments(st.session_state.deployments)
            
            if st.button("🗑️ Remove", key=f"remove_{deployment['id']}"):
                st.session_state.deployments.remove(deployment)
                save_deployments(st.session_state.deployments)
                st.rerun()

        # Manual execution controls
        st.markdown("---")
        st.subheader("Manual Execution")
        cols = st.columns(len(deployment['schedule_configs']))
        for idx, task in enumerate(deployment['schedule_configs']):
            with cols[idx]:
                if st.button(f"Run {task}", key=f"manual_{deployment['id']}_{task}"):
                    try:
                        module_path, func_name = deployment['strategy_module'].rsplit('.', 1)
                        module = importlib.import_module(module_path)
                        func = getattr(module, func_name)
                        thread = threading.Thread(target=func)
                        thread.start()
                        deployment['logs'].append(f"{datetime.datetime.now(IST)} - Manual {task} executed")
                    except Exception as e:
                        deployment['logs'].append(f"{datetime.datetime.now(IST)} - Manual {task} failed: {str(e)}")

        # Logs display
        st.markdown("**Recent Logs:**")
        for log in reversed(deployment['logs'][-5:]):
            st.code(log)

def dashboard():
    """Main dashboard view"""
    st.title("Strategy Deployment Monitor")
    
    # Auto-update status every 60 seconds
    update_deployment_status()
    
    if not st.session_state.deployments:
        st.info("No active deployments. Create one using the form below.")
        return
    
    for deployment in st.session_state.deployments:
        deployment_card(deployment)

# Main app layout
st.set_page_config(page_title="Trading Strategy Deployer", layout="wide")

tab1, tab2 = st.tabs(["Dashboard", "New Deployment"])

with tab1:
    dashboard()

with tab2:
    deployment_form()