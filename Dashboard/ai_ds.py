import streamlit as st
import google.generativeai as genai
from OMS.binance_oms import Binance
import json
import re
import os

# Initialize Binance OMS
binance_oms = Binance()

# Configure Gemini
def initialize_gemini(api_key, model_name):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

# System prompt for Gemini
TRADING_SYSTEM_PROMPT = """
You are a professional trading AI assistant for Binance exchange. Your capabilities include:

1. Order Management:
- Place market/limit orders (spot and futures)
- Close positions
- Set leverage
- Manage take-profit/stop-loss
- Handle bracket orders

2. Market Analysis:
- Calculate risk-reward ratios
- Suggest entry/exit points
- Analyze market conditions
- Identify trading opportunities

3. Position Management:
- View open positions
- Monitor account balance
- Adjust position sizing
- Hedge existing positions

For trading actions, ALWAYS respond with JSON using these exact structures:

Market Order:
{
  "action": "place_order",
  "symbol": "BTCUSDT",
  "side": "BUY/SELL",
  "quantity": 0.1,
  "order_type": "MARKET",
  "market_type": "spot/futures",
  "leverage": 20 (optional for futures),
  "quantity_type": "USD/CONTRACTS" (for futures)
}

Limit Order:
{
  "action": "place_order",
  "symbol": "ETHUSDT",
  "side": "BUY/SELL",
  "quantity": 0.5,
  "order_type": "LIMIT",
  "price": 2500.50,
  "market_type": "spot/futures",
  "leverage": 25 (optional),
  "time_in_force": "GTC/IOC"
}

Close Position:
{
  "action": "close_position",
  "symbol": "BTCUSDT",
  "percentage": 100,
  "market_type": "futures",
  "use_chaser": true/false
}

Set Leverage:
{
  "action": "set_leverage",
  "symbol": "ETHUSDT",
  "leverage": 30
}

Risk-Reward Setup:
{
  "action": "risk_reward_setup",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "risk_percent": 2,
  "reward_ratio": 2,
  "market_type": "futures",
  "leverage": 20
}

For non-trading requests (analysis, explanations), respond in clear natural language with markdown formatting when appropriate.

Safety First:
- Never suggest leverage > 50x
- Always recommend stop-loss
- Verify notional values meet Binance requirements
- Double-check order parameters before execution
"""

# Parse AI response and execute actions
def execute_trading_action(response_text):
    try:
        # Clean JSON response
        json_str = re.search(r'\{.*?\}', response_text, re.DOTALL).group()
        action = json.loads(json_str)
        
        if action['action'] == 'place_order':
            # Futures order
            if action.get('market_type') == 'futures':
                result = binance_oms.place_futures_order(
                    symbol=action['symbol'],
                    side=action['side'],
                    quantity=action['quantity'],
                    price=action.get('price'),
                    order_type=action['order_type'],
                    quantity_type=action.get('quantity_type', 'CONTRACTS')
                )
                if action.get('leverage'):
                    binance_oms.change_leverage(action['symbol'], action['leverage'])
            
            # Spot order
            else:
                result = binance_oms.place_order(
                    symbol=action['symbol'],
                    side=action['side'],
                    size=action['quantity'],
                    price=action.get('price'),
                    order_type=action['order_type']
                )
            
            return f"✅ Order executed: {result}" if result else "❌ Order failed"

        elif action['action'] == 'close_position':
            result = binance_oms.close_futures_positions(
                symbol=action['symbol'],
                percentage=action['percentage'],
                use_chaser=action.get('use_chaser', False)
            )
            return f"🚪 Position closed: {result[0]}" if result else "❌ Close failed"

        elif action['action'] == 'set_leverage':
            result = binance_oms.change_leverage(
                action['symbol'],
                action['leverage']
            )
            return f"⚖️ Leverage set to {action['leverage']}x" if result else "❌ Leverage change failed"

        elif action['action'] == 'risk_reward_setup':
            # Implement risk-reward calculation and order placement
            mark_price = binance_oms.client.futures_mark_price(symbol=action['symbol'])['markPrice']
            entry_price = float(mark_price)
            
            # Calculate position size based on risk percentage
            account_balance = binance_oms.get_futures_balance()['available']
            risk_amount = account_balance * (action['risk_percent'] / 100)
            
            # Calculate stop loss and take profit
            if action['side'] == 'BUY':
                stop_loss = entry_price * (1 - 0.01/action['leverage'])
                take_profit = entry_price * (1 + (0.01/action['leverage'])*action['reward_ratio'])
            else:
                stop_loss = entry_price * (1 + 0.01/action['leverage'])
                take_profit = entry_price * (1 - (0.01/action['leverage'])*action['reward_ratio'])
            
            # Place orders
            binance_oms.place_futures_order(
                symbol=action['symbol'],
                side=action['side'],
                quantity=risk_amount / (entry_price - stop_loss),
                order_type='MARKET',
                quantity_type='USD'
            )
            
            binance_oms.place_futures_order(
                symbol=action['symbol'],
                side='SELL' if action['side'] == 'BUY' else 'BUY',
                quantity=risk_amount / (entry_price - stop_loss),
                order_type='LIMIT',
                price=take_profit,
                quantity_type='CONTRACTS'
            )
            
            return f"""🎯 Risk-Reward Setup:
- Entry: {entry_price:.2f}
- Stop Loss: {stop_loss:.2f}
- Take Profit: {take_profit:.2f}
- Risk: {action['risk_percent']}% of account
- Reward Ratio: 1:{action['reward_ratio']}"""

    except Exception as e:
        return f"❌ Error executing action: {str(e)}"

# Streamlit UI
def main():
    st.set_page_config(page_title="AI Trading Agent", layout="wide")
    
    # Sidebar Controls
    with st.sidebar:
        st.header("🔧 Configuration")
        api_key = st.text_input("Gemini API Key", type="password")
        model_name = st.selectbox(
            "Model Version",
            ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
        )
        st.markdown("---")
        st.header("📊 Live Data")
        if st.button("Refresh Balances"):
            balance = binance_oms.get_futures_balance()
            st.metric("Futures Balance", f"{balance['available']:,.2f} / {balance['total']:,.2f}")
        
        if st.button("Show Positions"):
            positions = binance_oms.view_open_futures_positions()
            st.dataframe(positions, use_container_width=True)

    # Chat Interface
    st.title("🤖 AI Trading Agent")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "How can I assist with your trading today?"}
        ]

    # Display chat messages
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # User input
    if prompt := st.chat_input("Enter trading command or question"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        try:
            # Initialize Gemini
            model = initialize_gemini(api_key, model_name)
            
            # Generate response
            response = model.generate_content(TRADING_SYSTEM_PROMPT + "\n\nUser: " + prompt)
            
            # Check if response contains trading action
            if '{' in response.text and '}' in response.text:
                result = execute_trading_action(response.text)
                st.session_state.messages.append({"role": "assistant", "content": result})
                st.chat_message("assistant").write(result)
            else:
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.chat_message("assistant").write(response.text)
        
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.chat_message("assistant").write(error_msg)

    # System Monitor
    with st.expander("📈 System Monitor", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ Successful Orders")
            st.write(binance_oms.successful_orders[-3:])
            
        with col2:
            st.subheader("❌ Failed Orders")
            st.write(binance_oms.failed_orders[-3:])

if __name__ == "__main__":
    main()
