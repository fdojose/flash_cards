#!/usr/bin/env python3
"""
FSRS Integration Configuration Seeding Script

This script seeds the database with default FSRS integration configuration values.
Run this after the database migration to ensure all configuration values are available.

Usage:
    python seed_integration_config.py
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.admin.models import SystemConfig

# FSRS Integration Configuration Values
INTEGRATION_CONFIG_VALUES = {
    # FSRS Integration Variables
    "integration_enhancement_enabled": {
        "value": True, 
        "type": "boolean", 
        "description": "Master switch for FSRS integration enhancement", 
        "category": "fsrs_integration"
    },
    "integration_confirmation_threshold": {
        "value": 0.8, 
        "type": "float", 
        "description": "Accuracy required for integration confirmation", 
        "category": "fsrs_integration"
    },
    "integration_max_attempts": {
        "value": 3, 
        "type": "integer", 
        "description": "Max attempts before returning to isolation", 
        "category": "fsrs_integration"
    },
    "stability_boost_factor": {
        "value": 1.2, 
        "type": "float", 
        "description": "Stability multiplier on success", 
        "category": "fsrs_integration"
    },
    "stability_decay_factor": {
        "value": 0.8, 
        "type": "float", 
        "description": "Stability multiplier on failure", 
        "category": "fsrs_integration"
    },
    "stability_max_score": {
        "value": 3.0, 
        "type": "float", 
        "description": "Maximum stability score cap", 
        "category": "fsrs_integration"
    },
    "integration_failure_penalty": {
        "value": 0.85, 
        "type": "float", 
        "description": "Stability penalty for confirmed card failure", 
        "category": "fsrs_integration"
    },
    "reconsolidation_threshold": {
        "value": 2, 
        "type": "integer", 
        "description": "Failures before triggering reconsolidation", 
        "category": "fsrs_integration"
    },
    "stability_maintenance_boost": {
        "value": 1.05, 
        "type": "float", 
        "description": "Stability boost for confirmed cards on success", 
        "category": "fsrs_integration"
    },
    
    # Mastery Window Variables
    "default_mastery_window": {
        "value": 3, 
        "type": "integer", 
        "description": "Default mastery window when field count unavailable", 
        "category": "fsrs_mastery"
    },
    "isolation_min_mastery_window": {
        "value": 2, 
        "type": "integer", 
        "description": "Minimum mastery window in isolation phase", 
        "category": "fsrs_mastery"
    },
    "isolation_max_mastery_window": {
        "value": 8, 
        "type": "integer", 
        "description": "Maximum mastery window in isolation phase", 
        "category": "fsrs_mastery"
    },
    "isolation_field_multiplier": {
        "value": 1.5, 
        "type": "float", 
        "description": "Field count multiplier for large cards", 
        "category": "fsrs_mastery"
    },
    "single_field_mastery_window": {
        "value": 2, 
        "type": "integer", 
        "description": "Mastery window for single-field cards", 
        "category": "fsrs_mastery"
    },
    "two_field_mastery_window": {
        "value": 3, 
        "type": "integer", 
        "description": "Mastery window for two-field cards", 
        "category": "fsrs_mastery"
    },
    "integration_mastery_window": {
        "value": 2, 
        "type": "integer", 
        "description": "Mastery window for integration phase", 
        "category": "fsrs_mastery"
    },
    "required_mastery_window": {
        "value": 3, 
        "type": "integer", 
        "description": "Required window for isolation mastery calculation", 
        "category": "fsrs_mastery"
    },
    "isolation_mastery_percentage": {
        "value": 0.75, 
        "type": "float", 
        "description": "Accuracy threshold for isolation mastery", 
        "category": "fsrs_mastery"
    },
    "initial_stability_score": {
        "value": 1.0, 
        "type": "float", 
        "description": "Initial stability score for newly mastered cards", 
        "category": "fsrs_mastery"
    }
}


def seed_integration_config():
    """Seed the database with FSRS integration configuration values"""
    db = SessionLocal()
    
    try:
        created_count = 0
        updated_count = 0
        
        for key, config in INTEGRATION_CONFIG_VALUES.items():
            # Check if the configuration already exists
            existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            
            if existing:
                # Update existing configuration if different
                if (existing.value != str(config["value"]) or 
                    existing.value_type != config["type"] or
                    existing.description != config["description"] or
                    existing.category != config["category"]):
                    
                    existing.value = str(config["value"])
                    existing.value_type = config["type"]
                    existing.description = config["description"]
                    existing.category = config["category"]
                    updated_count += 1
                    print(f"Updated: {key}")
                else:
                    print(f"Skipped (unchanged): {key}")
            else:
                # Create new configuration
                SystemConfig.set_value(
                    db=db,
                    key=key,
                    value=config["value"],
                    value_type=config["type"],
                    description=config["description"],
                    category=config["category"]
                )
                created_count += 1
                print(f"Created: {key}")
        
        db.commit()
        
        print(f"\n✅ FSRS Integration Configuration Seeding Complete!")
        print(f"   Created: {created_count} configurations")
        print(f"   Updated: {updated_count} configurations")
        print(f"   Total: {len(INTEGRATION_CONFIG_VALUES)} FSRS parameters")
        
        # Verify configuration categories
        print(f"\n📊 Configuration Categories:")
        categories = {}
        for key, config in INTEGRATION_CONFIG_VALUES.items():
            category = config["category"]
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        for category, count in categories.items():
            print(f"   {category}: {count} parameters")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding FSRS integration configuration: {e}")
        sys.exit(1)
    finally:
        db.close()


def verify_config():
    """Verify that all FSRS integration configurations are properly loaded"""
    db = SessionLocal()
    
    try:
        print("\n🔍 Verifying FSRS Integration Configuration:")
        
        for key in INTEGRATION_CONFIG_VALUES.keys():
            config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if config:
                print(f"   ✓ {key}: {config.value} ({config.value_type})")
            else:
                print(f"   ❌ Missing: {key}")
                
    except Exception as e:
        print(f"❌ Error verifying configuration: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 FSRS Integration Configuration Seeding Script")
    print("=" * 50)
    
    # Seed configuration
    seed_integration_config()
    
    # Verify configuration
    verify_config()
    
    print("\n✅ Script completed successfully!")
