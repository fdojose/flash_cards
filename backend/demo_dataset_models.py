#!/usr/bin/env python3
"""
Dataset Models Demo Script

Demonstrates how the dataset models work with real acupuncture data.
This script shows the data structure without requiring a database connection.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demo_lung_meridian_structure():
    """Demo using the Lung Meridian dataset structure"""
    print("🫁 Lung Meridian Dataset Models Demo")
    print("=" * 50)
    
    try:
        from app.datasets.models import Dataset, Element, Field, Tag, ElementTag
        import uuid
        
        # Create a dataset
        lung_dataset = Dataset(
            name="Lung Meridian Points",
            description="Points of the Lung channel (Hand Taiyin) extracted from Claudia Focks' Atlas of Acupuncture."
        )
        print(f"📚 Dataset: {lung_dataset}")
        
        # Create an element for LU-1
        lu1_element = Element(
            dataset_id=lung_dataset.id,
            code="LU-1"
        )
        print(f"📍 Element: {lu1_element}")
        
        # Create fields for LU-1
        lu1_fields = [
            Field(
                element_id=lu1_element.id,
                field_name="chinese_name",
                field_value="中府",
                field_type="text"
            ),
            Field(
                element_id=lu1_element.id,
                field_name="english_name", 
                field_value="Central Residence",
                field_type="text"
            ),
            Field(
                element_id=lu1_element.id,
                field_name="location",
                field_value="6 cun lateral to the anterior midline, 1 cun below LU-2, slightly medial to the lower border of the coracoid process.",
                field_type="text"
            ),
            Field(
                element_id=lu1_element.id,
                field_name="how_to_find",
                field_value="Locate LU-2 in the deltopectoral triangle, then palpate 1 cun downward along the deltoid border.",
                field_type="text"
            ),
            Field(
                element_id=lu1_element.id,
                field_name="special_features",
                field_value="Front-mu point of the Lung, meeting point with the Spleen channel, entry point.",
                field_type="text"
            )
        ]
        
        print(f"\n🔧 Fields for {lu1_element.code}:")
        for field in lu1_fields:
            print(f"  {field}")
        
        # Create tags
        meridian_tag = Tag(name="meridian")
        lung_tag = Tag(name="lung")
        front_mu_tag = Tag(name="front-mu")
        
        print(f"\n🏷️  Tags:")
        print(f"  {meridian_tag}")
        print(f"  {lung_tag}")
        print(f"  {front_mu_tag}")
        
        # Create element-tag relationships
        element_tags = [
            ElementTag(element_id=lu1_element.id, tag_id=meridian_tag.id),
            ElementTag(element_id=lu1_element.id, tag_id=lung_tag.id),
            ElementTag(element_id=lu1_element.id, tag_id=front_mu_tag.id)
        ]
        
        print(f"\n🔗 Element-Tag Relationships:")
        for et in element_tags:
            print(f"  {et}")
        
        print("\n✅ Demo completed successfully!")
        print("\n📝 Data Structure Summary:")
        print("  • Dataset: Container for related learning elements")
        print("  • Element: Individual learning item with optional code")
        print("  • Field: Key-value pairs storing element properties") 
        print("  • Tag: Categorization labels")
        print("  • ElementTag: Many-to-many tag relationships")
        print("\n🎯 This structure supports:")
        print("  • Flexible field schemas per dataset")
        print("  • Multimedia content via media_url")
        print("  • Categorization and filtering")
        print("  • Efficient querying with proper indexes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in demo: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_field_types():
    """Demo different field types"""
    print("\n🎨 Field Types Demo")
    print("=" * 30)
    
    try:
        from app.datasets.models import Field
        import uuid
        
        # Different field types that could be used
        field_examples = [
            Field(
                element_id=uuid.uuid4(),
                field_name="name",
                field_value="Central Residence",
                field_type="text"
            ),
            Field(
                element_id=uuid.uuid4(),
                field_name="point_image", 
                field_value="Location on body",
                field_type="image",
                media_url="https://example.com/images/lu1_location.jpg"
            ),
            Field(
                element_id=uuid.uuid4(),
                field_name="pronunciation",
                field_value="zhōng fǔ",
                field_type="audio", 
                media_url="https://example.com/audio/lu1_pronunciation.mp3"
            ),
            Field(
                element_id=uuid.uuid4(),
                field_name="actions",
                field_value='["Regulates and descends Lung Qi", "Clears Heat in the Upper Burner"]',
                field_type="json"
            )
        ]
        
        for field in field_examples:
            print(f"  {field}")
        
        print("\n✅ Field types demo completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in field types demo: {e}")
        return False

def main():
    """Run the demo"""
    success1 = demo_lung_meridian_structure()
    success2 = demo_field_types()
    
    if success1 and success2:
        print("\n🎉 All demos completed successfully!")
        print("\n🚀 Dataset models are ready for Sub-Phase 3.2: Upload Endpoint")
    else:
        print("\n❌ Some demos failed")
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
