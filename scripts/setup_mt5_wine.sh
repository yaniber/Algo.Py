#!/bin/bash
# MetaTrader5 Wine Setup Script for Linux
# This script sets up Wine environment and installs MT5 for Linux users
# Based on: https://medium.com/@asc686f61/use-mt5-in-linux-with-docker-and-python-f8a9859d65b1

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

# Set up Wine environment variables
export WINEARCH=win64
export WINEPREFIX=${WINEPREFIX:-${HOME}/.wine_mt5}
export DISPLAY=${DISPLAY:-:99}
export WINEDLLOVERRIDES="mscoree,mshtml="

echo "Wine Environment Configuration:"
echo "  WINEARCH: $WINEARCH"
echo "  WINEPREFIX: $WINEPREFIX"
echo "  DISPLAY: $DISPLAY"
echo ""

# Start Xvfb if not running (for headless systems)
if [ "$DISPLAY" = ":99" ] && ! pgrep -f "Xvfb :99" > /dev/null; then
    echo "Starting virtual display (Xvfb)..."
    Xvfb :99 -screen 0 1024x768x24 &
    XVFB_PID=$!
    echo "Xvfb started with PID: $XVFB_PID"
    sleep 2
fi

# Initialize Wine prefix if it doesn't exist
if [ ! -d "${WINEPREFIX}" ]; then
    echo "Creating and initializing Wine prefix..."
    wineboot --init
    echo "Wine prefix created successfully"
else
    echo "Wine prefix already exists at ${WINEPREFIX}"
fi

# Install required Windows components
echo "Installing Windows components via winetricks..."
if command -v winetricks &> /dev/null; then
    echo "Installing vcrun2019 and core fonts..."
    winetricks -q vcrun2019 corefonts || echo "Some components may have failed to install (this is normal)"
else
    echo "winetricks not available - basic Wine functionality will be used"
fi

# Download MT5 installer
MT5_INSTALLER="${HOME}/mt5setup.exe"
if [ ! -f "${MT5_INSTALLER}" ]; then
    echo "Downloading MetaTrader5 installer..."
    # Using a generic MT5 installer URL (users should replace with their broker's)
    wget -O "${MT5_INSTALLER}" "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe" || \
    echo "Could not download MT5 installer. Please download manually from your broker."
fi

# Install MT5 if installer exists
if [ -f "${MT5_INSTALLER}" ]; then
    echo "Installing MetaTrader5..."
    wine "${MT5_INSTALLER}" /auto || echo "MT5 installation completed (exit code may be non-zero)"
    
    # Wait a bit for installation to complete
    sleep 5
    
    # Check if MT5 was installed
    MT5_PATH="${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe"
    if [ -f "${MT5_PATH}" ]; then
        echo "✓ MetaTrader5 installed successfully at: ${MT5_PATH}"
    else
        echo "⚠ MT5 installation may not be complete. Check manually."
        echo "Expected path: ${MT5_PATH}"
    fi
else
    echo "⚠ MT5 installer not found. Skipping installation."
    echo "Please download MT5 installer from your broker and run:"
    echo "  wine /path/to/your/mt5setup.exe /auto"
fi

# Install Python in Wine environment (if needed for MetaTrader5 package)
echo "Checking Python in Wine environment..."
wine python --version 2>/dev/null || {
    echo "Python not found in Wine. You may need to install Python in Wine:"
    echo "  1. Download Python installer for Windows"
    echo "  2. Install: wine python-installer.exe"
    echo "  3. Install MetaTrader5: wine python -m pip install MetaTrader5"
}

# Try to install MetaTrader5 Python package in Wine
echo "Attempting to install MetaTrader5 Python package in Wine..."
wine python -m pip install MetaTrader5 2>/dev/null && \
echo "✓ MetaTrader5 Python package installed in Wine" || \
echo "⚠ Could not install MetaTrader5 package in Wine (Python may not be available)"

# Create comprehensive environment file
ENV_FILE="${HOME}/.env.mt5"
cat > "${ENV_FILE}" << EOF
# MetaTrader5 Wine Configuration
# Copy these settings to your main .env file

# Wine Environment
export WINEARCH=win64
export WINEPREFIX=${WINEPREFIX}
export DISPLAY=:99
export WINEDLLOVERRIDES="mscoree,mshtml="

# MT5 Connection Details (Update with your credentials)
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
MT5_PATH=${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe

# Usage Instructions:
# 1. Source this environment: source ${ENV_FILE}
# 2. Start virtual display: Xvfb :99 -screen 0 1024x768x24 &
# 3. Run MT5 terminal: wine "\${MT5_PATH}"
# 4. Run Python scripts: wine python your_script.py

# For Docker/Supervisord usage:
# The Wine environment is pre-configured in the container
# MT5 can be started automatically via supervisord
EOF

echo ""
echo "🍷 MetaTrader5 Wine setup completed!"
echo ""
echo "📋 Next Steps:"
echo "1. Edit ${ENV_FILE} with your MT5 broker credentials"
echo "2. Source environment: source ${ENV_FILE}"
echo "3. Test Wine setup: wine --version"
echo "4. Test MT5 installation: wine \"${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe\""
echo "5. Test Python integration: wine python -c \"import MetaTrader5; print('MT5 available')\""
echo ""
echo "🐳 Docker Usage:"
echo "The Wine environment is pre-configured in Docker containers."
echo "Use supervisord to manage MT5 terminal automatically."
echo ""
echo "📚 Reference: https://medium.com/@asc686f61/use-mt5-in-linux-with-docker-and-python-f8a9859d65b1"