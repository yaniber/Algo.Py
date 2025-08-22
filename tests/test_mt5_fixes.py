#!/usr/bin/env python3
"""
Quick test for MT5 Wine fixes
Tests the key improvements made to address "Bad system call" and other Wine issues
"""

import os
import json
import sys

def test_seccomp_profile():
    """Test if seccomp profile exists and is valid"""
    print("🔐 Testing Seccomp Profile...")
    
    seccomp_path = "/home/runner/work/Algo.Py/Algo.Py/docker/seccomp-wine.json"
    if os.path.exists(seccomp_path):
        print(f"✅ Seccomp profile found: {seccomp_path}")
        
        # Validate JSON
        try:
            with open(seccomp_path, 'r') as f:
                profile = json.load(f)
            
            # Check key components
            if 'syscalls' in profile and 'defaultAction' in profile:
                print("✅ Seccomp profile structure valid")
                
                # Count allowed syscalls
                syscall_count = 0
                for syscall_group in profile.get('syscalls', []):
                    if 'names' in syscall_group:
                        syscall_count += len(syscall_group['names'])
                
                print(f"✅ Profile allows {syscall_count} syscalls (should fix 'Bad system call' errors)")
                return True
            else:
                print("❌ Seccomp profile missing required fields")
                return False
        except json.JSONDecodeError:
            print("❌ Seccomp profile is not valid JSON")
            return False
    else:
        print(f"❌ Seccomp profile missing: {seccomp_path}")
        return False

def test_docker_compose_config():
    """Test if docker-compose.yml has the seccomp fix"""
    print("\n🐳 Testing Docker Compose Configuration...")
    
    compose_path = "/home/runner/work/Algo.Py/Algo.Py/docker-compose.yml"
    if os.path.exists(compose_path):
        print(f"✅ Docker Compose file found: {compose_path}")
        
        with open(compose_path, 'r') as f:
            content = f.read()
        
        # Check for seccomp configuration
        if 'seccomp:./docker/seccomp-wine.json' in content:
            print("✅ Seccomp profile configured in docker-compose.yml")
            return True
        else:
            print("❌ Seccomp profile NOT configured in docker-compose.yml")
            print("   This will cause 'Bad system call' errors!")
            return False
    else:
        print(f"❌ Docker Compose file missing: {compose_path}")
        return False

def test_setup_script_enhancements():
    """Test if setup script has the XM and Python improvements"""
    print("\n📜 Testing Setup Script Enhancements...")
    
    script_path = "/home/runner/work/Algo.Py/Algo.Py/scripts/setup_mt5_wine.sh"
    if os.path.exists(script_path):
        print(f"✅ Setup script found: {script_path}")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Check for key improvements
        improvements = [
            ("XM broker support", "xm.com" in content.lower() or "XM" in content),
            ("Python installer handling", "python-3.11" in content or "python installer" in content.lower()),
            ("Enhanced error handling", "Bad system call" in content),
            ("MetaTrader5 package installation", "MetaTrader5" in content),
            ("Environment file generation", ".env.mt5" in content)
        ]
        
        all_good = True
        for improvement, check in improvements:
            if check:
                print(f"✅ {improvement} - implemented")
            else:
                print(f"⚠️  {improvement} - missing")
                all_good = False
        
        return all_good
    else:
        print(f"❌ Setup script missing: {script_path}")
        return False

def test_dockerfile_changes():
    """Test if Dockerfile has been fixed (no build-time Wine init)"""
    print("\n🏗️  Testing Dockerfile Changes...")
    
    dockerfile_path = "/home/runner/work/Algo.Py/Algo.Py/Dockerfile"
    if os.path.exists(dockerfile_path):
        print(f"✅ Dockerfile found: {dockerfile_path}")
        
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check that problematic build-time Wine initialization is removed
        if 'wineboot --init' not in content:
            print("✅ Build-time Wine initialization removed (prevents build errors)")
            return True
        else:
            print("❌ Build-time Wine initialization still present (may cause build errors)")
            return False
    else:
        print(f"❌ Dockerfile missing: {dockerfile_path}")
        return False

def test_documentation():
    """Test if documentation has been updated"""
    print("\n📚 Testing Documentation Updates...")
    
    # Check XM setup guide
    xm_guide_path = "/home/runner/work/Algo.Py/Algo.Py/docs/XM_SETUP.md"
    xm_guide_exists = os.path.exists(xm_guide_path)
    
    # Check updated integration docs
    integration_path = "/home/runner/work/Algo.Py/Algo.Py/docs/mt5_integration.md"
    integration_updated = False
    if os.path.exists(integration_path):
        with open(integration_path, 'r') as f:
            content = f.read()
        integration_updated = "Bad system call" in content and "seccomp" in content.lower()
    
    # Check diagnostic script
    diag_script_path = "/home/runner/work/Algo.Py/Algo.Py/scripts/diagnose_mt5_wine.sh"
    diag_script_exists = os.path.exists(diag_script_path) and os.access(diag_script_path, os.X_OK)
    
    if xm_guide_exists:
        print("✅ XM setup guide created")
    else:
        print("❌ XM setup guide missing")
    
    if integration_updated:
        print("✅ Integration docs updated with fixes")
    else:
        print("❌ Integration docs not updated")
    
    if diag_script_exists:
        print("✅ Diagnostic script created and executable")
    else:
        print("❌ Diagnostic script missing or not executable")
    
    return xm_guide_exists and integration_updated and diag_script_exists

def main():
    """Run all tests and provide summary"""
    print("🧪 Testing MT5 Wine Integration Fixes")
    print("=" * 50)
    
    tests = [
        ("Seccomp Profile", test_seccomp_profile),
        ("Docker Compose Config", test_docker_compose_config),
        ("Setup Script Enhancements", test_setup_script_enhancements),
        ("Dockerfile Changes", test_dockerfile_changes),
        ("Documentation Updates", test_documentation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
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
        print("\n🎉 All fixes implemented successfully!")
        print("\n📝 Next steps:")
        print("   1. Test with: docker-compose up -d")
        print("   2. Run setup: docker exec -it algopy_app ./scripts/setup_mt5_wine.sh")
        print("   3. Diagnose: docker exec -it algopy_app ./scripts/diagnose_mt5_wine.sh")
        print("   4. See docs/XM_SETUP.md for detailed XM broker setup")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())