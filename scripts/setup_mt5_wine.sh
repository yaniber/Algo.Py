#!/bin/bash
# MetaTrader5 Wine Setup Script for Linux
# This script sets up Wine environment and installs MT5 for Linux users
# Based on: https://medium.com/@asc686f61/use-mt5-in-linux-with-docker-and-python-f8a9859d65b1
# Enhanced for XM broker support: https://www.xm.com/fr/mt5

set -e

echo "Setting up MetaTrader5 with Wine for Linux (XM Broker Compatible)..."

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
echo "  Broker: XM (https://www.xm.com/fr/mt5)"
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
    # Create the directory first
    mkdir -p "${WINEPREFIX}"
    # Initialize Wine environment - this may show some warnings but should work with proper seccomp
    echo "Initializing Wine (this may take a few moments and show warnings)..."
    wineboot --init 2>/dev/null || {
        echo "⚠ Wine initialization completed with warnings (this is normal)"
        echo "  If you see 'Bad system call' errors, ensure Docker is running with:"
        echo "  docker-compose --security-opt seccomp:./docker/seccomp-wine.json"
    }
    echo "✓ Wine prefix created successfully"
else
    echo "✓ Wine prefix already exists at ${WINEPREFIX}"
fi

# Install required Windows components
echo "Installing Windows components via winetricks..."
if command -v winetricks &> /dev/null; then
    echo "Installing vcrun2019 and core fonts..."
    winetricks -q vcrun2019 corefonts || echo "Some components may have failed to install (this is normal)"
else
    echo "winetricks not available - basic Wine functionality will be used"
fi

# Download MT5 installer for XM Broker
MT5_INSTALLER="${HOME}/mt5setup.exe"
if [ ! -f "${MT5_INSTALLER}" ]; then
    echo "Downloading XM MetaTrader5 installer..."
    # XM provides their own MT5 installer
    # Users should download from: https://www.xm.com/fr/mt5
    # We'll try the generic installer as fallback, but users should get XM-specific version
    echo "⚠ For XM broker, please download the installer from:"
    echo "  https://www.xm.com/fr/mt5"
    echo ""
    echo "Attempting to download generic MT5 installer as fallback..."
    wget -O "${MT5_INSTALLER}" "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe" 2>/dev/null || {
        echo "❌ Could not download MT5 installer automatically."
        echo ""
        echo "📋 Manual Setup Required:"
        echo "1. Visit https://www.xm.com/fr/mt5"
        echo "2. Download the XM MT5 installer"
        echo "3. Copy it to ${MT5_INSTALLER}"
        echo "4. Run this script again"
        echo ""
        echo "💡 Alternative: Run 'wine /path/to/xm-mt5setup.exe /auto' manually"
    }
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

# Install Python in Wine environment (required for MetaTrader5 package)
echo "Setting up Python in Wine environment..."

# Check if Python is available in Wine
if ! wine python --version 2>/dev/null; then
    echo "Python not found in Wine. Setting up Python environment..."
    
    # Download Python installer for Windows
    PYTHON_INSTALLER="${HOME}/python-3.11.7-amd64.exe"
    if [ ! -f "${PYTHON_INSTALLER}" ]; then
        echo "Downloading Python installer for Windows..."
        wget -O "${PYTHON_INSTALLER}" "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe" || {
            echo "❌ Could not download Python installer"
            echo "Please download Python for Windows manually:"
            echo "  1. Go to https://www.python.org/downloads/windows/"
            echo "  2. Download Python 3.11.x (64-bit)"
            echo "  3. Save as ${PYTHON_INSTALLER}"
            echo "  4. Run: wine ${PYTHON_INSTALLER} /quiet InstallAllUsers=1 PrependPath=1"
            PYTHON_INSTALLER=""
        }
    fi
    
    # Install Python in Wine
    if [ -n "${PYTHON_INSTALLER}" ] && [ -f "${PYTHON_INSTALLER}" ]; then
        echo "Installing Python in Wine environment..."
        wine "${PYTHON_INSTALLER}" /quiet InstallAllUsers=1 PrependPath=1 || {
            echo "⚠ Python installation completed with warnings"
        }
        
        # Wait for installation to complete
        sleep 10
        
        # Verify Python installation
        if wine python --version 2>/dev/null; then
            echo "✓ Python installed successfully in Wine"
        else
            echo "⚠ Python installation may not be complete"
            echo "  Try manual installation: wine ${PYTHON_INSTALLER}"
        fi
    fi
