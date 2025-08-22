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

### Wine-Specific Issues (Linux)

1. **"Bad system call" errors (FIXED)**:
   - **Cause**: Docker seccomp profile blocking Wine syscalls
   - **Solution**: Now included in docker-compose.yml: `security_opt: seccomp:./docker/seccomp-wine.json`
   - **Verify**: Run `./scripts/diagnose_mt5_wine.sh` to check

2. **"Wine not found"**:
   - Verify Wine installation: `wine --version`
   - Check Wine architecture: `echo $WINEARCH`
   - Ensure Wine prefix exists: `ls -la /app/.wine`

3. **"MT5 terminal not found"**:
   - Check installation path: `/app/.wine/drive_c/Program Files/MetaTrader 5/`
   - For XM broker: Download installer from https://www.xm.com/fr/mt5
   - Install manually: `wine /path/to/xm-mt5setup.exe /auto`
   - Verify terminal executable exists

4. **"Wine initialization failed"**:
   - Set Wine environment: `export WINEARCH=win64 WINEPREFIX=/app/.wine`
   - Install required components: `winetricks vcrun2019`
   - Check Wine logs: `wine regedit` to test Wine functionality
   - **Critical**: Ensure seccomp profile is active in Docker

5. **"Display issues"**:
   - For headless systems, use virtual display: `export DISPLAY=:99`
   - Start Xvfb if needed: `Xvfb :99 -screen 0 1024x768x24`

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

The MT5 integration supports both Windows and Linux environments:

### Linux Docker Containers (via Wine)

While the MetaTrader5 Python package is Windows-only, you can still use MT5 functionality on Linux through Wine.

**⚠️ IMPORTANT**: Docker seccomp profile fix is now included to prevent "Bad system call" errors.

#### Quick Setup for XM Broker

The main Docker Compose setup now **automatically includes MT5 support** with Wine pre-configured:

```bash
# Build and run with MT5 support (includes seccomp fix)
docker-compose up -d

# The container now includes:
# ✅ Wine 64-bit environment pre-installed
# ✅ Xvfb virtual display for headless operation  
# ✅ Supervisord for service management
# ✅ MT5 ports exposed (1234 for rpyc, 5900 for VNC)
# ✅ Persistent Wine data volumes
# ✅ Docker seccomp profile fix for Wine syscalls

# Complete the MT5 setup for XM broker
docker exec -it algopy_app ./scripts/setup_mt5_wine.sh

# Diagnose any issues
docker exec -it algopy_app ./scripts/diagnose_mt5_wine.sh

# Manage MT5 services
docker exec -it algopy_app supervisorctl status
docker exec -it algopy_app supervisorctl start mt5
```

**For detailed XM broker setup instructions, see [docs/XM_SETUP.md](XM_SETUP.md).**

#### Manual Wine Setup
For local development or custom installations:

```bash
# Install Wine (Ubuntu/Debian)
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install wine wine32 wine64 winetricks

# Run the setup script
./scripts/setup_mt5_wine.sh

# Follow the instructions to configure your environment
```

### Windows Containers/Native
- **Native Support**: Direct MetaTrader5 installation without Wine
- **Full Performance**: No emulation overhead
- **Simple Setup**: `pip install MetaTrader5`

### Environment Configuration

#### Docker Wine Environment (Enhanced Setup)

The Docker container is pre-configured with comprehensive Wine environment based on [community best practices](https://medium.com/@asc686f61/use-mt5-in-linux-with-docker-and-python-f8a9859d65b1):

```bash
# Wine Configuration (automatically set in Docker)
export WINEARCH=win64
export WINEPREFIX=/app/.wine
export DISPLAY=:99
export WINEDLLOVERRIDES="mscoree,mshtml="

# Supervisord Services Available:
# - xvfb: Virtual display server for headless operation
# - mt5: MetaTrader 5 terminal (when configured)
# - streamlit: Main dashboard application
# - jupyter: Notebook server

# Check all services
supervisorctl status

# Start/Stop MT5 terminal
supervisorctl start mt5
supervisorctl stop mt5
supervisorctl restart mt5

# View service logs
supervisorctl tail -f mt5
supervisorctl tail -f xvfb
```

#### Manual Wine Environment

For Wine environments, set these variables:
```bash
export WINEARCH=win64
export WINEPREFIX=/app/.wine  # or ~/.wine_mt5 for local
export DISPLAY=:99  # for headless systems

# Your MT5 credentials
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password  
MT5_SERVER=your_broker_server
MT5_PATH=/app/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe
```

### Running with Wine

To run Python scripts with MT5 support on Linux:

```bash
# Start virtual display (if headless)
Xvfb :99 -screen 0 1024x768x24 &

# Set Wine environment
export WINEARCH=win64 WINEPREFIX=/app/.wine

# Run your Python script through Wine
wine python your_mt5_script.py
```

### Important Notes

- **Python Package**: The MetaTrader5 package must be installed within the Wine environment
- **Terminal Required**: MT5 terminal must be installed and accessible through Wine
- **Display**: Wine applications may require a display server (Xvfb for headless systems)
- **Performance**: Wine adds overhead but allows Linux compatibility
- **Graceful Degradation**: Code handles missing package gracefully when Wine/MT5 isn't available

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