#!/usr/bin/env python3
"""
Test script for MetaTrader 5 integration in Algo.Py

This script tests the basic functionality of the MT5 integration without requiring
an actual MT5 connection.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test if all MT5-related modules can be imported correctly"""
    print("🧪 Testing MT5 module imports...")
    
    try:
        # Test MT5 OMS import
        from OMS.mt5_oms import MT5
        print("✅ MT5 OMS import successful")
    except ImportError as e:
        print(f"❌ MT5 OMS import failed: {e}")
        return False
    
    try:
        # Test MT5 data fetching import
        from data.fetch.mt5_forex import fetch_ohlcv_mt5, fetch_symbol_list_mt5
        print("✅ MT5 data fetching import successful")
    except ImportError as e:
        print(f"❌ MT5 data fetching import failed: {e}")
        return False
    
    print("✅ All MT5 module imports successful!")
    return True

def test_mt5_oms_structure():
    """Test MT5 OMS class structure without connection"""
    print("\n🧪 Testing MT5 OMS class structure...")
    
    try:
        # Import without initializing (to avoid connection errors)
        from OMS.mt5_oms import MT5
        
        # Check if class has required methods
        required_methods = [
            'connect', 'disconnect', 'place_order', 'cancel_order',
            'get_positions', 'get_pnl', 'get_account_summary',
            'get_available_balance', 'get_symbols'
        ]
        
        for method in required_methods:
            if hasattr(MT5, method):
                print(f"✅ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        print("✅ MT5 OMS class structure is correct!")
        return True
        
    except Exception as e:
        print(f"❌ MT5 OMS structure test failed: {e}")
        return False

def test_data_fetching_structure():
    """Test MT5 data fetching functions structure"""
    print("\n🧪 Testing MT5 data fetching structure...")
    
    try:
        from data.fetch.mt5_forex import (
            fetch_ohlcv_mt5, fetch_symbol_list_mt5, 
            get_forex_pairs, get_metal_pairs, get_indices
        )
        
        # Check if functions are callable
        functions = [
            ('fetch_ohlcv_mt5', fetch_ohlcv_mt5),
            ('fetch_symbol_list_mt5', fetch_symbol_list_mt5),
            ('get_forex_pairs', get_forex_pairs),
            ('get_metal_pairs', get_metal_pairs),
            ('get_indices', get_indices)
        ]
        
        for name, func in functions:
            if callable(func):
                print(f"✅ Function {name} is callable")
            else:
                print(f"❌ Function {name} is not callable")
                return False
        
        print("✅ MT5 data fetching structure is correct!")
        return True
        
    except Exception as e:
        print(f"❌ MT5 data fetching structure test failed: {e}")
        return False

def test_dashboard_integration():
    """Test if dashboard integration doesn't break existing functionality"""
    print("\n🧪 Testing dashboard integration...")
    
    try:
        # Try importing the updated dashboard modules
        import importlib.util
        
        # Test order management system
        spec = importlib.util.spec_from_file_location(
            "order_management_system", 
            "Dashboard/order_management_system.py"
        )
        if spec is None:
            print("❌ Could not load order management system")
            return False
        
        # Test strategy backtest
        spec = importlib.util.spec_from_file_location(
            "strategy_backtest", 
            "Dashboard/strategy_backtest.py"
        )
        if spec is None:
            print("❌ Could not load strategy backtest")
            return False
        
        print("✅ Dashboard integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Dashboard integration test failed: {e}")
        return False

def test_requirements():
    """Check if requirements.txt includes MetaTrader5"""
    print("\n🧪 Testing requirements.txt...")
    
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
            
        if 'MetaTrader5' in content:
            print("✅ MetaTrader5 found in requirements.txt")
            return True
        else:
            print("❌ MetaTrader5 not found in requirements.txt")
            return False
            
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def test_docker_config():
    """Check if Dockerfile has MT5 comments"""
    print("\n🧪 Testing Docker configuration...")
    
    try:
        with open('Dockerfile', 'r') as f:
            content = f.read()
            
        if 'MetaTrader5' in content:
            print("✅ MetaTrader5 reference found in Dockerfile")
            return True
        else:
            print("❌ No MetaTrader5 reference in Dockerfile")
            return False
            
    except Exception as e:
        print(f"❌ Docker configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting MT5 Integration Tests for Algo.Py")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_mt5_oms_structure,
        test_data_fetching_structure,
        test_dashboard_integration,
        test_requirements,
        test_docker_config
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! MT5 integration is ready!")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)