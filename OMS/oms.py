import pandas as pd

class OMS:
    def __init__(self):
        self.orders = pd.DataFrame
        self.successful_orders = []
        self.failed_orders = []
        self.current_balance = int()
        self.execution_queue = []

    def add_to_queue(self, order_details):
        """
        Add a generic order to the execution queue.
        :param order_details: A dictionary with order-specific details (e.g., symbol, r2p score, close price).
        """
        self.execution_queue.append(order_details)
        print(f"Added to queue: {order_details}")

    def get_all_from_queue(self):
        """
        Fetch all entries from the execution queue.
        :return: A list of all queued entries.
        """
        return self.execution_queue
    
    def clear_queue(self):
        """
        Clear the execution queue.
        """
        self.execution_queue = []
        print("Execution queue cleared.")
    
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

    
    
    