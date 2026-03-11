#!/usr/bin/env python3
"""
Debug script to understand the exact issue with verify_token_only
"""

import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.auth.routes import create_access_token
from jose import JWTError, jwt

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def debug_verify_token_only(token: str) -> dict | None:
    """
    Debug version of verify_token_only with detailed logging
    """
    print(f"🔍 Verifying token: {token[:50]}...")
    print(f"🔍 Using SECRET_KEY: {SECRET_KEY[:20]}...")
    print(f"🔍 Using ALGORITHM: {ALGORITHM}")
    
    try:
        print("🔍 Attempting to decode token...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"🔍 Token decoded successfully: {payload}")
        
        # Check expiration
        exp = payload.get("exp")
        current_time = datetime.utcnow().timestamp()
        
        print(f"🔍 Token expiry: {exp}")
        print(f"🔍 Current time: {current_time}")
        
        if exp is None:
            print("❌ No expiration time in token")
            return None
            
        if current_time > exp:
            print("❌ Token has expired")
            return None
        
        print("✅ Token is valid and not expired")
        return payload
        
    except JWTError as e:
        print(f"❌ JWT Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

if __name__ == "__main__":
    # Create test token
    test_data = {"sub": "test@example.com"}
    token = create_access_token(test_data)
    
    # Test our debug function
    result = debug_verify_token_only(token)
    print(f"\nFinal result: {result}")