else
    echo "✓ Python already available in Wine"
    wine python --version
fi

# Try to install MetaTrader5 Python package in Wine
echo "Installing MetaTrader5 Python package in Wine..."
if wine python --version 2>/dev/null; then
    # First update pip
    wine python -m pip install --upgrade pip 2>/dev/null || echo "⚠ Could not upgrade pip in Wine"
    
    # Install MetaTrader5 package
    wine python -m pip install MetaTrader5 2>/dev/null && {
        echo "✅ MetaTrader5 Python package installed successfully in Wine"
        # Test the installation
        wine python -c "import MetaTrader5; print('✓ MetaTrader5 package version:', MetaTrader5.__version__)" 2>/dev/null || {
            echo "⚠ MetaTrader5 package installed but import test failed"
        }
    } || {
        echo "❌ Could not install MetaTrader5 package in Wine"
        echo "Manual installation: wine python -m pip install MetaTrader5"
    }
else
    echo "❌ Cannot install MetaTrader5 package - Python not available in Wine"
fi

# Create comprehensive environment file
ENV_FILE="${HOME}/.env.mt5"
cat > "${ENV_FILE}" << EOF
# MetaTrader5 Wine Configuration for XM Broker
# Copy these settings to your main .env file

# Wine Environment
export WINEARCH=win64
export WINEPREFIX=${WINEPREFIX}
export DISPLAY=:99
export WINEDLLOVERRIDES="mscoree,mshtml="

# XM MT5 Connection Details (Update with your XM account credentials)
MT5_LOGIN=your_xm_account_number
MT5_PASSWORD=your_xm_password  
MT5_SERVER=XM-MT5  # or specific XM server like XM-MT5-1, XM-MT5-2, etc.
MT5_PATH=${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe
MT5_BROKER=XM
MT5_BROKER_URL=https://www.xm.com/fr/mt5

# XM Broker Information
# Real accounts: Use the server provided in your XM account email
# Demo accounts: Usually XM-Demo or similar
# To find your server: Check XM member area or contact XM support

# Usage Instructions:
# 1. Get XM account from: https://www.xm.com/fr/mt5
# 2. Update credentials above with your XM account details
# 3. Source this environment: source ${ENV_FILE}
# 4. Start virtual display: Xvfb :99 -screen 0 1024x768x24 &
# 5. Run MT5 terminal: wine "\${MT5_PATH}"
# 6. Connect to XM servers in MT5 terminal
# 7. Run Python scripts: wine python your_mt5_script.py

# For Docker/Supervisord usage:
# The Wine environment is pre-configured in the container
# MT5 can be started automatically via supervisord
# Make sure to use: security_opt: - seccomp:./docker/seccomp-wine.json
EOF

echo ""
echo "🍷 MetaTrader5 Wine setup completed for XM Broker!"
echo ""
echo "📋 Next Steps for XM Integration:"
echo "1. Create XM account at: https://www.xm.com/fr/mt5"
echo "2. Download XM-specific MT5 from XM member area"
echo "3. Edit ${ENV_FILE} with your XM account credentials"
echo "4. Source environment: source ${ENV_FILE}"
echo "5. Test Wine setup: wine --version"
echo "6. Test MT5 installation: wine \"${WINEPREFIX}/drive_c/Program Files/MetaTrader 5/terminal64.exe\""
echo "7. Test Python integration: wine python -c \"import MetaTrader5; print('MT5 available')\""
echo ""
echo "🐳 Docker Usage:"
echo "The Wine environment is pre-configured in Docker containers."
echo "Use supervisord to manage MT5 terminal automatically."
echo "⚠️ IMPORTANT: Use 'security_opt: seccomp:./docker/seccomp-wine.json' to avoid 'Bad system call' errors!"
echo ""
echo "🔧 Troubleshooting:"
echo "- 'Bad system call' errors: Check seccomp profile in docker-compose.yml"
echo "- MT5 not connecting: Verify XM server name in MT5 terminal"
echo "- Python import errors: Ensure MetaTrader5 package is installed in Wine"
echo ""
echo "📚 References:"
echo "- Community guide: https://medium.com/@asc686f61/use-mt5-in-linux-with-docker-and-python-f8a9859d65b1"
echo "- XM Broker: https://www.xm.com/fr/mt5"