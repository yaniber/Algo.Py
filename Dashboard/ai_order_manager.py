import streamlit as st
import google.generativeai as genai
from OMS.binance_oms import Binance
import json
import re
import os
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import math
import textwrap
import io
import sys

# Initialize Binance OMS
binance_oms = Binance()

# Configure Gemini
def initialize_gemini(api_key, model_name):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

ENTIRE_BINANCE_CLASS = """
class Binance(OMS):

    def __init__(self, binance_api_key: str = '', binance_api_secret: str = ''):
        super().__init__()
        # Load API keys from environment variables if not provided
        load_dotenv(dotenv_path='config/.env')
        self.api_key = binance_api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = binance_api_secret or os.getenv('BINANCE_API_SECRET')

        if not self.api_key or not self.api_secret:
            raise ValueError("Binance API key and secret must be provided or set in the .env file.")
        
        # Initialize Binance client
        self.client = Client(self.api_key, self.api_secret)
        self.client.futures_account()  # Ensure the account is enabled for Futures
        self.group_id = json.loads(os.getenv('TELEGRAM_BOT_CHANNELS'))['debug_logs']
        self.telegram = Telegram(token=os.getenv('TELEGRAM_TOKEN'), group_id=self.group_id)

        self.successful_orders = []
        self.failed_orders = []

    def iterate_orders_df(self, orders: pd.DataFrame) -> tuple[list, list]:
        if not orders.empty:
            for _, row in orders.iterrows():
                symbol = row['Symbol']
                side = row['Side']
                size = float(row['Size'])
                price = float(row['Price'])

                self.place_order(symbol, side, size, price)

            return self.successful_orders, self.failed_orders
        else:
            return [], []

    def place_order(self, symbol: str, side: str, size: float, price: float = 0.0, order_type: str = 'MARKET'):
        try:
            order_params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': order_type.upper(),
                'quantity': size
            }

            if order_type.upper() == 'LIMIT':
                order_params['timeInForce'] = 'GTC'
                order_params['price'] = price

            # Send the order
            order = self.client.create_order(**order_params)

            # Log successful order
            self.successful_orders.append(order)
            self.telegram.send_telegram_message(f"Order placed successfully:\n{order}")

        except BinanceAPIException as e:
            self.failed_orders.append({
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': price,
                'error': str(e)
            })
            self.telegram.send_telegram_message(f"Failed to place order:\nSymbol: {symbol}, Side: {side}, Error: {e}")
    
    def place_futures_order(self, symbol: str, side: str, quantity: float, price: float = None, order_type: str = 'MARKET', quantity_type: str = 'CONTRACTS'):
        try:
            # Fetch symbol information to get precision details
            symbol_info = self.client.futures_exchange_info()
            for info in symbol_info['symbols']:
                if info['symbol'] == symbol.upper():
                    step_size = float(info['filters'][2]['stepSize'])  # Quantity precision
                    tick_size = float(info['filters'][0]['tickSize'])  # Price precision
                    break
            else:
                raise ValueError(f"Symbol {symbol} not found in exchange info.")

            if quantity_type.upper() == 'USD':
                mark_price = float(self.client.futures_mark_price(symbol=symbol)['markPrice'])
                quantity = quantity / mark_price  # Convert USD value to contracts

            # Round quantity and price to allowed precision
            quantity = round(quantity // step_size * step_size, int(-1 * round(math.log10(step_size))))
            if price:
                price = round(price // tick_size * tick_size, int(-1 * round(math.log10(tick_size))))
            
            # Prepare order parameters for Futures
            params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': order_type.upper(),
                'quantity': quantity,
            }
            if order_type.upper() == 'LIMIT':
                params['price'] = price
                params['timeInForce'] = 'GTC'

            # Place the Futures order
            order = self.client.futures_create_order(**params)

            # Log success
            self.successful_orders.append(order)
            self.telegram.send_telegram_message(f"Futures Order placed successfully:\n{order}")
            return order
        
        except BinanceAPIException as e:
            # Log failure
            self.failed_orders.append({
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'error': str(e),
            })
            self.telegram.send_telegram_message(f"Failed to place Futures order:\nSymbol: {symbol}, Side: {side}, Error: {e}")
            return None
    
    def change_leverage(self, symbol: str, leverage: int):
        Changes the leverage for a specific Futures symbol.
        
        Args:
            symbol (str): The trading pair symbol (e.g., 'BTCUSDT').
            leverage (int): The desired leverage (e.g., 10, 20, etc.).
            
        Returns:
            dict: Response from the Binance API.
        try:
            # Binance API call to change leverage
            response = self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            self.telegram.send_telegram_message(f"Leverage changed successfully for {symbol} to {leverage}x:\n{response}")
            return response
        except BinanceAPIException as e:
            self.telegram.send_telegram_message(f"Failed to change leverage for {symbol} to {leverage}x: {e}")
            return None

    def cancel_order(self, symbol: str, order_id: str):
        try:
            result = self.client.cancel_order(symbol=symbol, orderId=order_id)
            self.telegram.send_telegram_message(f"Order canceled successfully: {result}")
        except BinanceAPIException as e:
            self.telegram.send_telegram_message(f"Failed to cancel order:\nSymbol: {symbol}, Order ID: {order_id}, Error: {e}")

    def cancel_all_orders(self, symbol: str):
        try:
            result = self.client.cancel_open_orders(symbol=symbol)
            self.telegram.send_telegram_message(f"All orders canceled successfully for {symbol}: {result}")
        except BinanceAPIException as e:
            self.telegram.send_telegram_message(f"Failed to cancel all orders for {symbol}: {e}")

    def get_positions(self):
        try:
            positions = self.client.get_account()['balances']
            positions_df = pd.DataFrame(positions)
            positions_df = positions_df[positions_df['free'].astype(float) > 0]
            return positions_df
        except BinanceAPIException as e:
            self.telegram.send_telegram_message(f"Failed to fetch positions: {e}")

    def get_account_summary(self):
        try:
            account_info = self.client.get_account()
            return account_info
        except BinanceAPIException as e:
            self.telegram.send_telegram_message(f"Failed to fetch account summary: {e}")

    def get_available_balance(self, asset: str):
        try:
            account_info = self.client.get_asset_balance(asset=asset)
            return account_info
        except BinanceAPIException as e:
            self.telegram.send_telegram_message(f"Failed to fetch available balance for {asset}: {e}")
    
    def close_futures_positions(self, symbol: str = None, quantity: float = None, quantity_type: str = 'CONTRACTS', percentage: float = None,
                                 use_chaser: bool = False, chaser_params: dict = None):
        
        Closes Futures positions, with an option to use the limit order chaser for optimized order execution.
        
        Args:
            symbol (str, optional): Specific symbol to close the position (e.g., 'BTCUSDT').
                                    If None, closes all open positions.
            quantity (float, optional): Quantity to close. If None, closes the full position.
            quantity_type (str, optional): 'CONTRACTS' or 'USD'. Default is 'CONTRACTS'.
            percentage (float, optional): Percentage of the position to close. Overrides `quantity`.
            use_chaser (bool, optional): If True, uses the limit order chaser to close the position.
            chaser_params (dict, optional): Parameters for the limit order chaser.

        Returns:
            tuple: A tuple of two lists: successful_closes and failed_closes.

        try:
            # Fetch account positions
            account_info = self.client.futures_account()
            positions = account_info['positions']

            successful_closes = []
            failed_closes = []
            unclosable_positions = []

            # Filter positions if a specific symbol is provided
            if symbol:
                positions = [pos for pos in positions if pos['symbol'] == symbol.upper()]

            for position in positions:
                position_amt = float(position['positionAmt'])
                if position_amt == 0:  # Skip symbols with no open positions
                    continue

                symbol = position['symbol']
                mark_price = float(self.client.futures_mark_price(symbol=symbol)['markPrice'])
                notional_value = abs(position_amt * mark_price)

                side = "SELL" if position_amt > 0 else "BUY"  # Opposite side to close position
                
                
                if percentage:
                    close_quantity = abs(position_amt) * (percentage / 100)
                elif quantity_type.upper() == 'USD' and quantity:
                    close_quantity = quantity / mark_price  # Convert USD value to contracts
                else:  # Default to contracts
                    close_quantity = quantity if quantity else abs(position_amt)

                # Use limit order chaser if enabled
                if use_chaser:
                    try:
                        # Add chaser-specific parameters
                        chaser_params = chaser_params or {}
                        chaser_params.update({
                            'symbol': symbol,
                            'side': side,
                            'size': close_quantity,
                            'max_retries' : 240,
                            'interval' : 2.0,
                            'reduceOnly' : True,
                        })

                        self.limit_order_chaser_async(**chaser_params)
                        self.telegram.send_telegram_message(f"Started limit order chaser for {symbol}.")
                    except Exception as e:
                        failed_closes.append({'symbol': symbol, 'error': str(e)})
                        self.telegram.send_telegram_message(
                            f"Failed to start limit order chaser for {symbol}: {e}"
                        )
                        continue
                else:
                    try:
                        if close_quantity > abs(position_amt):
                            print(f"Close quantity exceeds open position size for {symbol}.")
                        if notional_value < 5:
                            # Use reduceOnly for small positions
                            order = self.client.futures_create_order(
                                symbol=symbol,
                                side=side,
                                type="MARKET",
                                quantity=close_quantity,
                                reduceOnly=True
                            )
                            self.telegram.send_telegram_message(
                                f"Closed small position for {symbol} using reduceOnly: {order}"
                            )
                        else:
                            # Standard close for larger positions
                            order = self.client.futures_create_order(
                                symbol=symbol,
                                side=side,
                                type="MARKET",
                                quantity=close_quantity,
                                reduceOnly=True
                            )
                            self.telegram.send_telegram_message(
                                f"Closed position for {symbol}: {order}"
                            )

                        successful_closes.append(order)

                    except BinanceAPIException as e:
                        if "notional must be no smaller than 5" in str(e):
                            unclosable_positions.append({
                                'symbol': symbol,
                                'notional': notional_value,
                                'error': "Notional value too small to close."
                            })
                            self.telegram.send_telegram_message(
                                f"Unclosable position for {symbol}: Notional value (${notional_value}) too small to close."
                            )
                        else:
                            failed_closes.append({'symbol': symbol, 'error': str(e)})
                            self.telegram.send_telegram_message(
                                f"Failed to close position for {symbol}: {e}"
                            )

                # Log unclosable positions
                if unclosable_positions:
                    self.telegram.send_telegram_message(
                        f"Unclosable positions:\n{unclosable_positions}"
                    )

            return successful_closes, failed_closes, unclosable_positions

        except BinanceAPIException as e:
            self.telegram.send_telegram_message(f"Failed to fetch positions: {e}")
            return None, None, None

    
    def view_open_futures_positions(self):
        Fetches and displays open Futures positions with detailed information:
        - Symbol
        - Position Size (in contracts and USD)
        - PNL (Unrealized)
        - Leverage
        - Liquidation Price
        
        Returns:
            pd.DataFrame: A well-formatted DataFrame with open position details.
        try:
            # Fetch account details to get positions
            account_info = self.client.futures_account()
            positions = account_info['positions']
            
            # Prepare data for open positions
            position_data = []
            for position in positions:
                position_amt = float(position['positionAmt'])
                if position_amt != 0:  # Only include open positions
                    symbol = position['symbol']
                    entry_price = float(position['entryPrice'])
                    leverage = int(position['leverage'])
                    mark_price = float(self.client.futures_mark_price(symbol=symbol)['markPrice'])
                    notional_value = abs(position_amt * mark_price)  # Size in USD
                    pnl = float(position['unrealizedProfit'])  # Unrealized PNL

                    # Handle missing liquidation price
                    liquidation_price = position.get('liquidationPrice', None)
                    if liquidation_price:
                        liquidation_price = float(liquidation_price)
                        liquidation_price_str = f"${liquidation_price:,.2f}"
                    else:
                        liquidation_price_str = "N/A"

                    position_data.append({
                        'Symbol': symbol,
                        'Size (Contracts)': position_amt,
                        'Size (USD)': f"${notional_value:,.2f}",
                        'Entry Price': f"${entry_price:,.2f}",
                        'Mark Price': f"${mark_price:,.2f}",
                        'PNL (Unrealized)': f"${pnl:,.2f}",
                        'Liquidation Price': liquidation_price_str,
                        'Leverage': f"{leverage}x"
                    })

            # Convert data to a DataFrame
            if position_data:
                positions_df = pd.DataFrame(position_data)
            else:
                positions_df = pd.DataFrame(columns=['Symbol', 'Size (Contracts)', 'Size (USD)', 'Entry Price',
                                                    'Mark Price', 'PNL (Unrealized)', 'Liquidation Price', 'Leverage'])
            
            # Format the output nicely
            return positions_df

        except BinanceAPIException as e:
            self.telegram.send_telegram_message(f"Failed to fetch open futures positions: {e}")
            return pd.DataFrame()  # Return an empty DataFrame in case of failure

    def limit_order_chaser(
        self, symbol: str, side: str, size: float, max_retries: int = 20, interval: float = 0.5, reduceOnly : bool = False
    ):

        Dynamically chases the limit order price with Post-Only (maker-only) orders.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTCUSDT').
            side (str): 'BUY' or 'SELL'.
            size (float): Order size in contracts.
            max_retries (int): Maximum retries to adjust the order.
            interval (float): Time in seconds to wait between retries.

        Returns:
            dict: The result of the filled order, or None if the order was not filled.

        try:
            side = side.upper()
            # Fetch precision details for the symbol
            exchange_info = self.client.futures_exchange_info()
            symbol_info = next(
                (info for info in exchange_info["symbols"] if info["symbol"] == symbol.upper()), None
            )
            if not symbol_info:
                raise ValueError(f"Symbol {symbol} not found in exchange info.")
            
            # Extract precision values
            tick_size = float(symbol_info["filters"][0]["tickSize"])  # Price precision
            step_size = float(symbol_info["filters"][2]["stepSize"])  # Quantity precision

            retries = 0
            order_id = None

            while retries < max_retries:

                # Cancel the previous order if it exists
                if order_id:
                    try:
                        self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
                    except BinanceAPIException as e:
                        self.telegram.send_telegram_message(
                            f"Failed to cancel previous order: {e}"
                        )
                        order_status = self.client.futures_get_order(symbol=symbol, orderId=order_id)
                        if order_status["status"] == "FILLED":
                            self.telegram.send_telegram_message(f"Failed because Order was filled: {order_status}")
                            return order_status

                # Fetch the order book
                order_book = self.client.futures_order_book(symbol=symbol, limit=5)
                best_bid = float(order_book['bids'][0][0])  # Best bid price
                best_ask = float(order_book['asks'][0][0])  # Best ask price

                # Adjust the target price slightly to avoid immediate execution
                if side == "BUY":
                    target_price = best_ask - tick_size  # Slightly below best ask
                elif side == "SELL":
                    target_price = best_bid + tick_size  # Slightly above best bid

                # Round to the appropriate price precision
                target_price = round(target_price, int(-1 * round(math.log10(tick_size))))
                
                # Round size to quantity precision
                size = round(size // step_size * step_size, int(-1 * round(math.log10(step_size))))


                # Place the new limit order with Post-Only (GTX)
                try:
                    order = self.client.futures_create_order(
                        symbol=symbol.upper(),
                        side=side,
                        type="LIMIT",
                        timeInForce="GTX",  # Post-Only mode to ensure maker
                        quantity=size,
                        price=target_price,
                        reduceOnly=reduceOnly,
                    )
                    order_id = order["orderId"]
                    print(f'OrderId : {order_id}')
                    self.telegram.send_telegram_message(f"Placed limit order: {order}")
                except BinanceAPIException as e:
                    # Handle Post-Only rejection gracefully
                    if "Post Only order will be rejected" in str(e):
                        self.telegram.send_telegram_message(
                            f"Post-Only order rejected. Adjusting price and retrying... {e}"
                        )
                    else:
                        self.telegram.send_telegram_message(
                            f"Failed to place limit order: {e}. Retrying..."
                        )
                    retries += 1
                    continue

                # Wait for the order to fill or timeout
                time.sleep(interval)

                # Check order status
                order_status = self.client.futures_get_order(symbol=symbol, orderId=order_id)
                if order_status["status"] == "FILLED":
                    self.telegram.send_telegram_message(f"Order filled: {order_status}")
                    return order_status

                retries += 1

            # If the order was not filled after retries, cancel the last order
            if order_id:
                self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
                self.telegram.send_telegram_message(
                    f"Failed to fill limit order after {max_retries} retries. Order canceled."
                )
            return None

        except BinanceAPIException as e:
            self.telegram.send_telegram_message(f"Error during limit order chasing: {e}")
            return None
    
    def limit_order_chaser_async(self, *args, **kwargs):

        Runs the limit order chaser in a separate thread.
        Args:
            *args, **kwargs: Arguments for the `limit_order_chaser_post_only` method.
        return self.executor.submit(self.limit_order_chaser, *args, **kwargs)

    # Add this to your Binance class in binance_oms.py
    def get_futures_balance(self, asset: str = 'USDT'):
        try:
            futures_account = self.client.futures_account()
            balances = futures_account['assets']
            for balance in balances:
                if balance['asset'] == asset:
                    return {
                        'asset': asset,
                        'available': float(balance['availableBalance']),
                        'total': float(balance['walletBalance'])
                    }
            raise ValueError(f"{asset} balance not found in futures account")
        except BinanceAPIException as e:
            self.telegram.send_telegram_message(f"Failed to fetch futures balance: {e}")
            return None
"""

