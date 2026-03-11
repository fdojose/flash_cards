#!/usr/bin/env python3
"""
Sub-Phase 3.3: Dataset Listing - Comprehensive Test Suite

This test suite validates the enhanced dataset listing functionality including:
- Basic dataset listing with metadata
- Search functionality
- Pagination
- Element listing for datasets
- Field summaries
- Performance and edge cases

Tests ensure the frontend can effectively show dataset lists with rich metadata.
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test framework and utilities
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Application imports
from main import app
from app.database import get_db, Base
from app.auth.models import User, UserRole
from app.datasets.models import Dataset, Element, Field
from app.auth.utils import get_password_hash, create_access_token


class TestSubPhase33:
    """Test class for Dataset Listing functionality"""
    
    def __init__(self):
        self.engine = None
        self.TestingSessionLocal = None
        self.client = None
        self.admin_token = None
        self.user_token = None
        self.test_datasets = []
        
    def setup_test_db(self):
        """Set up test database with in-memory SQLite"""
        print("🔧 Setting up test database...")
        
        # Use in-memory SQLite for testing
        SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
        self.engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
        
        # Override dependency
        def override_get_db():
            try:
                db = self.TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)
        
        print("✅ Test database setup complete")
    
    def create_test_users(self):
        """Create test users with proper roles"""
        print("👥 Creating test users...")
        
        db = self.TestingSessionLocal()
        try:
            # Create admin user
            admin_user = User(
                id="admin-uuid-test",
                name="Test Admin",
                email="admin@test.com",
                password_hash=get_password_hash("admin123")
            )
            db.add(admin_user)
            
            # Create admin role
            admin_role = UserRole(user_id="admin-uuid-test", role="admin")
            db.add(admin_role)
            
            # Create regular user
            regular_user = User(
                id="user-uuid-test",
                name="Test User",
                email="user@test.com",
                password_hash=get_password_hash("user123")
            )
            db.add(regular_user)
            
            # Create user role
            user_role = UserRole(user_id="user-uuid-test", role="user")
            db.add(user_role)
            
            db.commit()
            
            # Generate tokens
            self.admin_token = create_access_token(data={"sub": "admin@test.com"})
            self.user_token = create_access_token(data={"sub": "user@test.com"})
            
            print("✅ Test users created successfully")
            
        except Exception as e:
            print(f"❌ Error creating test users: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def create_test_datasets(self):
        """Create diverse test datasets for comprehensive testing"""
        print("📚 Creating test datasets...")
        
        db = self.TestingSessionLocal()
        try:
            # Dataset 1: Acupuncture Points (rich data)
            acup_dataset = Dataset(
                id="dataset1-uuid-test",
                name="Acupuncture Points - Lung Meridian",
                description="Traditional Chinese Medicine acupuncture points on the Lung meridian"
            )
            db.add(acup_dataset)
            
            # Elements for acupuncture dataset
            acup_elements_data = [
                {
                    "code": "LU-1",
                    "fields": {
                        "chinese_name": "中府",
                        "pinyin": "Zhōngfǔ",
                        "english_name": "Central Treasury",
                        "location": "On the lateral chest in the first intercostal space",
                        "functions": "Regulates lung qi, stops cough",
                        "image_url": "https://example.com/lu1.jpg"
                    }
                },
                {
                    "code": "LU-2", 
                    "fields": {
                        "chinese_name": "雲門",
                        "pinyin": "Yúnmén",
                        "english_name": "Cloud Gate",
                        "location": "In the subclavicular fossa",
                        "functions": "Dispels phlegm, stops cough",
                        "image_url": "https://example.com/lu2.jpg"
                    }
                },
                {
                    "code": "LU-3",
                    "fields": {
                        "chinese_name": "天府",
                        "pinyin": "Tiānfǔ",
                        "english_name": "Heavenly Palace",
                        "location": "On the radial side of biceps brachii",
                        "functions": "Calms the spirit, regulates qi"
                    }
                }
            ]
            
            for elem_data in acup_elements_data:
                element = Element(
                    dataset_id="dataset1-uuid-test",
                    code=elem_data["code"]
                )
                db.add(element)
                db.flush()  # Get the element ID
                
                # Add fields
                for field_name, field_value in elem_data["fields"].items():
                    field_type = "image" if "image" in field_name or "url" in field_name else "text"
                    field = Field(
                        element_id=element.id,
                        field_name=field_name,
                        field_value=field_value,
                        field_type=field_type,
                        media_url=field_value if field_type == "image" else None
                    )
                    db.add(field)
            
            # Dataset 2: Simple vocabulary (minimal data)
            vocab_dataset = Dataset(
                id="dataset2-uuid-test",
                name="Spanish Vocabulary",
                description="Basic Spanish words for beginners"
            )
            db.add(vocab_dataset)
            
            # Simple elements for vocabulary
            vocab_elements = [
                {"spanish": "hola", "english": "hello"},
                {"spanish": "gracias", "english": "thank you"},
                {"spanish": "por favor", "english": "please"},
                {"spanish": "adiós", "english": "goodbye"},
                {"spanish": "sí", "english": "yes"}
            ]
            
            for vocab_data in vocab_elements:
                element = Element(
                    dataset_id="dataset2-uuid-test"
                )
                db.add(element)
                db.flush()
                
                for field_name, field_value in vocab_data.items():
                    field = Field(
                        element_id=element.id,
                        field_name=field_name,
                        field_value=field_value,
                        field_type="text"
                    )
                    db.add(field)
            
            # Dataset 3: Mixed media dataset
            media_dataset = Dataset(
                id="dataset3-uuid-test",
                name="Musical Instruments",
                description="Learn musical instruments with audio samples"
            )
            db.add(media_dataset)
            
            # Mixed media elements
            media_elements = [
                {
                    "fields": {
                        "name": "Piano",
                        "category": "Keyboard",
                        "description": "A large musical instrument with keys",
                        "audio_sample": "https://example.com/piano.mp3",
                        "image": "https://example.com/piano.jpg"
                    }
                },
                {
                    "fields": {
                        "name": "Violin", 
                        "category": "String",
                        "description": "A four-stringed musical instrument",
                        "audio_sample": "https://example.com/violin.mp3",
                        "image": "https://example.com/violin.jpg"
                    }
                }
            ]
            
            for elem_data in media_elements:
                element = Element(dataset_id="dataset3-uuid-test")
                db.add(element)
                db.flush()
                
                for field_name, field_value in elem_data["fields"].items():
                    field_type = "text"
                    if "audio" in field_name:
                        field_type = "audio"
                    elif "image" in field_name:
                        field_type = "image"
                    
                    field = Field(
                        element_id=element.id,
                        field_name=field_name,
                        field_value=field_value,
                        field_type=field_type,
                        media_url=field_value if field_type in ["audio", "image"] else None
                    )
                    db.add(field)
            
            # Dataset 4: Empty dataset (edge case)
            empty_dataset = Dataset(
                id="dataset4-uuid-test",
                name="Empty Dataset",
                description="A dataset with no elements for testing edge cases"
            )
            db.add(empty_dataset)
            
            db.commit()
            
            self.test_datasets = [
                {"id": "dataset1-uuid-test", "name": "Acupuncture Points - Lung Meridian", "element_count": 3},
                {"id": "dataset2-uuid-test", "name": "Spanish Vocabulary", "element_count": 5},
                {"id": "dataset3-uuid-test", "name": "Musical Instruments", "element_count": 2},
                {"id": "dataset4-uuid-test", "name": "Empty Dataset", "element_count": 0}
            ]
            
            print("✅ Test datasets created successfully")
            
        except Exception as e:
            print(f"❌ Error creating test datasets: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def test_basic_dataset_listing(self):
        """Test 1: Basic dataset listing functionality"""
        print("\n🧪 Test 1: Basic dataset listing")
        
        response = self.client.get(
            "/api/v1/datasets/",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 4, f"Expected 4 datasets, got {len(data)}"
        
        # Check structure of first dataset
        first_dataset = data[0]
        required_fields = ["id", "name", "description", "created_at", "updated_at", "metadata"]
        for field in required_fields:
            assert field in first_dataset, f"Missing field: {field}"
        
        # Check metadata structure
        metadata = first_dataset["metadata"]
        metadata_fields = ["element_count", "field_types", "field_names"]
        for field in metadata_fields:
            assert field in metadata, f"Missing metadata field: {field}"
        
        print("✅ Basic dataset listing works correctly")
    
    def test_dataset_listing_with_search(self):
        """Test 2: Dataset search functionality"""
        print("\n🧪 Test 2: Dataset search functionality")
        
        # Test search by name
        response = self.client.get(
            "/api/v1/datasets/?search=acupuncture",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1, f"Expected 1 dataset for 'acupuncture' search, got {len(data)}"
        assert "Acupuncture" in data[0]["name"]
        
        # Test search by description
        response = self.client.get(
            "/api/v1/datasets/?search=spanish",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1, f"Expected 1 dataset for 'spanish' search, got {len(data)}"
        
        # Test case-insensitive search
        response = self.client.get(
            "/api/v1/datasets/?search=MUSICAL",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1, f"Expected 1 dataset for case-insensitive search, got {len(data)}"
        
        # Test no results
        response = self.client.get(
            "/api/v1/datasets/?search=nonexistent",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0, f"Expected 0 datasets for nonexistent search, got {len(data)}"
        
        print("✅ Dataset search functionality works correctly")
    
    def test_dataset_listing_pagination(self):
        """Test 3: Pagination functionality"""
        print("\n🧪 Test 3: Pagination functionality")
        
        # Test limit
        response = self.client.get(
            "/api/v1/datasets/?limit=2",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2, f"Expected 2 datasets with limit=2, got {len(data)}"
        
        # Test skip
        response = self.client.get(
            "/api/v1/datasets/?skip=2&limit=2",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2, f"Expected 2 datasets with skip=2&limit=2, got {len(data)}"
        
        # Test skip beyond available
        response = self.client.get(
            "/api/v1/datasets/?skip=10",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0, f"Expected 0 datasets with skip=10, got {len(data)}"
        
        print("✅ Pagination functionality works correctly")
    
    def test_dataset_count_endpoint(self):
        """Test 4: Dataset count endpoint"""
        print("\n🧪 Test 4: Dataset count endpoint")
        
        # Test total count
        response = self.client.get(
            "/api/v1/datasets/count",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_count" in data
        assert data["total_count"] == 4, f"Expected total count 4, got {data['total_count']}"
        
        # Test count with search
        response = self.client.get(
            "/api/v1/datasets/count?search=spanish",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1, f"Expected count 1 for Spanish search, got {data['total_count']}"
        
        print("✅ Dataset count endpoint works correctly")
    
    def test_dataset_elements_listing(self):
        """Test 5: Dataset elements listing"""
        print("\n🧪 Test 5: Dataset elements listing")
        
        # Test getting elements for acupuncture dataset
        response = self.client.get(
            f"/api/v1/datasets/dataset1-uuid-test/elements",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3, f"Expected 3 elements, got {len(data)}"
        
        # Check element structure
        first_element = data[0]
        required_fields = ["id", "code", "created_at", "fields"]
        for field in required_fields:
            assert field in first_element, f"Missing element field: {field}"
        
        # Check fields structure
        assert len(first_element["fields"]) > 0, "Element should have fields"
        first_field = first_element["fields"][0]
        field_fields = ["id", "field_name", "field_value", "field_type"]
        for field in field_fields:
            assert field in first_field, f"Missing field property: {field}"
        
        # Test pagination for elements
        response = self.client.get(
            f"/api/v1/datasets/dataset1-uuid-test/elements?limit=2",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2, f"Expected 2 elements with limit, got {len(data)}"
        
        # Test nonexistent dataset
        response = self.client.get(
            "/api/v1/datasets/nonexistent-uuid/elements",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 404
        
        print("✅ Dataset elements listing works correctly")
    
    def test_dataset_field_summary(self):
        """Test 6: Dataset field summary"""
        print("\n🧪 Test 6: Dataset field summary")
        
        # Test field summary for acupuncture dataset
        response = self.client.get(
            f"/api/v1/datasets/dataset1-uuid-test/fields/summary",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "dataset_id" in data
        assert "field_summary" in data
        assert data["dataset_id"] == "dataset1-uuid-test"
        
        field_summary = data["field_summary"]
        
        # Check that expected fields are present
        expected_fields = ["chinese_name", "pinyin", "english_name", "location", "functions"]
        for field_name in expected_fields:
            assert field_name in field_summary, f"Missing field in summary: {field_name}"
            assert "types" in field_summary[field_name]
            assert "total_usage" in field_summary[field_name]
        
        # Test mixed media dataset
        response = self.client.get(
            f"/api/v1/datasets/dataset3-uuid-test/fields/summary",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        field_summary = data["field_summary"]
        
        # Should have different field types
        has_text = False
        has_audio = False
        has_image = False
        
        for field_data in field_summary.values():
            types = field_data["types"]
            if "text" in types:
                has_text = True
            if "audio" in types:
                has_audio = True  
            if "image" in types:
                has_image = True
        
        assert has_text, "Should have text fields"
        assert has_audio, "Should have audio fields"
        assert has_image, "Should have image fields"
        
        # Test empty dataset
        response = self.client.get(
            f"/api/v1/datasets/dataset4-uuid-test/fields/summary",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["field_summary"] == {}, "Empty dataset should have empty field summary"
        
        print("✅ Dataset field summary works correctly")
    
    def test_metadata_accuracy(self):
        """Test 7: Metadata accuracy validation"""
        print("\n🧪 Test 7: Metadata accuracy validation")
        
        response = self.client.get(
            "/api/v1/datasets/",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert response.status_code == 200
        datasets = response.json()
        
        # Find and validate each test dataset
        for test_dataset in self.test_datasets:
            found_dataset = None
            for dataset in datasets:
                if dataset["id"] == test_dataset["id"]:
                    found_dataset = dataset
                    break
            
            assert found_dataset is not None, f"Dataset {test_dataset['id']} not found"
            
            metadata = found_dataset["metadata"]
            assert metadata["element_count"] == test_dataset["element_count"], \
                f"Element count mismatch for {test_dataset['name']}"
            
            # Validate field types and names are lists
            assert isinstance(metadata["field_types"], list)
            assert isinstance(metadata["field_names"], list)
            
            # Validate specific metadata for known datasets
            if test_dataset["id"] == "dataset1-uuid-test":  # Acupuncture
                assert "text" in metadata["field_types"]
                assert "image" in metadata["field_types"]
                expected_fields = ["chinese_name", "pinyin", "english_name", "location", "functions"]
                for field in expected_fields:
                    assert field in metadata["field_names"], f"Missing field {field} in acupuncture dataset"
            
            elif test_dataset["id"] == "dataset3-uuid-test":  # Musical Instruments
                assert "text" in metadata["field_types"]
                assert "audio" in metadata["field_types"]
                assert "image" in metadata["field_types"]
        
        print("✅ Metadata accuracy validation passed")
    
    def test_authentication_required(self):
        """Test 8: Authentication requirements"""
        print("\n🧪 Test 8: Authentication requirements")
        
        # Test without token
        response = self.client.get("/api/v1/datasets/")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        
        # Test with invalid token
        response = self.client.get(
            "/api/v1/datasets/",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401, f"Expected 401 with invalid token, got {response.status_code}"
        
        # Test user access (should work)
        response = self.client.get(
            "/api/v1/datasets/",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert response.status_code == 200, f"Expected 200 with user token, got {response.status_code}"
        
        print("✅ Authentication requirements working correctly")
    
    def test_error_handling(self):
        """Test 9: Error handling and edge cases"""
        print("\n🧪 Test 9: Error handling and edge cases")
        
        # Test invalid pagination parameters
        response = self.client.get(
            "/api/v1/datasets/?skip=-1",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert response.status_code == 422, "Should reject negative skip"
        
        response = self.client.get(
            "/api/v1/datasets/?limit=0",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert response.status_code == 422, "Should reject zero limit"
        
        response = self.client.get(
            "/api/v1/datasets/?limit=2000",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert response.status_code == 422, "Should reject excessive limit"
        
        # Test nonexistent dataset endpoints
        response = self.client.get(
            "/api/v1/datasets/nonexistent-uuid",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert response.status_code == 404
        
        response = self.client.get(
            "/api/v1/datasets/nonexistent-uuid/fields/summary",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert response.status_code == 404
        
        print("✅ Error handling working correctly")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Sub-Phase 3.3: Dataset Listing Test Suite")
        print("=" * 60)
        
        try:
            # Setup
            self.setup_test_db()
            self.create_test_users() 
            self.create_test_datasets()
            
            # Run tests
            self.test_basic_dataset_listing()
            self.test_dataset_listing_with_search()
            self.test_dataset_listing_pagination()
            self.test_dataset_count_endpoint()
            self.test_dataset_elements_listing()
            self.test_dataset_field_summary()
            self.test_metadata_accuracy()
            self.test_authentication_required()
            self.test_error_handling()
            
            print("\n" + "=" * 60)
            print("🎉 ALL TESTS PASSED! Sub-Phase 3.3 Implementation Complete")
            print("\n✅ Dataset Listing Features Validated:")
            print("   • Enhanced dataset listing with metadata")
            print("   • Search functionality (name and description)")
            print("   • Pagination support")
            print("   • Dataset count endpoint")
            print("   • Element listing per dataset")
            print("   • Field usage summaries")
            print("   • Authentication protection")
            print("   • Error handling and validation")
            print("\n🔄 Ready for Sub-Phase 4.1: Learning Session Models!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main test execution"""
    test_suite = TestSubPhase33()
    success = test_suite.run_all_tests()
    
    if not success:
        sys.exit(1)
    
    print("\n🎯 Sub-Phase 3.3: Dataset Listing - IMPLEMENTATION COMPLETE")
    print("💡 Frontend can now effectively show dataset lists with rich metadata")


if __name__ == "__main__":
    main()
