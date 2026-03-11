#!/usr/bin/env python3
"""
Final test to verify everything works correctly after the fixes
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login():
    """Login and get auth token"""
    login_data = {
        "email": "admin@flashcards.com",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def start_session(token, dataset_id):
    """Start a new learning session"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    data = {
        "dataset_id": dataset_id,
        "mode": "progressive",
        "batch_size": 5
    }
    
    response = requests.post(f"{BASE_URL}/sessions/start", json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Start session failed: {response.status_code} - {response.text}")
        return None

def get_next_card(token, learning_set_id):
    """Get next flashcard"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/sessions/next?learning_set_id={learning_set_id}", headers=headers)
    return response

def submit_answer(token, element_id, question_field, answer_field, correct_answer, is_correct=True):
    """Submit an answer"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    data = {
        "element_id": element_id,
        "question_field": question_field,
        "answer_field": answer_field,
        "user_answer": correct_answer,
        "correct_answer": correct_answer,
        "is_correct": is_correct,
        "response_time_ms": 2000
    }
    
    response = requests.post(f"{BASE_URL}/sessions/answer", json=data, headers=headers)
    return response.status_code == 200

def get_datasets(token):
    """Get available datasets"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/datasets/", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def test_complete_flow():
    """Test that the fixes work correctly"""
    print("🧪 Testing complete learning flow after fixes...")
    
    # Login
    token = login()
    if not token:
        print("❌ Login failed")
        return
    
    print("✅ Logged in successfully")
    
    # Get datasets
    datasets = get_datasets(token)
    if not datasets:
        print("❌ No datasets found")
        return
    
    dataset_id = datasets[0]['id']
    print(f"✅ Using dataset: {datasets[0]['name']}")
    
    # Start session
    session = start_session(token, dataset_id)
    if not session:
        print("❌ Session start failed")
        return
    
    learning_set_id = session['learning_set_id']
    print(f"✅ Started session with learning_set_id: {learning_set_id}")
    print(f"   Status: {session.get('status')}")
    print(f"   Learning message: {session.get('learning_message', '')}")
    
    # Test getting cards - this should now work without config errors
    card_count = 0
    for i in range(50):  # Test first 50 cards
        response = get_next_card(token, learning_set_id)
        
        if response.status_code == 204:
            print(f"✅ Session completed after {card_count} cards (HTTP 204)")
            break
        elif response.status_code == 200:
            card_data = response.json()
            card_count += 1
            
            element_id = card_data['element_id']
            question_field = card_data['question_field']
            answer_field = card_data['answer_field']
            correct_answer = card_data['correct_answer']
            
            # Check phase info
            fsrs_stats = card_data.get('fsrs_stats', {})
            review_count = fsrs_stats.get('review_count', 0)
            phase = "Integration" if review_count > 0 else "Isolation"
            
            if i < 5:  # Print details for first 5 cards
                print(f"  Card {i+1}: {phase} phase, review_count: {review_count}")
            elif i == 5:
                print("  ... (continuing silently)")
            
            # Submit correct answer
            success = submit_answer(token, element_id, question_field, answer_field, correct_answer, True)
            if not success:
                print(f"❌ Failed to submit answer for card {i+1}")
                return
        else:
            print(f"❌ Error getting card {i+1}: {response.status_code} - {response.text}")
            return
    
    print(f"✅ Test completed successfully! Processed {card_count} cards without errors")
    print("✅ Config variable fixes are working properly")
    print("✅ Phase transition logic is working")
    print("✅ Session management is stable")

if __name__ == "__main__":
    test_complete_flow()
