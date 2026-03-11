#!/usr/bin/env python3
"""
Debug script to test token verification
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.auth.dependencies import verify_token_only
    from app.auth.routes import create_access_token
    from jose import jwt
    import os
    
    # Check constants
    routes_secret = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    routes_algo = os.getenv("ALGORITHM", "HS256")
    
    print(f"Routes SECRET_KEY: {routes_secret[:20]}...")
    print(f"Routes ALGORITHM: {routes_algo}")
    
    print("\nCreating test token...")
    test_data = {"sub": "test@example.com"}
    token = create_access_token(test_data)
    print(f"Token created: {token[:50]}...")
    
    # Try to decode with same values used in routes.py
    print("\nDecoding token with routes constants...")
    try:
        decoded_routes = jwt.decode(token, routes_secret, algorithms=[routes_algo])
        print(f"Routes decode successful: {decoded_routes}")
    except Exception as e:
        print(f"Routes decode failed: {e}")
    
    print("\nVerifying token with dependencies function...")
    payload = verify_token_only(token)
    print(f"Dependencies payload: {payload}")
    
    if payload:
        print("✅ Token verification successful")
        print(f"Subject: {payload.get('sub')}")
    else:
        print("❌ Token verification failed")
        
        # Check dependencies constants 
        from app.auth.dependencies import SECRET_KEY, ALGORITHM
        print(f"Dependencies SECRET_KEY: {SECRET_KEY[:20]}...")
        print(f"Dependencies ALGORITHM: {ALGORITHM}")
        
        if SECRET_KEY != routes_secret:
            print("🚨 SECRET_KEY mismatch!")
        if ALGORITHM != routes_algo:
            print("🚨 ALGORITHM mismatch!")
        
except Exception as e:
    import traceback
    print(f"Error: {e}")
    print("Traceback:")
    traceback.print_exc()
