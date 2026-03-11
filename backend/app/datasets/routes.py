"""
Dataset Routes

FastAPI routes for dataset management, upload, and listing.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
import json

from .models import Dataset, Element, Field
from .schemas import DatasetCreate, DatasetResponse, DatasetUpload, ElementResponse, DatasetListResponse, DatasetMetadata, DatasetUploadResponse
from ..auth.dependencies import get_current_user, get_admin_user
from ..auth.models import User
from ..database import get_db

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("/", response_model=List[DatasetListResponse])
async def list_datasets(
    skip: int = Query(0, ge=0, description="Number of datasets to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of datasets to return"),
    search: Optional[str] = Query(None, description="Search datasets by name or description"),
    include_inactive: bool = Query(False, description="Include inactive/disabled datasets"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all available datasets with metadata
    
    This endpoint returns datasets with enriched metadata including:
    - Element count
    - Available field types
    - Available field names
    - Search filtering support
    - Active/inactive status filtering
    """
    # Build base query
    query = db.query(Dataset)
    
    # Filter by active status (default: only active datasets)
    if not include_inactive:
        query = query.filter(Dataset.is_active == True)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            func.lower(Dataset.name).like(search_term) |
            func.lower(Dataset.description).like(search_term)
        )
    
    # Apply pagination
    datasets = query.offset(skip).limit(limit).all()
    
    # Build response with metadata
    result = []
    for dataset in datasets:
        # Get element count
        element_count = db.query(func.count(Element.id)).filter(
            Element.dataset_id == dataset.id
        ).scalar()
        
        # Get distinct field types and names
        field_types_query = db.query(distinct(Field.field_type)).join(Element).filter(Element.dataset_id == dataset.id).all()
        field_names_query = db.query(distinct(Field.field_name)).join(Element).filter(Element.dataset_id == dataset.id).all()
        
        field_types = [row[0] for row in field_types_query if row[0]]
        field_names = [row[0] for row in field_names_query if row[0]]
        
        # Create metadata
        metadata = DatasetMetadata(
            element_count=element_count,
            field_types=field_types,
            field_names=field_names
        )
        
        # Create enhanced response
        dataset_response = DatasetListResponse(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            is_active=dataset.is_active,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            metadata=metadata
        )
        
        result.append(dataset_response)
    
    return result


