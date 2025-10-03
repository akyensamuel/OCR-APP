# Template Editor - Quick Start Guide

## 🚀 How to Use

### **Step 1: Access the Editor**
1. Go to your template (Template ID: 18 - the handwritten billing report)
2. Click the blue **"Template Editor"** button
3. Editor opens with your 182 detected cells

### **Step 2: Edit Cells**
- **Double-click** any cell to edit
- Type new content
- Press **Enter** to save
- Cell updates automatically!

### **Step 3: Add/Remove Rows**
- Click **"Add Row Top"** or **"Add Row Bottom"**
- Or **right-click** a cell → "Insert Row Above/Below"
- To delete: Right-click → "Delete Row"

### **Step 4: Add/Remove Columns**
- Click **"Add Column Left"** or **"Add Column Right"**
- Or **right-click** a cell → "Insert Column Left/Right"
- To delete: Right-click → "Delete Column"

### **Step 5: Mark Headers**
- Click **"Mark as Header"** button
- Click cells you want as headers (they turn blue)
- Click button again to exit header mode

### **Step 6: Save**
- Changes auto-save as you edit
- Click **"Save Changes"** for full save
- Or press **Ctrl+S**

## 🎯 Quick Actions

| Action | How To |
|--------|--------|
| Edit cell | Double-click cell |
| Save edit | Press Enter |
| Cancel edit | Press Escape |
| Add row | Toolbar or right-click |
| Delete row | Right-click → Delete Row |
| Add column | Toolbar or right-click |
| Delete column | Right-click → Delete Column |
| Mark header | Header mode → Click cell |
| Save all | Ctrl+S or "Save Changes" |
| Reload | Click "Reload" button |
| Context menu | Right-click any cell |

## 📊 Example Use Case

**Your Billing Report Template (182 cells):**

1. **Fix a typo in header:**
   - Double-click "Acconut Number" 
   - Change to "Account Number"
   - Press Enter ✅

2. **Add missing column:**
   - Click "Add Column Right"
   - Edit header to "Status"
   - Add data in cells below ✅

3. **Remove empty row:**
   - Right-click empty row
   - Select "Delete Row"
   - Confirm ✅

4. **Mark headers:**
   - Click "Mark as Header"
   - Click all first-row cells
   - They turn blue ✅

5. **Save & Done:**
   - Click "Save Changes"
   - See green "Saved successfully!" ✅

## 🎨 Visual Guide

```
┌─────────────────────────────────────────┐
│  Template Editor: Billing Report       │
│  [Save] [Add Row] [Add Col] [Header]   │
├─────────────────────────────────────────┤
│  #  │  A  │  B  │  C  │  D  │  E  │    │
├─────┼─────┼─────┼─────┼─────┼─────┤    │
│  1  │ ID  │Name │Amt  │Date │Stat │ ←Headers (blue)
├─────┼─────┼─────┼─────┼─────┼─────┤    │
│  2  │ 001 │John │$100 │1/1  │Paid │ ←Double-click to edit
│  3  │ 002 │Jane │$200 │1/2  │Due  │    │
│  4  │     │     │     │     │     │ ←Right-click for menu
└─────────────────────────────────────────┘
```

## ⌨️ Keyboard Shortcuts

- **Ctrl+S** - Save template
- **Enter** - Save cell edit
- **Escape** - Cancel edit
- **Tab** - Navigate (coming soon)

## 🔧 Troubleshooting

**Q: Changes not saving?**
A: Check console for errors, ensure you pressed Enter after editing

**Q: Can't see context menu?**
A: Right-click directly on a cell, not on borders

**Q: Deleted wrong row/column?**
A: Click "Reload" to restore from last save

**Q: Headers not showing?**
A: Make sure you're in header mode (button shows "Header Mode: ON")

## 🎉 You're Ready!

Test URL: http://127.0.0.1:8000/templates/18/editor/

Your template is fully editable now! 🚀
