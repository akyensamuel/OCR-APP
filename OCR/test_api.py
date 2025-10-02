"""
Test script for REST API endpoints
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OCR.settings')
django.setup()

import requests
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

def test_api():
    """Test REST API endpoints"""
    print("=" * 60)
    print("REST API TEST")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000/api/v1"
    
    # Create or get test user and token
    print("\n[Setup] Creating test user and token...")
    try:
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'is_staff': False,
                'is_superuser': False
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing user: {user.username}")
        
        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        print(f"✅ Token: {token.key}")
        
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        return
    
    headers = {
        'Authorization': f'Token {token.key}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Get Templates
    print("\n[Test 1] GET /api/v1/templates/")
    try:
        response = requests.get(f"{base_url}/templates/", headers=headers)
        if response.status_code == 200:
            templates = response.json()
            print(f"✅ SUCCESS: Found {len(templates)} template(s)")
            if templates:
                print(f"   First template: {templates[0].get('name')}")
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 2: Get Documents
    print("\n[Test 2] GET /api/v1/documents/")
    try:
        response = requests.get(f"{base_url}/documents/", headers=headers)
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ SUCCESS: Found {len(documents)} document(s)")
            if documents:
                print(f"   First document: {documents[0].get('name')}")
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 3: Get Statistics
    print("\n[Test 3] GET /api/v1/statistics/")
    try:
        response = requests.get(f"{base_url}/statistics/", headers=headers)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ SUCCESS: Retrieved statistics")
            print(f"   Total documents: {stats.get('total_documents')}")
            print(f"   Total templates: {stats.get('total_templates')}")
            print(f"   Average confidence: {stats.get('average_confidence')}%")
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 4: Search Documents
    print("\n[Test 4] GET /api/v1/documents/?search=table")
    try:
        response = requests.get(f"{base_url}/documents/?search=table", headers=headers)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ SUCCESS: Search returned {len(results)} result(s)")
        else:
            print(f"❌ FAILED: Status {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 5: Filter Documents
    print("\n[Test 5] GET /api/v1/documents/?processing_status=completed")
    try:
        response = requests.get(
            f"{base_url}/documents/?processing_status=completed",
            headers=headers
        )
        if response.status_code == 200:
            results = response.json()
            print(f"✅ SUCCESS: Filter returned {len(results)} completed document(s)")
        else:
            print(f"❌ FAILED: Status {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    # Test 6: Test without authentication
    print("\n[Test 6] GET /api/v1/documents/ (without token)")
    try:
        response = requests.get(f"{base_url}/documents/")
        if response.status_code == 401:
            print(f"✅ SUCCESS: Authentication required (401 status)")
        else:
            print(f"⚠️  UNEXPECTED: Status {response.status_code}")
            print(f"   Expected 401 Unauthorized")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\n📝 Note: API is available at http://127.0.0.1:8000/api/v1/")
    print(f"🔑 Test Token: {token.key}")
    print("\nYou can now test the API using:")
    print(f"  curl -H 'Authorization: Token {token.key}' http://127.0.0.1:8000/api/v1/documents/")

if __name__ == '__main__':
    test_api()
