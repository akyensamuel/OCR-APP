"""
Test document reprocessing workflow
"""
import sys
import os
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OCR.settings')
django.setup()

from editor.models import TextDocument
from ocr_processing.ocr_core import OCREngine
from django.conf import settings

def test_reprocess_document():
    """Test reprocessing a document that shows error"""
    
    print("=" * 70)
    print("DOCUMENT REPROCESS TEST")
    print("=" * 70)
    
    # Find documents with errors
    print("\n1️⃣  Looking for documents with errors...")
    error_docs = TextDocument.objects.filter(
        extracted_text__icontains='PDF processing error'
    )
    
    if not error_docs.exists():
        print("✅ No documents with errors found!")
        print("   All documents processed successfully")
        return
    
    print(f"⚠️  Found {error_docs.count()} document(s) with errors:")
    for doc in error_docs:
        print(f"   - ID {doc.id}: {doc.title}")
        print(f"     Error: {doc.extracted_text[:100]}...")
    
    # Test reprocessing first error document
    test_doc = error_docs.first()
    print(f"\n2️⃣  Testing reprocess on: {test_doc.title}")
    print(f"   Document ID: {test_doc.id}")
    print(f"   Original file: {test_doc.original_file}")
    
    if not test_doc.original_file:
        print("❌ No original file available")
        return
    
    # Get file path
    full_path = os.path.join(settings.MEDIA_ROOT, test_doc.original_file.name)
    
    if not os.path.exists(full_path):
        print(f"❌ File not found: {full_path}")
        return
    
    print(f"✅ File exists: {full_path}")
    
    # Test OCR processing
    print("\n3️⃣  Running OCR on document...")
    try:
        ocr_engine = OCREngine()
        ocr_result = ocr_engine.extract_text(full_path)
        
        print(f"✅ OCR completed!")
        print(f"   Engine: {ocr_result.engine}")
        print(f"   Confidence: {ocr_result.confidence:.1f}%")
        print(f"   Text length: {len(ocr_result.text)} characters")
        print(f"   Text preview: {ocr_result.text[:200]}...")
        
        # Check if it's still an error
        if 'error' in ocr_result.text.lower() or ocr_result.confidence == 0:
            print("\n⚠️  Still showing error!")
            print(f"   Full text: {ocr_result.text}")
        else:
            print("\n✅ SUCCESS! Text extracted properly")
        
        # Ask if should save to database
        print("\n4️⃣  Update database?")
        print("   This will replace the error message with extracted text")
        response = input("   Save changes? (yes/no): ").strip().lower()
        
        if response == 'yes':
            test_doc.extracted_text = ocr_result.text
            test_doc.confidence_score = ocr_result.confidence
            test_doc.processing_status = 'completed'
            test_doc.save()
            print("✅ Document updated in database!")
        else:
            print("⏭️  Skipped database update")
            
    except Exception as e:
        print(f"❌ OCR failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reprocess_document()
