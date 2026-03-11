#!/usr/bin/env python3
"""
Test script for Sub-Phase 2.1: User & Role Models

This script verifies that:
1. User and UserRole models are properly defined
2. Models can be imported without errors
3. Migration files are created correctly
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_model_imports():
    """Test that auth models can be imported successfully"""
    try:
        from app.auth.models import User, UserRole
        print("✅ Successfully imported User and UserRole models")
        return True
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False

def test_model_attributes():
    """Test that models have expected attributes"""
    try:
        from app.auth.models import User, UserRole
        
        # Check User model attributes
        user_expected_attrs = [
            'id', 'email', 'name', 'hashed_password', 
            'is_active', 'is_admin', 'created_at', 'updated_at'
        ]
        
        for attr in user_expected_attrs:
            if not hasattr(User, attr):
                print(f"❌ User model missing attribute: {attr}")
                return False
        
        # Check UserRole model attributes
        role_expected_attrs = ['user_id', 'role']
        
        for attr in role_expected_attrs:
            if not hasattr(UserRole, attr):
                print(f"❌ UserRole model missing attribute: {attr}")
                return False
        
        print("✅ All expected model attributes are present")
        return True
        
    except Exception as e:
        print(f"❌ Error checking model attributes: {e}")
        return False

def test_migration_files():
    """Test that migration files exist"""
    migration_files = [
        "migrations/env.py",
        "alembic.ini",
    ]
    
    # Check for migration version files
    import glob
    version_files = glob.glob("migrations/versions/*.py")
    
    if not version_files:
        print("❌ No migration version files found")
        return False
    
    for file_path in migration_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing migration file: {file_path}")
            return False
    
    print(f"✅ Migration files are present ({len(version_files)} version files)")
    return True

def test_base_inheritance():
    """Test that models inherit from the correct Base"""
    try:
        from app.auth.models import User, UserRole
        from app.database import Base
        
        if not issubclass(User, Base):
            print("❌ User model does not inherit from Base")
            return False
            
        if not issubclass(UserRole, Base):
            print("❌ UserRole model does not inherit from Base")
            return False
        
        print("✅ Models properly inherit from Base")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Base inheritance: {e}")
        return False

def main():
    """Run all tests for Sub-Phase 2.1"""
    print("🧪 Testing Sub-Phase 2.1: User & Role Models")
    print("=" * 50)
    
    tests = [
        ("Model Imports", test_model_imports),
        ("Model Attributes", test_model_attributes),
        ("Migration Files", test_migration_files),
        ("Base Inheritance", test_base_inheritance),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running test: {test_name}")
        result = test_func()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Sub-Phase 2.1 implementation is successful!")
        return True
    else:
        print("🚨 Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