@router.get("/count")
async def get_datasets_count(
    search: Optional[str] = Query(None, description="Search datasets by name or description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get total count of datasets (optionally filtered by search)"""
    query = db.query(func.count(Dataset.id))
    
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            func.lower(Dataset.name).like(search_term) |
            func.lower(Dataset.description).like(search_term)
        )
    
    total_count = query.scalar()
    return {"total_count": total_count}


@router.get("/{dataset_id}/elements", response_model=List[ElementResponse])
async def get_dataset_elements(
    dataset_id: str,
    skip: int = Query(0, ge=0, description="Number of elements to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of elements to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get elements for a specific dataset with pagination"""
    # Check if dataset exists
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Get elements with their fields
    elements = db.query(Element).filter(
        Element.dataset_id == dataset_id
    ).offset(skip).limit(limit).all()
    
    return [ElementResponse.from_orm(element) for element in elements]


@router.get("/{dataset_id}/fields/summary")
async def get_dataset_field_summary(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a summary of field usage in a dataset"""
    # Check if dataset exists
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Get field statistics
    field_stats = db.query(
        Field.field_name,
        Field.field_type,
        func.count(Field.id).label('usage_count')
    ).join(Element).filter(
        Element.dataset_id == dataset_id
    ).group_by(Field.field_name, Field.field_type).all()
    
    field_summary = {}
    for stat in field_stats:
        field_name = stat.field_name
        if field_name not in field_summary:
            field_summary[field_name] = {
                "types": {},
                "total_usage": 0
            }
        field_summary[field_name]["types"][stat.field_type] = stat.usage_count
        field_summary[field_name]["total_usage"] += stat.usage_count
    
    return {
        "dataset_id": dataset_id,
        "field_summary": field_summary
    }


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific dataset by ID"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    return DatasetResponse.from_orm(dataset)


@router.post("/", response_model=DatasetResponse)
async def create_dataset(
    dataset_data: DatasetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Admin only
):
    """Create a new dataset (admin only)"""
    db_dataset = Dataset(
        name=dataset_data.name,
        description=dataset_data.description
    )
    
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    
    return DatasetResponse.from_orm(db_dataset)


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Admin only
):
    """Upload a dataset from JSON file (admin only)"""
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a JSON file"
        )
    
    try:
        content = await file.read()
        data = json.loads(content.decode('utf-8'))
        
        # Validate data structure
        if not isinstance(data, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON structure. Root must be an object."
            )
        
        if 'name' not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required field: 'name'"
            )
        
        if 'elements' not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required field: 'elements'"
            )
        
        if not isinstance(data['elements'], list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'elements' must be an array"
            )
        
        if len(data['elements']) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset must contain at least one element"
            )
        
        # Create dataset
        db_dataset = Dataset(
            name=data['name'],
            description=data.get('description', '')
        )
        db.add(db_dataset)
        db.flush()  # Get the dataset ID without committing
        
        elements_created = 0
        fields_created = 0
        
        # Create elements and fields
        for element_data in data['elements']:
            if not isinstance(element_data, dict):
                continue
                
            db_element = Element(
                dataset_id=db_dataset.id,
                code=element_data.get('code')
            )
            db.add(db_element)
            db.flush()  # Get the element ID
            elements_created += 1
            
            # Handle fields - could be nested 'fields' object or direct key-value pairs
            fields_data = element_data.get('fields', {})
            if fields_data:
                # Nested structure like Lung Meridian data
                for field_name, field_value in fields_data.items():
                    # Handle different field types
                    if isinstance(field_value, list):
                        # Convert lists to JSON string (e.g., actions)
                        field_value_str = json.dumps(field_value)
                        field_type = "json"
                    elif isinstance(field_value, dict):
                        # Convert objects to JSON string
                        field_value_str = json.dumps(field_value)
                        field_type = "json"
                    else:
                        # Simple string values
                        field_value_str = str(field_value)
                        field_type = "text"
                    
                    db_field = Field(
                        element_id=db_element.id,
                        field_name=field_name,
                        field_value=field_value_str,
                        field_type=field_type
                    )
                    db.add(db_field)
                    fields_created += 1
            else:
                # Direct key-value pairs (skip 'code' as it's already handled)
                for field_name, field_value in element_data.items():
                    if field_name == 'code':
                        continue
                        
                    # Handle different field types
                    if isinstance(field_value, list):
                        field_value_str = json.dumps(field_value)
                        field_type = "json"
                    elif isinstance(field_value, dict):
                        field_value_str = json.dumps(field_value)
                        field_type = "json"
                    else:
                        field_value_str = str(field_value)
                        field_type = "text"
                    
                    db_field = Field(
                        element_id=db_element.id,
                        field_name=field_name,
                        field_value=field_value_str,
                        field_type=field_type
                    )
                    db.add(db_field)
                    fields_created += 1
        
        db.commit()
        db.refresh(db_dataset)
        
        # Create upload summary
        upload_summary = f"Successfully created {elements_created} flashcard(s) with {fields_created} field(s)"
        
        # Create the response with additional statistics
        response_data = {
            **DatasetResponse.from_orm(db_dataset).dict(),
            "elements_created": elements_created,
            "fields_created": fields_created,
            "upload_summary": upload_summary
        }
        
        return DatasetUploadResponse(**response_data)
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing upload: {str(e)}"
        )


@router.post("/json", response_model=DatasetResponse)
async def create_dataset_from_json(
    dataset_data: DatasetUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Admin only
):
    """Create dataset from JSON data in request body (admin only)"""
    try:
        # Create dataset
        db_dataset = Dataset(
            name=dataset_data.name,
            description=dataset_data.description
        )
        db.add(db_dataset)
        db.flush()
        
        # Create elements and fields
        for element_data in dataset_data.elements:
            db_element = Element(
                dataset_id=db_dataset.id,
                code=element_data.get('code')
            )
            db.add(db_element)
            db.flush()
            
            # Handle fields - could be nested 'fields' object or direct key-value pairs
            fields_data = element_data.get('fields', {})
            if fields_data:
                # Nested structure like Lung Meridian data
                for field_name, field_value in fields_data.items():
                    # Handle different field types
                    if isinstance(field_value, list):
                        field_value_str = json.dumps(field_value)
                        field_type = "json"
                    elif isinstance(field_value, dict):
                        field_value_str = json.dumps(field_value)
                        field_type = "json"
                    else:
                        field_value_str = str(field_value)
                        field_type = "text"
                    
                    db_field = Field(
                        element_id=db_element.id,
                        field_name=field_name,
                        field_value=field_value_str,
                        field_type=field_type
                    )
                    db.add(db_field)
            else:
                # Direct key-value pairs (skip 'code' as it's already handled)
                for field_name, field_value in element_data.items():
                    if field_name == 'code':
                        continue
                        
                    # Handle different field types
                    if isinstance(field_value, list):
                        field_value_str = json.dumps(field_value)
                        field_type = "json"
                    elif isinstance(field_value, dict):
                        field_value_str = json.dumps(field_value)
                        field_type = "json"
                    else:
                        field_value_str = str(field_value)
                        field_type = "text"
                    
                    db_field = Field(
                        element_id=db_element.id,
                        field_name=field_name,
                        field_value=field_value_str,
                        field_type=field_type
                    )
                    db.add(db_field)
        
        db.commit()
        db.refresh(db_dataset)
        
        return DatasetResponse.from_orm(db_dataset)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating dataset: {str(e)}"
        )


@router.get("/{dataset_id}/elements", response_model=List[ElementResponse])
async def get_dataset_elements(
    dataset_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all elements in a dataset"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    elements = db.query(Element).filter(
        Element.dataset_id == dataset_id
    ).offset(skip).limit(limit).all()
    
    return [ElementResponse.from_orm(element) for element in elements]


@router.patch("/{dataset_id}/toggle")
async def toggle_dataset_status(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Admin only
):
    """Toggle dataset active status (enable/disable) - admin only"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # Toggle the is_active status
    dataset.is_active = not dataset.is_active
    db.commit()
    db.refresh(dataset)
    
    status_text = "enabled" if dataset.is_active else "disabled"
    return {
        "message": f"Dataset {status_text} successfully",
        "dataset_id": dataset.id,
        "is_active": dataset.is_active
    }


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)  # Admin only
):
    """Delete a dataset and all its elements (admin only)"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    db.delete(dataset)
    db.commit()
    
    return {"message": "Dataset deleted successfully"}
