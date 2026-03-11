"""
System Configuration Models

This module defines models for system-wide configuration settings
that can be modified by administrators.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

# Import shared Base from database configuration
from ..database import Base


class SystemConfig(Base):
    """Global system configuration settings"""
    __tablename__ = "system_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), nullable=False, default="string")  # string, integer, float, boolean
    description = Column(Text)
    category = Column(String(50), nullable=False, default="general")  # learning, spaced_repetition, gamification, etc.
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemConfig(key='{self.key}', value='{self.value}')>"
    
    @property
    def typed_value(self):
        """Return the value converted to its appropriate type"""
        if self.value_type == "integer":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "boolean":
            return self.value.lower() in ("true", "1", "yes", "on")
        else:
            return self.value
    
    @classmethod
    def set_value(cls, db, key: str, value, value_type: str = "string", description: str = None, category: str = "general"):
        """Set a configuration value, creating or updating as needed"""
        config = db.query(cls).filter(cls.key == key).first()
        
        if config:
            config.value = str(value)
            config.value_type = value_type
            if description:
                config.description = description
            config.category = category
        else:
            config = cls(
                key=key,
                value=str(value),
                value_type=value_type,
                description=description,
                category=category
            )
            db.add(config)
        
        db.commit()
        db.refresh(config)
        return config
    
    @classmethod
    def get_value(cls, db, key: str, default=None):
        """Get a configuration value, returning default if not found"""
        config = db.query(cls).filter(cls.key == key).first()
        return config.typed_value if config else default