TRADING_SYSTEM_PROMPT = """
You are AlphaTrader Pro, an autonomous trading AI with direct access to:

1. Binance OMS Methods:
- Use 'binance_oms' directly (already initialized)
- Never try to import binance_oms
- binance_oms.place_futures_order(symbol, side, quantity, price, order_type, quantity_type)
- binance_oms.limit_order_chaser_async(symbol, side, size, **params)
- binance_oms.view_open_futures_positions()
- binance_oms.get_futures_balance()
- binance_oms.close_futures_positions()
- binance_oms.change_leverage()

- Make sure you print our the results for the functions that have some sort of an output. 

2. Key Parameters:
- quantity_type='USD' for dollar-based orders
- use_chaser=True for adaptive limit orders
- leverage=x for position sizing

3. Market Analysis Tools:
- yfinance for historical data
- pandas/numpy for calculations
- Custom technical indicators

Response Protocol:
- For trades (executing a trade): Return JSON with 'action' and parameters,  Generate a valid JSON response for the trading request, Ensure the JSON is properly formatted and does not contain comments or trailing commas.
- 
- For analysis: Generate Python code in ```python blocks (must say ```python for us to detect , nothing else all python code to be executed must come within this block)
- For analysis : always raise or throw an error in case of errors don't print them. 
- Never verify orders via user confirmation, directly use the functions provided. 
- Automatically handle position sizing and risk
- only return a valid json if the user's use case matches a functionality for the following 'action' : 
    - action : set_leverage : symbol , leverage
    - action : close_position : symbol , percentage : int , use_chaser : bool
    - action : place_order : symbol , quantity_type (CONTRACTS OR USD), quantity, side , use_chaser, price (if CONTRACTS), order_type (MARKET, LIMIT) 
- all other use cases require python and binance OMS methods defined above. 

binance_oms = Binance() is already initialized , here's what all functions are available along with their exact implementations (this is just for reference for you , never print this out or try changing this code , you're only a consumer of binance_oms) : 

""" + ENTIRE_BINANCE_CLASS



