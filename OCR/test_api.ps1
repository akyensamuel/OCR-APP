# PowerShell API Test Script
# Tests the OCR Web Application REST API

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "REST API TEST (PowerShell)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://127.0.0.1:8000/api/v1"

# Test 1: Get Token
Write-Host "[Test 1] Getting authentication token..." -ForegroundColor Yellow
try {
    $tokenBody = @{
        username = "testuser"
        password = "testpass123"
    } | ConvertTo-Json
    
    $tokenResponse = Invoke-RestMethod -Uri "$baseUrl/auth/token/" `
        -Method Post `
        -Body $tokenBody `
        -ContentType "application/json"
    
    $token = $tokenResponse.token
    Write-Host "✅ SUCCESS: Token obtained" -ForegroundColor Green
    Write-Host "   Token: $token" -ForegroundColor Gray
} catch {
    Write-Host "❌ FAILED: Could not get token" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit
}
Write-Host ""

# Create headers for authenticated requests
$headers = @{
    "Authorization" = "Token $token"
    "Content-Type" = "application/json"
}

# Test 2: List Templates
Write-Host "[Test 2] GET /api/v1/templates/" -ForegroundColor Yellow
try {
    $templates = Invoke-RestMethod -Uri "$baseUrl/templates/" `
        -Method Get `
        -Headers $headers
    
    Write-Host "✅ SUCCESS: Found $($templates.Count) template(s)" -ForegroundColor Green
    if ($templates.Count -gt 0) {
        Write-Host "   First template: $($templates[0].name)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
}
Write-Host ""

# Test 3: List Documents
Write-Host "[Test 3] GET /api/v1/documents/" -ForegroundColor Yellow
try {
    $documents = Invoke-RestMethod -Uri "$baseUrl/documents/" `
        -Method Get `
        -Headers $headers
    
    Write-Host "✅ SUCCESS: Found $($documents.Count) document(s)" -ForegroundColor Green
    if ($documents.Count -gt 0) {
        Write-Host "   First document: $($documents[0].name)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: Get Statistics
Write-Host "[Test 4] GET /api/v1/statistics/" -ForegroundColor Yellow
try {
    $stats = Invoke-RestMethod -Uri "$baseUrl/statistics/" `
        -Method Get `
        -Headers $headers
    
    Write-Host "✅ SUCCESS: Retrieved statistics" -ForegroundColor Green
    Write-Host "   Total documents: $($stats.total_documents)" -ForegroundColor Gray
    Write-Host "   Total templates: $($stats.total_templates)" -ForegroundColor Gray
    Write-Host "   Average confidence: $($stats.average_confidence)%" -ForegroundColor Gray
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
}
Write-Host ""

# Test 5: Search Documents
Write-Host "[Test 5] GET /api/v1/documents/?search=screenshot" -ForegroundColor Yellow
try {
    $searchResults = Invoke-RestMethod -Uri "$baseUrl/documents/?search=screenshot" `
        -Method Get `
        -Headers $headers
    
    Write-Host "✅ SUCCESS: Search returned $($searchResults.Count) result(s)" -ForegroundColor Green
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 6: Filter Documents
Write-Host "[Test 6] GET /api/v1/documents/?processing_status=completed" -ForegroundColor Yellow
try {
    $filtered = Invoke-RestMethod -Uri "$baseUrl/documents/?processing_status=completed" `
        -Method Get `
        -Headers $headers
    
    Write-Host "✅ SUCCESS: Filter returned $($filtered.Count) completed document(s)" -ForegroundColor Green
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
}
Write-Host ""

# Test 7: Get Template Details
Write-Host "[Test 7] GET /api/v1/templates/1/" -ForegroundColor Yellow
try {
    $template = Invoke-RestMethod -Uri "$baseUrl/templates/1/" `
        -Method Get `
        -Headers $headers
    
    Write-Host "✅ SUCCESS: Retrieved template details" -ForegroundColor Green
    Write-Host "   Name: $($template.name)" -ForegroundColor Gray
    Write-Host "   Field count: $($template.field_count)" -ForegroundColor Gray
    Write-Host "   Is active: $($template.is_active)" -ForegroundColor Gray
} catch {
    Write-Host "⚠️  Template ID 1 not found (expected if no templates exist)" -ForegroundColor DarkYellow
}
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "TEST COMPLETE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 API is available at: $baseUrl" -ForegroundColor White
Write-Host "🔑 Your token: $token" -ForegroundColor White
Write-Host ""
Write-Host "Example PowerShell commands:" -ForegroundColor Yellow
Write-Host ""
Write-Host "# List documents:" -ForegroundColor Gray
Write-Host "`$headers = @{`"Authorization`" = `"Token $token`"}" -ForegroundColor Cyan
Write-Host "Invoke-RestMethod -Uri '$baseUrl/documents/' -Headers `$headers" -ForegroundColor Cyan
Write-Host ""
Write-Host "# Get statistics:" -ForegroundColor Gray
Write-Host "Invoke-RestMethod -Uri '$baseUrl/statistics/' -Headers `$headers" -ForegroundColor Cyan
Write-Host ""
Write-Host "# Search documents:" -ForegroundColor Gray
Write-Host "Invoke-RestMethod -Uri '$baseUrl/documents/?search=keyword' -Headers `$headers" -ForegroundColor Cyan
