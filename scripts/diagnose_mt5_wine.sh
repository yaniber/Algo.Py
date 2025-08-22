#!/bin/bash
# Enhanced MT5 Wine Diagnostics Script
# This script diagnoses common issues with MT5 Wine setup in Docker

echo "🔍 MetaTrader5 Wine Diagnostics"
echo "=" * 50

# Test 1: Check Docker seccomp configuration
echo "1. Checking Docker Seccomp Configuration..."
if [ -f "./docker/seccomp-wine.json" ]; then
    echo "✅ Seccomp profile found: ./docker/seccomp-wine.json"
else
    echo "❌ Missing seccomp profile: ./docker/seccomp-wine.json"
    echo "   This is likely causing 'Bad system call' errors!"
fi

# Test 2: Check Wine installation
echo ""
echo "2. Testing Wine Installation..."
if command -v wine &> /dev/null; then
    wine_version=$(wine --version 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ Wine version: $wine_version"
    else
        echo "❌ Wine installed but not responding (possible seccomp issue)"
        echo "   Try: export WINEDEBUG=-all; wine --version"
    fi
else
    echo "❌ Wine not installed"
fi

# Test 3: Check environment variables
echo ""
echo "3. Checking Wine Environment Variables..."
required_vars=("WINEARCH" "WINEPREFIX" "DISPLAY" "WINEDLLOVERRIDES")
for var in "${required_vars[@]}"; do
    value="${!var}"
    if [ -n "$value" ]; then
        echo "✅ $var=$value"
    else
        echo "❌ $var not set"
    fi
done

# Test 4: Check Wine prefix
echo ""
echo "4. Checking Wine Prefix..."
WINEPREFIX=${WINEPREFIX:-/app/.wine}
if [ -d "$WINEPREFIX" ]; then
    echo "✅ Wine prefix exists: $WINEPREFIX"
    
    # Check key directories
    if [ -d "$WINEPREFIX/drive_c" ]; then
        echo "✅ Drive C exists"
    else
        echo "❌ Drive C missing - Wine not initialized"
    fi
    
    if [ -d "$WINEPREFIX/drive_c/windows" ]; then
        echo "✅ Windows directory exists"
    else
        echo "⚠️  Windows directory missing"
    fi
else
    echo "❌ Wine prefix missing: $WINEPREFIX"
    echo "   Run: wineboot --init"
fi

# Test 5: Check Xvfb display
echo ""
echo "5. Testing Virtual Display..."
DISPLAY=${DISPLAY:-:99}
if pgrep -f "Xvfb $DISPLAY" > /dev/null; then
    echo "✅ Xvfb running on $DISPLAY"
else
    echo "⚠️  Xvfb not running on $DISPLAY"
    echo "   Start with: Xvfb $DISPLAY -screen 0 1024x768x24 &"
fi

# Test 6: Test Wine functionality
echo ""
echo "6. Testing Wine Functionality..."
if command -v wine &> /dev/null; then
    # Test basic Wine command
    if wine cmd /c echo "Wine test" 2>/dev/null | grep -q "Wine test"; then
        echo "✅ Basic Wine functionality works"
    else
        echo "❌ Wine functionality test failed"
        echo "   This suggests seccomp or initialization issues"
    fi
fi

# Test 7: Check Python in Wine
echo ""
echo "7. Testing Python in Wine..."
if wine python --version 2>/dev/null; then
    python_version=$(wine python --version 2>/dev/null)
    echo "✅ Python in Wine: $python_version"
    
    # Test MetaTrader5 package
    if wine python -c "import MetaTrader5" 2>/dev/null; then
        mt5_version=$(wine python -c "import MetaTrader5; print(MetaTrader5.__version__)" 2>/dev/null)
        echo "✅ MetaTrader5 package: $mt5_version"
    else
        echo "⚠️  MetaTrader5 package not installed in Wine"
        echo "   Install with: wine python -m pip install MetaTrader5"
    fi
else
    echo "❌ Python not available in Wine"
    echo "   Install Python for Windows in Wine environment"
fi

# Test 8: Check MT5 installation
echo ""
echo "8. Checking MT5 Installation..."
WINEPREFIX=${WINEPREFIX:-/app/.wine}
mt5_paths=(
    "$WINEPREFIX/drive_c/Program Files/MetaTrader 5/terminal64.exe"
    "$WINEPREFIX/drive_c/Program Files (x86)/MetaTrader 5/terminal64.exe"
)

mt5_found=false
for path in "${mt5_paths[@]}"; do
    if [ -f "$path" ]; then
        echo "✅ MT5 terminal found: $path"
        mt5_found=true
        break
    fi
done

if [ "$mt5_found" = false ]; then
    echo "⚠️  MT5 terminal not found"
    echo "   Download XM MT5 from: https://www.xm.com/fr/mt5"
    echo "   Install with: wine /path/to/xm-mt5setup.exe /auto"
fi

# Test 9: Check supervisord services
echo ""
echo "9. Checking Supervisord Services..."
if command -v supervisorctl &> /dev/null; then
    echo "✅ Supervisorctl available"
    supervisorctl status 2>/dev/null | while IFS= read -r line; do
        if echo "$line" | grep -q "RUNNING"; then
            echo "✅ $line"
        else
            echo "⚠️  $line"
        fi
    done
else
    echo "⚠️  Supervisorctl not available (normal outside Docker)"
fi

# Summary and recommendations
echo ""
echo "=" * 50
echo "📋 Diagnostic Summary"
echo ""

# Count issues
issues=0

if [ ! -f "./docker/seccomp-wine.json" ]; then
    ((issues++))
    echo "🔧 CRITICAL: Add seccomp profile to fix 'Bad system call' errors"
fi

if ! command -v wine &> /dev/null || ! wine --version 2>/dev/null >/dev/null; then
    ((issues++))
    echo "🔧 CRITICAL: Fix Wine installation/configuration"
fi

if [ ! -d "${WINEPREFIX:-/app/.wine}/drive_c" ]; then
    ((issues++))
    echo "🔧 HIGH: Initialize Wine environment with 'wineboot --init'"
fi

if ! wine python --version 2>/dev/null >/dev/null; then
    ((issues++))
    echo "🔧 MEDIUM: Install Python in Wine environment"
fi

if [ "$mt5_found" = false ]; then
    ((issues++))
    echo "🔧 MEDIUM: Install XM MT5 terminal"
fi

if [ $issues -eq 0 ]; then
    echo "🎉 No critical issues found! MT5 Wine setup looks good."
    echo ""
    echo "📝 Next steps:"
    echo "   1. Configure XM account credentials in ~/.env.mt5"
    echo "   2. Test MT5 connection: supervisorctl start mt5"
    echo "   3. Run your trading scripts with Wine"
else
    echo "⚠️  Found $issues issue(s) that need attention."
    echo ""
    echo "🚀 Quick fix commands:"
    echo "   1. docker-compose down"
    echo "   2. Ensure seccomp profile exists: ls docker/seccomp-wine.json" 
    echo "   3. docker-compose up -d"
    echo "   4. docker exec -it algopy_app ./scripts/setup_mt5_wine.sh"
fi

echo ""
echo "📚 For detailed setup instructions, see:"
echo "   - docs/XM_SETUP.md"
echo "   - https://www.xm.com/fr/mt5"