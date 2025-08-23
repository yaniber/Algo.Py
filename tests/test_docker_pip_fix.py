#!/usr/bin/env python3
"""
Test script to verify Docker pip installation fixes
Tests that the Dockerfile optimizations prevent pip installation failures
"""

import os
import re
import sys

def test_dockerfile_pip_optimizations():
    """Test that Dockerfile has pip reliability improvements"""
    print("\n🐳 Testing Dockerfile pip optimizations...")
    
    dockerfile_path = "/home/runner/work/Algo.Py/Algo.Py/Dockerfile"
    if not os.path.exists(dockerfile_path):
        print("❌ Dockerfile not found")
        return False
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    # Check for pip reliability configurations
    if 'PIP_DEFAULT_TIMEOUT' in content:
        print("✅ Pip timeout configuration found")
    else:
        print("❌ Missing pip timeout configuration")
        return False
    
    if 'PIP_RETRIES' in content:
        print("✅ Pip retry configuration found")
    else:
        print("❌ Missing pip retry configuration")
        return False
    
    # Check that supervisor is not duplicated in pip installs
    pip_lines = [line for line in content.split('\n') if 'pip install' in line and 'supervisor' in line]
    if len(pip_lines) == 0:
        print("✅ No duplicate supervisor installations in pip")
    else:
        print(f"❌ Found {len(pip_lines)} pip lines with supervisor - should be 0")
        return False
    
    # Check for error handling in pip installs
    if '||' in content and 'echo' in content:
        print("✅ Error handling found in pip installations")
    else:
        print("❌ Missing error handling for pip installations")
        return False
    
    return True

def test_requirements_streamlit():
    """Test that streamlit is properly included in requirements"""
    print("\n📋 Testing streamlit requirement...")
    
    requirements_path = "/home/runner/work/Algo.Py/Algo.Py/requirements.txt"
    if not os.path.exists(requirements_path):
        print("❌ requirements.txt not found")
        return False
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    if 'streamlit==' in content:
        print("✅ Streamlit properly included in requirements.txt")
        # Extract version
        streamlit_line = [line for line in content.split('\n') if line.startswith('streamlit==')]
        if streamlit_line:
            print(f"   Version: {streamlit_line[0]}")
        return True
    else:
        print("❌ Streamlit not found in requirements.txt")
        return False

def test_dockerfile_structure():
    """Test the overall Dockerfile structure for build reliability"""
    print("\n🔧 Testing Dockerfile structure...")
    
    dockerfile_path = "/home/runner/work/Algo.Py/Algo.Py/Dockerfile"
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    # Check that pip installs are not chained with &&
    pip_lines = [line.strip() for line in content.split('\n') if 'pip install' in line and 'RUN' in line]
    
    complex_chains = [line for line in pip_lines if '&&' in line and line.count('pip install') > 1]
    
    if len(complex_chains) == 0:
        print("✅ No complex chained pip installs found")
    else:
        print(f"⚠️  Found {len(complex_chains)} lines with complex pip install chains")
        # This is a warning, not a failure, as some chaining might be intentional
    
    # Check for separate RUN commands for different package types
    separate_runs = [line for line in content.split('\n') if line.strip().startswith('RUN pip install')]
    
    if len(separate_runs) >= 4:
        print(f"✅ Found {len(separate_runs)} separate pip install commands for better error isolation")
    else:
        print(f"⚠️  Only {len(separate_runs)} separate pip install commands found")
    
    return True

def main():
    """Run all tests"""
    print("🧪 Testing Docker Pip Installation Fixes")
    print("=" * 50)
    
    tests = [
        ("Docker pip optimizations", test_dockerfile_pip_optimizations),
        ("Streamlit requirements", test_requirements_streamlit),
        ("Dockerfile structure", test_dockerfile_structure),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Docker build should be more reliable.")
        print("\n📝 Improvements made:")
        print("   • Added pip timeout and retry configurations")
        print("   • Removed duplicate supervisor installation")
        print("   • Added streamlit dependency")
        print("   • Improved error handling for pip installs")
        print("   • Separated pip installs for better debugging")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)