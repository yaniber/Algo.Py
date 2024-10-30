import pandas as pd

class OMS:
    def __init__(self):
        self.orders = pd.DataFrame
        self.successful_orders = []
        self.failed_orders = []
        self.current_balance = int()


    
    def iterate_orders_df(self, orders_df: pd.DataFrame):
        pass 
    
    def place_order(self, order_type: str, symbol: str, quantity: int, price: float):
        pass 
    
    def cancel_order(self, order_id: str):
        pass 
    
    def get_positions(self):
        pass 
    
    def get_pnl(self):
        pass 
    
    def get_account_summary(self):
        pass 

    def get_available_balance(self):
        pass 

    
    
    