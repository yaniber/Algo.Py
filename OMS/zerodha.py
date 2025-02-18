import os
import sys
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from OMS.oms import OMS
from jugaad_trader import Zerodha as Zerodha_sdk
import pyotp
import json
from dotenv import load_dotenv
import pandas as pd
from OMS.telegram import Telegram

class Zerodha(OMS):   
    def __init__(self, userid: str = None, password: str = None, totp: str = None):
        
        if not userid or not password or not totp:
            load_dotenv(dotenv_path='config/.env')
            self.userid = os.getenv('USER_ID')
            self.password = os.getenv('PASSWORD')
            self.totp = os.getenv('TOTP_SECRET')
        else:
            self.userid = userid
            self.password = password
            self.totp = totp
        
        if not self.userid or not self.password or not self.totp:
            raise ValueError("Variables for USER_ID, PASSWORD, or TOTP_SECRET are not set.")
        
        otp_gen = pyotp.TOTP(self.totp)
        print(f'---------- userid : {self.userid}, password : {self.password}, totp : {self.totp}')
        self.kite = Zerodha_sdk(user_id=self.userid, password=self.password, twofa=otp_gen.now())
        self.kite.login()
        self.telegram = Telegram()
        self.successful_orders = []
        self.failed_orders = []
    
    def iterate_orders_df(self, orders: pd.DataFrame) -> tuple[list, list]:
        if not orders.empty:
            for _, row in orders.iterrows():
                
                symbol = row['Column']
                if '.NS' in symbol:
                    symbol = symbol.replace('.NS', '')
                side = row['Side']
                size = int(row['Size'])
                price = float(row['Price'])
                
                self.place_order(symbol, side, size, price)
            
            return self.successful_orders, self.failed_orders
        else:
            return [], []
        

    def place_order(self, symbol: str, side: str, size: int, price: float, order_type: str = 'MARKET'):
        try:
            # TODO: Add order handling in telegram
            self.telegram.send_telegram_message(f"Placing Order: \nSymbol: {symbol}, Side: {side}, Size: {size}, Price: {price}, Order Type: {order_type}")
            order_id = self.kite.place_order(tradingsymbol=symbol,
                                    exchange=self.kite.EXCHANGE_NSE,
                                    transaction_type=self.kite.TRANSACTION_TYPE_BUY if side == 'Buy' else self.kite.TRANSACTION_TYPE_SELL,
                                    quantity=size,
                                    order_type=self.kite.ORDER_TYPE_MARKET if order_type == 'MARKET' else self.kite.ORDER_TYPE_LIMIT,       # TODO: Add limit order type
                                    product=self.kite.PRODUCT_CNC,
                                    variety=self.kite.VARIETY_REGULAR)
        except Exception as e:
            self.failed_orders.append({
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': price,
                'status': 'REJECTED',
                'error': str(e),
                'fill_price': None,
                'fill_quantity': None,
                'order_id': None,
                'orders_df': json.dumps({})
            })
            self.telegram.send_telegram_message(f"Exception in placing order: \nSymbol: {symbol}, Side: {side}, Size: {size}, Price: {price} \nError: {str(e)}")
        
        orders = pd.DataFrame(self.kite.orders())

        status = orders[orders['order_id'] == order_id]['status'].values[0]

        if status == 'REJECTED':
            errmsg = orders[orders['order_id'] == order_id]['status_message'].values[0]
            self.failed_orders.append({
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': price,
                'status': status,
                'error': errmsg,
                'fill_price': None,
                'fill_quantity': None,
                'order_id': order_id,
                'orders_df': orders.to_json()
            })
            self.telegram.send_telegram_message(f"Order Rejected: \nSymbol: {symbol}, Side: {side}, Size: {size}, Price: {price} \nStatus: {status} \nError: {errmsg}")
        
        elif status == 'COMPLETE':
            fill_price = orders[orders['order_id'] == order_id]['average_price'].values[0]
            fill_quantity = orders[orders['order_id'] == order_id]['filled_quantity'].values[0]
            self.successful_orders.append({
                'symbol': symbol,
                'side': side,
                'size': size,
                'price': price,
                'status': status,
                'error': None,
                'fill_price': fill_price,
                'fill_quantity': fill_quantity,
                'order_id': order_id,
                'orders_df': orders.to_json()
            })
            self.telegram.send_telegram_message(f"Order Executed: \nSymbol: {symbol}, Side: {side}, Size: {size}, Price: {price} \nStatus: {status} \nFill Price: {fill_price} \nFill Quantity: {fill_quantity}")
        
    
    def cancel_order(self, order_id: str):
        pass 
    
    def get_positions(self):
        try:
            # Fetch positions
            positions = self.kite.positions()["net"]
            positions_df = pd.DataFrame(positions)

            if not positions_df.empty:
                positions_df = positions_df[["tradingsymbol", "quantity", "average_price", "last_price", "pnl"]]
                positions_df.rename(columns={
                    "tradingsymbol": "Symbol",
                    "quantity": "Size",
                    "average_price": "Entry Price",
                    "last_price": "Mark Price",
                    "pnl": "PnL"
                }, inplace=True)

            # Fetch holdings
            holdings = self.kite.holdings()
            holdings_df = pd.DataFrame(holdings)

            if not holdings_df.empty:
                holdings_df = holdings_df[["tradingsymbol", "quantity", "average_price", "last_price", "pnl"]]
                holdings_df.rename(columns={
                    "tradingsymbol": "Symbol",
                    "quantity": "Size",
                    "average_price": "Entry Price",
                    "last_price": "Mark Price",
                    "pnl": "PnL"
                }, inplace=True)

            return {"positions": positions_df, "holdings": holdings_df}

        except Exception as e:
            self.telegram.send_telegram_message(f"Failed to fetch positions and holdings: {e}")
            print(f"Failed to fetch positions and holdings: {e}")
            return {"positions": pd.DataFrame(), "holdings": pd.DataFrame()}

    
    def get_pnl(self):
        pass 
    
    def get_account_summary(self):
        pass 

    def get_available_balance(self):
        margins = self.kite.margins(segment="equity")
        return margins['available']['cash'] 

if __name__ == '__main__':
    zerodha = Zerodha()
    print(zerodha.get_available_balance())
    #zerodha2 = Zerodha()
    #print(zerodha2.get_available_balance())
    print(zerodha.get_positions())
    
    