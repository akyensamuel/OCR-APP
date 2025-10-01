# OCR Web Application - Complete Installation Guide

## 📋 Table of Contents
1. [Required Applications](#required-applications)
2. [Python Dependencies](#python-dependencies)
3. [Installation Instructions](#installation-instructions)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Verification](#verification)

---

## 🔧 Required Applications

### 1. **Tesseract OCR Engine** ⭐ CRITICAL
### 2. **Poppler package** VERY NECESSARY FOR PDF OPERATIONS
Tesseract is the primary OCR engine used for text extraction from images and documents.

#### Windows Installation:
1. **Download Installer:**
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest installer (e.g., `tesseract-ocr-w64-setup-5.3.3.20231005.exe`)

2. **Install Tesseract:**
   - Run the installer
   - **Important:** Note the installation path (default: `C:\Program Files\Tesseract-OCR\`)
   - Check "Add to PATH" option during installation (recommended)

3. **Add to PATH (if not done automatically):**
   ```cmd
   # Open System Environment Variables
   # Add to PATH: C:\Program Files\Tesseract-OCR
   ```

4. **Verify Installation:**
   ```cmd
   tesseract --version
   ```
   Expected output: `tesseract 5.x.x`

#### Ubuntu/Debian Installation:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev
```

#### macOS Installation:
```bash
brew install tesseract
```

#### Manual PATH Configuration (if needed):
If Tesseract is not in PATH, you can configure it in your Django settings or OCR core:

**Option 1: Set in Python code** (ocr_processing/ocr_core.py):
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**Option 2: Set as Environment Variable:**
```cmd
# Windows
setx TESSERACT_PATH "C:\Program Files\Tesseract-OCR\tesseract.exe"

# Linux/Mac
export TESSERACT_PATH="/usr/bin/tesseract"
```

---

### 2. **Python 3.8+** ⭐ REQUIRED
The application requires Python 3.8 or higher.

#### Check Python Version:
```bash
python --version
# or
python3 --version
```

#### Download Python (if needed):
- Windows: https://www.python.org/downloads/windows/
- macOS: `brew install python3`
- Ubuntu: `sudo apt-get install python3 python3-pip`

---

## 📦 Python Dependencies

All Python dependencies are listed in `requirements.txt`:

### Core Dependencies:
- **Django 5.2.6** - Web framework
- **pytesseract 0.3.13** - Python wrapper for Tesseract
- **easyocr 1.7.2** - Alternative OCR engine (deep learning-based)
- **opencv-python-headless 4.12.0** - Image processing
- **Pillow 11.3.0** - Image handling
- **torch 2.8.0** - Deep learning framework (for EasyOCR)
- **numpy 2.2.6** - Numerical computing

### Additional Dependencies:
- djangorestframework - API support
- scikit-image - Advanced image processing
- scipy - Scientific computing
- PyYAML - Configuration files

---

## 🚀 Installation Instructions

### Step 1: Clone Repository
```bash
git clone https://github.com/akyensamuel/OCR-APP.git
cd OCR-APP
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv virtual

# Activate virtual environment
# Windows (CMD)
virtual\Scripts\activate.bat

# Windows (PowerShell)
virtual\Scripts\Activate.ps1

# Linux/Mac
source virtual/bin/activate
```

### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Note:** This may take 5-10 minutes as it downloads PyTorch and other large packages.

### Step 4: Install Tesseract OCR
Follow the [Tesseract installation instructions](#1-tesseract-ocr-engine--critical) above for your operating system.

### Step 5: Database Setup
```bash
cd OCR

# Create database tables
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser
```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

### Step 7: Collect Static Files (Optional for Production)
```bash
python manage.py collectstatic --noinput
```

### Step 8: Run Development Server
```bash
python manage.py runserver
```

### Step 9: Access Application
- **Main Application:** http://127.0.0.1:8000/
- **Admin Panel:** http://127.0.0.1:8000/admin/
- **Templates:** http://127.0.0.1:8000/templates/
- **Documents:** http://127.0.0.1:8000/documents/

---

## ⚙️ Configuration

### Tesseract Language Data (Optional)
For better OCR accuracy with specific languages:

1. **Download Language Data:**
   - Go to: https://github.com/tesseract-ocr/tessdata
   - Download desired language files (e.g., `eng.traineddata`, `spa.traineddata`)

2. **Install Language Data:**
   ```bash
   # Windows
   Copy to: C:\Program Files\Tesseract-OCR\tessdata\
   
   # Linux
   sudo cp *.traineddata /usr/share/tesseract-ocr/5/tessdata/
   
   # macOS
   cp *.traineddata /usr/local/share/tessdata/
   ```

### EasyOCR Models (Automatic Download)
EasyOCR will automatically download required models (~100MB) on first use. The models are cached for future use.

**Default cache location:**
- Windows: `C:\Users\<username>\.EasyOCR\`
- Linux/Mac: `~/.EasyOCR/`

### Django Settings Configuration

Edit `OCR/OCR/settings.py` for:

1. **Media Files Path:**
   ```python
   MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
   MEDIA_URL = '/media/'
   ```

2. **Database (Production):**
   ```python
   # For PostgreSQL
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'ocr_db',
           'USER': 'your_user',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

3. **Allowed Hosts (Production):**
   ```python
   ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
   ```

---

## 🔍 Troubleshooting

### Issue 1: "Tesseract is not installed or it's not in your PATH"
**Solution:**
1. Verify Tesseract is installed: `tesseract --version`
2. Add Tesseract to PATH (see installation section)
3. Or configure manually in code:
   ```python
   # In ocr_processing/ocr_core.py, add at the top:
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### Issue 2: "EasyOCR initialization failed"
**Solution:**
- This is non-critical; application will fall back to Tesseract
- For full EasyOCR support:
  ```bash
  pip install torch torchvision easyocr --upgrade
  ```

### Issue 3: "No module named 'cv2'"
**Solution:**
```bash
pip install opencv-python-headless
```

### Issue 4: "Template upload shows 0 fields"
**Possible Causes:**
1. Tesseract not installed → Install Tesseract
2. OCR engines not available → Check installation
3. Document quality too poor → Try preprocessing

**Fallback:** The application will create a mock 3-field structure if OCR engines are unavailable.

### Issue 5: PyTorch Installation Issues (Windows)
**Solution:**
```bash
# Install specific PyTorch version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Issue 6: Permission Issues (Linux/Mac)
**Solution:**
```bash
# Fix media directory permissions
chmod -R 755 media/
chmod -R 755 static/
```

---

## ✅ Verification

### Verify Tesseract Installation:
```bash
tesseract --version
tesseract --list-langs
```

### Verify Python Dependencies:
```bash
pip list | grep -E "(Django|pytesseract|easyocr|opencv)"
```

### Test OCR Functionality:
1. Navigate to: http://127.0.0.1:8000/upload/
2. Upload a template (blank form)
3. Check if fields are detected
4. If "Found 3 fields" appears and you haven't installed Tesseract, the fallback system is working
5. If actual fields are detected, Tesseract is working correctly

### Check Django Installation:
```bash
python manage.py check
# Should show: System check identified no issues
```

### Test Database Connection:
```bash
python manage.py migrate --check
# Should show migration status without errors
```

---

## 📝 Quick Reference

### Essential Applications to Install:
1. ✅ **Python 3.8+** - Core runtime
2. ✅ **Tesseract OCR** - Text extraction engine
3. ✅ **pip** - Python package manager (comes with Python)
4. ⚙️ **Virtual Environment** - Isolated Python environment (recommended)

### Applications on PATH Required:
- **python** (or python3)
- **pip** (or pip3)
- **tesseract** ⭐ CRITICAL FOR OCR

### Optional (Handled by Python packages):
- OpenCV (installed via opencv-python)
- PyTorch (installed via pip)
- EasyOCR (installed via pip)

---

## 🎯 Summary

**Minimum Requirements:**
```
✅ Python 3.8+
✅ Tesseract OCR Engine (in PATH)
✅ pip install -r requirements.txt
✅ python manage.py migrate
```

**Recommended Setup:**
```
✅ All minimum requirements
✅ Virtual environment
✅ Tesseract language data
✅ EasyOCR models downloaded
✅ Sufficient disk space (~2GB for dependencies)
```

**That's it!** The application will gracefully handle missing optional components and provide clear feedback about what needs to be installed.

---

## 🆘 Need Help?

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Verify all required applications are installed
3. Check application logs: `ocr_app.log`
4. Enable debug mode in Django settings for detailed errors
5. Open an issue on GitHub with error details

**Common Error Patterns:**
- `TesseractNotFoundError` → Install Tesseract and add to PATH
- `ModuleNotFoundError` → Run `pip install -r requirements.txt`
- `OperationalError` → Run `python manage.py migrate`
- Import errors → Activate virtual environment first
