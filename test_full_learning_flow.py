#!/usr/bin/env python3
"""
Test script to verify the complete learning flow:
1. Start new session
2. Complete first batch (isolation)
3. Verify transition to integration phase
4. Complete integration phase
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
    response = requests.get(f"{BASE_URL}/datasets", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def simulate_learning_session():
    """Simulate a complete learning session"""
    # Login
    token = login()
    if not token:
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
        return
    
    learning_set_id = session['learning_set_id']
    print(f"✅ Started session with learning_set_id: {learning_set_id}")
    
    card_count = 0
    session_count = 1
    
    # Learning loop
    while True:
        print(f"\n--- Session {session_count} ---")
        
        # Get cards until session is complete
        session_card_count = 0
        while True:
            response = get_next_card(token, learning_set_id)
            
            if response.status_code == 204:
                # Session complete
                print(f"✅ Session {session_count} completed after {session_card_count} cards")
                print(f"   Completion message: {response.text}")
                break
            elif response.status_code == 200:
                # Got a card
                card_data = response.json()
                card_count += 1
                session_card_count += 1
                
                element_id = card_data['element_id']
                question_field = card_data['question_field']
                answer_field = card_data['answer_field']
                correct_answer = card_data['correct_answer']
                
                # Check if isolation or integration phase
                fsrs_stats = card_data.get('fsrs_stats', {})
                review_count = fsrs_stats.get('review_count', 0)
                phase = "Integration" if review_count > 0 else "Isolation"
                
                print(f"  Card {session_card_count} (total {card_count}): {phase} phase, review_count: {review_count}")
                
                # Submit correct answer
                success = submit_answer(token, element_id, question_field, answer_field, correct_answer, True)
                if not success:
                    print(f"❌ Failed to submit answer for card {card_count}")
                    return
            else:
                print(f"❌ Error getting next card: {response.status_code} - {response.text}")
                return
        
        # Check if we should start another session
        if session_count >= 3:  # Limit to 3 sessions for testing
            break
            
        # Start new session for next batch
        session_count += 1
        session = start_session(token, dataset_id)
        if session:
            learning_set_id = session['learning_set_id']
            print(f"✅ Started new session with learning_set_id: {learning_set_id}")
        else:
            print("❌ Failed to start new session")
            break
    
    print(f"\n🎉 Testing completed! Total cards reviewed: {card_count}")

if __name__ == "__main__":
    simulate_learning_session()
