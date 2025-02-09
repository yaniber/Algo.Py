import streamlit as st
import google.generativeai as genai
from OMS.binance_oms import Binance
import json
import re
import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Initialize Binance OMS
binance_oms = Binance()

# Configure Gemini
def initialize_gemini(api_key, model_name):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

# Enhanced system prompt
TRADING_SYSTEM_PROMPT = """
You are AlphaTrader, an advanced AI trading agent with direct access to Binance exchange. You have these capabilities:

1. Direct Function Access:
- get_account_balance()
- get_open_positions()
- calculate_risk_reward()
- fetch_market_data()
- execute_trade() [requires confirmation]
- run_technical_analysis()
- manage_orders()

2. Trading Skills:
- Auto-calculate position sizing based on risk %
- Implement complex order types (OCO, bracket)
- Technical analysis (ATR, RSI, etc.)
- Portfolio optimization
- Risk management enforcement

3. Communication Protocol:
- For informational requests, respond directly
- For trade executions, provide JSON blueprint
- For complex analysis, generate Python code
- Always verify orders with user
- Maintain conversation context

4. Safety Protocols:
- Never exceed 5% risk per trade
- Maximum leverage: 20x
- Minimum notional checks
- Always suggest stop loss

Current Market Conditions: {market_conditions}

User Portfolio Summary: {portfolio_summary}
"""

# Arbitrary code execution environment
class CodeExecutor:
    def __init__(self):
        self.available_modules = {
            'pd': pd,
            'yf': yf,
            'datetime': datetime,
            'timedelta': timedelta,
            'binance': binance_oms
        }
    
    def execute_safe(self, code, user_confirmation=False):
        if not user_confirmation:
            return "❌ Execution requires user confirmation"
        
        try:
            loc = {}
            exec(f"def __temp_func__():\n    {code}\n__temp_func__()", 
                 self.available_modules, loc)
            return loc.get('result', 'Code executed successfully')
        except Exception as e:
            return f"❌ Execution error: {str(e)}"

# Enhanced trading functions
def get_symbol_info(symbol):
    try:
        info = binance_oms.client.futures_exchange_info()
        for s in info['symbols']:
            if s['symbol'] == symbol:
                return {
                    'min_notional': float(s['filters'][3]['notional']),
                    'tick_size': float(s['filters'][0]['tickSize']),
                    'step_size': float(s['filters'][1]['stepSize'])
                }
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def adjust_quantity(symbol, amount):
    symbol_info = get_symbol_info(symbol)
    if not symbol_info:
        return amount
    
    mark_price = float(binance_oms.client.futures_mark_price(symbol=symbol)['markPrice'])
    min_notional = symbol_info['min_notional']
    
    calculated_qty = amount / mark_price
    notional_value = calculated_qty * mark_price
    
    if notional_value < min_notional:
        adjusted_qty = min_notional / mark_price
        return round(adjusted_qty, 8)
    
    return round(calculated_qty, 8)

# Streamlit UI
def main():
    st.set_page_config(page_title="AlphaTrader AI", layout="wide")
    executor = CodeExecutor()
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "🖖 I'm AlphaTrader, your AI trading partner. How can I assist today?"
        }]
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Configuration")
        api_key = st.text_input("Gemini API Key", type="password")
        model_name = st.selectbox(
            "Model Version",
            ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
        )
        
        st.header("📊 Live Data")
        if st.button("🔄 Refresh Account"):
            with st.spinner("Updating portfolio..."):
                balance = binance_oms.get_futures_balance()
                positions = binance_oms.view_open_futures_positions()
                st.session_state.balance = balance
                st.session_state.positions = positions
        
        if 'balance' in st.session_state:
            st.metric("Futures Balance", 
                     f"{st.session_state.balance['available']:,.2f} / {st.session_state.balance['total']:,.2f}")
        
        if 'positions' in st.session_state:
            st.dataframe(st.session_state.positions, use_container_width=True)

    # Chat interface
    st.title("🤖 AlphaTrader AI")
    
    # Display chat history
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
    
    # User input
    if prompt := st.chat_input("What's your trading plan?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        try:
            # Initialize AI model
            model = initialize_gemini(api_key, model_name)
            
            # Generate market context
            market_conditions = "Bullish"  # Replace with actual analysis
            portfolio_summary = binance_oms.get_futures_balance()
            
            # Generate response
            response = model.generate_content(
                TRADING_SYSTEM_PROMPT.format(
                    market_conditions=market_conditions,
                    portfolio_summary=json.dumps(portfolio_summary)
                ) + f"\n\nUser: {prompt}"
            )
            
            # Parse AI response
            response_text = response.text
            
            # Handle different response types
            if '```python' in response_text:
                # Code execution request
                code = re.search(r'```python(.*?)```', response_text, re.DOTALL).group(1)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Generated code:\n```python\n{code}\n```\nExecute this code?"
                })
                st.chat_message("assistant").code(code)
                
                if st.button("✅ Confirm Execution"):
                    result = executor.execute_safe(code, True)
                    st.session_state.messages.append({
                        "role": "system",
                        "content": f"Code execution result:\n{result}"
                    })
                    st.rerun()
            
            elif '{' in response_text and '}' in response_text:
                # Trading action request
                action = json.loads(re.search(r'\{.*?\}', response_text, re.DOTALL).group())
                
                # Handle notional requirements
                if action.get('action') == 'place_order':
                    symbol = action['symbol']
                    amount = action['quantity']
                    adjusted_qty = adjust_quantity(symbol, amount)
                    
                    if adjusted_qty != amount:
                        st.warning(f"Adjusted quantity to meet minimum notional: {adjusted_qty}")
                        action['quantity'] = adjusted_qty
                
                st.session_state.pending_action = action
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"⚠️ Confirm trade:\n```json\n{json.dumps(action, indent=2)}\n```"
                })
                st.chat_message("assistant").json(action)
                
                if st.button("✅ Confirm Trade"):
                    result = execute_trading_action(action)
                    st.session_state.messages.append({
                        "role": "system",
                        "content": f"Trade execution result:\n{result}"
                    })
                    st.rerun()
            
            else:
                # Natural language response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text
                })
                st.chat_message("assistant").write(response_text)
        
        except Exception as e:
            error_msg = f"❌ System Error: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.chat_message("assistant").write(error_msg)

    # System monitor
    with st.expander("🔍 System Monitor"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ Active Orders")
            if binance_oms.successful_orders:
                st.json(binance_oms.successful_orders[-3:])
            else:
                st.info("No recent orders")
        
        with col2:
            st.subheader("📈 Market Data")
            if 'pending_action' in st.session_state:
                symbol = st.session_state.pending_action.get('symbol', 'BTCUSDT')
                klines = binance_oms.client.futures_klines(
                    symbol=symbol, interval='1h', limit=24
                )
                df = pd.DataFrame(klines, columns=[
                    'time', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'trades',
                    'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])
                st.line_chart(df.set_index('time')['close'])

if __name__ == "__main__":
    main()
