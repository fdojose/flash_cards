#!/usr/bin/env python3
"""
Upload Demo Script for Sub-Phase 3.2

This script demonstrates how to use the upload endpoints with the Lung Meridian dataset.
It shows both the file upload and JSON body upload methods.

Note: This requires a running FastAPI server and admin authentication.
"""

import json
import requests
import os

def demo_upload_endpoints():
    """Demo the upload functionality"""
    print("🫁 Dataset Upload Demo")
    print("=" * 30)
    
    # Sample Lung Meridian data (first 3 points for demo)
    sample_data = {
        "name": "Lung Meridian Points (Demo)",
        "description": "Sample points from the Lung channel for testing upload functionality",
        "elements": [
            {
                "code": "LU-1",
                "fields": {
                    "chinese_name": "中府",
                    "english_name": "Central Residence",
                    "location": "6 cun lateral to the anterior midline, 1 cun below LU-2, slightly medial to the lower border of the coracoid process.",
                    "how_to_find": "Locate LU-2 in the deltopectoral triangle, then palpate 1 cun downward along the deltoid border.",
                    "actions": [
                        "Regulates and descends Lung Qi",
                        "Clears Heat in the Upper Burner",
                        "Regulates water passages"
                    ],
                    "special_features": "Front-mu point of the Lung, meeting point with the Spleen channel, entry point."
                }
            },
            {
                "code": "LU-2",
                "fields": {
                    "chinese_name": "云门",
                    "english_name": "Cloud Gate",
                    "location": "6 cun lateral to the anterior midline, in the center of the deltopectoral triangle.",
                    "how_to_find": "Locate the junction between the clavicle and coracoid process in the deltopectoral triangle.",
                    "actions": [
                        "Clears Lung Heat",
                        "Descends Lung Qi",
                        "Opens the channel and sinew channel"
                    ],
                    "special_features": ""
                }
            }
        ]
    }
    
    print("📊 Sample Dataset Structure:")
    print(f"  Name: {sample_data['name']}")
    print(f"  Description: {sample_data['description']}")
    print(f"  Elements: {len(sample_data['elements'])}")
    
    print(f"\n📍 Sample Element (LU-1):")
    lu1 = sample_data['elements'][0]
    print(f"  Code: {lu1['code']}")
    print(f"  Fields: {list(lu1['fields'].keys())}")
    
    print(f"\n🔧 Field Types Detected:")
    for field_name, field_value in lu1['fields'].items():
        if isinstance(field_value, list):
            field_type = "json (list)"
        elif isinstance(field_value, dict):
            field_type = "json (object)"
        else:
            field_type = "text"
        print(f"  {field_name}: {field_type}")
    
    print(f"\n📝 Upload Instructions:")
    print("  1. Start the FastAPI server:")
    print("     cd backend && uvicorn main:app --reload")
    print("  ")
    print("  2. Register an admin user:")
    print("     POST /auth/register")
    print("     {\"email\": \"admin@example.com\", \"password\": \"password123\", \"is_admin\": true}")
    print("  ")
    print("  3. Login to get JWT token:")
    print("     POST /auth/login")
    print("     {\"email\": \"admin@example.com\", \"password\": \"password123\"}")
    print("  ")
    print("  4. Upload via JSON body:")
    print("     POST /datasets/json")
    print("     Headers: {\"Authorization\": \"Bearer <jwt_token>\"}")
    print("     Body: <sample_data_json>")
    print("  ")
    print("  5. Upload via file:")
    print("     POST /datasets/upload")
    print("     Headers: {\"Authorization\": \"Bearer <jwt_token>\"}")
    print("     Form-data: file=<lung_meridian.json>")
    
    # Save sample data to file for upload testing
    sample_file = "lung_meridian_sample.json"
    with open(sample_file, 'w') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Sample data saved to: {sample_file}")
    print("  Use this file to test the /datasets/upload endpoint")
    
    print(f"\n🌐 API Endpoints Available:")
    print("  GET    /datasets/              - List all datasets")
    print("  GET    /datasets/{id}          - Get specific dataset") 
    print("  POST   /datasets/              - Create empty dataset")
    print("  POST   /datasets/upload        - Upload dataset from file")
    print("  POST   /datasets/json          - Upload dataset from JSON body")
    print("  GET    /datasets/{id}/elements - Get dataset elements")
    print("  DELETE /datasets/{id}          - Delete dataset")
    
    print(f"\n✅ Upload demo completed!")
    return True

def demo_curl_commands():
    """Show sample curl commands for testing"""
    print(f"\n🔧 Sample cURL Commands:")
    print("=" * 25)
    
    print("# 1. Register admin user")
    print('curl -X POST "http://localhost:8000/auth/register" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"email": "admin@example.com", "password": "password123", "is_admin": true}\'')
    
    print("\n# 2. Login to get token")
    print('curl -X POST "http://localhost:8000/auth/login" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"email": "admin@example.com", "password": "password123"}\'')
    
    print("\n# 3. Upload dataset via file")
    print('curl -X POST "http://localhost:8000/datasets/upload" \\')
    print('  -H "Authorization: Bearer <jwt_token>" \\')
    print('  -F "file=@lung_meridian_sample.json"')
    
    print("\n# 4. Upload dataset via JSON body")
    print('curl -X POST "http://localhost:8000/datasets/json" \\')
    print('  -H "Authorization: Bearer <jwt_token>" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d @lung_meridian_sample.json')
    
    print("\n# 5. List uploaded datasets")
    print('curl -X GET "http://localhost:8000/datasets/" \\')
    print('  -H "Authorization: Bearer <jwt_token>"')
    
    return True

def main():
    """Run the upload demo"""
    demo_upload_endpoints()
    demo_curl_commands()
    
    print(f"\n🎉 Upload endpoint demo completed!")
    print(f"\n🚀 Ready to test with a running FastAPI server!")

if __name__ == "__main__":
    main()
