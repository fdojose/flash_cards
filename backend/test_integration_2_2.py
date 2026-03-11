#!/usr/bin/env python3
"""
Integration Test for Sub-Phase 2.2: Auth Routes

This script starts the FastAPI server and tests the actual endpoints.
"""

import subprocess
import time
import requests
import json
import signal
import os
import sys

# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

def start_server():
    """Start the FastAPI server"""
    try:
        # Change to backend directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Start uvicorn server
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", SERVER_HOST, 
            "--port", str(SERVER_PORT),
            "--reload"
        ]
        
        process = subprocess.Popen(
            cmd, 
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        print("🚀 Starting FastAPI server...")
        time.sleep(3)
        
        # Check if server is running
        try:
            response = requests.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                print(f"✅ Server started successfully at {BASE_URL}")
                return process
            else:
                print("❌ Server not responding")
                return None
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to server")
            return None
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def test_register_endpoint():
    """Test user registration endpoint"""
    try:
        url = f"{BASE_URL}/api/v1/auth/register"
        data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "testpassword123"
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("email") == "test@example.com":
                print("✅ Registration endpoint works correctly")
                return True, result
            else:
                print("❌ Registration response missing expected data")
                return False, None
        else:
            print(f"❌ Registration failed with status {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error testing registration: {e}")
        return False, None

def test_login_endpoint():
    """Test user login endpoint"""
    try:
        url = f"{BASE_URL}/api/v1/auth/login"
        data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("access_token") and result.get("token_type") == "bearer":
                print("✅ Login endpoint works correctly")
                return True, result["access_token"]
            else:
                print("❌ Login response missing token data")
                return False, None
        else:
            print(f"❌ Login failed with status {response.status_code}: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error testing login: {e}")
        return False, None

def test_protected_endpoint(token):
    """Test protected endpoint with JWT token"""
    try:
        url = f"{BASE_URL}/api/v1/auth/me"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("email") == "test@example.com":
                print("✅ Protected endpoint works correctly")
                return True
            else:
                print("❌ Protected endpoint response missing expected data")
                return False
        else:
            print(f"❌ Protected endpoint failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing protected endpoint: {e}")
        return False

def test_unauthorized_access():
    """Test that protected endpoints reject invalid tokens"""
    try:
        url = f"{BASE_URL}/api/v1/auth/me"
        headers = {
            "Authorization": "Bearer invalid-token"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 401:
            print("✅ Unauthorized access properly rejected")
            return True
        else:
            print(f"❌ Expected 401 but got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing unauthorized access: {e}")
        return False

def stop_server(process):
    """Stop the FastAPI server"""
    try:
        if process:
            process.terminate()
            process.wait(timeout=5)
            print("🛑 Server stopped")
    except subprocess.TimeoutExpired:
        process.kill()
        print("🛑 Server forcefully stopped")
    except Exception as e:
        print(f"❌ Error stopping server: {e}")

def main():
    """Run integration tests"""
    print("🧪 Integration Test for Sub-Phase 2.2: Auth Routes")
    print("=" * 60)
    
    # Start server
    server_process = start_server()
    if not server_process:
        print("❌ Could not start server. Exiting.")
        return False
    
    try:
        tests_passed = 0
        total_tests = 4
        
        # Test registration
        print("\n🔍 Testing user registration...")
        reg_success, user_data = test_register_endpoint()
        if reg_success:
            tests_passed += 1
        
        # Test login
        print("\n🔍 Testing user login...")
        login_success, token = test_login_endpoint()
        if login_success:
            tests_passed += 1
        
        # Test protected endpoint
        if token:
            print("\n🔍 Testing protected endpoint...")
            if test_protected_endpoint(token):
                tests_passed += 1
        
        # Test unauthorized access
        print("\n🔍 Testing unauthorized access...")
        if test_unauthorized_access():
            tests_passed += 1
        
        # Results
        print("\n" + "=" * 60)
        print("📊 Integration Test Results:")
        print(f"  Registration: {'✅ PASS' if reg_success else '❌ FAIL'}")
        print(f"  Login: {'✅ PASS' if login_success else '❌ FAIL'}")
        print(f"  Protected Route: {'✅ PASS' if token and tests_passed >= 3 else '❌ FAIL'}")
        print(f"  Unauthorized Rejection: {'✅ PASS' if tests_passed == 4 else '❌ FAIL'}")
        
        print(f"\n🎯 Overall: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            print("🎉 All integration tests passed!")
            print("\n📋 Sub-Phase 2.2 is complete! Ready for Sub-Phase 2.3.")
            return True
        else:
            print("🚨 Some integration tests failed.")
            return False
            
    finally:
        stop_server(server_process)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
