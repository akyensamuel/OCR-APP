# REST API Documentation

## Overview
The OCR Web Application provides a comprehensive REST API for programmatic access to all features including document processing, template management, search, and export functionality.

**Base URL:** `http://localhost:8000/api/v1/`

**API Version:** v1

## Authentication

The API uses Token-based authentication. All API requests require an authentication token in the header.

### Obtain Token
```http
POST /api/v1/auth/token/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

### Using the Token
Include the token in the Authorization header for all API requests:

```http
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

## API Endpoints

### Templates

#### List Templates
```http
GET /api/v1/templates/
```

**Query Parameters:**
- `is_active` (boolean): Filter by active status
- `processing_status` (string): Filter by processing status
- `search` (string): Search by name or description
- `ordering` (string): Sort by field (e.g., `-created_at`, `name`)

**Response:**
```json
[
    {
        "id": 1,
        "name": "Invoice Template",
        "description": "Standard invoice processing",
        "field_count": 5,
        "is_active": true,
        "created_at": "2025-10-01T10:00:00Z",
        "document_count": 12
    }
]
```

#### Get Template Details
```http
GET /api/v1/templates/{id}/
```

**Response:**
```json
{
    "id": 1,
    "name": "Invoice Template",
    "description": "Standard invoice processing",
    "structure": {...},
    "field_count": 5,
    "is_active": true,
    "processing_status": "completed",
    "created_at": "2025-10-01T10:00:00Z",
    "updated_at": "2025-10-02T12:30:00Z",
    "created_by": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com"
    },
    "document_count": 12,
    "field_names": ["Invoice Number", "Date", "Total Amount", "Vendor", "Items"],
    "sample_image": "/media/templates/sample.png"
}
```

#### Create Template
```http
POST /api/v1/templates/
Content-Type: application/json

{
    "name": "New Template",
    "description": "Template description",
    "structure": {...},
    "is_active": true
}
```

#### Update Template
```http
PUT /api/v1/templates/{id}/
PATCH /api/v1/templates/{id}/
```

#### Delete Template
```http
DELETE /api/v1/templates/{id}/
```

#### Get Template Documents
```http
GET /api/v1/templates/{id}/documents/
```

Returns all documents associated with this template.

#### Activate/Deactivate Template
```http
POST /api/v1/templates/{id}/activate/
POST /api/v1/templates/{id}/deactivate/
```

#### Export Template to Excel
```http
GET /api/v1/templates/{id}/export_excel/
```

Downloads an Excel file with all template documents.

---

### Documents

#### List Documents
```http
GET /api/v1/documents/
```

**Query Parameters:**
- `processing_status` (string): Filter by status
- `template` (integer): Filter by template ID
- `confidence_min` (float): Minimum confidence score
- `confidence_max` (float): Maximum confidence score
- `search` (string): Search by name or text content
- `ordering` (string): Sort by field

**Response:**
```json
[
    {
        "id": 1,
        "name": "invoice_001.png",
        "confidence_score": 95.5,
        "processing_status": "completed",
        "template_name": "Invoice Template",
        "uploaded_by_name": "admin",
        "created_at": "2025-10-02T14:20:00Z"
    }
]
```

#### Get Document Details
```http
GET /api/v1/documents/{id}/
```

**Response:**
```json
{
    "id": 1,
    "name": "invoice_001.png",
    "file": "/media/uploads/invoice_001.png",
    "file_url": "http://localhost:8000/media/uploads/invoice_001.png",
    "text_content": "Extracted text content...",
    "extracted_data": {...},
    "extracted_fields": {
        "Invoice Number": {"value": "INV-001", "confidence": 98.5},
        "Date": {"value": "2025-10-01", "confidence": 95.2}
    },
    "confidence_score": 95.5,
    "processing_status": "completed",
    "template": {
        "id": 1,
        "name": "Invoice Template",
        "field_count": 5
    },
    "uploaded_by": {
        "id": 1,
        "username": "admin"
    },
    "created_at": "2025-10-02T14:20:00Z",
    "updated_at": "2025-10-02T14:21:00Z",
    "excel_file": "/media/exports/invoice_001.xlsx",
    "excel_file_url": "http://localhost:8000/media/exports/invoice_001.xlsx"
}
```

