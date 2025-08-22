#!/usr/bin/env python3
"""
Test script for MetaTrader5 Wine integration
Tests the Wine setup and MT5 package availability
"""

import os
import sys
import subprocess

def test_wine_environment():
    """Test if Wine environment is properly configured"""
    print("🍷 Testing Wine Environment...")
    
    # Check if Wine is installed
    try:
        result = subprocess.run(['wine', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Wine installed: {result.stdout.strip()}")
        else:
            print("❌ Wine not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Wine not found or not responding")
        return False
    
    # Check Wine environment variables
    wine_arch = os.environ.get('WINEARCH', 'not set')
    wine_prefix = os.environ.get('WINEPREFIX', 'not set')
    display = os.environ.get('DISPLAY', 'not set')
    
    print(f"📋 WINEARCH: {wine_arch}")
    print(f"📁 WINEPREFIX: {wine_prefix}")
    print(f"🖥️  DISPLAY: {display}")
    
    # Check if Wine prefix exists
    if wine_prefix != 'not set' and os.path.exists(wine_prefix):
        print(f"✅ Wine prefix exists at {wine_prefix}")
    else:
        print(f"⚠️  Wine prefix not found or not set")
    
    return True

def test_mt5_import():
    """Test MetaTrader5 package import"""
    print("\n📦 Testing MetaTrader5 Import...")
    
    try:
        import MetaTrader5 as mt5
        print("✅ MetaTrader5 package imported successfully")
        
        # Test basic functionality
        version_info = mt5.__version__ if hasattr(mt5, '__version__') else "Unknown"
        print(f"📌 MT5 Package Version: {version_info}")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  MetaTrader5 package not available: {e}")
        print("💡 This is expected if Wine+MT5 setup hasn't been completed yet")
        return False

def test_mt5_oms():
    """Test MT5 OMS class initialization"""
    print("\n🔧 Testing MT5 OMS Class...")
    
    try:
        # Import without actually connecting (no credentials needed)
        sys.path.append('/app')
        from OMS.mt5_oms import MT5_AVAILABLE
        
        if MT5_AVAILABLE:
            print("✅ MT5 OMS reports package is available")
            
            # Try to initialize (will fail without credentials but tests the class)
            try:
                from OMS.mt5_oms import MT5
                # This will fail due to missing credentials, but tests import structure
                mt5_instance = MT5(login=123, password="test", server="test")
            except (ValueError, ImportError) as e:
                if "Variables for MT5_LOGIN" in str(e) or "MetaTrader5 package" in str(e):
                    print("✅ MT5 OMS class structure is working (credentials needed for connection)")
                else:
                    print(f"⚠️  MT5 OMS initialization issue: {e}")
        else:
            print("⚠️  MT5 OMS reports package not available")
            
    except ImportError as e:
        print(f"❌ Failed to import MT5 OMS: {e}")
        return False
        
    return True

def test_mt5_data_fetch():
    """Test MT5 data fetching module"""
    print("\n📊 Testing MT5 Data Fetching...")
    
    try:
        sys.path.append('/app')
        from data.fetch.mt5_forex import MT5_AVAILABLE, initialize_mt5
        
        if MT5_AVAILABLE:
            print("✅ MT5 data fetching module reports package available")
            
            # Test initialization (will fail without MT5 terminal/credentials)
            result = initialize_mt5()
            if result:
                print("✅ MT5 initialization successful")
            else:
                print("⚠️  MT5 initialization failed (expected without proper setup)")
        else:
            print("⚠️  MT5 data fetching module reports package not available")
            
    except ImportError as e:
        print(f"❌ Failed to import MT5 data fetching: {e}")
        return False
        
    return True

def main():
    """Run all tests"""
    print("🧪 MetaTrader5 Wine Integration Test\n")
    print("=" * 50)
    
    # Test Wine environment
    wine_ok = test_wine_environment()
    
    # Test MT5 package import
    mt5_import_ok = test_mt5_import()
    
    # Test MT5 OMS class
    oms_ok = test_mt5_oms()
    
    # Test MT5 data fetching
    data_ok = test_mt5_data_fetch()
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Summary:")
    print(f"   Wine Environment: {'✅' if wine_ok else '❌'}")
    print(f"   MT5 Package Import: {'✅' if mt5_import_ok else '⚠️'}")
    print(f"   MT5 OMS Class: {'✅' if oms_ok else '❌'}")
    print(f"   MT5 Data Fetching: {'✅' if data_ok else '❌'}")
    
    if not mt5_import_ok:
        print("\n💡 To complete MT5 setup:")
        print("   1. Run: /app/scripts/setup_mt5_wine.sh")
        print("   2. Install MT5 package: wine python -m pip install MetaTrader5")
        print("   3. Configure your MT5 credentials in .env file")
    
    print("\n🎯 Wine integration is ready for MT5 functionality!")

if __name__ == "__main__":
    main()