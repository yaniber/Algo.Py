import streamlit as st
import google.generativeai as genai
from OMS.binance_oms import Binance  # Assuming same OMS structure
import pandas as pd
import re

# Initialize Binance OMS
def initialize_binance():
    try:
        return Binance()
    except Exception as e:
        st.error(f"Failed to initialize Binance OMS: {str(e)}")
        return None

# Configure Gemini
def configure_gemini(api_key, model_name):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

# System prompt template
SYSTEM_PROMPT = """
You are a professional trading assistant for Binance exchange. Your capabilities include:

1. Understanding trading commands in natural language
2. Executing orders (market, limit, stop-loss)
3. Managing positions (close, modify)
4. Providing account information (balance, positions)
5. Calculating risk/reward ratios
6. Explaining trading concepts

Available functions:
- get_balance(asset: str)
- get_positions(symbol: str = None)
- place_order(symbol: str, side: str, quantity: float, 
             order_type: str, price: float = None, 
             leverage: int = None, stop_loss: float = None,
             take_profit: float = None)
- close_position(symbol: str, percentage: int = 100)
- calculate_rr(symbol: str, entry: float, stop_loss: float, 
              take_profit: float, quantity: float)

When asked to perform trading actions:
1. Always confirm parameters before execution
2. Verify risk management parameters if missing
3. For order placement, always suggest risk management
4. Format numbers to appropriate decimal places
5. Prefer async confirmation for market orders

Respond concisely but professionally. Use trading terminology correctly.
"""

# Function calling handler
def execute_function_call(binance_oms, function_call):
    func_name = function_call.name
    args = function_call.args
    
    try:
        if func_name == "get_balance":
            balance = binance_oms.get_futures_balance(args["asset"])
            return f"Balance: {balance['available']} {args['asset']} available, {balance['total']} total"
        
        elif func_name == "get_positions":
            positions = binance_oms.view_open_futures_positions(args.get("symbol"))
            return positions.to_dict() if not positions.empty else "No open positions"
        
        elif func_name == "place_order":
            # Handle different order types
            if args["order_type"].upper() == "MARKET":
                result = binance_oms.place_futures_order(
                    symbol=args["symbol"],
                    side=args["side"],
                    quantity=args["quantity"],
                    order_type="MARKET",
                    leverage=args.get("leverage", 20)
                )
            elif args["order_type"].upper() == "LIMIT":
                result = binance_oms.limit_order_chaser_async(
                    symbol=args["symbol"],
                    side=args["side"],
                    size=args["quantity"],
                    price=args["price"]
                )
            
            return f"Order executed: {result}"
        
        elif func_name == "close_position":
            result = binance_oms.close_futures_positions(
                symbol=args["symbol"],
                percentage=args["percentage"]
            )
            return f"Position closed: {result}"
        
        elif func_name == "calculate_rr":
            risk = abs(float(args["entry"]) - float(args["stop_loss"]))
            reward = abs(float(args["take_profit"]) - float(args["entry"]))
            rr_ratio = round(reward / risk, 2)
            return f"Risk/Reward Ratio: 1:{rr_ratio}"
        
        return "Function not implemented"
    
    except Exception as e:
        return f"Error executing {func_name}: {str(e)}"

# Chat interface
def chat_interface(binance_oms, model):
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", 
                                        "content": "How can I assist with your trading today?"})

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Handle function responses
            if "function_call" in message:
                st.markdown(f"**Action:** {message['function_call']}")
            else:
                st.markdown(message["content"])

            # Display structured data
            if "positions" in message:
                st.dataframe(pd.DataFrame(message["positions"]))
            elif "balance" in message:
                st.metric("Account Balance", message["balance"])

    # Accept user input
    if prompt := st.chat_input("Enter trading command..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate response
        response = model.generate_content({
            "parts": [SYSTEM_PROMPT, *st.session_state.messages],
            "tools": [{
                "function_declarations": [
                    # Define all available functions here
                    {
                        "name": "place_order",
                        "description": "Execute a trade order",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "symbol": {"type": "string"},
                                "side": {"enum": ["BUY", "SELL"]},
                                "quantity": {"type": "number"},
                                "order_type": {"enum": ["MARKET", "LIMIT"]},
                                "price": {"type": "number"},
                                "leverage": {"type": "integer"},
                                "stop_loss": {"type": "number"},
                                "take_profit": {"type": "number"}
                            },
                            "required": ["symbol", "side", "quantity", "order_type"]
                        }
                    },
                    # Add other function definitions...
                ]
            }]
        })

        # Handle function calling
        if response.candidates[0].content.parts[0].function_call:
            fc = response.candidates[0].content.parts[0].function_call
            result = execute_function_call(binance_oms, fc)
            
            # Add function response to history
            st.session_state.messages.append({
                "role": "function",
                "name": fc.name,
                "content": str(result)
            })
            
            # Generate final response
            final_response = model.generate_content({
                "parts": [SYSTEM_PROMPT, *st.session_state.messages]
            })
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.markdown(final_response.text)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": final_response.text
                })
        
        else:
            # Display normal response
            with st.chat_message("assistant"):
                st.markdown(response.text)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response.text
                })

# Main app
def main():
    st.set_page_config(page_title="AI Trading Assistant", layout="wide")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        model_name = st.selectbox(
            "Gemini Model",
            ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"],
            index=0
        )
        
        api_key = st.text_input("Gemini API Key", type="password")
        
        if not api_key:
            st.info("Enter Gemini API key to continue")
            st.stop()
            
        binance_oms = initialize_binance()
        if not binance_oms:
            st.stop()
    
    # Initialize Gemini
    try:
        model = configure_gemini(api_key, model_name)
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {str(e)}")
        st.stop()
    
    # Main interface
    st.title("🤖 AI Trading Assistant")
    st.write("**Natural Language Trading Interface**")
    
    chat_interface(binance_oms, model)

if __name__ == "__main__":
    main()