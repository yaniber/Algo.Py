import sys
import os
import requests
import time

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger.custom_logger import get_logger

logger = get_logger(__file__)

def get_retry(url: str, headers: dict = None, params: dict = None, rate_limit: int = None, paginate: bool = False, retry_count: int = 3):
    complete_data = []
    current_retry = 0

    while current_retry < retry_count:
        response = requests.get(url, headers=headers, params=params)
        
        # Error in getting data
        if response.status_code != 200:
            print('msg=%s, url=%s, response_status_code=%s', 'Error in getting data from api', url, response.status_code)
            current_retry += 1
            time.sleep(rate_limit * 30)
            continue
        
        data = response.json()
        
        # End of data
        if not data:
            print('No data found')
            break
        
        # Append data
        complete_data.extend(data)
        
        # Need to find a way to paginate for all apis
        if paginate:
            if 'page' in params:
                params['page'] += 1
                current_retry = 0  # Reset retry count for new page
            else:
                break
        else:
            break
        
        # Rate limit
        time.sleep(rate_limit)
    
    if current_retry == retry_count:
        print('msg=%s, url=%s, retry_count=%s', 'Failed to get data from api after retries', url, retry_count)
        raise Exception('Failed to get data from api after retries')
    
    return complete_data
