# 🔧 Poppler PATH Issue - Solution

## 🔴 Current Situation

**What's Happening:**
- ✅ Poppler works in **Command Prompt (CMD)**
- ❌ Poppler does NOT work in **PowerShell**
- ❌ Python/Django **cannot access** Poppler

**Test Results:**
```
CMD:        pdftoppm -v  ✅ WORKS
PowerShell: pdftoppm -v  ❌ FAILS
Python:     subprocess   ❌ FAILS
```

**Impact:**
Your Django application **CANNOT** process PDFs until this is fixed.

---

## ✅ Solution: Restart VS Code

### Why This Happens:
When you add something to System PATH:
- CMD picks it up immediately (reads from registry)
- PowerShell needs to be restarted
- VS Code needs to be restarted
- Python subprocesses inherit PATH from parent process

### Quick Fix:

1. **Save all your work**
2. **Close VS Code completely** (don't just close the window - use File → Exit)
3. **Reopen VS Code**
4. **Open terminal in VS Code** (PowerShell)
5. **Test:**
   ```powershell
   pdftoppm -v
   ```
   Should now show: `pdftoppm version 25.07.0`

6. **Verify in Python:**
   ```powershell
   cd D:\code\optR\OCR
   D:\code\optR\virtual\Scripts\python.exe quick_test.py
   ```
   Should show: `✅ SUCCESS: Poppler is accessible!`

7. **Start Django server:**
   ```powershell
   python manage.py runserver
   ```

8. **Test PDF preview:**
   - Go to: http://127.0.0.1:8000/templates/
   - Click **View** on your PDF template
   - Should work! 🎉

---

## 🔍 Alternative: Check PATH Configuration

If restarting VS Code doesn't work, verify PATH is set correctly:

### Check System PATH:
1. Press `Win + X` → **System**
2. **Advanced system settings** → **Environment Variables**
3. Under **System variables**, find **Path**
4. Look for Poppler entry (e.g., `C:\Program Files\poppler-xx.x.x\Library\bin`)

### Where is Poppler installed?
Since `pdftoppm` works in CMD, let's find it:

**In CMD (not PowerShell):**
```cmd
where pdftoppm
```

This will show the full path to the Poppler executable.

**Common locations:**
- `C:\Program Files\poppler-xx.x.x\Library\bin\`
- `C:\Users\<username>\AppData\Local\Programs\Poppler\bin\`
- Conda environment: `C:\Users\<username>\anaconda3\Library\bin\`

---

## 🎯 Expected Behavior After Fix

Once PATH is properly configured and VS Code is restarted:

1. **PowerShell test:**
   ```powershell
   pdftoppm -v
   # Output: pdftoppm version 25.07.0
   ```

2. **Python test:**
   ```powershell
   python quick_test.py
   # Output: ✅ SUCCESS: Poppler is accessible!
   ```

3. **Django test:**
   - PDF templates show preview ✅
   - No "Unable to get page count" error ✅

---

## 🚨 If Still Not Working

### Option 1: Use CMD Instead of PowerShell
VS Code can use CMD as default terminal:
1. Press `Ctrl + Shift + P`
2. Type: "Terminal: Select Default Profile"
3. Choose: **Command Prompt**
4. Close and reopen terminal

### Option 2: Manually Specify Poppler Path in Code

Find where Poppler is installed:
```cmd
where pdftoppm
```

Then modify `ocr_processing/utils.py`:
```python
from pdf2image import convert_from_path

# Add poppler_path parameter
POPPLER_PATH = r'C:\path\to\poppler\bin'  # Use path from 'where pdftoppm'

images = convert_from_path(
    pdf_path,
    poppler_path=POPPLER_PATH
)
```

### Option 3: Add to PowerShell Profile
Add Poppler to PowerShell's PATH permanently:

```powershell
# Check current PowerShell PATH
$env:Path

# Add Poppler (replace with actual path)
$env:Path += ";C:\Program Files\poppler-25.07.0\Library\bin"

# To make permanent, add to PowerShell profile:
notepad $PROFILE
# Add: $env:Path += ";C:\Program Files\poppler-25.07.0\Library\bin"
```

---

## 📝 Summary

**Current Status:**
- ✅ Poppler is installed (v25.07.0)
- ✅ pdf2image Python library installed
- ⚠️  Poppler not accessible to PowerShell/Python

**Next Steps:**
1. **Restart VS Code** (most likely fix)
2. If that doesn't work, find where Poppler is with `where pdftoppm` in CMD
3. Verify that path is in System PATH
4. Consider switching VS Code to use CMD instead of PowerShell

**After fixing:**
Run `python quick_test.py` - should show ✅ SUCCESS
