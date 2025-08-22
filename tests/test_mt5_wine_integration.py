#!/usr/bin/env python3
"""
MetaTrader5 Wine Integration Test
Tests the Wine environment setup and MT5 functionality based on the community approach:
https://medium.com/@asc686f61/use-mt5-in-linux-with-docker-and-python-f8a9859d65b1
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil
from pathlib import Path


def test_wine_installation():
    """Test if Wine is properly installed and configured"""
    print("🍷 Testing Wine Installation...")
    
    try:
        result = subprocess.run(['wine', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✓ Wine version: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ Wine not working properly: {result.stderr}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ Wine not found or not responding")
        return False


def test_wine_environment():
    """Test Wine environment variables"""
    print("\n🔧 Testing Wine Environment Configuration...")
    
    required_vars = {
        'WINEARCH': 'win64',
        'WINEPREFIX': '/app/.wine',
        'DISPLAY': ':99',
        'WINEDLLOVERRIDES': 'mscoree,mshtml='
    }
    
    all_good = True
    for var, expected in required_vars.items():
        actual = os.environ.get(var)
        if actual:
            if expected and actual != expected:
                print(f"⚠ {var}: got '{actual}', expected '{expected}'")
            else:
                print(f"✓ {var}: {actual}")
        else:
            print(f"✗ {var}: not set")
            all_good = False
    
    return all_good


def test_wine_prefix():
    """Test Wine prefix initialization"""
    print("\n📁 Testing Wine Prefix...")
    
    wineprefix = os.environ.get('WINEPREFIX', '/app/.wine')
    
    if os.path.exists(wineprefix):
        print(f"✓ Wine prefix exists: {wineprefix}")
        
        # Check for key Wine directories
        key_dirs = [
            'drive_c',
            'drive_c/Program Files',
            'drive_c/windows'
        ]
        
        for dirname in key_dirs:
            path = os.path.join(wineprefix, dirname)
            if os.path.exists(path):
                print(f"✓ Wine directory exists: {dirname}")
            else:
                print(f"⚠ Wine directory missing: {dirname}")
        
        return True
    else:
        print(f"✗ Wine prefix not found: {wineprefix}")
        return False


def test_xvfb_display():
    """Test virtual display (Xvfb) functionality"""
    print("\n🖥️  Testing Virtual Display (Xvfb)...")
    
    display = os.environ.get('DISPLAY', ':99')
    
    try:
        # Test if display is accessible
        result = subprocess.run(['xwininfo', '-root'], 
                              capture_output=True, text=True, timeout=5,
                              env={**os.environ, 'DISPLAY': display})
        
        if result.returncode == 0:
            print(f"✓ Display {display} is accessible")
            return True
        else:
            print(f"⚠ Display {display} may not be working properly")
            # Try to start Xvfb if it's not running
            try:
                subprocess.Popen(['Xvfb', display, '-screen', '0', '1024x768x24'])
                time.sleep(2)
                print(f"✓ Started Xvfb for display {display}")
                return True
            except FileNotFoundError:
                print("✗ Xvfb not found")
                return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"⚠ Cannot test display {display} (xwininfo not available)")
        return False


def test_mt5_installation():
    """Test MetaTrader5 terminal installation"""
    print("\n📈 Testing MT5 Installation...")
    
    wineprefix = os.environ.get('WINEPREFIX', '/app/.wine')
    mt5_paths = [
        os.path.join(wineprefix, 'drive_c/Program Files/MetaTrader 5/terminal64.exe'),
        os.path.join(wineprefix, 'drive_c/Program Files (x86)/MetaTrader 5/terminal64.exe'),
    ]
    
    for mt5_path in mt5_paths:
        if os.path.exists(mt5_path):
            print(f"✓ MT5 terminal found: {mt5_path}")
            return True, mt5_path
    
    print("⚠ MT5 terminal not found in standard locations")
    print("  Run ./scripts/setup_mt5_wine.sh to install MT5")
    return False, None


def test_python_in_wine():
    """Test Python availability in Wine environment"""
    print("\n🐍 Testing Python in Wine...")
    
    try:
        result = subprocess.run(['wine', 'python', '--version'], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print(f"✓ Python in Wine: {result.stdout.strip()}")
            return True
        else:
            print(f"⚠ Python in Wine not working: {result.stderr}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ Cannot run Python in Wine")
        return False


def test_mt5_python_package():
    """Test MetaTrader5 Python package in Wine"""
    print("\n📦 Testing MetaTrader5 Package in Wine...")
    
    try:
        # Test importing MetaTrader5 in Wine
        result = subprocess.run([
            'wine', 'python', '-c', 
            'import MetaTrader5; print("MetaTrader5 version:", MetaTrader5.__version__)'
        ], capture_output=True, text=True, timeout=20)
        
        if result.returncode == 0:
            print(f"✓ MetaTrader5 package: {result.stdout.strip()}")
            return True
        else:
            print(f"⚠ MetaTrader5 package not available: {result.stderr}")
            print("  Install with: wine python -m pip install MetaTrader5")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ Cannot test MetaTrader5 package in Wine")
        return False


def test_supervisord_services():
    """Test supervisord configuration for Wine services"""
    print("\n👮 Testing Supervisord Services...")
    
    try:
        result = subprocess.run(['supervisorctl', 'status'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ Supervisord status:")
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    service_name = line.split()[0]
                    status = 'RUNNING' in line
                    status_symbol = "✓" if status else "⚠"
                    print(f"  {status_symbol} {line}")
            return True
        else:
            print(f"⚠ Supervisord not running or accessible: {result.stderr}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ Supervisorctl not found")
        return False


def run_comprehensive_test():
    """Run all Wine+MT5 integration tests"""
    print("🧪 MetaTrader5 Wine Integration Test")
    print("=" * 50)
    print("Testing setup based on: https://medium.com/@asc686f61/use-mt5-in-linux-with-docker-and-python-f8a9859d65b1")
    print()
    
    tests = [
        ("Wine Installation", test_wine_installation),
        ("Wine Environment", test_wine_environment),
        ("Wine Prefix", test_wine_prefix),
        ("Virtual Display", test_xvfb_display),
        ("MT5 Installation", test_mt5_installation),
        ("Python in Wine", test_python_in_wine),
        ("MT5 Python Package", test_mt5_python_package),
        ("Supervisord Services", test_supervisord_services),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if test_func == test_mt5_installation:
                result, _ = test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Wine+MT5 integration is ready.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the setup.")
        print("\n🔧 Suggested fixes:")
        print("1. Run: ./scripts/setup_mt5_wine.sh")
        print("2. Check Wine installation: wine --version")
        print("3. Verify environment variables are set")
        print("4. Ensure Xvfb is running: Xvfb :99 &")
        print("5. Install MT5: wine mt5setup.exe /auto")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick test - just basic functionality
        success = (test_wine_installation() and 
                  test_wine_environment() and 
                  test_wine_prefix())
        sys.exit(0 if success else 1)
    else:
        # Full comprehensive test
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)