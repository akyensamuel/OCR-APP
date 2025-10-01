"""
Verification script to check if new table detection is being used
Tests the /upload/ endpoint
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OCR.settings')
django.setup()

from templates.models import Template
from django.conf import settings


def verify_table_detection_integration():
    """Verify that table detection is integrated in the upload flow"""
    
    print("\n" + "="*70)
    print("🔍 VERIFYING TABLE DETECTION INTEGRATION")
    print("="*70 + "\n")
    
    # Check 1: View code
    print("1️⃣ Checking template_upload view code...")
    
    import inspect
    from templates import views
    
    source = inspect.getsource(views.template_upload)
    
    checks = {
        'TableDetector imported': 'from ocr_processing.table_detector import TableDetector' in source,
        'table_detector initialized': 'TableDetector(ocr_engine)' in source,
        'detect_table_structure called': 'detect_table_structure(' in source,
        'Excel export called': 'export_to_excel_template(' in source,
        'Visualization called': 'visualize_table_detection(' in source,
        'Detection method set': "'detection_method': 'table_detection'" in source,
        'Fallback to simple extraction': "'simple_extraction'" in source,
    }
    
    all_passed = True
    for check_name, check_result in checks.items():
        status = "✅" if check_result else "❌"
        print(f"   {status} {check_name}")
        if not check_result:
            all_passed = False
    
    print()
    
    # Check 2: URL routing
    print("2️⃣ Checking URL routing...")
    from django.urls import reverse
    
    try:
        upload_url = reverse('templates:template_upload')
        print(f"   ✅ Upload URL: {upload_url}")
        print(f"   ✅ Full URL: http://127.0.0.1:8000{upload_url}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_passed = False
    
    print()
    
    # Check 3: Recent uploads
    print("3️⃣ Checking recent template uploads...")
    recent_templates = Template.objects.all().order_by('-created_at')[:5]
    
    if not recent_templates:
        print("   ⚠️  No templates found in database")
        print("   💡 Upload a template to test: http://127.0.0.1:8000/upload/")
    else:
        print(f"   Found {recent_templates.count()} recent template(s)\n")
        
        for template in recent_templates:
            print(f"   📄 Template: {template.name}")
            print(f"      Status: {template.processing_status}")
            
            if template.structure:
                detection_method = template.structure.get('detection_method', 'unknown')
                note = template.structure.get('note', 'N/A')
                
                if detection_method == 'table_detection':
                    print(f"      ✅ Method: {detection_method} (NEW TABLE DETECTION)")
                    print(f"      ✅ Note: {note}")
                    
                    # Check for additional features
                    if 'rows' in template.structure and 'cols' in template.structure:
                        print(f"      ✅ Grid: {template.structure['rows']}x{template.structure['cols']}")
                    
                    if 'headers' in template.structure:
                        headers = template.structure.get('headers', {})
                        print(f"      ✅ Headers: {list(headers.values())}")
                    
                    if 'grid_confidence' in template.structure:
                        print(f"      ✅ Confidence: {template.structure['grid_confidence']:.1f}%")
                    
                elif detection_method == 'simple_extraction':
                    print(f"      ⚠️  Method: {detection_method} (Fallback)")
                    print(f"      ⚠️  Note: {note}")
                else:
                    print(f"      ❓ Method: {detection_method}")
                
                # Check for generated files
                if template.file:
                    base_path = os.path.join(settings.MEDIA_ROOT, template.file.name)
                    base_name = os.path.splitext(base_path)[0]
                    
                    excel_path = f"{base_name}_template.xlsx"
                    viz_path = f"{base_name}_detected.jpg"
                    
                    if os.path.exists(excel_path):
                        print(f"      ✅ Excel template: {os.path.basename(excel_path)}")
                    
                    if os.path.exists(viz_path):
                        print(f"      ✅ Visualization: {os.path.basename(viz_path)}")
            else:
                print(f"      ❌ No structure data")
            
            print()
    
    print()
    
    # Check 4: Module availability
    print("4️⃣ Checking module availability...")
    
    try:
        from ocr_processing.table_detector import TableDetector
        print("   ✅ table_detector module available")
        
        from ocr_processing.ocr_core import OCREngine
        ocr_engine = OCREngine()
        detector = TableDetector(ocr_engine)
        print("   ✅ TableDetector can be initialized")
        
        # Check methods
        methods = ['detect_table_structure', 'structure_to_dict', 'export_to_excel_template']
        for method in methods:
            if hasattr(detector, method):
                print(f"   ✅ Method available: {method}")
            else:
                print(f"   ❌ Method missing: {method}")
                all_passed = False
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_passed = False
    
    print()
    
    # Summary
    print("="*70)
    if all_passed:
        print("✅ TABLE DETECTION IS INTEGRATED AND ACTIVE")
    else:
        print("⚠️  SOME CHECKS FAILED - REVIEW ABOVE")
    print("="*70 + "\n")
    
    # Instructions
    print("📋 TO TEST:")
    print("   1. Go to: http://127.0.0.1:8000/upload/")
    print("   2. Upload a table image")
    print("   3. Check the template detail page")
    print("   4. Look for:")
    print("      • 'detection_method': 'table_detection'")
    print("      • Excel template file (.xlsx)")
    print("      • Visualization file (_detected.jpg)")
    print("      • Grid dimensions (rows x cols)")
    print("      • Headers extracted")
    print("      • Grid confidence score")
    print()
    
    return all_passed


if __name__ == "__main__":
    verify_table_detection_integration()