#### Create Document
```http
POST /api/v1/documents/
Content-Type: multipart/form-data

{
    "name": "document_name",
    "file": <file>,
    "template_id": 1  // optional
}
```

The document will be automatically processed with OCR upon creation.

#### Update Document
```http
PUT /api/v1/documents/{id}/
PATCH /api/v1/documents/{id}/
```

#### Delete Document
```http
DELETE /api/v1/documents/{id}/
```

#### Export Document to Excel
```http
GET /api/v1/documents/{id}/export_excel/
```

#### Export Document to PDF
```http
GET /api/v1/documents/{id}/export_pdf/
```

#### Reprocess Document
```http
POST /api/v1/documents/{id}/reprocess/
```

Reprocesses the document with OCR engine.

---

### OCR Processing

#### Process Image/Document
```http
POST /api/v1/ocr/process/
Content-Type: multipart/form-data

{
    "file": <file>,
    "template_id": 1,  // optional
    "extract_structure": true  // optional
}
```

**Response:**
```json
{
    "text": "Extracted text content...",
    "confidence": 95.5,
    "status": "success",
    "template": "Invoice Template"
}
```

**File Requirements:**
- Maximum size: 10MB
- Allowed formats: .jpg, .jpeg, .png, .pdf, .tiff, .bmp

---

### Statistics

#### Get Dashboard Statistics
```http
GET /api/v1/statistics/
```

**Response:**
```json
{
    "total_documents": 50,
    "total_templates": 5,
    "recent_documents": [...],
    "documents_by_template": [
        {
            "name": "Invoice Template",
            "doc_count": 25
        }
    ],
    "average_confidence": 92.5,
    "processing_status_breakdown": {
        "completed": 45,
        "pending": 3,
        "failed": 2
    }
}
```

---

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Resource deleted successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

**Error Format:**
```json
{
    "error": "Error message description",
    "detail": "Additional details if available"
}
```

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `page` (integer): Page number
- `page_size` (integer): Items per page (default: 20)

**Response Format:**
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/v1/documents/?page=2",
    "previous": null,
    "results": [...]
}
```

---

## Filtering and Search

Most list endpoints support filtering and search:

### Search
Use `?search=keyword` to search across relevant fields.

### Filtering
Use query parameters matching field names:
- `?is_active=true`
- `?processing_status=completed`
- `?template=1`

### Ordering
Use `?ordering=field_name` to sort results:
- `?ordering=created_at` (ascending)
- `?ordering=-created_at` (descending)
- `?ordering=name,-created_at` (multiple fields)

---

## Usage Examples

### Python (requests)
```python
import requests

# Obtain token
response = requests.post(
    'http://localhost:8000/api/v1/auth/token/',
    json={'username': 'admin', 'password': 'password'}
)
token = response.json()['token']

# Make authenticated request
headers = {'Authorization': f'Token {token}'}
response = requests.get(
    'http://localhost:8000/api/v1/documents/',
    headers=headers
)
documents = response.json()
```

### cURL
```bash
# Obtain token
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Get documents
curl -X GET http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"

# Upload and process document
curl -X POST http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -F "name=invoice_001" \
  -F "file=@/path/to/invoice.png" \
  -F "template_id=1"
```

### JavaScript (fetch)
```javascript
// Obtain token
const response = await fetch('http://localhost:8000/api/v1/auth/token/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username: 'admin', password: 'password'})
});
const {token} = await response.json();

// Get documents
const docs = await fetch('http://localhost:8000/api/v1/documents/', {
    headers: {'Authorization': `Token ${token}`}
});
const documents = await docs.json();
```

---

## Rate Limiting

Currently, there are no rate limits implemented. This may change in future versions.

---

## Versioning

The API uses URL versioning. Current version: `v1`

Future versions will be available at:
- `/api/v2/`
- `/api/v3/`

---

## Support

For API support or to report issues:
- Email: support@example.com
- Documentation: http://localhost:8000/api/docs/
- Issue Tracker: GitHub Issues

---

## Changelog

### v1.0.0 (October 2, 2025)
- Initial API release
- Template management endpoints
- Document CRUD operations
- OCR processing endpoint
- Statistics and analytics
- Authentication with tokens
- Export functionality (Excel, PDF)
- Search and filtering
