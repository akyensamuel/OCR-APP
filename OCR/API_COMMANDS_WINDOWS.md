# API Testing Commands for Windows

## Using PowerShell (Invoke-RestMethod)

### 1. Get Authentication Token
```powershell
$body = @{username="testuser"; password="testpass123"} | ConvertTo-Json
$tokenResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/token/" -Method Post -Body $body -ContentType "application/json"
$token = $tokenResponse.token
```

### 2. Set Headers
```powershell
$headers = @{
    "Authorization" = "Token $token"
}
```

### 3. List All Documents
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/documents/" -Headers $headers
```

### 4. List All Templates
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/templates/" -Headers $headers
```

### 5. Get Statistics
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/statistics/" -Headers $headers
```

### 6. Search Documents
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/documents/?search=keyword" -Headers $headers
```

### 7. Filter by Template
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/documents/?template=1" -Headers $headers
```

### 8. Filter by Status
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/documents/?processing_status=completed" -Headers $headers
```

### 9. Get Document Details
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/documents/1/" -Headers $headers
```

### 10. Get Template Details
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/templates/1/" -Headers $headers
```

---

## Using curl (Windows with Git Bash or WSL)

### 1. Get Token
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"testuser\",\"password\":\"testpass123\"}"
```

### 2. Save Token
```bash
TOKEN="88f6edbb5ce7b1eeab710d4b9d6c68b12ae509f4"
```

### 3. List Documents
```bash
curl -H "Authorization: Token $TOKEN" \
  http://127.0.0.1:8000/api/v1/documents/
```

### 4. Search Documents
```bash
curl -H "Authorization: Token $TOKEN" \
  "http://127.0.0.1:8000/api/v1/documents/?search=keyword"
```

---

## Using Python requests

### Complete Example
```python
import requests

# Base URL
base_url = "http://127.0.0.1:8000/api/v1"

# 1. Get token
response = requests.post(
    f"{base_url}/auth/token/",
    json={"username": "testuser", "password": "testpass123"}
)
token = response.json()["token"]

# 2. Set headers
headers = {"Authorization": f"Token {token}"}

# 3. List documents
documents = requests.get(f"{base_url}/documents/", headers=headers).json()
print(f"Found {len(documents)} documents")

# 4. Search documents
results = requests.get(
    f"{base_url}/documents/",
    headers=headers,
    params={"search": "keyword"}
).json()

# 5. Get statistics
stats = requests.get(f"{base_url}/statistics/", headers=headers).json()
print(f"Total documents: {stats['total_documents']}")
```

---

## Quick Test Script

### PowerShell (Recommended for Windows)
```powershell
# Run the test script
.\test_api.ps1
```

### Python
```bash
python test_api.py
```

---

## Common Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/token/` | Get authentication token |
| GET | `/api/v1/templates/` | List all templates |
| GET | `/api/v1/templates/{id}/` | Get template details |
| POST | `/api/v1/templates/` | Create new template |
| GET | `/api/v1/documents/` | List all documents |
| GET | `/api/v1/documents/{id}/` | Get document details |
| POST | `/api/v1/documents/` | Upload and process document |
| GET | `/api/v1/statistics/` | Get dashboard statistics |
| POST | `/api/v1/ocr/process/` | Process image with OCR |

---

## Query Parameters

### Search
```
?search=keyword
```

### Filter by Template
```
?template=1
```

### Filter by Status
```
?processing_status=completed
```

### Filter by Confidence
```
?confidence_min=80&confidence_max=100
```

### Ordering
```
?ordering=-created_at
```

### Pagination
```
?page=2
```

---

## Test Token

For testing purposes, use:
```
Token: 88f6edbb5ce7b1eeab710d4b9d6c68b12ae509f4
Username: testuser
Password: testpass123
```

---

## Troubleshooting

### PowerShell curl doesn't work
PowerShell has its own `curl` alias that points to `Invoke-WebRequest`. Use `Invoke-RestMethod` instead:

❌ **Don't use:**
```powershell
curl -H "Authorization: Token XXX" http://...
```

✅ **Use instead:**
```powershell
$headers = @{"Authorization" = "Token XXX"}
Invoke-RestMethod -Uri "http://..." -Headers $headers
```

### Server not running
```bash
cd d:\code\optR\OCR
python manage.py runserver
```

### Token expired
Get a new token:
```powershell
$body = @{username="testuser"; password="testpass123"} | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/token/" -Method Post -Body $body -ContentType "application/json"
$token = $response.token
```

---

## Full Working Example (PowerShell)

```powershell
# 1. Get token
$body = @{username="testuser"; password="testpass123"} | ConvertTo-Json
$tokenResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/token/" -Method Post -Body $body -ContentType "application/json"
$token = $tokenResponse.token
Write-Host "Token: $token"

# 2. Create headers
$headers = @{"Authorization" = "Token $token"}

# 3. Get documents
$documents = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/documents/" -Headers $headers
Write-Host "Found $($documents.Count) documents"

# 4. Get statistics
$stats = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/statistics/" -Headers $headers
Write-Host "Total templates: $($stats.total_templates)"
Write-Host "Total documents: $($stats.total_documents)"
Write-Host "Average confidence: $($stats.average_confidence)%"

# 5. Search
$results = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/documents/?search=screenshot" -Headers $headers
Write-Host "Search returned $($results.Count) results"
```

Save as `test_api_simple.ps1` and run with:
```powershell
.\test_api_simple.ps1
```
