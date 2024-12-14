import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
from nsepython import nsefetch, nse_eq_symbols
from datetime import datetime, timedelta
from utils.decorators import cache_decorator
import pandas as pd
import requests
from io import StringIO
import time
import cloudscraper

#@cache_decorator(expire=60*60*24*30)
def fetch_symbol_list_gecko_meme():
    url = "https://app.geckoterminal.com/api/p1/solana/pools"
    params = {
        "include": "dex,dex.network,dex.network.network_metric,tokens",
        "page": 1,
        "include_network_metrics": "true",
        "include_meta": "1",
        "volume_24h[gte]": "1000000",
        "pool_creation_hours_ago[lte]": "1200",
        "has_social": "1",
        "sort": "-24h_volume",
        "networks": "solana",
    }
    headers = {
        "User-Agent": "PostmanRuntime/7.42.0",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    scraper = cloudscraper.create_scraper()  # Create a scraper object that bypasses Cloudflare
    scraper.headers.update(headers)  # Update headers for all requests
    
    sol_addresses = []

    while True:
        response = scraper.get(url, params=params)

        if response.status_code == 403:
            print("403 Forbidden: Ensure you are authorized to access the API.")
            break
        elif response.status_code != 200:
            print(f"Error: Unable to fetch data, status code {response.status_code}")
            break

        print(response.text)
        data = response.json()
        print(data)
        pools = data.get("data", [])
        
        for pool in pools:
            attributes = pool.get("attributes", {})
            name = attributes.get("name", "")
            address = attributes.get("address", "")
            if name.lower().endswith("/ sol"):
                sol_addresses.append(address)

        links = data.get("links", {})
        next_page = links.get("next")
        if not next_page:
            break

        params["page"] += 1
        time.sleep(3)

    return sol_addresses


def fetch_ohlcv_data_gecko_meme(address, days=15, resolution="minute", aggregate=5):
    """
    Fetch OHLCV data for a given address over the last `days` with specified resolution and aggregate.

    Parameters:
        address (str): The pool address (e.g., from earlier API call).
        days (int): Number of days of data to fetch.
        resolution (str): Timeframe resolution ("minute", "hour", or "day").
        aggregate (int): Aggregation period (default: 5).
    
    Returns:
        pandas.DataFrame: OHLCV data with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
    """
    base_url = f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{address}/ohlcv/{resolution}"
    headers = {
        "User-Agent": "PostmanRuntime/7.42.0",
        "Accept": "application/json",
    }
    params = {
        "aggregate": aggregate,
        "limit": 1000,  # Max limit per API call
        "currency": "USD",
        "token": "base",
    }

    # Initialize variables for pagination
    current_timestamp = int(datetime.now(datetime.UTC).timestamp())  # Current timestamp in epoch
    start_timestamp = int((datetime.now(datetime.UTC) - timedelta(days=days)).timestamp())
    all_data = []

    while current_timestamp > start_timestamp:
        # Update the `before_timestamp` parameter
        params["before_timestamp"] = current_timestamp

        # Make the API request
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code} - {response.text}")
            break

        # Parse the response
        json_data = response.json()
        ohlcv_data = json_data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
        if not ohlcv_data:  # Break if no more data
            break

        # Append data to the list
        all_data.extend(ohlcv_data)

        # Update `current_timestamp` for pagination (use the earliest timestamp from the fetched data)
        current_timestamp = ohlcv_data[-1][0]

    # Convert to a DataFrame
    data = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume"])

    # Format the timestamp column
    if not data.empty:
        data["timestamp"] = pd.to_datetime(data["timestamp"], unit="s")
        data["timestamp"] = data["timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S')

    return data.sort_values("timestamp")  # Return sorted data