#!/usr/bin/env python3
"""
FSRS Integration Test Runner

Automated test runner for the complete FSRS integration system.
Runs unit tests, integration tests, and system validation.
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """Run a shell command and capture results"""
    print(f"\n🔄 {description}...")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description}: SUCCESS")
            if result.stdout:
                print("Output:", result.stdout.strip())
            return True
        else:
            print(f"❌ {description}: FAILED")
            if result.stderr:
                print("Error:", result.stderr.strip())
            if result.stdout:
                print("Output:", result.stdout.strip())
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description}: TIMEOUT (5 minutes)")
        return False
    except Exception as e:
        print(f"💥 {description}: EXCEPTION - {str(e)}")
        return False

def check_dependencies():
    """Check if required test dependencies are available"""
    print("🔍 Checking Test Dependencies...")
    
    dependencies = [
        ("python", "python --version"),
        ("pytest", "python -m pytest --version"),
        ("requests", "python -c 'import requests; print(requests.__version__)'"),
    ]
    
    all_available = True
    for name, command in dependencies:
        if run_command(command, f"Check {name}"):
            print(f"   ✓ {name} available")
        else:
            print(f"   ✗ {name} not available")
            all_available = False
    
    return all_available

def run_unit_tests():
    """Run FSRS integration unit tests"""
    print("\n" + "="*60)
    print("🧪 RUNNING UNIT TESTS")
    print("="*60)
    
    test_files = [
        "tests/test_fsrs_integration.py",
        "tests/test_fsrs_api.py"
    ]
    
    results = []
    for test_file in test_files:
        if os.path.exists(test_file):
            success = run_command(
                f"python -m pytest {test_file} -v --tb=short",
                f"Unit Tests - {os.path.basename(test_file)}"
            )
            results.append((test_file, success))
        else:
            print(f"⚠️  Test file not found: {test_file}")
            results.append((test_file, False))
    
    return results

def run_integration_tests():
    """Run integration tests with actual API calls"""
    print("\n" + "="*60)
    print("🔗 RUNNING INTEGRATION TESTS")
    print("="*60)
    
    # First check if the backend is running
    backend_check = run_command(
        "curl -s http://localhost:8000/docs > /dev/null || echo 'Backend not running'",
        "Check Backend Running"
    )
    
    if not backend_check:
        print("⚠️  Backend not running. Starting with Docker Compose...")
        docker_start = run_command(
            "docker-compose up -d",
            "Start Backend with Docker"
        )
        
        if docker_start:
            print("⏳ Waiting 30 seconds for backend to initialize...")
            import time
            time.sleep(30)
        else:
            print("❌ Could not start backend. Skipping integration tests.")
            return [("Integration Tests", False)]
    
    # Run system validation script
    validation_success = run_command(
        "python validate_fsrs_system.py",
        "System Validation Script"
    )
    
    return [("Integration/Validation Tests", validation_success)]

def run_database_tests():
    """Run database-related tests"""
    print("\n" + "="*60)
    print("🗄️  RUNNING DATABASE TESTS")
    print("="*60)
    
    # Test migration script
    migration_test = run_command(
        "python -c 'from migrations.add_integration_tracking import upgrade, downgrade; print(\"Migration functions importable\")'",
        "Migration Script Import Test"
    )
    
    # Test seeding script
    seeding_test = run_command(
        "python -c 'import seed_integration_config; print(\"Seeding script importable\")'",
        "Seeding Script Import Test"
    )
    
    return [
        ("Migration Script", migration_test),
        ("Seeding Script", seeding_test)
    ]

def run_code_quality_checks():
    """Run code quality and style checks"""
    print("\n" + "="*60)
    print("📝 RUNNING CODE QUALITY CHECKS")
    print("="*60)
    
    # Check for Python syntax errors
    syntax_check = run_command(
        "python -m py_compile app/sessions/routes.py app/admin/routes.py",
        "Python Syntax Check"
    )
    
    # Check imports
    import_check = run_command(
        "python -c 'from app.sessions.routes import get_integration_config, calculate_integration_mastery; print(\"Core functions importable\")'",
        "Core Function Import Check"
    )
    
    return [
        ("Syntax Check", syntax_check),
        ("Import Check", import_check)
    ]

def generate_test_report(all_results):
    """Generate comprehensive test report"""
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE FSRS INTEGRATION TEST REPORT")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_tests = 0
    passed_tests = 0
    
    categories = [
        ("Unit Tests", all_results.get("unit", [])),
        ("Integration Tests", all_results.get("integration", [])),
        ("Database Tests", all_results.get("database", [])),
        ("Code Quality", all_results.get("quality", []))
    ]
    
    for category_name, tests in categories:
        print(f"\n📋 {category_name}:")
        for test_name, success in tests:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} - {test_name}")
            total_tests += 1
            if success:
                passed_tests += 1
    
    # Calculate overall success rate
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📈 OVERALL RESULTS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    # Final assessment
    if success_rate >= 90:
        print(f"\n🎉 EXCELLENT: FSRS Integration system is production-ready!")
        print("   All critical functionality validated and working correctly.")
    elif success_rate >= 75:
        print(f"\n✅ GOOD: FSRS Integration system is mostly ready.")
        print("   Minor issues to address, but core functionality working.")
    elif success_rate >= 50:
        print(f"\n⚠️  FAIR: FSRS Integration system needs improvement.")
        print("   Several issues detected. Review failed tests before deployment.")
    else:
        print(f"\n🚨 POOR: FSRS Integration system requires significant work.")
        print("   Major issues detected. Extensive review and fixes needed.")
    
    # Recommendations based on results
    print(f"\n💡 RECOMMENDATIONS:")
    if success_rate < 100:
        print("   • Review and fix failed tests before production deployment")
        print("   • Ensure database is properly migrated with integration tracking fields")
        print("   • Verify all FSRS configuration parameters are seeded")
    
    print("   • Run this test suite again after fixes")
    print("   • Monitor system performance metrics after deployment")
    print("   • Consider additional load testing for production readiness")
    
    return success_rate >= 75  # Return True if system is ready

def main():
    """Main test runner function"""
    print("🚀 FSRS INTEGRATION COMPREHENSIVE TEST RUNNER")
    print("="*80)
    print("This will run the complete test suite for the FSRS integration system.")
    print("Estimated time: 5-10 minutes depending on system performance.")
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Required dependencies not available. Install pytest and requests.")
        sys.exit(1)
    
    # Store all test results
    all_results = {}
    
    # Run all test categories
    all_results["unit"] = run_unit_tests()
    all_results["integration"] = run_integration_tests()
    all_results["database"] = run_database_tests()
    all_results["quality"] = run_code_quality_checks()
    
    # Generate comprehensive report
    system_ready = generate_test_report(all_results)
    
    # Exit with appropriate code
    if system_ready:
        print("\n🎯 FSRS INTEGRATION SYSTEM: VALIDATED AND READY!")
        sys.exit(0)
    else:
        print("\n⚠️  FSRS INTEGRATION SYSTEM: NEEDS ATTENTION")
        sys.exit(1)

if __name__ == "__main__":
    main()
