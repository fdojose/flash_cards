# Frontend-Backend Integration Test
# =================================

import requests
import json

def test_frontend_backend_integration():
    """Test that frontend can connect to backend APIs"""
    
    backend_url = "http://localhost:8000"
    
    print("🧪 Testing Frontend-Backend Integration...")
    print("=" * 50)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend health check: PASSED")
        else:
            print(f"❌ Backend health check: FAILED ({response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend health check: FAILED (Connection error: {e})")
    
    # Test 2: API documentation access
    try:
        response = requests.get(f"{backend_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API documentation: ACCESSIBLE")
        else:
            print(f"❌ API documentation: FAILED ({response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ API documentation: FAILED (Connection error: {e})")
    
    # Test 3: CORS headers for frontend
    try:
        response = requests.options(f"{backend_url}/api/auth/register", timeout=5, headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        })
        cors_headers = response.headers.get('Access-Control-Allow-Origin', '')
        if 'localhost:3000' in cors_headers or cors_headers == '*':
            print("✅ CORS configuration: CONFIGURED")
        else:
            print(f"❌ CORS configuration: MISSING (Headers: {dict(response.headers)})")
    except requests.exceptions.RequestException as e:
        print(f"❌ CORS configuration: FAILED (Connection error: {e})")
    
    # Test 4: API endpoints accessibility
    api_endpoints = [
        "/api/auth/register",
        "/api/datasets/",
        "/api/dashboard/stats"
    ]
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(f"{backend_url}{endpoint}", timeout=5)
            # We expect 401/422 for protected endpoints, not 404
            if response.status_code in [200, 401, 422]:
                print(f"✅ API endpoint {endpoint}: ACCESSIBLE")
            else:
                print(f"❌ API endpoint {endpoint}: FAILED ({response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"❌ API endpoint {endpoint}: FAILED (Connection error: {e})")
    
    print("\n🔧 Integration Notes:")
    print("- Make sure backend is running: cd backend && uvicorn main:app --reload")
    print("- Make sure frontend is configured with VITE_API_URL=http://localhost:8000/api")
    print("- Check that CORS is enabled for localhost:3000 in backend settings")
    print("\n📚 Next steps:")
    print("- Start backend: cd backend && uvicorn main:app --reload")
    print("- Start frontend: cd frontend && npm run dev")
    print("- Test login/registration from frontend UI")

if __name__ == "__main__":
    test_frontend_backend_integration()
