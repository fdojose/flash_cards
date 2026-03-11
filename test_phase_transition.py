#!/usr/bin/env python3
"""
Test script to check phase transition logic
"""
import requests
import json

# Backend URL
BASE_URL = "http://localhost:8000"

# Test learning set ID (from database query)
LEARNING_SET_ID = "006614bd-568c-436c-a4bf-a2d18efc41f1"

def test_login():
    """Test user login to get auth token"""
    login_data = {
        "email": "admin@flashcards.com",
        "password": "admin123"
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data, headers=headers)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_get_next_card(token):
    """Test getting next flashcard to trigger phase transition"""
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json"
    }
    
    url = f"{BASE_URL}/api/v1/sessions/next"
    params = {"learning_set_id": LEARNING_SET_ID}
    
    response = requests.get(url, headers=headers, params=params)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response

if __name__ == "__main__":
    # Test login
    token = test_login()
    if not token:
        print("Could not authenticate - check credentials")
        exit(1)
    
    print(f"Authenticated successfully")
    
    # Test getting next card (should trigger phase transition)
    response = test_get_next_card(token)
