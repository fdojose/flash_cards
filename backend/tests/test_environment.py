#!/usr/bin/env python3
"""
PHASE 8.1: UNIT TESTS - Simple Test Configuration
=================================================

Simplified test setup that validates test environment
and runs basic functionality tests without complex imports.
"""

import os
import sys
import json
from datetime import datetime
from uuid import uuid4

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

def test_python_environment():
    """Test Python environment setup"""
    print("🔧 Testing Python Environment")
    
    # Check Python version
    python_version = sys.version_info
    assert python_version >= (3, 8), f"Python 3.8+ required, got {python_version}"
    print(f"   ✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check required modules can be imported
    required_modules = [
        "json", "datetime", "uuid", "os", "sys"
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module} module available")
        except ImportError:
            assert False, f"Required module {module} not available"
    
    print("   ✅ Python environment ready")
    return True

def test_basic_data_structures():
    """Test basic data structure handling"""
    print("📊 Testing Basic Data Structures")
    
    # Test UUID generation
    test_uuid = str(uuid4())
    assert len(test_uuid) == 36
    assert test_uuid.count('-') == 4
    print(f"   ✅ UUID generation: {test_uuid}")
    
    # Test datetime handling
    now = datetime.utcnow()
    assert isinstance(now, datetime)
    print(f"   ✅ Datetime handling: {now}")
    
    # Test JSON serialization
    test_data = {
        "id": test_uuid,
        "name": "Test Data",
        "timestamp": now.isoformat(),
        "items": ["item1", "item2", "item3"]
    }
    
    json_str = json.dumps(test_data, default=str)
    parsed_data = json.loads(json_str)
    
    assert parsed_data["id"] == test_uuid
    assert parsed_data["name"] == "Test Data"
    assert len(parsed_data["items"]) == 3
    print("   ✅ JSON serialization/deserialization")
    
    print("   ✅ Basic data structures working")
    return True

def test_file_system_access():
    """Test file system access for test artifacts"""
    print("📁 Testing File System Access")
    
    # Test read access to backend directory
    assert os.path.exists(backend_dir)
    assert os.path.isdir(backend_dir)
    print(f"   ✅ Backend directory accessible: {backend_dir}")
    
    # Test write access for test results
    test_dir = os.path.join(backend_dir, "tests")
    os.makedirs(test_dir, exist_ok=True)
    assert os.path.exists(test_dir)
    print(f"   ✅ Test directory accessible: {test_dir}")
    
    # Test temporary file creation
    temp_file = os.path.join(test_dir, "test_temp.txt")
    with open(temp_file, 'w') as f:
        f.write("Test file content")
    
    assert os.path.exists(temp_file)
    
    with open(temp_file, 'r') as f:
        content = f.read()
    assert content == "Test file content"
    
    # Clean up
    os.remove(temp_file)
    print("   ✅ File creation and cleanup")
    
    print("   ✅ File system access working")
    return True

def test_imports_availability():
    """Test which imports are available"""
    print("📦 Testing Import Availability")
    
    # Test standard library imports
    standard_imports = [
        ("os", "Operating system interface"),
        ("sys", "System-specific parameters"),
        ("json", "JSON encoder/decoder"),
        ("datetime", "Date and time handling"),
        ("uuid", "UUID generation"),
        ("pathlib", "Object-oriented filesystem paths")
    ]
    
    for module, description in standard_imports:
        try:
            __import__(module)
            print(f"   ✅ {module}: {description}")
        except ImportError:
            print(f"   ❌ {module}: {description} - NOT AVAILABLE")
    
    # Test optional testing imports
    testing_imports = [
        ("pytest", "Testing framework"),
        ("httpx", "HTTP client for testing"),
        ("sqlalchemy", "Database toolkit"),
        ("fastapi", "Web framework")
    ]
    
    available_testing = []
    for module, description in testing_imports:
        try:
            __import__(module)
            print(f"   ✅ {module}: {description}")
            available_testing.append(module)
        except ImportError:
            print(f"   ⚠️  {module}: {description} - Not available")
    
    print(f"   📊 Testing modules available: {len(available_testing)}/{len(testing_imports)}")
    
    # Test app imports
    app_imports = [
        ("app.database", "Database configuration"),
        ("app.auth.models", "Authentication models"),
        ("app.datasets.models", "Dataset models"),
        ("app.sessions.models", "Session models"),
        ("main", "FastAPI application")
    ]
    
    available_app = []
    for module, description in app_imports:
        try:
            __import__(module)
            print(f"   ✅ {module}: {description}")
            available_app.append(module)
        except ImportError as e:
            print(f"   ⚠️  {module}: {description} - {e}")
    
    print(f"   📊 App modules available: {len(available_app)}/{len(app_imports)}")
    
    if len(available_app) == len(app_imports):
        print("   🎉 Full application environment available!")
        return "full"
    elif len(available_testing) >= 2:
        print("   ⚡ Partial testing environment available")
        return "partial"
    else:
        print("   🔧 Basic testing environment only")
        return "basic"

def test_configuration_files():
    """Test configuration file presence"""
    print("⚙️  Testing Configuration Files")
    
    config_files = [
        ("requirements.txt", "Python dependencies"),
        ("requirements-test.txt", "Testing dependencies"),
        (".env.example", "Environment template"),
        ("pytest.ini", "Pytest configuration"),
        ("Dockerfile", "Container configuration")
    ]
    
    found_configs = 0
    for filename, description in config_files:
        file_path = os.path.join(backend_dir, filename)
        if os.path.exists(file_path):
            print(f"   ✅ {filename}: {description}")
            found_configs += 1
        else:
            print(f"   ⚠️  {filename}: {description} - Not found")
    
    print(f"   📊 Configuration files: {found_configs}/{len(config_files)}")
    
    # Check if tests directory exists
    tests_dir = os.path.join(backend_dir, "tests")
    if os.path.exists(tests_dir):
        test_files = [f for f in os.listdir(tests_dir) if f.startswith("test_") and f.endswith(".py")]
        print(f"   📊 Test files found: {len(test_files)}")
        for test_file in test_files:
            print(f"      - {test_file}")
    else:
        print("   ⚠️  Tests directory not found")
    
    print("   ✅ Configuration check complete")
    return found_configs

def run_environment_validation():
    """Run complete environment validation"""
    print("=" * 60)
    print("🧪 PHASE 8.1: TEST ENVIRONMENT VALIDATION")
    print("=" * 60)
    
    tests = [
        ("Python Environment", test_python_environment),
        ("Data Structures", test_basic_data_structures),
        ("File System", test_file_system_access),
        ("Configuration Files", test_configuration_files)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = {"status": "PASS", "result": result}
            print(f"✅ {test_name}: PASSED\n")
        except Exception as e:
            results[test_name] = {"status": "FAIL", "error": str(e)}
            print(f"❌ {test_name}: FAILED - {e}\n")
    
    # Import availability test
    try:
        import_result = test_imports_availability()
        results["Import Availability"] = {"status": "INFO", "result": import_result}
        print(f"📦 Import Availability: {import_result.upper()}\n")
    except Exception as e:
        results["Import Availability"] = {"status": "FAIL", "error": str(e)}
        print(f"❌ Import Availability: FAILED - {e}\n")
    
    print("=" * 60)
    print("📊 ENVIRONMENT VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r["status"] == "PASS")
    total = len([r for r in results.values() if r["status"] in ["PASS", "FAIL"]])
    
    for test_name, result in results.items():
        status_emoji = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "📊"
        print(f"{status_emoji} {test_name}: {result['status']}")
    
    print(f"\n📈 Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Environment validation successful!")
        print("🚀 Ready for comprehensive testing!")
    else:
        print("⚠️  Some validation tests failed")
        print("💡 Basic testing may still be possible")
    
    print("=" * 60)
    return results

def main():
    """Main entry point"""
    results = run_environment_validation()
    
    # Determine next steps based on results
    import_status = results.get("Import Availability", {}).get("result", "basic")
    
    if import_status == "full":
        print("\n🎯 NEXT STEPS:")
        print("   1. Run comprehensive unit tests: python tests/run_tests.py")
        print("   2. Run specific module tests: python tests/run_tests.py --module auth")
        print("   3. Generate coverage report: python tests/run_tests.py --report")
    elif import_status == "partial":
        print("\n🎯 NEXT STEPS:")
        print("   1. Install missing dependencies: pip install -r requirements-test.txt")
        print("   2. Run basic tests: python tests/run_tests.py --quick")
    else:
        print("\n🎯 NEXT STEPS:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Install test dependencies: pip install -r requirements-test.txt")
        print("   3. Set up database: Check database configuration")
    
    return 0 if all(r["status"] != "FAIL" for r in results.values()) else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