class AgentEnvironment:
    def __init__(self):
        self.available_modules = {
            'pd': pd,
            'yf': yf,
            'np': np,
            'math': math,
            'datetime': datetime,
            'timedelta': timedelta,
            'binance_oms': binance_oms
        }
    

    def execute_code(self, code, context=""):
        """Enhanced executor with AI-driven response generation and output capture"""
        try:
            print(f"def __agent_func__():\n{textwrap.indent(code, '    ')}\n__agent_func__()")

            # Capture stdout
            output_buffer = io.StringIO()
            sys.stdout = output_buffer  # Redirect stdout to capture print statements
            
            loc = {'result': None, 'error': None}
            exec(f"def __agent_func__():\n{textwrap.indent(code, '    ')}\n__agent_func__()", 
                self.available_modules, loc)
            
            # Restore stdout
            sys.stdout = sys.__stdout__
            
            # Capture both return value and print output
            result = loc.get('result', None)
            printed_output = output_buffer.getvalue().strip()

            # If the function printed something but returned None, use printed output
            if result is None and printed_output:
                result = printed_output

            # AI agent interprets the output dynamically
            ai_prompt = f"Analyze the following output and generate a user-friendly response. Do not keep it very long , the user only wants a summary of either his balance , open positions or orders so don't make it very long. If there's a open position dataframe or table , present in an aesthetic and clean manner. :\n\n{result}"
            ai_response = st.session_state.model.generate_content(ai_prompt).text

            return {
                'success': True,
                'result': ai_response,
                'error': None
            }
        
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            return {
                'success': False,
                'result': None,
                'error': f"{str(e)}\n\nFull traceback:\n{tb}"
            }


