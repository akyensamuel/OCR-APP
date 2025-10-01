"""Test if pdf2image can actually convert a PDF"""
import sys
import os

# Add Django settings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OCR.settings')

import django
django.setup()

from django.conf import settings

def test_pdf_conversion():
    """Test PDF to image conversion"""
    print("=" * 70)
    print("PDF2IMAGE CONVERSION TEST")
    print("=" * 70)
    
    # Test 1: Check if pdf2image is importable
    print("\n1️⃣  Testing pdf2image import...")
    try:
        from pdf2image import convert_from_path
        print("✅ pdf2image imported successfully")
    except ImportError as e:
        print(f"❌ Cannot import pdf2image: {e}")
        return False
    
    # Test 2: Find a PDF file in media/uploads
    print("\n2️⃣  Looking for PDF files...")
    uploads_path = os.path.join(settings.MEDIA_ROOT, 'uploads')
    pdf_files = []
    
    if os.path.exists(uploads_path):
        for root, dirs, files in os.walk(uploads_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
    
    if not pdf_files:
        print("⚠️  No PDF files found in uploads directory")
        print(f"   Searched in: {uploads_path}")
        return False
    
    print(f"✅ Found {len(pdf_files)} PDF file(s)")
    test_pdf = pdf_files[0]
    print(f"   Testing with: {os.path.basename(test_pdf)}")
    
    # Test 3: Try to convert PDF
    print("\n3️⃣  Testing PDF conversion...")
    try:
        images = convert_from_path(test_pdf, first_page=1, last_page=1)
        print(f"✅ Successfully converted PDF!")
        print(f"   Page size: {images[0].size}")
        print(f"   Format: {images[0].format}")
        print(f"   Mode: {images[0].mode}")
        return True
    except Exception as e:
        print(f"❌ PDF conversion failed!")
        print(f"   Error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Check if it's a Poppler PATH issue
        if "poppler" in str(e).lower() or "path" in str(e).lower():
            print("\n💡 This looks like a Poppler PATH issue!")
            print("   Poppler executables are not accessible to Python subprocesses")
        
        return False

if __name__ == "__main__":
    success = test_pdf_conversion()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ PDF PROCESSING IS WORKING!")
        print("   Your OCR application should be able to process PDFs")
    else:
        print("❌ PDF PROCESSING IS NOT WORKING")
        print("   Need to fix Poppler configuration")
    print("=" * 70)
