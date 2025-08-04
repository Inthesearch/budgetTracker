import requests
import json

# Test CORS configuration
def test_cors():
    base_url = "https://budgettracker-yiw5.onrender.com"
    
    # Test endpoints
    endpoints = [
        "/",
        "/health",
        "/cors-test",
        "/api/v1/category/list"
    ]
    
    print("Testing CORS configuration...")
    print("=" * 50)
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\nTesting: {url}")
        
        try:
            # Test with different origins
            headers = {
                'Origin': 'https://your-frontend-domain.com',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ Success!")
            else:
                print("❌ Failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("CORS Test Complete")

if __name__ == "__main__":
    test_cors() 