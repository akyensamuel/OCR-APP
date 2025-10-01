"""
Test script for advanced table detection
Tests the new table detection on sample images
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OCR.settings')
django.setup()

from ocr_processing.ocr_core import OCREngine
from ocr_processing.table_detector import TableDetector, visualize_table_detection
import cv2
import numpy as np


def create_sample_table_image(output_path: str):
    """Create a sample table image for testing"""
    # Create a white image
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    
    # Define table dimensions
    rows = 5
    cols = 4
    cell_width = 180
    cell_height = 100
    start_x = 50
    start_y = 50
    
    # Draw grid lines
    for i in range(rows + 1):
        y = start_y + i * cell_height
        cv2.line(img, (start_x, y), (start_x + cols * cell_width, y), (0, 0, 0), 2)
    
    for j in range(cols + 1):
        x = start_x + j * cell_width
        cv2.line(img, (x, start_y), (x, start_y + rows * cell_height), (0, 0, 0), 2)
    
    # Add header text
    headers = ["Name", "Age", "Department", "Salary"]
    for j, header in enumerate(headers):
        x = start_x + j * cell_width + 20
        y = start_y + 30
        cv2.putText(img, header, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    # Add sample data
    sample_data = [
        ["John Doe", "30", "IT", "$5000"],
        ["Jane Smith", "28", "HR", "$4500"],
        ["Bob Johnson", "35", "Sales", "$6000"],
        ["Alice Brown", "32", "IT", "$5500"]
    ]
    
    for i, row_data in enumerate(sample_data):
        for j, cell_text in enumerate(row_data):
            x = start_x + j * cell_width + 20
            y = start_y + (i + 1) * cell_height + 60
            cv2.putText(img, cell_text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Save image
    cv2.imwrite(output_path, img)
    print(f"✅ Created sample table image: {output_path}")
    
    return output_path


def test_table_detection():
    """Test the table detection system"""
    print("\n" + "="*70)
    print("🔍 TESTING ADVANCED TABLE DETECTION")
    print("="*70 + "\n")
    
    # Create sample image
    sample_path = "media/test_table.png"
    os.makedirs("media", exist_ok=True)
    create_sample_table_image(sample_path)
    
    # Initialize detector
    print("\n1️⃣ Initializing OCR Engine and Table Detector...")
    ocr_engine = OCREngine()
    table_detector = TableDetector(ocr_engine)
    print(f"   ✅ OCR Engine: {'Tesseract' if ocr_engine.tesseract_available else 'EasyOCR'}")
    
    # Test morphology method
    print("\n2️⃣ Testing Morphology-based Detection...")
    structure_morph = table_detector.detect_table_structure(sample_path, method="morphology")
    
    if structure_morph:
        print(f"   ✅ Detected: {structure_morph.rows}x{structure_morph.cols} table")
        print(f"   ✅ Headers: {structure_morph.headers}")
        print(f"   ✅ Grid Confidence: {structure_morph.grid_confidence:.1f}%")
        print(f"   ✅ Total Cells: {len(structure_morph.cells)}")
        
        # Show some cell data
        print("\n   📊 Sample Cell Data:")
        for i, cell in enumerate(structure_morph.cells[:8]):  # Show first 8 cells
            if cell.text:
                print(f"      [{cell.row},{cell.col}]: '{cell.text}' (conf: {cell.confidence:.1f}%)")
    else:
        print("   ❌ Failed to detect table with morphology method")
    
    # Test Hough method
    print("\n3️⃣ Testing Hough Transform Detection...")
    structure_hough = table_detector.detect_table_structure(sample_path, method="hough")
    
    if structure_hough:
        print(f"   ✅ Detected: {structure_hough.rows}x{structure_hough.cols} table")
        print(f"   ✅ Headers: {structure_hough.headers}")
        print(f"   ✅ Grid Confidence: {structure_hough.grid_confidence:.1f}%")
    else:
        print("   ❌ Failed to detect table with Hough method")
    
    # Export to Excel
    if structure_morph:
        print("\n4️⃣ Exporting to Excel Template...")
        excel_path = "media/test_table_template.xlsx"
        success = table_detector.export_to_excel_template(structure_morph, excel_path)
        
        if success:
            print(f"   ✅ Excel template saved: {excel_path}")
        else:
            print("   ⚠️  Excel export failed (openpyxl not installed?)")
            print("   💡 Install with: pip install openpyxl")
    
    # Create visualization
    if structure_morph:
        print("\n5️⃣ Creating Visualization...")
        viz_path = "media/test_table_detected.jpg"
        success = visualize_table_detection(sample_path, structure_morph, viz_path)
        
        if success:
            print(f"   ✅ Visualization saved: {viz_path}")
        else:
            print("   ❌ Visualization failed")
    
    # Convert to dictionary
    if structure_morph:
        print("\n6️⃣ Converting to Dictionary (for JSON/Database)...")
        struct_dict = table_detector.structure_to_dict(structure_morph)
        print(f"   ✅ Dictionary keys: {list(struct_dict.keys())}")
        print(f"   ✅ Field names: {struct_dict.get('field_names', [])}")
    
    print("\n" + "="*70)
    print("✅ TABLE DETECTION TEST COMPLETE")
    print("="*70 + "\n")
    
    # Summary
    print("📋 SUMMARY:")
    print(f"   • Morphology Method: {'✅ Success' if structure_morph else '❌ Failed'}")
    print(f"   • Hough Method: {'✅ Success' if structure_hough else '❌ Failed'}")
    print(f"   • Excel Export: {'✅ Available' if success else '⚠️  Needs openpyxl'}")
    print(f"   • Sample Files: media/test_table*.[png,xlsx,jpg]")
    
    return structure_morph


def test_with_real_template():
    """Test with a real template if available"""
    print("\n" + "="*70)
    print("🔍 TESTING WITH REAL TEMPLATES")
    print("="*70 + "\n")
    
    from templates.models import Template
    
    templates = Template.objects.all()
    
    if not templates:
        print("⚠️  No templates found in database")
        print("💡 Upload a template through the web interface first")
        return
    
    print(f"Found {templates.count()} template(s) in database\n")
    
    for template in templates[:3]:  # Test first 3
        print(f"\n📄 Testing Template: {template.name}")
        print(f"   File: {template.file.name}")
        
        if not os.path.exists(template.file.path):
            print(f"   ❌ File not found: {template.file.path}")
            continue
        
        # Initialize detector
        ocr_engine = OCREngine()
        table_detector = TableDetector(ocr_engine)
        
        # Detect structure
        structure = table_detector.detect_table_structure(template.file.path)
        
        if structure:
            print(f"   ✅ Detected: {structure.rows}x{structure.cols} table")
            print(f"   ✅ Headers: {list(structure.headers.values())}")
            print(f"   ✅ Confidence: {structure.grid_confidence:.1f}%")
            
            # Update template in database
            struct_dict = table_detector.structure_to_dict(structure)
            template.structure = struct_dict
            template.save()
            print(f"   ✅ Updated template structure in database")
        else:
            print(f"   ❌ Failed to detect table structure")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    print("\n🚀 ADVANCED TABLE DETECTION TEST SUITE\n")
    
    # Test 1: Sample image
    structure = test_table_detection()
    
    # Test 2: Real templates
    test_with_real_template()
    
    print("\n✨ All tests complete! Check media/ folder for outputs.\n")
