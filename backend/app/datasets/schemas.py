"""
Dataset Schemas

Pydantic models for dataset-related request/response validation.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from uuid import UUID


class DatasetBase(BaseModel):
    """Base dataset schema"""
    name: str
    description: Optional[str] = None


class DatasetCreate(DatasetBase):
    """Schema for creating a new dataset"""
    pass


class DatasetResponse(DatasetBase):
    """Schema for dataset response"""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DatasetMetadata(BaseModel):
    """Dataset metadata for listing with additional statistics"""
    element_count: int
    field_types: List[str]
    field_names: List[str]
    

class DatasetListResponse(DatasetBase):
    """Enhanced schema for dataset listing with metadata"""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metadata: DatasetMetadata
    
    class Config:
        from_attributes = True


class FieldResponse(BaseModel):
    """Schema for field response"""
    id: UUID
    field_name: str
    field_value: str
    field_type: str
    media_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class ElementResponse(BaseModel):
    """Schema for element response"""
    id: UUID
    code: Optional[str] = None
    created_at: datetime
    fields: List[FieldResponse] = []
    
    class Config:
        from_attributes = True


class DatasetUpload(BaseModel):
    """Schema for uploading dataset via JSON"""
    name: str
    description: Optional[str] = None
    elements: List[Dict[str, Any]]  # List of dictionaries with field data


class DatasetUploadResponse(DatasetResponse):
    """Enhanced schema for dataset upload response with statistics"""
    elements_created: int
    fields_created: int
    upload_summary: str


class ElementCreate(BaseModel):
    """Schema for creating individual elements"""
    code: Optional[str] = None
    fields: Dict[str, str]  # field_name -> field_value mapping
