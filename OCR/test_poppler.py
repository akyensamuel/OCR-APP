"""
Poppler Installation Test Script
=================================
This script checks if Poppler is correctly installed and accessible.
"""

import sys
import subprocess

def test_pdf2image():
    """Test if pdf2image library is installed"""
    try:
        import pdf2image
        print("✅ pdf2image library is installed (version: {})".format(pdf2image.__version__ if hasattr(pdf2image, '__version__') else 'unknown'))
        return True
    except ImportError:
        print("❌ pdf2image is NOT installed")
        print("   Fix: pip install pdf2image")
        return False

def test_poppler_commands():
    """Test if Poppler executables are accessible"""
    commands = ['pdfinfo', 'pdftoppm', 'pdfimages']
    poppler_found = False
    
    for cmd in commands:
        try:
            # Try to run the command with version flag
            if sys.platform == 'win32':
                result = subprocess.run([cmd, '-v'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
            else:
                result = subprocess.run([cmd, '-version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
            
            if result.returncode == 0 or result.stdout or result.stderr:
                version_info = (result.stdout + result.stderr).strip().split('\n')[0]
                print(f"✅ {cmd} is accessible: {version_info}")
                poppler_found = True
            else:
                print(f"⚠️  {cmd} found but returned error")
        except FileNotFoundError:
            print(f"❌ {cmd} is NOT in PATH")
        except subprocess.TimeoutExpired:
            print(f"⚠️  {cmd} command timed out")
        except Exception as e:
            print(f"❌ Error testing {cmd}: {str(e)}")
    
    return poppler_found

def test_pdf_conversion():
    """Test actual PDF to image conversion"""
    try:
        from pdf2image import convert_from_path
        print("\n📄 Testing PDF conversion capability...")
        
        # This will fail if Poppler is not available
        # but we're just checking if the function is importable
        print("✅ convert_from_path function is available")
        print("   Note: Actual conversion requires a PDF file and working Poppler")
        return True
    except ImportError as e:
        print(f"❌ Cannot import convert_from_path: {e}")
        return False

def check_path_variable():
    """Check PATH environment variable"""
    import os
    path_var = os.environ.get('PATH', '')
    
    if sys.platform == 'win32':
        # Look for poppler in PATH
        poppler_paths = [p for p in path_var.split(';') if 'poppler' in p.lower()]
        if poppler_paths:
            print("\n📁 Poppler paths found in PATH:")
            for p in poppler_paths:
                print(f"   {p}")
        else:
            print("\n⚠️  No 'poppler' directory found in PATH")
            print("   This might be okay if Poppler executables are elsewhere in PATH")

def main():
    print("=" * 70)
    print("POPPLER & PDF2IMAGE INSTALLATION TEST")
    print("=" * 70)
    print()
    
    # Test 1: Check pdf2image package
    print("1️⃣  Checking pdf2image Python package...")
    pdf2image_ok = test_pdf2image()
    print()
    
    # Test 2: Check Poppler executables
    print("2️⃣  Checking Poppler executables in PATH...")
    poppler_ok = test_poppler_commands()
    print()
    
    # Test 3: Check conversion function
    print("3️⃣  Checking PDF conversion capability...")
    conversion_ok = test_pdf_conversion()
    print()
    
    # Test 4: Check PATH variable
    print("4️⃣  Checking PATH environment variable...")
    check_path_variable()
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if pdf2image_ok and poppler_ok:
        print("✅ ALL CHECKS PASSED!")
        print("   Your system is ready for PDF processing.")
    elif pdf2image_ok and not poppler_ok:
        print("⚠️  PARTIAL SETUP")
        print("   • pdf2image is installed ✅")
        print("   • Poppler is NOT accessible ❌")
        print()
        print("📖 NEXT STEPS:")
        print("   1. Install Poppler (see POPPLER_SETUP.md)")
        print("   2. Add Poppler bin folder to System PATH")
        print("   3. Restart your terminal/IDE")
        print("   4. Run this script again")
    elif not pdf2image_ok:
        print("❌ SETUP INCOMPLETE")
        print("   • pdf2image is NOT installed ❌")
        print()
        print("📖 NEXT STEPS:")
        print("   1. Install pdf2image: pip install pdf2image")
        print("   2. Install Poppler (see POPPLER_SETUP.md)")
        print("   3. Run this script again")
    else:
        print("⚠️  UNEXPECTED STATE")
        print("   Review the output above for details")
    
    print()
    print("📚 For detailed instructions, see: POPPLER_SETUP.md")
    print("=" * 70)

if __name__ == "__main__":
    main()
