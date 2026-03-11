#!/usr/bin/env python3
"""
PHASE 8.1: UNIT TESTS - Test Runner and Configuration
====================================================

Main test runner for the flashcard learning system with:
- pytest configuration
- Coverage reporting
- Test discovery
- Performance benchmarks
"""

import os
import sys
import pytest
import subprocess
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def run_tests():
    """Run all tests with coverage reporting"""
    print("=" * 60)
    print("🧪 PHASE 8.1: RUNNING COMPREHENSIVE UNIT TESTS")
    print("=" * 60)
    
    # Test configuration
    pytest_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker checking
        "--cov=app",  # Coverage for app module
        "--cov-report=html",  # HTML coverage report
        "--cov-report=term-missing",  # Terminal coverage with missing lines
        "--cov-fail-under=80",  # Fail if coverage below 80%
        "--asyncio-mode=auto",  # Auto asyncio mode
        str(Path(__file__).parent),  # Test directory
    ]
    
    # Run tests
    result = pytest.main(pytest_args)
    
    print("\n" + "=" * 60)
    if result == 0:
        print("✅ ALL TESTS PASSED!")
        print("📊 Coverage report generated in htmlcov/")
    else:
        print("❌ SOME TESTS FAILED!")
        print("📋 Check test output above for details")
    print("=" * 60)
    
    return result

def run_quick_tests():
    """Run tests without coverage for quick feedback"""
    print("🏃‍♂️ Running quick tests (no coverage)...")
    
    pytest_args = [
        "-v",
        "--tb=short",
        "--asyncio-mode=auto",
        str(Path(__file__).parent),
    ]
    
    return pytest.main(pytest_args)

def run_specific_module(module_name):
    """Run tests for specific module"""
    print(f"🎯 Running tests for module: {module_name}")
    
    test_file = Path(__file__).parent / f"test_{module_name}.py"
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    pytest_args = [
        "-v",
        "--tb=short",
        "--asyncio-mode=auto",
        str(test_file),
    ]
    
    return pytest.main(pytest_args)

def run_integration_tests():
    """Run integration tests (if they exist)"""
    integration_dir = Path(__file__).parent / "integration"
    if integration_dir.exists():
        print("🔗 Running integration tests...")
        pytest_args = [
            "-v",
            "--tb=short",
            "--asyncio-mode=auto",
            str(integration_dir),
        ]
        return pytest.main(pytest_args)
    else:
        print("ℹ️  No integration tests found")
        return 0

def check_test_dependencies():
    """Check if all test dependencies are installed"""
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "pytest-cov",
        "httpx",
        "sqlalchemy",
        "fastapi"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: pip install -r requirements-test.txt")
        return False
    
    return True

def generate_test_report():
    """Generate comprehensive test report"""
    print("📊 Generating test report...")
    
    # Run tests with JUnit XML output
    pytest_args = [
        "--tb=short",
        "--cov=app",
        "--cov-report=xml",
        "--junitxml=test-results.xml",
        str(Path(__file__).parent),
    ]
    
    result = pytest.main(pytest_args)
    
    if result == 0:
        print("✅ Test report generated: test-results.xml")
        print("📊 Coverage report generated: coverage.xml")
    
    return result

def validate_test_environment():
    """Validate test environment setup"""
    print("🔧 Validating test environment...")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in a virtual environment")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check if backend app can be imported
    try:
        import app
        print("✅ Backend app importable")
    except ImportError as e:
        print(f"❌ Cannot import backend app: {e}")
        return False
    
    # Check database connectivity
    try:
        from app.database import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ Database connection working")
    except Exception as e:
        print(f"⚠️  Database connection issue: {e}")
        print("   Tests will use SQLite in-memory database")
    
    return True

def main():
    """Main test runner entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Flashcard Learning System Test Runner")
    parser.add_argument("--quick", action="store_true", help="Run tests without coverage")
    parser.add_argument("--module", type=str, help="Run tests for specific module")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--report", action="store_true", help="Generate test report")
    parser.add_argument("--validate", action="store_true", help="Validate test environment")
    
    args = parser.parse_args()
    
    # Validate environment first
    if not validate_test_environment():
        print("❌ Test environment validation failed")
        return 1
    
    # Check dependencies
    if not check_test_dependencies():
        return 1
    
    # Run specific test type
    if args.validate:
        print("✅ Test environment validation complete")
        return 0
    elif args.quick:
        return run_quick_tests()
    elif args.module:
        return run_specific_module(args.module)
    elif args.integration:
        return run_integration_tests()
    elif args.report:
        return generate_test_report()
    else:
        return run_tests()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
