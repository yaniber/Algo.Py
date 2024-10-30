import os
import requests
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def send_telegram_message(message, token=None, chat_id=None):
    if token is None:
        token = os.getenv('TELEGRAM_TOKEN')
        chat_ids = os.getenv('TELEGRAM_GROUP_ID').split(',')
        print(token , chat_ids)
    
    for chat_id in chat_ids:
        print(chat_id)
        print(type(chat_id))
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
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


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv('config/.env')
    send_telegram_message('Starting Over. *No positions open.*')