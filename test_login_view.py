"""
Test script to verify login page loads correctly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from django.test import Client
from django.urls import reverse

# Create a test client
client = Client()

# Test 1: Access login page
print("Test 1: Accessing login page...")
response = client.get('/login/')
print(f"Status Code: {response.status_code}")
print(f"Template Used: {response.template_name if hasattr(response, 'template_name') else 'N/A'}")

if response.status_code == 200:
    print("✅ Login page loads successfully!")
else:
    print(f"❌ Error: {response.status_code}")

# Test 2: Access home page
print("\nTest 2: Accessing home page...")
response = client.get('/')
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    print("✅ Home page loads successfully!")
else:
    print(f"❌ Error: {response.status_code}")

# Test 3: Check if template exists
print("\nTest 3: Checking template files...")
from django.template.loader import get_template
try:
    template = get_template('auth/index.html')
    print("✅ Template 'auth/index.html' found!")
except Exception as e:
    print(f"❌ Template error: {e}")

print("\n✅ All tests completed!")
