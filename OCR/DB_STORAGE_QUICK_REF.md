# Quick Reference: Database Storage

## 🎯 Quick Summary
**Files are now stored in db.sqlite3 instead of file system folders!**

## ✅ What's Done
- ✅ Models updated (14 new fields total)
- ✅ Migrations applied
- ✅ Upload logic converted
- ✅ File serving views created
- ✅ URLs configured
- ✅ Backward compatible

## 🚀 Test It Now

### 1. Upload Template
```
http://localhost:8000/upload/
Upload any image/PDF → Should work!
```

### 2. Check Database
```python
python manage.py shell
>>> from templates.models import Template
>>> t = Template.objects.latest('created_at')
>>> print(t.file_data is not None)  # Should be True
>>> print(f"{len(t.file_data)} bytes stored")
```

### 3. Download File
```
Go to template detail page
Click any download link → File served from database!
```

## 📦 Key Files

### New Module
- `basemode/file_storage.py` - All utility functions

### Modified Models
- `templates/models.py` - 8 new binary fields
- `documents/models.py` - 6 new binary fields

### Modified Views
- `templates/views.py` - Updated upload + 3 serving views
- `documents/views.py` - Updated upload + 2 serving views

## 🔧 Usage Examples

### Save to Database
```python
from basemode.file_storage import save_file_to_db

file_info = save_file_to_db(uploaded_file)
model.file_data = file_info['file_data']
model.file_name = file_info['file_name']
model.file_type = file_info['file_type']
model.save()
```

### Serve from Database
```python
from basemode.file_storage import serve_file_from_db

return serve_file_from_db(
    model.file_data,
    model.file_name,
    model.file_type,
    as_attachment=True
)
```

### Process with Temp File
```python
from basemode.file_storage import get_temp_file_path, cleanup_temp_file

# Create temp file
temp_path = get_temp_file_path(model.file_data, model.file_name)

# Process it
result = ocr_engine.extract_text(temp_path)

# Clean up
cleanup_temp_file(temp_path)
```

## 🌟 Benefits
- **Deployment**: Just copy db.sqlite3
- **Backup**: One file = complete backup
- **Portability**: No broken file paths
- **Atomic**: Files + metadata in one transaction

## 📊 Before vs After

### Before (File System)
```
media/
  templates/
    form1.jpg
    form2.pdf
  documents/
    doc1.jpg
    excel/
      doc1.xlsx
```

### After (Database)
```
db.sqlite3
  └─ Contains everything!
     ├─ Template files
     ├─ Document files
     ├─ Excel exports
     └─ Visualizations
```

## ⚡ Quick Commands

### Check All Files in DB
```python
python manage.py shell

# Count templates with files in DB
from templates.models import Template
print(f"Templates in DB: {Template.objects.filter(file_data__isnull=False).count()}")

# Count documents with files in DB
from documents.models import Document
print(f"Documents in DB: {Document.objects.filter(file_data__isnull=False).count()}")
```

### Migrate Old Files
```python
python manage.py shell

# Copy-paste this to migrate existing files
from basemode.file_storage import read_file_from_path
from templates.models import Template
from documents.models import Document

# Migrate templates
for t in Template.objects.filter(file_data__isnull=True):
    if t.file:
        try:
            info = read_file_from_path(t.file.path)
            t.file_data = info['file_data']
            t.file_name = info['file_name']
            t.file_type = info['file_type']
            t.file_size = info['file_size']
            t.save()
            print(f"✅ {t.name}")
        except: pass

# Migrate documents
for d in Document.objects.filter(file_data__isnull=True):
    if d.file:
        try:
            info = read_file_from_path(d.file.path)
            d.file_data = info['file_data']
            d.file_name = info['file_name']
            d.file_type = info['file_type']
            d.file_size = info['file_size']
            d.save()
            print(f"✅ {d.name}")
        except: pass
```

## 🎯 URL Reference

### Templates
```
/templates/<id>/file/          → Original file
/templates/<id>/excel/         → Excel template
/templates/<id>/visualization/ → Detection image
```

### Documents
```
/documents/<id>/file/       → Original document
/documents/<id>/excel-file/ → Excel export
```

## 📝 Model Fields Reference

### Template
```python
file_data           # Binary file content
file_name           # "form.jpg"
file_type           # "image/jpeg"
file_size           # 123456 (bytes)
excel_template_data # Excel binary
excel_template_name # "form_template.xlsx"
visualization_data  # Image binary
visualization_name  # "form_detected.jpg"
```

### Document
```python
file_data   # Binary file content
file_name   # "doc.jpg"
file_type   # "image/jpeg"
file_size   # 123456 (bytes)
excel_data  # Excel export binary
excel_name  # "doc_extracted.xlsx"
```

## 🔍 Troubleshooting

### Problem: File not found
**Solution**: Check if file_data is in database
```python
template = Template.objects.get(id=1)
print(template.file_data is not None)  # Should be True
```

### Problem: OCR fails
**Solution**: Check temp file creation
```python
from basemode.file_storage import get_temp_file_path
temp = get_temp_file_path(template.file_data, template.file_name)
print(f"Temp file: {temp}")
print(f"Exists: {os.path.exists(temp)}")
```

### Problem: Database too large
**Solution**: Check file sizes
```python
from templates.models import Template
total = sum(t.file_size or 0 for t in Template.objects.all())
print(f"Total: {total / 1024 / 1024:.2f} MB")
```

## 💾 Backup Command
```bash
# Backup everything (Windows)
copy db.sqlite3 db_backup_%date:~-4%%date:~-7,2%%date:~-10,2%.sqlite3

# Backup everything (Linux/Mac)
cp db.sqlite3 db_backup_$(date +%Y%m%d).sqlite3
```

## ✨ That's It!

Your system now stores files in the database. 

**Test it**: Upload a template and check that it works!

For more details:
- Full guide: `DATABASE_STORAGE_MIGRATION.md`
- Implementation: `MIGRATION_COMPLETE.md`
