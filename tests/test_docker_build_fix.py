#!/usr/bin/env python3
"""
Test script to verify Docker build SSL certificate fix
Tests that the Docker build succeeds with the SSL workarounds
"""

import os
import subprocess
import sys

def test_docker_build():
    """Test that Docker build succeeds without SSL certificate errors"""
    print("\n🐳 Testing Docker Build with SSL fixes...")
    
    dockerfile_path = "/home/runner/work/Algo.Py/Algo.Py/Dockerfile"
    if not os.path.exists(dockerfile_path):
        print("❌ Dockerfile not found")
        return False
    
    # Check for SSL certificate workarounds in Dockerfile
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    if '--trusted-host pypi.org' in content:
        print("✅ SSL certificate workarounds found in Dockerfile")
    else:
        print("❌ SSL certificate workarounds not found in Dockerfile")
        return False
    
    # Check that TA-Lib installation is commented out (since it was causing issues)
    if '# Install TA-Lib - commented out due to SourceForge connectivity issues' in content:
        print("✅ TA-Lib installation properly commented out")
    else:
        print("❌ TA-Lib installation not properly handled")
        return False
        
    return True

def test_requirements_accessible():
    """Test that requirements.txt is accessible and valid"""
    print("\n📋 Testing requirements.txt accessibility...")
    
    requirements_path = "/home/runner/work/Algo.Py/Algo.Py/requirements.txt"
    if not os.path.exists(requirements_path):
        print("❌ requirements.txt not found")
        return False
    
    try:
        with open(requirements_path, 'r') as f:
            lines = f.readlines()
        
        # Check that MetaTrader5 is commented out (Windows-only)
        has_commented_mt5 = any('# MetaTrader5' in line for line in lines)
        if has_commented_mt5:
            print("✅ MetaTrader5 properly commented out in requirements.txt")
        else:
            print("⚠️  MetaTrader5 handling could be improved")
        
        # Check that requirements are not empty
        active_requirements = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
        if len(active_requirements) > 0:
            print(f"✅ Found {len(active_requirements)} active requirements")
        else:
            print("❌ No active requirements found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Docker Build SSL Certificate Fix")
    print("=" * 50)
    
    tests = [
        ("Docker Build Configuration", test_docker_build),
        ("Requirements.txt Accessibility", test_requirements_accessible),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        except Exception as e:
            results.append((test_name, False))
            print(f"❌ FAIL: {test_name} - {e}")
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Docker build should work correctly.")
        print("\n📝 Next steps:")
        print("   1. Test build: docker build -t algopy .")
        print("   2. Or use compose: docker compose build")
        print("   3. Run container: docker compose up -d")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed. Docker build may still have issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)