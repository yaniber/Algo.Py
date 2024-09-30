from utils.db.fetch import fetch_latest_date
import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

latest_date = fetch_latest_date(market_name='indian_equity', timeframe='1d')
print(latest_date)