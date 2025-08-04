import os
from dotenv import load_dotenv

load_dotenv()

print("=== CORS Configuration Debug ===")
print(f"CORS_ORIGINS environment variable: {os.getenv('CORS_ORIGINS')}")

# Test the config
from app.config import settings
print(f"Settings CORS origins: {settings.cors_origins}")

print("\n=== Testing API Endpoints ===")
import requests

base_url = "https://budgettracker-yiw5.onrender.com"

# Test basic endpoints
endpoints = ["/", "/health", "/cors-test"]

for endpoint in endpoints:
    try:
        response = requests.get(f"{base_url}{endpoint}")
        print(f"{endpoint}: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        print(f"{endpoint}: Error - {e}")

print("\n=== CORS Headers Test ===")
# Test CORS headers
try:
    headers = {
        'Origin': 'https://example.com',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type'
    }
    response = requests.options(f"{base_url}/api/v1/category/list", headers=headers)
    print(f"OPTIONS request status: {response.status_code}")
    print(f"CORS headers: {dict(response.headers)}")
except Exception as e:
    print(f"CORS test error: {e}") 