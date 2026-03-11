"""
Dataset Models

Defines SQLAlchemy models for datasets, elements, and fields.
Based on the flashcard learning logic specification.
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

# Import shared Base from database configuration
from app.database import Base


class Dataset(Base):
    """Dataset model - groups of learning elements"""
    __tablename__ = "datasets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False, index=True)  # For enabling/disabling datasets
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    elements = relationship("Element", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dataset(id={self.id}, name='{self.name}')>"


class Element(Base):
    """Element model - individual learning items within a dataset"""
    __tablename__ = "elements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(255), index=True)  # Optional identifier/code for the element (e.g., "LU-1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    dataset = relationship("Dataset", back_populates="elements")
    fields = relationship("Field", back_populates="element", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Element(id={self.id}, code='{self.code}', dataset_id={self.dataset_id})>"


class Field(Base):
    """Field model - key-value pairs for element data"""
    __tablename__ = "fields"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    element_id = Column(UUID(as_uuid=True), ForeignKey("elements.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(255), nullable=False, index=True)  # e.g., "name", "location", "description"
    field_value = Column(Text, nullable=False)
    field_type = Column(String(50), default="text", index=True)  # "text", "image", "audio"
    media_url = Column(Text)  # Optional URL for media content
    
    # Relationships
    element = relationship("Element", back_populates="fields")
    
    def __repr__(self):
        return f"<Field(id={self.id}, name='{self.field_name}', type='{self.field_type}', element_id={self.element_id})>"


# Optional: Tags for categorizing elements
class Tag(Base):
    """Tag model for categorizing elements"""
    __tablename__ = "tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"


class ElementTag(Base):
    """Many-to-many relationship between elements and tags"""
    __tablename__ = "element_tags"
    
    element_id = Column(UUID(as_uuid=True), ForeignKey("elements.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    
    def __repr__(self):
        return f"<ElementTag(element_id={self.element_id}, tag_id={self.tag_id})>"
