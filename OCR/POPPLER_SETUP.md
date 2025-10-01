# 🚀 Quick Poppler Setup Guide for PDF Preview

## Problem
You're seeing this error when viewing PDF templates:
```
PDF processing error: Unable to get page count. Is poppler installed and in PATH?
```

## What is Poppler?
Poppler is a PDF rendering library that converts PDF pages to images. It's required by the `pdf2image` Python library to display PDF previews in the application.

---

## ✅ Solution: Install Poppler (Windows)

### Step 1: Download Poppler
1. Go to: **https://github.com/oschwartz10612/poppler-windows/releases/**
2. Download the latest release (e.g., `Release-24.08.0-0.zip`)

### Step 2: Extract and Place
1. Extract the ZIP file
2. Copy the entire folder to: `C:\Program Files\poppler-24.08.0\`
3. You should now have: `C:\Program Files\poppler-24.08.0\Library\bin\`

### Step 3: Add to System PATH
1. Press `Win + X` → Select **System**
2. Click **Advanced system settings** (right side)
3. Click **Environment Variables** button
4. Under **System variables**, find and select **Path**
5. Click **Edit**
6. Click **New**
7. Add this path: `C:\Program Files\poppler-24.08.0\Library\bin`
8. Click **OK** → **OK** → **OK** to save all changes

### Step 4: Verify Installation
1. **Close all open terminals and VS Code**
2. Reopen Command Prompt
3. Run:
   ```cmd
   pdfinfo -v
   ```
   You should see: `pdfinfo version X.XX.X`

### Step 5: Restart Your Server
1. Stop your Django development server (`Ctrl+C`)
2. Start it again:
   ```cmd
   python manage.py runserver
   ```

---

## 🧪 Test PDF Preview
1. Go to: http://127.0.0.1:8000/templates/
2. Click **View** button on any PDF template
3. The PDF should now preview correctly in the modal!

---

## 🔧 Alternative: Specify Poppler Path in Code (Optional)

If you don't want to add Poppler to PATH, you can specify the path directly in the code:

**Edit `ocr_processing/utils.py`:**

Find the `convert_from_path` calls and add `poppler_path`:

```python
from pdf2image import convert_from_path

# Add poppler_path parameter
images = convert_from_path(
    pdf_path,
    poppler_path=r'C:\Program Files\poppler-24.08.0\Library\bin'
)
```

---

## 📦 Python Package Status
✅ **pdf2image** is now installed in your virtual environment

---

## 🐧 Linux/Mac Users

### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

### macOS:
```bash
brew install poppler
```

---

## ❓ Still Having Issues?

### Check if Poppler is in PATH:
```cmd
where pdftoppm
where pdfinfo
```

If these commands don't work, Poppler is not in your PATH yet.

### Common Mistakes:
- ❌ Added wrong path to PATH (should be the `bin` folder)
- ❌ Didn't restart terminal after adding to PATH
- ❌ Didn't restart Django server after installing Poppler
- ❌ Downloaded wrong Poppler package (use oschwartz10612's Windows release)

### Quick Test Script:
```python
try:
    from pdf2image import convert_from_path
    print("✅ pdf2image is installed")
    
    # This will fail if Poppler is not in PATH
    # but will tell you exactly what's wrong
    import subprocess
    result = subprocess.run(['pdfinfo', '-v'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Poppler is accessible:", result.stdout.strip())
    else:
        print("❌ Poppler is not in PATH")
except ImportError:
    print("❌ pdf2image is not installed")
except FileNotFoundError:
    print("❌ Poppler executables not found in PATH")
```

Save as `test_poppler.py` and run:
```cmd
python test_poppler.py
```

---

## 📚 More Information
For detailed installation instructions, see: **INSTALLATION_GUIDE.md**