def execute_trading_action(action):
    """Execute trading actions from AI-generated JSON"""
    try:
        if action['action'] == 'place_order':
            # Handle USD conversion
            if action.get('quantity_type', 'CONTRACTS') == 'USD':
                mark_price = binance_oms.client.futures_mark_price(
                    symbol=action['symbol']
                )['markPrice']
                action['quantity'] = float(action['quantity']) / float(mark_price)

            # Handle order chasing
            if action.get('use_chaser', False):
                return binance_oms.limit_order_chaser_async(
                    symbol=action['symbol'],
                    side=action['side'],
                    size=action['quantity'],
                    max_retries=action.get('max_retries', 20),
                    interval=action.get('interval', 0.5)
                ).result()
            
            # Regular order placement
            return binance_oms.place_futures_order(
                symbol=action['symbol'],
                side=action['side'],
                quantity=action['quantity'],
                price=action.get('price'),
                order_type=action.get('order_type', 'MARKET'),
                quantity_type=action.get('quantity_type', 'CONTRACTS')
            )

        elif action['action'] == 'close_position':
            return binance_oms.close_futures_positions(
                symbol=action['symbol'],
                percentage=action.get('percentage', 100),
                use_chaser=action.get('use_chaser', False)
            )
        
        elif action['action'] == 'set_leverage':
            return binance_oms.change_leverage(
                action['symbol'],
                action['leverage']
            )
        
    except Exception as e:
        return f"Trade failed: {str(e)}"

