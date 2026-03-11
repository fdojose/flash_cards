#!/usr/bin/env python3
"""
Test script to verify that the phase transition fix works correctly
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

def test_phase_transitions():
    """Test that phase transitions work correctly"""
    print("🧪 Testing phase transition fix...")
    
    # Login
    token = login()
    if not token:
        return
    
    print("✅ Logged in successfully")
    
    # Start session
    dataset_id = "29c6388b-339f-463f-b568-7f3b203103ea"
    session = start_session(token, dataset_id)
    if not session:
        return
    
    learning_set_id = session['learning_set_id']
    print(f"✅ Started session with learning_set_id: {learning_set_id}")
    
    card_count = 0
    isolation_cards = 0
    integration_cards = 0
    
    # Process cards and track phases
    for i in range(20):  # Test first 20 cards
        response = get_next_card(token, learning_set_id)
        
        if response.status_code == 204:
            print(f"✅ Session completed after {card_count} cards (expected after integration)")
            print(f"   Isolation phase cards: {isolation_cards}")
            print(f"   Integration phase cards: {integration_cards}")
            break
        elif response.status_code == 200:
            card_data = response.json()
            card_count += 1
            
            element_id = card_data['element_id']
            question_field = card_data['question_field']
            answer_field = card_data['answer_field']
            correct_answer = card_data['correct_answer']
            
            # Check phase
            fsrs_stats = card_data.get('fsrs_stats', {})
            review_count = fsrs_stats.get('review_count', 0)
            
            if review_count == 0:
                phase = "Isolation (new card)"
                isolation_cards += 1
            elif review_count >= 1:
                phase = "Integration (review)"
                integration_cards += 1
            
            if card_count <= 15:  # Only show first 15 for brevity
                print(f"  Card {card_count}: {phase} (review_count: {review_count})")
            elif card_count == 16:
                print("  ... (continuing)")
            
            # Submit correct answer
            success = submit_answer(token, element_id, question_field, answer_field, correct_answer, True)
            if not success:
                print(f"❌ Failed to submit answer for card {card_count}")
                return
        else:
            print(f"❌ Error getting card {card_count + 1}: {response.status_code} - {response.text}")
            return
    
    # Analyze results
    print(f"\n📊 Test Results:")
    print(f"   Total cards processed: {card_count}")
    print(f"   Isolation phase cards: {isolation_cards}")
    print(f"   Integration phase cards: {integration_cards}")
    
    if isolation_cards >= 5 and integration_cards > 0:
        print("✅ SUCCESS: Phase transition working correctly!")
        print("   - Isolation phase processed initial cards")
        print("   - Integration phase activated for reviews")
    elif isolation_cards >= 10 and integration_cards == 0:
        print("❌ FAILURE: Session completed without integration phase")
    else:
        print(f"⚠️  PARTIAL: Unexpected pattern - needs investigation")

if __name__ == "__main__":
    test_phase_transitions()
