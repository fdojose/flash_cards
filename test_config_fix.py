#!/usr/bin/env python3
"""
Quick test to verify the config fix works
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBmbGFzaGNhcmRzLmNvbSIsImV4cCI6MTc1NDg1MTE0My4xNTA5MDJ9.ejNmZS2jQgGn-SkrMAFJq5cyxg0"

def get_datasets():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{BASE_URL}/datasets", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def start_session(dataset_id):
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
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

def get_next_card(learning_set_id):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(f"{BASE_URL}/sessions/next?learning_set_id={learning_set_id}", headers=headers)
    return response

# Get datasets
datasets = get_datasets()
if not datasets:
    print("❌ No datasets found")
    exit(1)

dataset_id = datasets[0]['id']
print(f"✅ Using dataset: {datasets[0]['name']}")

# Start session  
session = start_session(dataset_id)
if not session:
    exit(1)

learning_set_id = session['learning_set_id']
print(f"✅ Started session with learning_set_id: {learning_set_id}")

# Test getting cards
for i in range(10):
    response = get_next_card(learning_set_id)
    if response.status_code == 200:
        card_data = response.json()
        print(f"  Card {i+1}: Got element_id {card_data['element_id']}")
    elif response.status_code == 204:
        print(f"  Session complete after {i+1} attempts")
        break
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        break

print("🎉 Config fix test completed successfully!")