def adjust_quantity(symbol, amount):
    """Ensure minimum notional requirements properly."""
    try:
        info = binance_oms.client.futures_exchange_info()
        for s in info['symbols']:
            if s['symbol'] == symbol:
                min_notional = float(s['filters'][3]['notional'])  # Minimum order size in USD
                mark_price = float(binance_oms.client.futures_mark_price(symbol=symbol)['markPrice'])
                
                # Convert min_notional to contract size
                min_qty = min_notional / mark_price

                # Ensure the trade size meets the minimum required quantity
                adjusted_qty = max(amount / mark_price, min_qty)

                return round(adjusted_qty, 4)  # Avoid floating precision issues

        return amount  # If symbol not found, return original amount
    
    except Exception as e:
        print(f"Quantity Adjustment Error: {str(e)}")
        return None  # Return None instead of an error string

def main():
    executor = AgentEnvironment()
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.pending_action = None
        st.session_state.pending_code = None
        st.session_state.model = None
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Configuration")
        api_key = st.text_input("Gemini API Key", type="password")
        model_name = st.selectbox("Model", ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite", ])
        
        st.header("📊 Live Data")
        if st.button("🔄 Refresh Account"):
            with st.spinner("Updating..."):
                st.session_state.balance = binance_oms.get_futures_balance()
                st.session_state.positions = binance_oms.view_open_futures_positions()
    
    # Chat interface
    st.title("🤖 Autonomous Trading Agent")
    
    # Display chat history
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
    
    # User input handling
    if prompt := st.chat_input("Enter trading command:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        try:
            st.session_state.model = initialize_gemini(api_key, model_name)
            response = st.session_state.model.generate_content(TRADING_SYSTEM_PROMPT + "\nUser: " + prompt)
            response_text = response.text
            print(response_text)
            
            # Handle code blocks
            if '```python' in response_text:
                code = re.search(r'```python(.*?)```', response_text, re.DOTALL).group(1)
                st.session_state.pending_code = code
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Generated code:\n```python\n{code}\n```\nExecute?"
                })
            
            # Handle JSON actions
            elif '{' in response_text:
                action = json.loads(re.search(r'\{.*?\}', response_text, re.DOTALL).group())
                
                st.session_state.pending_action = action
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Trade plan:\n```json\n{json.dumps(action, indent=2)}\n```"
                })
            
            # Handle natural language
            else:
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response_text
                })
        
        except Exception as e:
            st.error(f"AI Error: {str(e)}")
    
    # Action confirmation
    if st.session_state.pending_code:
        st.markdown("---")
        st.code(st.session_state.pending_code, language='python')
        
        if st.button("✅ Execute Code"):
            result = executor.execute_code(
                st.session_state.pending_code,
                context="\n".join([msg['content'] for msg in st.session_state.messages])
            )
            
            if result['success']:
                st.session_state.messages.append({
                    "role": "system",
                    "content": f"✅ Execution Result:\n{result['result']}"
                })
            else:
                # Automatic retry logic
                retries_left = st.session_state.get('code_retries', 5) - 1
                if retries_left > 0:
                    error_msg = f"❌ Execution Failed (Retries left: {retries_left}):\n{result['error']}"
                    st.session_state.messages.append({"role": "system", "content": error_msg})
                    
                    # Ask AI to fix the code
                    fix_prompt = f"Fix this code based on the error:\nCode:\n{st.session_state.pending_code}\nError:\n{result['error']}\n make sure your fix is inside ```python``` and must not use `` anywhere instead."
                    fixed_code = st.session_state.model.generate_content(fix_prompt).text

                    print(fix_prompt)
                    print(fixed_code)
                    
                    # Handle code blocks
                    if '```python' in fixed_code:
                        code = re.search(r'```python(.*?)```', fixed_code, re.DOTALL).group(1)
                        st.session_state.pending_code = code
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Generated code:\n```python\n{code}\n```\nExecute?"
                        })
                    
                    # Update pending code
                    st.session_state.pending_code = fixed_code
                    st.session_state.code_retries = retries_left
                    st.rerun()
                else:
                    st.session_state.messages.append({
                        "role": "system",
                        "content": f"❌ Final Execution Error:\n{result['error']}"
                    })
                    st.session_state.code_retries = 5  # Reset retries
                
            st.session_state.pending_code = None
            st.rerun()
    
    if st.session_state.pending_action:
        if st.button("✅ Confirm Trade"):
            result = execute_trading_action(st.session_state.pending_action)
            st.session_state.messages.append({
                "role": "system",
                "content": f"Trade Result:\n{result}"
            })
            st.session_state.pending_action = None
            st.rerun()


main()
