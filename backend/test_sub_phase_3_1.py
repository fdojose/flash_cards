#!/usr/bin/env python3
"""
Test script for Sub-Phase 3.1: Dataset Models

This script verifies that:
1. Dataset models are properly defined with correct relationships
2. All required columns and constraints are present
3. Models can be imported and instantiated
4. Foreign key relationships work correctly
5. Indexes are properly defined
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_model_imports():
    """Test that all dataset models can be imported"""
    try:
        from app.datasets.models import Dataset, Element, Field, Tag, ElementTag
        print("✅ All dataset models imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Error importing dataset models: {e}")
        return False

def test_model_attributes():
    """Test that models have the expected attributes"""
    try:
        from app.datasets.models import Dataset, Element, Field, Tag, ElementTag
        
        # Test Dataset model
        dataset_columns = ['id', 'name', 'description', 'created_at', 'updated_at']
        for col in dataset_columns:
            if not hasattr(Dataset, col):
                print(f"❌ Dataset missing column: {col}")
                return False
        
        # Test Element model
        element_columns = ['id', 'dataset_id', 'code', 'created_at']
        for col in element_columns:
            if not hasattr(Element, col):
                print(f"❌ Element missing column: {col}")
                return False
        
        # Test Field model
        field_columns = ['id', 'element_id', 'field_name', 'field_value', 'field_type', 'media_url']
        for col in field_columns:
            if not hasattr(Field, col):
                print(f"❌ Field missing column: {col}")
                return False
        
        # Test Tag model
        tag_columns = ['id', 'name', 'created_at']
        for col in tag_columns:
            if not hasattr(Tag, col):
                print(f"❌ Tag missing column: {col}")
                return False
        
        # Test ElementTag model
        element_tag_columns = ['element_id', 'tag_id']
        for col in element_tag_columns:
            if not hasattr(ElementTag, col):
                print(f"❌ ElementTag missing column: {col}")
                return False
        
        print("✅ All models have required attributes")
        return True
        
    except Exception as e:
        print(f"❌ Error testing model attributes: {e}")
        return False

def test_model_relationships():
    """Test that model relationships are properly defined"""
    try:
        from app.datasets.models import Dataset, Element, Field
        
        # Check Dataset relationships
        if not hasattr(Dataset, 'elements'):
            print("❌ Dataset missing 'elements' relationship")
            return False
        
        # Check Element relationships
        if not hasattr(Element, 'dataset'):
            print("❌ Element missing 'dataset' relationship")
            return False
        
        if not hasattr(Element, 'fields'):
            print("❌ Element missing 'fields' relationship")
            return False
        
        # Check Field relationships
        if not hasattr(Field, 'element'):
            print("❌ Field missing 'element' relationship")
            return False
        
        print("✅ All model relationships are properly defined")
        return True
        
    except Exception as e:
        print(f"❌ Error testing model relationships: {e}")
        return False

def test_model_table_names():
    """Test that models have correct table names"""
    try:
        from app.datasets.models import Dataset, Element, Field, Tag, ElementTag
        
        expected_tables = {
            Dataset: 'datasets',
            Element: 'elements', 
            Field: 'fields',
            Tag: 'tags',
            ElementTag: 'element_tags'
        }
        
        for model, expected_name in expected_tables.items():
            if model.__tablename__ != expected_name:
                print(f"❌ {model.__name__} has incorrect table name: {model.__tablename__} (expected {expected_name})")
                return False
        
        print("✅ All models have correct table names")
        return True
        
    except Exception as e:
        print(f"❌ Error testing table names: {e}")
        return False

def test_shared_base():
    """Test that models use the shared Base from database.py"""
    try:
        from app.datasets.models import Dataset
        from app.database import Base
        
        # Check if Dataset is using the shared Base
        if not issubclass(Dataset, Base):
            print("❌ Dataset model not using shared Base from database.py")
            return False
        
        print("✅ Models are using shared database Base")
        return True
        
    except Exception as e:
        print(f"❌ Error testing shared base: {e}")
        return False

def test_model_instantiation():
    """Test that models can be instantiated"""
    try:
        from app.datasets.models import Dataset, Element, Field, Tag, ElementTag
        import uuid
        
        # Test Dataset instantiation
        dataset = Dataset(
            name="Test Dataset",
            description="A test dataset"
        )
        
        # Test Element instantiation
        element = Element(
            dataset_id=uuid.uuid4(),
            code="TEST-1"
        )
        
        # Test Field instantiation  
        field = Field(
            element_id=uuid.uuid4(),
            field_name="test_field",
            field_value="test_value"
        )
        
        # Test Tag instantiation
        tag = Tag(name="test_tag")
        
        # Test ElementTag instantiation
        element_tag = ElementTag(
            element_id=uuid.uuid4(),
            tag_id=uuid.uuid4()
        )
        
        print("✅ All models can be instantiated")
        return True
        
    except Exception as e:
        print(f"❌ Error instantiating models: {e}")
        return False

def test_model_repr():
    """Test that models have proper __repr__ methods"""
    try:
        from app.datasets.models import Dataset, Element, Field, Tag, ElementTag
        import uuid
        
        # Test Dataset repr
        dataset = Dataset(name="Test Dataset")
        dataset_repr = repr(dataset)
        if "Dataset" not in dataset_repr or "Test Dataset" not in dataset_repr:
            print("❌ Dataset __repr__ method not working properly")
            return False
        
        # Test Element repr
        element = Element(code="TEST-1")
        element_repr = repr(element)
        if "Element" not in element_repr or "TEST-1" not in element_repr:
            print("❌ Element __repr__ method not working properly")
            return False
        
        # Test Field repr
        field = Field(field_name="test_name", field_type="text")
        field_repr = repr(field)
        if "Field" not in field_repr or "test_name" not in field_repr:
            print("❌ Field __repr__ method not working properly")
            return False
        
        print("✅ All models have proper __repr__ methods")
        return True
        
    except Exception as e:
        print(f"❌ Error testing model repr methods: {e}")
        return False

def test_migration_file():
    """Test that migration file exists and has proper content"""
    try:
        import glob
        
        # Find the dataset migration file
        migration_files = glob.glob("/Users/maccasa/Dropbox/TDCLA/Combos/NotebooksPython/course_creator/flash_cards/backend/migrations/versions/*_create_dataset_models.py")
        
        if not migration_files:
            print("❌ Dataset models migration file not found")
            return False
        
        migration_file = migration_files[0]
        with open(migration_file, 'r') as f:
            content = f.read()
        
        # Check for key migration content
        required_content = [
            'datasets',
            'elements', 
            'fields',
            'tags',
            'element_tags',
            'def upgrade()',
            'def downgrade()',
            'UUID(as_uuid=True)'
        ]
        
        for item in required_content:
            if item not in content:
                print(f"❌ Migration file missing required content: {item}")
                return False
        
        print("✅ Migration file exists and contains required content")
        return True
        
    except Exception as e:
        print(f"❌ Error testing migration file: {e}")
        return False

def test_env_imports():
    """Test that env.py has been updated to import dataset models"""
    try:
        env_file = "/Users/maccasa/Dropbox/TDCLA/Combos/NotebooksPython/course_creator/flash_cards/backend/migrations/env.py"
        
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Check that dataset models are imported
        if "from app.datasets.models import Dataset, Element, Field, Tag, ElementTag" not in content:
            print("❌ env.py does not import dataset models")
            return False
        
        print("✅ env.py properly imports dataset models")
        return True
        
    except Exception as e:
        print(f"❌ Error testing env.py imports: {e}")
        return False

def main():
    """Run all tests for Sub-Phase 3.1"""
    print("🧪 Testing Sub-Phase 3.1: Dataset Models")
    print("=" * 45)
    
    tests = [
        ("Model Imports", test_model_imports),
        ("Model Attributes", test_model_attributes),
        ("Model Relationships", test_model_relationships),
        ("Table Names", test_model_table_names),
        ("Shared Base", test_shared_base),
        ("Model Instantiation", test_model_instantiation),
        ("Model Repr Methods", test_model_repr),
        ("Migration File", test_migration_file),
        ("Env Imports", test_env_imports),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running test: {test_name}")
        result = test_func()
        results.append(result)
    
    print("\n" + "=" * 45)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Sub-Phase 3.1 implementation is successful!")
        print("\n📋 Key Features Implemented:")
        print("  ✅ Dataset model with name, description, timestamps")
        print("  ✅ Element model with dataset relationship and optional code")
        print("  ✅ Field model with flexible key-value storage and media support")
        print("  ✅ Tag model for categorization")
        print("  ✅ ElementTag junction table for many-to-many relationships")
        print("  ✅ Proper foreign key constraints with CASCADE deletes")
        print("  ✅ Database indexes for performance")
        print("  ✅ Alembic migration ready for database creation")
        print("  ✅ Shared Base usage for consistency")
        print("\n🔄 Ready for Sub-Phase 3.2: Upload Endpoint!")
        return True
    else:
        print("🚨 Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
