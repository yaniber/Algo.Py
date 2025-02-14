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
from concurrent.futures import ThreadPoolExecutor
import time


class Telegram(OMS):
    
    def __init__(self, token: str = None, group_id: str = None, error_group_id: str = None):
        super().__init__()
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
        self.error_group_id = error_group_id
    
    def send_telegram_message(self, message, group_id=None):
        if group_id is None:
            group_id = self.group_id

        def send_message():
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {
                'chat_id': group_id,
                'text': message,
                'parse_mode': 'Markdown'
            }

            retries = 5
            backoff = 2  # Initial backoff in seconds

            for attempt in range(retries):
                try:
                    response = requests.post(url, data=payload)
                    response.raise_for_status()
                    response_data = response.json()
                    if not response_data.get('ok'):
                        print(f"Error sending message: {response_data.get('description')}")
                        raise Exception(response_data.get('description'))
                    return response_data  # Success
                except requests.exceptions.HTTPError as err:
                    if response.status_code == 429:  # Too Many Requests
                        print(f"Rate limit hit. Retrying in {backoff} seconds...")
                        time.sleep(backoff)
                        backoff *= 2  # Exponential backoff
                    else:
                        print(f"HTTP error occurred: {err}")
                        break
                except requests.exceptions.RequestException as err:
                    print(f"Error occurred: {err}")
                    break

        # Offload the task to a thread
        self.executor.submit(send_message)
    
    def send_error_message(self, message: str):

        if not self.error_group_id:
            raise UnboundLocalError("Initiate class with valid error group id.")
        self.send_telegram_message(message=message, group_id=self.error_group_id)

    
    def iterate_orders_df(self, orders_df: pd.DataFrame):
        pass 

    def execute(self, fresh_entries, fresh_exits):

        message = (f"fresh_entries : {fresh_entries}\n"
                        f"fresh_exits : {fresh_exits}")
        
        self.send_telegram_message(message)
    