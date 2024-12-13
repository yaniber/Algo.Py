import os
import sys
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from OMS.oms import OMS
from jugaad_trader import Zerodha
import pyotp
import json
from dotenv import load_dotenv
import pandas as pd
import requests

class Telegram(OMS):
    
    def __init__(self, token: str = None, group_id: str = None):
        if not token or not group_id:
            load_dotenv(dotenv_path='config/.env')
            self.token = os.getenv('TELEGRAM_TOKEN')
            self.group_id = os.getenv('TELEGRAM_GROUP_ID') 
            if token:
                self.token = token
            if group_id:
                self.group_id = group_id
        else:
            self.token = token
            self.group_id = group_id
    
    def send_telegram_message(self, message: str):

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        payload = {
            'chat_id': self.group_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
            response_data = response.json()
            if not response_data.get('ok'):
                print(f"Error sending message: {response_data.get('description')}")
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
        except requests.exceptions.RequestException as err:
            print(f"Error occurred: {err}")
    
    def iterate_orders_df(self, orders_df: pd.DataFrame):
        pass 
    
    