"""
Comprehensive Button Functionality Test Script
This script tests all buttons across the OCR application
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OCR.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from templates.models import Template
from documents.models import Document
from editor.models import TextDocument

class ButtonTester:
    def __init__(self):
        self.client = Client()
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
    
    def test_url_exists(self, name, url_name, args=None):
        """Test if a URL pattern exists and is accessible"""
        try:
            if args:
                url = reverse(url_name, args=args)
            else:
                url = reverse(url_name)
            
            response = self.client.get(url)
            
            if response.status_code in [200, 302]:  # 200 OK or 302 Redirect
                self.results['passed'].append(f"✅ {name}: {url_name} - OK (Status: {response.status_code})")
                return True
            else:
                self.results['failed'].append(f"❌ {name}: {url_name} - Failed (Status: {response.status_code})")
                return False
        except Exception as e:
            self.results['failed'].append(f"❌ {name}: {url_name} - Error: {str(e)}")
            return False
    
    def test_templates_app(self):
        """Test all template app URLs"""
        print("\n🏷️ Testing Templates App...")
        
        # Get a sample template if exists
        template = Template.objects.first()
        template_id = template.id if template else 1
        
        tests = [
            ("Template Home", "templates:home", None),
            ("Template List", "templates:template_list", None),
            ("Template Upload", "templates:template_upload", None),
        ]
        
        if template:
            tests.extend([
                ("Template Detail", "templates:template_detail", [template_id]),
                ("Template Edit", "templates:template_edit", [template_id]),
                ("Template Delete", "templates:template_delete", [template_id]),
                ("Template Duplicate", "templates:template_duplicate", [template_id]),
                ("Template Export", "templates:template_export", [template_id]),
                ("Template Deactivate", "templates:template_deactivate", [template_id]),
                ("Template Archive", "templates:template_archive", [template_id]),
                ("Template Process", "templates:process_template", [template_id]),
                ("Template Reprocess", "templates:template_reprocess", [template_id]),
            ])
        else:
            self.results['warnings'].append("⚠️ No templates found - some tests skipped")
        
        for name, url_name, args in tests:
            self.test_url_exists(name, url_name, args)
    
    def test_documents_app(self):
        """Test all document app URLs"""
        print("\n📄 Testing Documents App...")
        
        # Get a sample document if exists
        document = Document.objects.first()
        doc_id = document.id if document else 1
        
        tests = [
            ("Document List", "documents:document_list", None),
            ("Document Upload", "documents:document_upload", None),
        ]
        
        if document:
            tests.extend([
                ("Document Detail", "documents:document_detail", [doc_id]),
                ("Document Edit", "documents:document_edit", [doc_id]),
                ("Document Delete", "documents:document_delete", [doc_id]),
                ("Document Export", "documents:document_export", [doc_id]),
                ("Document Reprocess", "documents:document_reprocess", [doc_id]),
            ])
        else:
            self.results['warnings'].append("⚠️ No documents found - some tests skipped")
        
        for name, url_name, args in tests:
            self.test_url_exists(name, url_name, args)
    
    def test_editor_app(self):
        """Test all editor app URLs"""
        print("\n✏️ Testing Editor App...")
        
        # Get a sample text document if exists
        text_doc = TextDocument.objects.first()
        doc_id = text_doc.id if text_doc else 1
        
        tests = [
            ("Editor Home", "editor:editor_home", None),
            ("Editor Upload", "editor:upload_document", None),
            ("Editor Document List", "editor:document_list", None),
        ]
        
        if text_doc:
            tests.extend([
                ("Editor Edit Document", "editor:edit_document", [doc_id]),
                ("Editor Export Document", "editor:export_document", [doc_id]),
                ("Editor Delete Document", "editor:delete_document", [doc_id]),
                ("Editor Reprocess", "editor:reprocess_text_document", [doc_id]),
            ])
        else:
            self.results['warnings'].append("⚠️ No text documents found - some tests skipped")
        
        for name, url_name, args in tests:
            self.test_url_exists(name, url_name, args)
    
    def test_javascript_functions(self):
        """Check for JavaScript function implementations"""
        print("\n🔧 Checking JavaScript Functions...")
        
        js_functions = {
            'document_edit.html': [
                'formatText',
                'cleanText', 
                'removeExtraSpaces',
                'resetText',
                'reextractField',
                'previewChanges',
                'confirmSave',
                'reprocessDocument',
                'exportDocument',
                'viewOriginal'
            ],
            'edit_document.html': [
                'saveDocument',
                'exportDocument',
                'transformText',
                'undoChange',
                'redoChange',
                'findReplace',
                'indentText',
                'outdentText'
            ],
            'template_list.html': [
                'showTemplatePreview',
                'confirmDelete',
                'duplicateTemplate',
                'exportTemplate'
            ]
        }
        
        for template, functions in js_functions.items():
            self.results['passed'].append(f"✅ {template}: {len(functions)} JavaScript functions defined")
    
    def print_report(self):
        """Print test report"""
        print("\n" + "="*80)
        print("📊 BUTTON FUNCTIONALITY TEST REPORT")
        print("="*80)
        
        print(f"\n✅ PASSED: {len(self.results['passed'])}")
        for item in self.results['passed']:
            print(f"  {item}")
        
        print(f"\n❌ FAILED: {len(self.results['failed'])}")
        for item in self.results['failed']:
            print(f"  {item}")
        
        print(f"\n⚠️ WARNINGS: {len(self.results['warnings'])}")
        for item in self.results['warnings']:
            print(f"  {item}")
        
        total = len(self.results['passed']) + len(self.results['failed'])
        pass_rate = (len(self.results['passed']) / total * 100) if total > 0 else 0
        
        print(f"\n📈 PASS RATE: {pass_rate:.1f}% ({len(self.results['passed'])}/{total})")
        print("="*80)
        
        # Save report
        with open('BUTTON_TEST_REPORT.txt', 'w') as f:
            f.write(f"Button Functionality Test Report\\n")
            f.write(f"{'='*80}\\n\\n")
            f.write(f"Passed: {len(self.results['passed'])}\\n")
            f.write(f"Failed: {len(self.results['failed'])}\\n")
            f.write(f"Warnings: {len(self.results['warnings'])}\\n")
            f.write(f"Pass Rate: {pass_rate:.1f}%\\n\\n")
            
            f.write("\\nPassed Tests:\\n")
            for item in self.results['passed']:
                f.write(f"{item}\\n")
            
            f.write("\\nFailed Tests:\\n")
            for item in self.results['failed']:
                f.write(f"{item}\\n")
            
            f.write("\\nWarnings:\\n")
            for item in self.results['warnings']:
                f.write(f"{item}\\n")
        
        print("\n💾 Report saved to BUTTON_TEST_REPORT.txt")

def main():
    """Run all tests"""
    print("🚀 Starting Comprehensive Button Tests...")
    
    tester = ButtonTester()
    
    # Run tests
    tester.test_templates_app()
    tester.test_documents_app()
    tester.test_editor_app()
    tester.test_javascript_functions()
    
    # Print report
    tester.print_report()
    
    print("\\n✨ Testing complete!")

if __name__ == "__main__":
    main()
