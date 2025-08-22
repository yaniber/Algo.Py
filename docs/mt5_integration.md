# MetaTrader 5 Integration Guide

This guide explains how to set up and use MetaTrader 5 (MT5) with the Algo.Py trading framework.

## Overview

The MT5 integration allows you to:
- Connect to MT5 brokerage accounts via the dashboard UI
- Load available trading pairs (Forex, CFDs, Metals)
- Import historical data for strategy development and backtesting
- Execute trades directly from Algo.Py strategies
- Monitor positions and account balance in real-time

## Prerequisites

### 1. MetaTrader 5 Terminal
- Download and install MetaTrader 5 from your broker
- Ensure you have a working trading account with your broker
- The MT5 terminal should be running when using Algo.Py

### 2. Python Package
The `MetaTrader5` Python package is automatically installed via requirements.txt:

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Environment Variables
Add your MT5 credentials to `config/.env`:

```env
# METATRADER 5 DETAILS
MT5_LOGIN=12345678        # Your MT5 account number
MT5_PASSWORD=your_password # Your MT5 password
MT5_SERVER=your_broker     # Your broker's server (e.g., "MetaQuotes-Demo")
MT5_PATH=/path/to/mt5      # Optional: Path to MT5 terminal executable
```

### 2. Account Setup
- Ensure your MT5 account has trading permissions enabled
- Verify that algorithmic trading is allowed in your MT5 terminal:
  - Tools → Options → Expert Advisors
  - Check "Allow algorithmic trading"

## Using MT5 in Dashboard

### 1. Order Management System
1. Navigate to the Order Management System page
2. Select "MetaTrader 5" from the Exchange dropdown
3. Choose your market type:
   - **Forex**: Major and minor currency pairs
   - **CFDs**: Stock indices and commodities
   - **Metals**: Precious metals like Gold, Silver

### 2. Placing Orders
- Enter symbol (e.g., EURUSD, XAUUSD, US30)
- Select order type (Market or Limit)
- Specify volume in lots
- Click "Place MT5 Order"

### 3. Account Monitoring
- View account balance and equity
- Monitor open positions
- Check recent order history

## Backtesting with MT5 Data

### 1. Asset Selection
1. Go to the Strategy Backtester page
2. Select your timeframe
3. In the Asset Universe section, use the new MT5 tabs:
   - **MT5 Forex**: Major pairs, all forex pairs
   - **MT5 Metals**: Precious metals and indices

### 2. Historical Data
The system automatically fetches historical data from your MT5 terminal for backtesting.

## Supported Markets

### Forex Pairs
- **Major Pairs**: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD
- **Minor Pairs**: EURGBP, EURJPY, GBPJPY, CHFJPY, etc.
- **Exotic Pairs**: Depending on your broker

### Metals & Commodities
- **Precious Metals**: XAUUSD (Gold), XAGUSD (Silver), XPTUSD (Platinum), XPDUSD (Palladium)
- **Energy**: Crude Oil, Natural Gas (broker-dependent)

### Indices (CFDs)
- **US**: US30 (Dow Jones), SPX500 (S&P 500), NAS100 (NASDAQ)
- **European**: GER30 (DAX), UK100 (FTSE), FRA40 (CAC)
- **Asian**: JPN225 (Nikkei), HK50 (Hang Seng)

## Timeframes Supported

- 1 minute (1m)
- 5 minutes (5m)
- 15 minutes (15m)
- 30 minutes (30m)
- 1 hour (1h)
- 4 hours (4h)
- 1 day (1d)
- 1 week (1w)
- 1 month (1M)

## Troubleshooting

### Connection Issues
1. **"Not connected to MT5"**: 
   - Ensure MT5 terminal is running
   - Check credentials in config/.env
   - Verify server name is correct

2. **"Failed to initialize MT5"**:
   - Make sure MetaTrader5 Python package is installed
   - Check if MT5_PATH is correct (if specified)
   - Try running without MT5_PATH first

3. **"Symbol not found"**:
   - Verify symbol name with your broker
   - Check if symbol is visible in Market Watch
   - Some symbols may not be available in your account type

### Order Execution Issues
1. **"Insufficient margin"**: 
   - Check account balance
   - Reduce position size
   - Verify leverage settings

2. **"Market is closed"**: 
   - Check trading hours for the instrument
   - Some instruments have limited trading hours

3. **"Invalid volume"**:
   - Check minimum/maximum volume for the symbol
   - Ensure volume is in correct increments (usually 0.01 lots)

### Data Issues
1. **"No data retrieved"**: 
   - Check if symbol exists and is subscribed
   - Verify date range is reasonable
   - Some symbols may have limited historical data

2. **"Failed to get symbols"**:
   - Refresh Market Watch in MT5 terminal
   - Check connection to broker server

## Docker Deployment

The MT5 integration works in Docker environments. The Python MetaTrader5 package is installed automatically, but note that:

- You don't need to install the MT5 terminal in Docker
- The MT5 connection will work through the API if you have MT5 running on the host
- For production deployments, consider running MT5 on a separate Windows server

## Code Examples

### Basic MT5 Connection
```python
from OMS.mt5_oms import MT5

# Initialize MT5 connection
mt5_oms = MT5()

# Check connection
if mt5_oms.connected:
    print("Connected to MT5")
    
    # Get account info
    account = mt5_oms.get_account_info()
    print(f"Balance: {account['balance']}")
    
    # Place a buy order
    success = mt5_oms.place_order(
        symbol="EURUSD",
        side="BUY", 
        size=0.1,  # 0.1 lots
        order_type="MARKET"
    )
```

### Fetching Historical Data
```python
from data.fetch.mt5_forex import fetch_ohlcv_mt5
from datetime import datetime, timedelta

# Get last 30 days of EURUSD hourly data
start_date = datetime.now() - timedelta(days=30)
df = fetch_ohlcv_mt5("EURUSD", "1h", start_date)

print(f"Retrieved {len(df)} candlesticks")
print(df.head())
```

## Best Practices

1. **Connection Management**: Always check if MT5 is connected before placing orders
2. **Error Handling**: Implement proper error handling for network issues
3. **Position Sizing**: Calculate position sizes based on account balance and risk
4. **Symbol Validation**: Verify symbols exist before using in strategies
5. **Testing**: Test strategies with small positions first

## Support

For MT5-specific issues:
1. Check the official MetaTrader 5 Python documentation
2. Verify with your broker that API access is enabled
3. Test connection using the provided test script: `python tests/test_mt5_integration.py`

For Algo.Py integration questions, refer to the main documentation or community forums.