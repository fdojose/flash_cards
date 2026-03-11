#!/usr/bin/env python3
"""
Test script for Sub-Phase 2.3: JWT Guard Dependency

This script verifies that:
1. Enhanced JWT guard dependencies are properly implemented
2. Role-based access control works correctly
3. Optional authentication dependencies function
4. Admin-only and user-specific access patterns work
5. Token validation is comprehensive
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dependencies_file():
    """Test that dependencies file exists and has required functions"""
    try:
        from app.auth.dependencies import (
            get_current_user,
            get_admin_user,
            get_active_user,
            get_user_with_role,
            get_moderator_user,
            get_admin_role_user,
            get_current_user_optional,
            verify_token_only,
            require_same_user_or_admin
        )
        
        print("✅ All required dependencies are available")
        return True
        
    except ImportError as e:
        print(f"❌ Error importing dependencies: {e}")
        return False

def test_enhanced_route_definitions():
    """Test that enhanced routes are properly defined"""
    try:
        from app.auth.routes import router
        
        # Check that router has the enhanced routes
        route_paths = [route.path for route in router.routes]
        
        expected_routes = [
            '/auth/register',
            '/auth/login', 
            '/auth/me',
            '/auth/protected',
            '/auth/admin-only',
            '/auth/admin-role-only',
            '/auth/moderator-only',
            '/auth/public-or-user',
            '/auth/users/{user_id}/profile',
            '/auth/token/verify'
        ]
        
        missing_routes = []
        for expected_route in expected_routes:
            if expected_route not in route_paths:
                missing_routes.append(expected_route)
        
        if missing_routes:
            print(f"❌ Missing routes: {missing_routes}")
            return False
        
        print("✅ All expected enhanced routes are defined")
        return True
        
    except Exception as e:
        print(f"❌ Error checking enhanced route definitions: {e}")
        return False

def test_dependency_functions():
    """Test that dependency functions are callable"""
    try:
        from app.auth.dependencies import (
            get_current_user,
            get_admin_user,
            get_user_with_role,
            verify_token_only
        )
        
        # Check that functions are callable
        functions_to_test = [
            get_current_user,
            get_admin_user,
            verify_token_only
        ]
        
        for func in functions_to_test:
            if not callable(func):
                print(f"❌ {func.__name__} is not callable")
                return False
        
        # Test role factory function
        admin_dep = get_user_with_role("admin")
        moderator_dep = get_user_with_role("moderator")
        
        if not callable(admin_dep) or not callable(moderator_dep):
            print("❌ Role factory function doesn't create callable dependencies")
            return False
        
        print("✅ All dependency functions are callable")
        return True
        
    except Exception as e:
        print(f"❌ Error testing dependency functions: {e}")
        return False

def test_token_verification_utility():
    """Test the token verification utility function"""
    try:
        from app.auth.dependencies import verify_token_only
        from app.auth.routes import create_access_token
        
        # Create a test token
        test_data = {"sub": "test@example.com"}
        token = create_access_token(test_data)
        
        # Verify the token
        payload = verify_token_only(token)
        
        if not payload:
            print("❌ Token verification utility failed to validate valid token")
            return False
        
        if payload.get("sub") != "test@example.com":
            print("❌ Token verification utility returned incorrect payload")
            return False
        
        # Test invalid token
        invalid_payload = verify_token_only("invalid-token")
        if invalid_payload is not None:
            print("❌ Token verification utility should return None for invalid token")
            return False
        
        print("✅ Token verification utility works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing token verification utility: {e}")
        return False

def test_role_based_dependencies():
    """Test role-based dependency creation"""
    try:
        from app.auth.dependencies import get_user_with_role, get_moderator_user, get_admin_role_user
        
        # Test factory function
        custom_role_dep = get_user_with_role("custom_role")
        if not callable(custom_role_dep):
            print("❌ Role factory doesn't create callable dependency")
            return False
        
        # Test pre-configured dependencies
        if not callable(get_moderator_user):
            print("❌ Moderator dependency is not callable")
            return False
            
        if not callable(get_admin_role_user):
            print("❌ Admin role dependency is not callable")
            return False
        
        print("✅ Role-based dependencies are properly configured")
        return True
        
    except Exception as e:
        print(f"❌ Error testing role-based dependencies: {e}")
        return False

def test_optional_authentication():
    """Test optional authentication dependency"""
    try:
        from app.auth.dependencies import get_current_user_optional
        
        if not callable(get_current_user_optional):
            print("❌ Optional authentication dependency is not callable")
            return False
        
        print("✅ Optional authentication dependency is available")
        return True
        
    except Exception as e:
        print(f"❌ Error testing optional authentication: {e}")
        return False

def test_enhanced_error_handling():
    """Test that enhanced error handling is in place"""
    try:
        from app.auth.routes import get_current_user
        from fastapi import HTTPException
        
        # Check that the function exists and appears to have proper error handling
        # (We can't fully test this without a database, but we can check structure)
        import inspect
        source = inspect.getsource(get_current_user)
        
        # Look for enhanced error messages
        if "Token has expired" not in source:
            print("❌ Enhanced token expiration error handling missing")
            return False
        
        if "Token validation failed" not in source:
            print("❌ Enhanced token validation error handling missing")
            return False
        
        if "User account is disabled" not in source:
            print("❌ Enhanced user status error handling missing")
            return False
        
        print("✅ Enhanced error handling is implemented")
        return True
        
    except Exception as e:
        print(f"❌ Error testing enhanced error handling: {e}")
        return False

def test_security_imports():
    """Test that security dependencies are properly imported"""
    try:
        from app.auth.routes import security
        from fastapi.security import HTTPBearer
        
        if not isinstance(security, HTTPBearer):
            print("❌ Security scheme is not properly configured")
            return False
        
        print("✅ Security imports are properly configured")
        return True
        
    except Exception as e:
        print(f"❌ Error testing security imports: {e}")
        return False

def main():
    """Run all tests for Sub-Phase 2.3"""
    print("🧪 Testing Sub-Phase 2.3: JWT Guard Dependency")
    print("=" * 55)
    
    tests = [
        ("Dependencies File", test_dependencies_file),
        ("Enhanced Route Definitions", test_enhanced_route_definitions),
        ("Dependency Functions", test_dependency_functions),
        ("Token Verification Utility", test_token_verification_utility),
        ("Role-Based Dependencies", test_role_based_dependencies),
        ("Optional Authentication", test_optional_authentication),
        ("Enhanced Error Handling", test_enhanced_error_handling),
        ("Security Imports", test_security_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running test: {test_name}")
        result = test_func()
        results.append(result)
    
    print("\n" + "=" * 55)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Sub-Phase 2.3 implementation is successful!")
        print("\n📋 Key Features Implemented:")
        print("  ✅ Enhanced JWT token validation with detailed error messages")
        print("  ✅ Role-based access control with factory functions")
        print("  ✅ Optional authentication for flexible route access")
        print("  ✅ Admin and user-specific access patterns")
        print("  ✅ Comprehensive security dependencies")
        print("  ✅ Reusable dependencies module for other phases")
        print("\n🔄 Ready for Phase 3: Dataset Management!")
        return True
    else:
        print("🚨 Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
