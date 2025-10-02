"""
Test script to reprocess document ID 3 with the fixed code
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, r'd:\code\optR\OCR')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OCR.settings')
django.setup()

from documents.models import Document
from templates.models import Template
from ocr_processing.ocr_core import OCREngine
from ocr_processing.table_detector import TableDetector
from django.conf import settings

print("=" * 80)
print("REPROCESSING DOCUMENT ID 3")
print("=" * 80)

# Get document
doc = Document.objects.get(id=3)
print(f"\nDocument: {doc.name}")
print(f"Template: {doc.template.name if doc.template else 'None'}")
print(f"Current Status: {doc.processing_status}")
print(f"\nCurrent Extracted Data:")
print(f"  Keys: {list(doc.extracted_data.keys())}")
print(f"  Fields: {doc.extracted_data.get('fields', [])}")
print(f"  Cells: {len(doc.extracted_data.get('cells', []))} cells")

# Get file path
full_path = os.path.join(settings.MEDIA_ROOT, str(doc.file))
print(f"\nFile path: {full_path}")
print(f"File exists: {os.path.exists(full_path)}")

# Initialize OCR
print("\n" + "=" * 80)
print("STARTING REPROCESSING...")
print("=" * 80)

ocr_engine = OCREngine()

if doc.template:
    # Check if template has table structure
    has_table_structure = (
        doc.template.structure and 
        ('headers' in doc.template.structure or 'cells' in doc.template.structure)
    )
    
    print(f"\nTemplate has table structure: {has_table_structure}")
    
    if has_table_structure:
        print("\nUsing table detection method...")
        table_detector = TableDetector(ocr_engine)
        table_structure = table_detector.detect_table_structure(full_path, method="morphology")
        
        if table_structure:
            print(f"SUCCESS! Table detected:")
            print(f"  Rows: {table_structure.rows}")
            print(f"  Columns: {table_structure.cols}")
            print(f"  Cells: {len(table_structure.cells)}")
            
            extracted_data = table_detector.structure_to_dict(table_structure)
            doc.extracted_data = extracted_data
            doc.processing_status = 'completed'
            doc.save()
            
            print(f"\nExtracted data saved:")
            print(f"  Keys: {list(extracted_data.keys())}")
            print(f"  Cells: {len(extracted_data.get('cells', []))}")
            
            # Show first few cells
            cells = extracted_data.get('cells', [])
            print(f"\nFirst 5 cells:")
            for i, cell in enumerate(cells[:5]):
                print(f"  Cell {i}: Row {cell['row']}, Col {cell['col']}, Text: '{cell['text']}', Confidence: {cell['confidence']}")
        else:
            print("WARNING: No table structure detected in document!")
            print("Would use fallback extraction here...")

print("\n" + "=" * 80)
print("REPROCESSING COMPLETE")
print("=" * 80)

# Show updated document
doc.refresh_from_db()
print(f"\nUpdated Document:")
print(f"  Status: {doc.processing_status}")
print(f"  Extracted data keys: {list(doc.extracted_data.keys())}")
print(f"  Number of cells: {len(doc.extracted_data.get('cells', []))}")
print(f"  Number of fields: {len(doc.extracted_data.get('fields', []))}")
