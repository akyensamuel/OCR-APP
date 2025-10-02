"""
Test script for PDF export functionality
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OCR.settings')
django.setup()

from documents.models import Document, Template
from ocr_processing.pdf_filler import PDFFiller
import tempfile

def test_pdf_generation():
    """Test PDF generation with sample data"""
    print("=" * 60)
    print("PDF EXPORT TEST")
    print("=" * 60)
    
    # Test 1: Simple text PDF
    print("\n[Test 1] Generating simple text PDF...")
    try:
        pdf_filler = PDFFiller()
        output_path = os.path.join(tempfile.gettempdir(), 'test_simple.pdf')
        
        sample_text = """This is a test document.
        
It contains multiple paragraphs to test the PDF generation.

The PDF should include:
- Proper formatting
- Line breaks
- Professional styling
        """
        
        metadata = {
            'Author': 'Test Script',
            'Subject': 'PDF Export Test',
            'Date': 'October 2, 2025'
        }
        
        pdf_filler.create_pdf_from_text(
            text=sample_text,
            output_path=output_path,
            title="Test Document",
            metadata=metadata
        )
        
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"✅ SUCCESS: PDF created at {output_path}")
            print(f"   File size: {size:,} bytes")
        else:
            print("❌ FAILED: PDF file not created")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Template-based PDF with database
    print("\n[Test 2] Testing with database documents...")
    try:
        # Check if we have any documents
        doc_count = Document.objects.count()
        template_count = Template.objects.count()
        
        print(f"   Documents in database: {doc_count}")
        print(f"   Templates in database: {template_count}")
        
        if doc_count > 0:
            # Get first document
            document = Document.objects.first()
            print(f"   Testing with document: {document.name}")
            
            output_path = os.path.join(tempfile.gettempdir(), 'test_template.pdf')
            
            if document.template:
                print(f"   Document has template: {document.template.name}")
                pdf_filler.create_pdf_from_template_data(
                    document=document,
                    template=document.template,
                    output_path=output_path
                )
                
                if os.path.exists(output_path):
                    size = os.path.getsize(output_path)
                    print(f"✅ SUCCESS: Template PDF created at {output_path}")
                    print(f"   File size: {size:,} bytes")
                else:
                    print("❌ FAILED: Template PDF not created")
            else:
                print("   ⚠️  Document has no template, using plain text method")
                pdf_filler.create_pdf_from_text(
                    text=document.text_content or "No text content",
                    output_path=output_path,
                    title=document.name
                )
                
                if os.path.exists(output_path):
                    size = os.path.getsize(output_path)
                    print(f"✅ SUCCESS: Plain text PDF created at {output_path}")
                    print(f"   File size: {size:,} bytes")
        else:
            print("   ⚠️  No documents found in database")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Multi-document PDF
    print("\n[Test 3] Testing multi-document PDF...")
    try:
        if doc_count > 0 and template_count > 0:
            # Get first template and its documents
            template = Template.objects.first()
            documents = Document.objects.filter(template=template)[:3]
            
            if documents.exists():
                print(f"   Creating consolidated PDF with {documents.count()} documents")
                output_path = os.path.join(tempfile.gettempdir(), 'test_consolidated.pdf')
                
                pdf_filler.create_consolidated_pdf(
                    documents=list(documents),
                    template=template,
                    output_path=output_path
                )
                
                if os.path.exists(output_path):
                    size = os.path.getsize(output_path)
                    print(f"✅ SUCCESS: Consolidated PDF created at {output_path}")
                    print(f"   File size: {size:,} bytes")
                else:
                    print("❌ FAILED: Consolidated PDF not created")
            else:
                print("   ⚠️  No documents found for template")
        else:
            print("   ⚠️  Insufficient data for multi-document test")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    test_pdf_generation()
