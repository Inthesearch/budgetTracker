import requests
import json

def test_cors():
    """Test CORS configuration"""
    url = "http://localhost:8000/health"
    
    # Test with different origins
    headers = {
        'Origin': 'http://localhost:3000',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print(f"Response Body: {response.text}")
        
        # Check for CORS headers
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers',
            'Access-Control-Allow-Credentials'
        ]
        
        print("\nCORS Headers:")
        for header in cors_headers:
            if header in response.headers:
                print(f"  {header}: {response.headers[header]}")
            else:
                print(f"  {header}: NOT FOUND")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cors() 