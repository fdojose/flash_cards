#!/usr/bin/env python3
"""
Create demo datasets for testing the flashcard application
"""

import json
import requests
import sys

# API configuration
API_BASE = "http://localhost:8000/api/v1"

# Demo datasets to create
demo_datasets = [
    {
        "name": "Spanish Basic Vocabulary",
        "description": "Essential Spanish words for beginners",
        "elements": [
            {
                "fields": [
                    {"name": "spanish", "value": "hola"},
                    {"name": "english", "value": "hello"},
                    {"name": "category", "value": "greetings"}
                ]
            },
            {
                "fields": [
                    {"name": "spanish", "value": "adiós"},
                    {"name": "english", "value": "goodbye"},
                    {"name": "category", "value": "greetings"}
                ]
            },
            {
                "fields": [
                    {"name": "spanish", "value": "gracias"},
                    {"name": "english", "value": "thank you"},
                    {"name": "category", "value": "courtesy"}
                ]
            },
            {
                "fields": [
                    {"name": "spanish", "value": "por favor"},
                    {"name": "english", "value": "please"},
                    {"name": "category", "value": "courtesy"}
                ]
            },
            {
                "fields": [
                    {"name": "spanish", "value": "casa"},
                    {"name": "english", "value": "house"},
                    {"name": "category", "value": "nouns"}
                ]
            }
        ]
    },
    {
        "name": "Math Facts",
        "description": "Basic arithmetic for quick practice",
        "elements": [
            {
                "fields": [
                    {"name": "problem", "value": "7 × 8"},
                    {"name": "answer", "value": "56"},
                    {"name": "category", "value": "multiplication"}
                ]
            },
            {
                "fields": [
                    {"name": "problem", "value": "9 × 6"},
                    {"name": "answer", "value": "54"},
                    {"name": "category", "value": "multiplication"}
                ]
            },
            {
                "fields": [
                    {"name": "problem", "value": "144 ÷ 12"},
                    {"name": "answer", "value": "12"},
                    {"name": "category", "value": "division"}
                ]
            },
            {
                "fields": [
                    {"name": "problem", "value": "15 + 27"},
                    {"name": "answer", "value": "42"},
                    {"name": "category", "value": "addition"}
                ]
            }
        ]
    },
    {
        "name": "Countries and Capitals",
        "description": "World geography practice",
        "elements": [
            {
                "fields": [
                    {"name": "country", "value": "France"},
                    {"name": "capital", "value": "Paris"},
                    {"name": "continent", "value": "Europe"}
                ]
            },
            {
                "fields": [
                    {"name": "country", "value": "Japan"},
                    {"name": "capital", "value": "Tokyo"},
                    {"name": "continent", "value": "Asia"}
                ]
            },
            {
                "fields": [
                    {"name": "country", "value": "Brazil"},
                    {"name": "capital", "value": "Brasília"},
                    {"name": "continent", "value": "South America"}
                ]
            },
            {
                "fields": [
                    {"name": "country", "value": "Australia"},
                    {"name": "capital", "value": "Canberra"},
                    {"name": "continent", "value": "Oceania"}
                ]
            }
        ]
    }
]

def login_admin():
    """Login as admin and get access token"""
    login_data = {
        "email": "admin@example.com",
        "password": "admin123"
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def create_dataset_via_api(dataset_data, token):
    """Create a dataset using the admin API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # First create the dataset
    dataset_info = {
        "name": dataset_data["name"],
        "description": dataset_data["description"]
    }
    
    response = requests.post(f"{API_BASE}/datasets/", json=dataset_info, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create dataset '{dataset_data['name']}': {response.text}")
        return None
    
    dataset = response.json()
    dataset_id = dataset["id"]
    print(f"✅ Created dataset: {dataset_data['name']} (ID: {dataset_id})")
    
    # Add elements to the dataset
    for element_data in dataset_data["elements"]:
        element_payload = {
            "dataset_id": dataset_id,
            "fields": element_data["fields"]
        }
        
        response = requests.post(f"{API_BASE}/datasets/{dataset_id}/elements", json=element_payload, headers=headers)
        if response.status_code == 201:
            print(f"  ✅ Added element with fields: {[f['name'] + '=' + f['value'] for f in element_data['fields']]}")
        else:
            print(f"  ❌ Failed to add element: {response.text}")
    
    return dataset_id

def main():
    print("🚀 Creating demo datasets...")
    
    # Login as admin
    token = login_admin()
    if not token:
        sys.exit(1)
    
    print("✅ Logged in as admin")
    
    # Create each demo dataset
    created_datasets = []
    for dataset_data in demo_datasets:
        dataset_id = create_dataset_via_api(dataset_data, token)
        if dataset_id:
            created_datasets.append(dataset_id)
    
    print(f"\n🎉 Successfully created {len(created_datasets)} demo datasets!")
    print("\n📚 Available datasets:")
    for i, dataset in enumerate(demo_datasets, 1):
        print(f"  {i}. {dataset['name']} - {dataset['description']}")
    
    print(f"\n🎯 You can now test the learning functionality at http://localhost:3000")

if __name__ == "__main__":
    main()
