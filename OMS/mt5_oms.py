import os
import sys
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from OMS.oms import OMS
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime
import logging
from OMS.telegram import Telegram

# Try to import MetaTrader5, handle gracefully if not available (Linux/Mac environments)
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False
    print("Warning: MetaTrader5 package not available. MT5 functionality will be disabled.")

class MT5(OMS):   
    def __init__(self, login: int = None, password: str = None, server: str = None, path: str = None):
        super().__init__()
        
        # Check if MetaTrader5 is available
        if not MT5_AVAILABLE:
            raise ImportError("MetaTrader5 package is not available. This is expected on Linux/Mac systems. MT5 functionality requires Windows.")
            
        # Load environment variables if credentials not provided
        if not login or not password or not server:
            load_dotenv(dotenv_path='config/.env')
            self.login = login or int(os.getenv('MT5_LOGIN', 0))
            self.password = password or os.getenv('MT5_PASSWORD')
            self.server = server or os.getenv('MT5_SERVER')
            self.path = path or os.getenv('MT5_PATH')  # Optional: path to MT5 terminal
        else:
            self.login = login
            self.password = password
            self.server = server
            self.path = path
        
        if not self.login or not self.password or not self.server:
            raise ValueError("Variables for MT5_LOGIN, MT5_PASSWORD, or MT5_SERVER are not set.")
        
        # Initialize MT5 connection
        self.connected = False
        self.connect()
        
        # Initialize logging and telegram
        try:
            self.telegram = Telegram()
        except:
            self.telegram = None
            
        self.successful_orders = []
        self.failed_orders = []

    def connect(self):
        """Establish connection to MT5 terminal"""
        try:
            # Initialize MT5 terminal
            if self.path:
                if not mt5.initialize(path=self.path):
                    print(f"Failed to initialize MT5 with path: {self.path}")
                    return False
            else:
                if not mt5.initialize():
                    print("Failed to initialize MT5")
                    return False
            
            # Login to MT5 account
            if not mt5.login(self.login, password=self.password, server=self.server):
                print(f"Failed to login to MT5 account {self.login}")
                mt5.shutdown()
                return False
            
            self.connected = True
            print(f"Successfully connected to MT5 account: {self.login}")
            return True
            
        except Exception as e:
            print(f"Error connecting to MT5: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from MT5 terminal"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("Disconnected from MT5")

    def get_account_info(self):
        """Get account information"""
        if not self.connected:
            print("Not connected to MT5")
            return None
        
        account_info = mt5.account_info()
        if account_info is None:
            print("Failed to get account info")
            return None
        
        return account_info._asdict()

    def get_symbols(self):
        """Get available symbols"""
        if not self.connected:
            print("Not connected to MT5")
            return []
        
        symbols = mt5.symbols_get()
        if symbols is None:
            print("Failed to get symbols")
            return []
        
        return [symbol.name for symbol in symbols if symbol.visible]

    def iterate_orders_df(self, orders: pd.DataFrame) -> tuple[list, list]:
        """Process orders from DataFrame"""
        if not orders.empty:
            for _, row in orders.iterrows():
                symbol = row['Symbol']
                side = row['Side']  # 'BUY' or 'SELL'
                size = float(row['Size'])
                price = float(row['Price']) if 'Price' in row else None
                order_type = row.get('OrderType', 'MARKET')

                self.place_order(symbol, side, size, price, order_type)

            return self.successful_orders, self.failed_orders
        else:
            return [], []

    def place_order(self, symbol: str, side: str, size: float, price: float = None, order_type: str = 'MARKET'):
        """Place order on MT5"""
        if not self.connected:
            error_msg = "Not connected to MT5"
            print(error_msg)
            self.failed_orders.append({
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': price,
                'error': error_msg,
                'timestamp': datetime.now()
            })
            return False

        try:
            # Prepare order request
            order_type_mt5 = mt5.ORDER_TYPE_BUY if side.upper() == 'BUY' else mt5.ORDER_TYPE_SELL
            
            if order_type.upper() == 'MARKET':
                order_type_mt5 = mt5.ORDER_TYPE_BUY if side.upper() == 'BUY' else mt5.ORDER_TYPE_SELL
            elif order_type.upper() == 'LIMIT':
                order_type_mt5 = mt5.ORDER_TYPE_BUY_LIMIT if side.upper() == 'BUY' else mt5.ORDER_TYPE_SELL_LIMIT
            
            # Get symbol info for lot size validation
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                error_msg = f"Symbol {symbol} not found"
                print(error_msg)
                self.failed_orders.append({
                    'symbol': symbol,
                    'side': side,
                    'size': size,
                    'price': price,
                    'error': error_msg,
                    'timestamp': datetime.now()
                })
                return False

            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": size,
                "type": order_type_mt5,
                "deviation": 20,
                "magic": 123456,
                "comment": "Algo.Py order",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Add price for limit orders
            if price is not None and order_type.upper() == 'LIMIT':
                request["price"] = price

            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                error_msg = "Order send failed - no result"
                print(error_msg)
                self.failed_orders.append({
                    'symbol': symbol,
                    'side': side,
                    'size': size,
                    'price': price,
                    'error': error_msg,
                    'timestamp': datetime.now()
                })
                return False

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = f"Order failed: {result.comment}"
                print(error_msg)
                self.failed_orders.append({
                    'symbol': symbol,
                    'side': side,
                    'size': size,
                    'price': price,
                    'error': error_msg,
                    'timestamp': datetime.now(),
                    'retcode': result.retcode
                })
                return False

            # Order successful
            success_info = {
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': result.price,
                'order_id': result.order,
                'timestamp': datetime.now(),
                'volume': result.volume
            }
            print(f"Order placed successfully: {success_info}")
            self.successful_orders.append(success_info)
            
            # Send telegram notification if available
            if self.telegram:
                message = f"✅ MT5 Order Executed\nSymbol: {symbol}\nSide: {side}\nSize: {size}\nPrice: {result.price}"
                try:
                    self.telegram.send_message(message)
                except:
                    pass
            
            return True

        except Exception as e:
            error_msg = f"Exception placing order: {str(e)}"
            print(error_msg)
            self.failed_orders.append({
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': price,
                'error': error_msg,
                'timestamp': datetime.now()
            })
            return False

    def cancel_order(self, order_id: int):
        """Cancel an order"""
        if not self.connected:
            print("Not connected to MT5")
            return False

        try:
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": order_id,
            }
            
            result = mt5.order_send(request)
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Failed to cancel order {order_id}: {result.comment if result else 'No result'}")
                return False
            
            print(f"Order {order_id} cancelled successfully")
            return True
            
        except Exception as e:
            print(f"Exception cancelling order {order_id}: {str(e)}")
            return False

    def get_positions(self):
        """Get current positions"""
        if not self.connected:
            print("Not connected to MT5")
            return pd.DataFrame()

        try:
            positions = mt5.positions_get()
            if positions is None:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys()) if positions else pd.DataFrame()
            return df
            
        except Exception as e:
            print(f"Error getting positions: {str(e)}")
            return pd.DataFrame()

    def get_pnl(self):
        """Get total P&L"""
        try:
            account_info = self.get_account_info()
            if account_info:
                return account_info.get('profit', 0.0)
            return 0.0
        except Exception as e:
            print(f"Error getting PnL: {str(e)}")
            return 0.0

    def get_account_summary(self):
        """Get account summary"""
        return self.get_account_info()

    def get_available_balance(self):
        """Get available balance"""
        try:
            account_info = self.get_account_info()
            if account_info:
                return account_info.get('balance', 0.0)
            return 0.0
        except Exception as e:
            print(f"Error getting balance: {str(e)}")
            return 0.0

    def __del__(self):
        """Cleanup on object destruction"""
        self.disconnect()


if __name__ == '__main__':
    # Test MT5 connection
    try:
        mt5_oms = MT5()
        print("MT5 Account Info:", mt5_oms.get_account_info())
        print("Available Balance:", mt5_oms.get_available_balance())
        print("Symbols count:", len(mt5_oms.get_symbols()))
        print("Current Positions:")
        print(mt5_oms.get_positions())
    except Exception as e:
        print(f"Test failed: {str(e)}")