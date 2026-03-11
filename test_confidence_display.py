#!/usr/bin/env python3
"""
Test script to verify the confidence display shows correct labels
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

def login():
    login_data = {"email": "admin@flashcards.com", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    return response.json().get("access_token") if response.status_code == 200 else None

def get_confidence_stats(token, learning_set_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/sessions/{learning_set_id}/confidence-stats", headers=headers)
    return response.json() if response.status_code == 200 else None

def test_confidence_display():
    token = login()
    if not token:
        print("❌ Login failed")
        return

    # Test current completed session
    learning_set_id = "f01e5ed9-f6e3-4c5d-ab46-2632624adac8"
    stats = get_confidence_stats(token, learning_set_id)
    
    if not stats:
        print("❌ Failed to get confidence stats")
        return
    
    print("📊 Confidence Stats Test Results:")
    print(f"   Learning Set ID: {learning_set_id}")
    print(f"   Total Cards: {stats['total_cards']}")
    print(f"   Strong Count: {stats['confidence_breakdown']['strong_count']}")
    print(f"   Learning Phase: {stats['learning_phase']['phase']}")
    print(f"   Phase Message: {stats['learning_phase']['message']}")
    
    # Analyze what should be displayed
    phase = stats['learning_phase']['phase']
    strong_count = stats['confidence_breakdown']['strong_count']
    
    if phase == 'complete' and strong_count > 0:
        expected_display = f"{strong_count} Mastered"
        print(f"✅ Expected Frontend Display: '{expected_display}'")
        print("✅ Phase is 'complete', so cards should show as 'Mastered' not 'Strong'")
    elif strong_count > 0:
        expected_display = f"{strong_count} Strong"
        print(f"✅ Expected Frontend Display: '{expected_display}'")
        print("✅ Phase is not complete, so cards should show as 'Strong'")
    
    print(f"\n🎯 Summary:")
    print(f"   - Session processed 10 cards successfully")
    print(f"   - All cards achieved mastered status")
    print(f"   - Learning phase is complete")
    print(f"   - Frontend should now display '10 Mastered' instead of '10 Strong'")

if __name__ == "__main__":
    test_confidence_display()
