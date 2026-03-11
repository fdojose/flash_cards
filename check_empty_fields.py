#!/usr/bin/env python3
"""
Database inspection script to find empty field_value records
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the path so we can import the models
sys.path.append('./backend')

from backend.app.datasets.models import Field, Element, Dataset

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://flashcard_user:dev_password@localhost:5433/flashcard_dev"
)

# Create engine and session
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_empty_fields():
    """Check for fields with empty or null values"""
    db = SessionLocal()
    
    try:
        print("🔍 Checking for empty field_value records...")
        
        # Query for fields with empty or null values
        empty_fields = db.query(Field).filter(
            (Field.field_value == "") | (Field.field_value == None)
        ).all()
        
        print(f"Found {len(empty_fields)} fields with empty values:")
        
        for field in empty_fields:
            # Get the element and dataset info
            element = db.query(Element).filter(Element.id == field.element_id).first()
            dataset = db.query(Dataset).filter(Dataset.id == element.dataset_id).first() if element else None
            
            print(f"  - Field ID: {field.id}")
            print(f"    Field Name: {field.field_name}")
            print(f"    Field Value: '{field.field_value}'")
            print(f"    Element ID: {field.element_id}")
            print(f"    Dataset: {dataset.name if dataset else 'Unknown'}")
            print(f"    ---")
            
        # Also check for fields with only whitespace
        whitespace_fields = db.query(Field).filter(
            Field.field_value != None,
            Field.field_value != ""
        ).all()
        
        whitespace_count = 0
        for field in whitespace_fields:
            if field.field_value and field.field_value.strip() == "":
                whitespace_count += 1
                element = db.query(Element).filter(Element.id == field.element_id).first()
                dataset = db.query(Dataset).filter(Dataset.id == element.dataset_id).first() if element else None
                
                print(f"  - WHITESPACE Field ID: {field.id}")
                print(f"    Field Name: {field.field_name}")
                print(f"    Field Value: '{field.field_value}' (length: {len(field.field_value)})")
                print(f"    Element ID: {field.element_id}")
                print(f"    Dataset: {dataset.name if dataset else 'Unknown'}")
                print(f"    ---")
        
        print(f"Found {whitespace_count} fields with only whitespace")
        
        # Get a count of total fields
        total_fields = db.query(Field).count()
        print(f"Total fields in database: {total_fields}")
        
        # Check if any elements have fewer than 2 valid fields
        print("\n🔍 Checking elements with insufficient valid fields...")
        elements = db.query(Element).all()
        problematic_elements = []
        
        for element in elements:
            valid_fields = [f for f in element.fields if f.field_value and f.field_value.strip() != ""]
            if len(valid_fields) < 2:
                dataset = db.query(Dataset).filter(Dataset.id == element.dataset_id).first()
                problematic_elements.append((element, dataset, len(valid_fields)))
        
        print(f"Found {len(problematic_elements)} elements with < 2 valid fields:")
        for element, dataset, valid_count in problematic_elements:
            print(f"  - Element ID: {element.id}")
            print(f"    Dataset: {dataset.name if dataset else 'Unknown'}")
            print(f"    Valid fields: {valid_count}")
            print(f"    Total fields: {len(element.fields)}")
            for field in element.fields:
                print(f"      - {field.field_name}: '{field.field_value}'")
            print(f"    ---")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_empty_fields()
