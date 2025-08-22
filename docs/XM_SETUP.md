# MetaTrader 5 XM Broker Integration Guide

## Quick Setup for XM Broker

This guide helps you set up MetaTrader 5 with XM broker in Docker using Wine on Linux.

### Prerequisites

1. **XM Account**: Create account at [XM.com](https://www.xm.com/fr/mt5)
2. **Docker**: Ensure Docker and Docker Compose are installed
3. **Account Details**: Have your XM login credentials ready

### Step 1: Fix Docker Seccomp (Critical!)

The main issue causing "Bad system call" errors is Docker's security profile blocking Wine syscalls.

**Solution**: The `docker-compose.yml` now includes:
```yaml
security_opt:
  - seccomp:./docker/seccomp-wine.json
```

This allows Wine to function properly in Docker containers.

### Step 2: Build and Start Container

```bash
# Build with MT5 support
docker-compose up -d

# Verify container is running
docker exec -it algopy_app supervisorctl status
```

### Step 3: Setup MT5 for XM

```bash
# Run the enhanced setup script
docker exec -it algopy_app ./scripts/setup_mt5_wine.sh

# The script will:
# ✅ Initialize Wine environment (no more "Bad system call" errors)
# ✅ Install Python in Wine
# ✅ Install MetaTrader5 Python package
# ✅ Prepare XM-specific configuration
```

### Step 4: Install XM MT5 Terminal

Since each broker has specific MT5 versions, download from XM:

```bash
# Option 1: Download XM MT5 manually
# 1. Visit https://www.xm.com/fr/mt5
# 2. Download the installer
# 3. Copy to container:
docker cp /path/to/xm-mt5setup.exe algopy_app:/tmp/mt5setup.exe

# Option 2: Install manually in container
docker exec -it algopy_app wine /tmp/mt5setup.exe /auto
```

### Step 5: Configure XM Connection

Edit your configuration:
```bash
# Edit the generated environment file
docker exec -it algopy_app nano ~/.env.mt5
```

Update with your XM account details:
```bash
# XM MT5 Connection Details
MT5_LOGIN=your_xm_account_number
MT5_PASSWORD=your_xm_password  
MT5_SERVER=XM-Demo  # or XM-MT5-1, XM-MT5-2, etc.
```

**XM Server Names:**
- Demo accounts: `XM-Demo` 
- Real accounts: `XM-MT5-1`, `XM-MT5-2`, etc. (check your XM account email)

### Step 6: Test the Setup

```bash
# Test Wine and MT5 integration
docker exec -it algopy_app python tests/test_mt5_wine_integration.py

# Test Python MetaTrader5 package
docker exec -it algopy_app wine python -c "import MetaTrader5; print('MT5 Ready!')"

# Start MT5 terminal (optional)
docker exec -it algopy_app supervisorctl start mt5
```

## Troubleshooting

### "Bad system call" Errors
- **Cause**: Docker seccomp profile blocking Wine syscalls
- **Fix**: Ensure `security_opt: seccomp:./docker/seccomp-wine.json` in docker-compose.yml

### MT5 Terminal Not Found
- **Cause**: XM-specific installer needed
- **Fix**: Download MT5 installer from XM member area, not generic

### Python Package Import Errors
- **Cause**: MetaTrader5 package not installed in Wine
- **Fix**: Run `docker exec -it algopy_app wine python -m pip install MetaTrader5`

### Connection to XM Servers Failed
- **Cause**: Wrong server name or credentials
- **Fix**: Check XM account email for correct server name

## XM Broker Specifics

### Account Types
- **Demo Account**: Server usually `XM-Demo`
- **Real Account**: Server like `XM-MT5-1`, `XM-MT5-2` (varies by region)

### Getting Server Information
1. Log into XM member area
2. Go to "My Accounts" → "MT5 Accounts"
3. Find your server name and account details
4. Or contact XM support for server information

### XM Resources
- **Main Site**: https://www.xm.com/fr/mt5
- **Support**: Available in XM member area
- **Documentation**: Available after account creation

## File Structure

```
├── docker/
│   └── seccomp-wine.json          # Fixed seccomp profile for Wine
├── scripts/
│   └── setup_mt5_wine.sh          # Enhanced setup script
├── docker-compose.yml             # Updated with seccomp fix
├── Dockerfile                     # Streamlined Wine setup
└── docs/
    └── XM_SETUP.md                # This file
```

## Integration with Algo.Py

Once setup is complete, use MT5 in your Python scripts:

```python
# Your algo.py strategies can now use:
from OMS.mt5_oms import MT5OrderManagementSystem

# Initialize with XM connection
mt5_oms = MT5OrderManagementSystem(
    login=your_xm_account,
    password=your_xm_password,
    server="XM-Demo"  # or your XM server
)
```

The MT5 integration will handle Wine environment automatically when running in Docker.