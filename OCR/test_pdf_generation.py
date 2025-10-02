"""
Test PDF generation for reprocessed document 3
"""
import os
import sys
import django

sys.path.insert(0, r'd:\code\optR\OCR')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OCR.settings')
django.setup()

from documents.models import Document
from templates.models import Template
from ocr_processing.pdf_filler import PDFFiller
from django.conf import settings

print("=" * 80)
print("TESTING PDF EXPORT FOR DOCUMENT 3")
print("=" * 80)

# Get document
doc = Document.objects.get(id=3)
template = doc.template

print(f"\nDocument: {doc.name}")
print(f"Template: {template.name}")
print(f"\nExtracted Data Summary:")
print(f"  Keys: {list(doc.extracted_data.keys())}")
print(f"  Cells: {len(doc.extracted_data.get('cells', []))}")
print(f"  Fields: {len(doc.extracted_data.get('fields', []))}")

# Create output directory
output_dir = os.path.join(settings.MEDIA_ROOT, 'test_exports')
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'document_3_test.pdf')

print(f"\nGenerating PDF to: {output_path}")

# Create PDF
pdf_filler = PDFFiller()
try:
    pdf_path = pdf_filler.create_pdf_from_template_data(
        doc,
        template,
        output_path
    )
    
    print(f"\n✅ PDF created successfully!")
    print(f"   Location: {pdf_path}")
    print(f"   Size: {os.path.getsize(pdf_path):,} bytes")
    
    # Verify file exists
    if os.path.exists(pdf_path):
        print(f"\n✅ PDF file verified - ready to open!")
    else:
        print(f"\n❌ ERROR: PDF file not found at {pdf_path}")
        
except Exception as e:
    print(f"\n❌ ERROR creating PDF: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
