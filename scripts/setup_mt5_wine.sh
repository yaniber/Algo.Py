#!/bin/bash
# MetaTrader5 Wine Setup Script for Linux
# This script sets up Wine environment and installs MT5 for Linux users

set -e

echo "Setting up MetaTrader5 with Wine for Linux..."

# Check if Wine is installed
if ! command -v wine &> /dev/null; then
    echo "Error: Wine is not installed. Please install Wine first:"
    echo "  sudo apt update"
    echo "  sudo dpkg --add-architecture i386"
    echo "  sudo apt install wine wine32 wine64 winetricks"
    exit 1
fi

# Set up Wine environment
export WINEARCH=win64
export WINEPREFIX=${HOME}/.wine_mt5
export DISPLAY=${DISPLAY:-:99}

echo "Initializing Wine environment at ${WINEPREFIX}..."

# Initialize Wine prefix
if [ ! -d "${WINEPREFIX}" ]; then
    echo "Creating Wine prefix..."
    wineboot --init
    echo "Wine prefix created successfully"
fi

# Install required Windows components
echo "Installing Windows components via winetricks (if available)..."
if command -v winetricks &> /dev/null; then
    winetricks -q vcrun2019 corefonts || echo "Some components may have failed to install"
else
    echo "winetricks not available - you may need to install Windows components manually"
    echo "Wine basic functionality should still work for most cases"
fi

# Download MT5 installer if not present
MT5_INSTALLER="${HOME}/mt5setup.exe"
if [ ! -f "${MT5_INSTALLER}" ]; then
    echo "Downloading MetaTrader5 installer..."
    wget -O "${MT5_INSTALLER}" "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
fi

# Install MT5
echo "Installing MetaTrader5..."
if wine "${MT5_INSTALLER}" /auto; then
    echo "MetaTrader5 installed successfully"
else
    echo "MT5 installation may have encountered issues, but this is normal"
fi

# Install MetaTrader5 Python package in Wine environment
echo "Installing MetaTrader5 Python package..."
wine python -m pip install MetaTrader5 || echo "Python package installation may require manual setup"

# Create environment file template
ENV_FILE="${HOME}/.env.mt5"
if [ ! -f "${ENV_FILE}" ]; then
    cat > "${ENV_FILE}" << EOF
# MetaTrader5 Configuration for Wine
# Copy these settings to your main .env file

# Wine environment
export WINEARCH=win64
export WINEPREFIX=${WINEPREFIX}
export DISPLAY=:99

# MT5 Connection Details
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
MT5_PATH=${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe

# To use MetaTrader5 with Wine:
# 1. Source this file: source ~/.env.mt5
# 2. Start Xvfb if needed: Xvfb :99 -screen 0 1024x768x24 &
# 3. Run your Python script with Wine: wine python your_script.py
EOF
    echo "Environment template created at ${ENV_FILE}"
fi

echo ""
echo "MetaTrader5 Wine setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit ${ENV_FILE} with your MT5 credentials"
echo "2. Source the environment: source ${ENV_FILE}"
echo "3. Start virtual display if needed: Xvfb :99 -screen 0 1024x768x24 &"
echo "4. Test installation: wine python -c \"import MetaTrader5; print('MT5 available')\""
echo ""
echo "For Docker usage, the Wine environment is pre-configured."