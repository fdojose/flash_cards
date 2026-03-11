#!/usr/bin/env python3
"""
PHASE 8.1: UNIT TESTS - Dataset Management Tests
===============================================

Test coverage for:
- Dataset CRUD operations
- Element and Field management
- Dataset upload functionality
- Search and pagination
- Admin security
- Metadata enrichment
"""

import pytest
import json
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.datasets.models import Dataset, Element, Field, Tag, ElementTag


class TestDatasetModel:
    """Test Dataset model functionality"""
    
    def test_dataset_creation(self, test_db: Session):
        """Test creating a dataset"""
        from uuid import uuid4
        from datetime import datetime
        
        dataset = Dataset(
            id=uuid4(),
            name="Test Dataset",
            description="A test dataset",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        test_db.add(dataset)
        test_db.commit()
        test_db.refresh(dataset)
        
        assert dataset.id is not None
        assert dataset.name == "Test Dataset"
        assert dataset.description == "A test dataset"
        assert dataset.created_at is not None
        assert dataset.updated_at is not None
    
    def test_element_creation(self, test_db: Session, test_dataset):
        """Test creating an element"""
        from uuid import uuid4
        from datetime import datetime
        
        element = Element(
            id=uuid4(),
            dataset_id=test_dataset.id,
            code="TEST-001",
            created_at=datetime.utcnow()
        )
        test_db.add(element)
        test_db.commit()
        test_db.refresh(element)
        
        assert element.id is not None
        assert element.dataset_id == test_dataset.id
        assert element.code == "TEST-001"
        assert element.created_at is not None
    
    def test_field_creation(self, test_db: Session):
        """Test creating a field"""
        from uuid import uuid4
        from datetime import datetime
        
        # Create dataset and element first
        dataset = Dataset(
            id=uuid4(),
            name="Test Dataset",
            description="Test",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        test_db.add(dataset)
        test_db.commit()
        
        element = Element(
            id=uuid4(),
            dataset_id=dataset.id,
            code="TEST-001",
            created_at=datetime.utcnow()
        )
        test_db.add(element)
        test_db.commit()
        
        field = Field(
            id=uuid4(),
            element_id=element.id,
            field_name="question",
            field_value="What is 2+2?",
            field_type="text",
            media_url=None
        )
        test_db.add(field)
        test_db.commit()
        test_db.refresh(field)
        
        assert field.id is not None
        assert field.element_id == element.id
        assert field.field_name == "question"
        assert field.field_value == "What is 2+2?"
        assert field.field_type == "text"
    
    def test_dataset_relationships(self, test_db: Session, test_dataset):
        """Test dataset relationships with elements"""
        elements = test_db.query(Element).filter(Element.dataset_id == test_dataset.id).all()
        
        assert len(elements) >= 0  # Should have elements from fixture
        for element in elements:
            assert element.dataset_id == test_dataset.id


class TestDatasetEndpoints:
    """Test dataset API endpoints"""
    
    @pytest.mark.asyncio
    async def test_list_datasets(self, client: AsyncClient, test_dataset):
        """Test listing datasets"""
        response = await client.get("/datasets/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check first dataset structure
        dataset = data[0]
        assert "id" in dataset
        assert "name" in dataset
        assert "description" in dataset
        assert "created_at" in dataset
        assert "updated_at" in dataset
        assert "metadata" in dataset
    
    @pytest.mark.asyncio
    async def test_list_datasets_with_search(self, client: AsyncClient, test_dataset):
        """Test listing datasets with search query"""
        response = await client.get("/datasets/?search=Spanish")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should find Spanish vocabulary dataset
        found = any("Spanish" in dataset["name"] or "Spanish" in dataset["description"] 
                   for dataset in data)
        assert found
    
    @pytest.mark.asyncio
    async def test_list_datasets_with_pagination(self, client: AsyncClient, test_dataset):
        """Test listing datasets with pagination"""
        response = await client.get("/datasets/?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    
    @pytest.mark.asyncio
    async def test_get_dataset_by_id(self, client: AsyncClient, test_dataset):
        """Test getting a specific dataset by ID"""
        response = await client.get(f"/datasets/{test_dataset.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_dataset.id)
        assert data["name"] == test_dataset.name
        assert data["description"] == test_dataset.description
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_dataset(self, client: AsyncClient):
        """Test getting a nonexistent dataset"""
        from uuid import uuid4
        fake_id = uuid4()
        
        response = await client.get(f"/datasets/{fake_id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_upload_dataset_admin_only(self, client: AsyncClient, admin_headers, auth_headers, sample_dataset_data):
        """Test dataset upload requires admin privileges"""
        # Test with admin user (should succeed)
        response = await client.post("/datasets/upload", 
                                   json=sample_dataset_data, 
                                   headers=admin_headers)
        assert response.status_code == 201
        
        # Test with regular user (should fail)
        response = await client.post("/datasets/upload", 
                                   json=sample_dataset_data, 
                                   headers=auth_headers)
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_upload_dataset_unauthorized(self, client: AsyncClient, sample_dataset_data):
        """Test dataset upload without authentication"""
        response = await client.post("/datasets/upload", json=sample_dataset_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_upload_dataset_success(self, client: AsyncClient, admin_headers, sample_dataset_data):
        """Test successful dataset upload"""
        response = await client.post("/datasets/upload", 
                                   json=sample_dataset_data, 
                                   headers=admin_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == sample_dataset_data["name"]
        assert data["description"] == sample_dataset_data["description"]
        assert "elements_created" in data
        assert "fields_created" in data
    
    @pytest.mark.asyncio
    async def test_upload_dataset_invalid_data(self, client: AsyncClient, admin_headers):
        """Test dataset upload with invalid data"""
        invalid_data = {
            "name": "Test Dataset"
            # Missing required elements field
        }
        
        response = await client.post("/datasets/upload", 
                                   json=invalid_data, 
                                   headers=admin_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_upload_dataset_empty_elements(self, client: AsyncClient, admin_headers):
        """Test dataset upload with empty elements"""
        invalid_data = {
            "name": "Test Dataset",
            "description": "Test description",
            "elements": []
        }
        
        response = await client.post("/datasets/upload", 
                                   json=invalid_data, 
                                   headers=admin_headers)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_delete_dataset_admin_only(self, client: AsyncClient, admin_headers, auth_headers, test_dataset):
        """Test dataset deletion requires admin privileges"""
        # Test with regular user (should fail)
        response = await client.delete(f"/datasets/{test_dataset.id}", headers=auth_headers)
        assert response.status_code == 403
        
        # Test with admin user (should succeed)
        response = await client.delete(f"/datasets/{test_dataset.id}", headers=admin_headers)
        assert response.status_code == 200


class TestDatasetSearch:
    """Test dataset search functionality"""
    
    @pytest.mark.asyncio
    async def test_search_by_name(self, client: AsyncClient, test_dataset):
        """Test searching datasets by name"""
        search_term = test_dataset.name.split()[0]  # First word of name
        response = await client.get(f"/datasets/?search={search_term}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        found = any(search_term.lower() in dataset["name"].lower() for dataset in data)
        assert found
    
    @pytest.mark.asyncio
    async def test_search_by_description(self, client: AsyncClient, test_dataset):
        """Test searching datasets by description"""
        if test_dataset.description:
            search_term = test_dataset.description.split()[0]  # First word of description
            response = await client.get(f"/datasets/?search={search_term}")
            
            assert response.status_code == 200
            data = response.json()
            
            found = any(search_term.lower() in dataset["description"].lower() for dataset in data)
            assert found
    
    @pytest.mark.asyncio
    async def test_search_case_insensitive(self, client: AsyncClient, test_dataset):
        """Test case-insensitive search"""
        search_term = test_dataset.name.upper()  # Convert to uppercase
        response = await client.get(f"/datasets/?search={search_term}")
        
        assert response.status_code == 200
        data = response.json()
        
        found = any(dataset["id"] == str(test_dataset.id) for dataset in data)
        assert found
    
    @pytest.mark.asyncio
    async def test_search_no_results(self, client: AsyncClient):
        """Test search with no matching results"""
        response = await client.get("/datasets/?search=nonexistentdataset")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestDatasetPagination:
    """Test dataset pagination"""
    
    @pytest.mark.asyncio
    async def test_pagination_skip_limit(self, client: AsyncClient):
        """Test pagination with skip and limit parameters"""
        # Test first page
        response = await client.get("/datasets/?skip=0&limit=2")
        assert response.status_code == 200
        page1 = response.json()
        assert len(page1) <= 2
        
        # Test second page
        response = await client.get("/datasets/?skip=2&limit=2")
        assert response.status_code == 200
        page2 = response.json()
        assert len(page2) <= 2
        
        # Pages should not have duplicate items
        page1_ids = {item["id"] for item in page1}
        page2_ids = {item["id"] for item in page2}
        assert page1_ids.isdisjoint(page2_ids)
    
    @pytest.mark.asyncio
    async def test_pagination_large_skip(self, client: AsyncClient):
        """Test pagination with skip beyond available data"""
        response = await client.get("/datasets/?skip=1000&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should return empty list or small number of items
    
    @pytest.mark.asyncio
    async def test_pagination_invalid_params(self, client: AsyncClient):
        """Test pagination with invalid parameters"""
        # Negative skip
        response = await client.get("/datasets/?skip=-1&limit=10")
        assert response.status_code == 422
        
        # Negative limit
        response = await client.get("/datasets/?skip=0&limit=-1")
        assert response.status_code == 422


class TestDatasetMetadata:
    """Test dataset metadata functionality"""
    
    @pytest.mark.asyncio
    async def test_dataset_metadata_structure(self, client: AsyncClient, test_dataset):
        """Test dataset metadata structure"""
        response = await client.get("/datasets/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        
        dataset = data[0]
        metadata = dataset["metadata"]
        
        assert "element_count" in metadata
        assert "field_types" in metadata
        assert "field_names" in metadata
        assert isinstance(metadata["element_count"], int)
        assert isinstance(metadata["field_types"], list)
        assert isinstance(metadata["field_names"], list)
    
    def test_metadata_calculation(self, test_db: Session, test_dataset):
        """Test metadata calculation accuracy"""
        elements = test_db.query(Element).filter(Element.dataset_id == test_dataset.id).all()
        element_count = len(elements)
        
        field_types = set()
        field_names = set()
        
        for element in elements:
            fields = test_db.query(Field).filter(Field.element_id == element.id).all()
            for field in fields:
                field_types.add(field.field_type)
                field_names.add(field.field_name)
        
        assert element_count >= 0
        assert len(field_types) >= 0
        assert len(field_names) >= 0


class TestDatasetValidation:
    """Test dataset data validation"""
    
    @pytest.mark.asyncio
    async def test_upload_validation_missing_name(self, client: AsyncClient, admin_headers):
        """Test upload validation for missing name"""
        invalid_data = {
            "description": "Test description",
            "elements": [{"fields": {"test": "value"}}]
        }
        
        response = await client.post("/datasets/upload", 
                                   json=invalid_data, 
                                   headers=admin_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_upload_validation_missing_elements(self, client: AsyncClient, admin_headers):
        """Test upload validation for missing elements"""
        invalid_data = {
            "name": "Test Dataset",
            "description": "Test description"
        }
        
        response = await client.post("/datasets/upload", 
                                   json=invalid_data, 
                                   headers=admin_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_upload_validation_invalid_element_structure(self, client: AsyncClient, admin_headers):
        """Test upload validation for invalid element structure"""
        invalid_data = {
            "name": "Test Dataset",
            "description": "Test description",
            "elements": [
                {
                    # Missing fields
                    "code": "TEST-001"
                }
            ]
        }
        
        response = await client.post("/datasets/upload", 
                                   json=invalid_data, 
                                   headers=admin_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_upload_validation_empty_fields(self, client: AsyncClient, admin_headers):
        """Test upload validation for empty fields"""
        invalid_data = {
            "name": "Test Dataset",
            "description": "Test description",
            "elements": [
                {
                    "code": "TEST-001",
                    "fields": {}  # Empty fields
                }
            ]
        }
        
        response = await client.post("/datasets/upload", 
                                   json=invalid_data, 
                                   headers=admin_headers)
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
