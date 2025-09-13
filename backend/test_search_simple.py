#!/usr/bin/env python3
"""
Simple Search Test - Test the search API endpoint directly
"""

import requests
import json

def test_search_api():
    base_url = "http://localhost:8080"
    
    print("🔍 Testing Search API Endpoint")
    print("=" * 50)
    
    # Test 1: Search without auth (should fail)
    print("\n1. Testing search without authentication...")
    response = requests.post(f"{base_url}/search/", 
                           json={"query": "jules", "limit": 10})
    print(f"Status: {response.status_code}")
    if response.status_code == 403:
        print("✓ Correctly requires authentication")
    else:
        print("✗ Authentication not working properly")
    
    # Test 2: Try to get an auth token (would need real password)
    print("\n2. Testing auth endpoint...")
    auth_response = requests.post(f"{base_url}/auth/login",
                                json={"email": "bharani@gmail.com", "password": "test"})
    print(f"Auth Status: {auth_response.status_code}")
    print(f"Auth Response: {auth_response.text[:100]}...")
    
    # Test 3: Check if health endpoint works
    print("\n3. Testing health endpoint...")
    health_response = requests.get(f"{base_url}/health")
    print(f"Health Status: {health_response.status_code}")
    print(f"Health Response: {health_response.text}")
    
    # Test 4: Check available endpoints
    print("\n4. Testing OpenAPI docs...")
    docs_response = requests.get(f"{base_url}/docs")
    print(f"Docs Status: {docs_response.status_code}")
    if docs_response.status_code == 200:
        print("✓ API documentation accessible")
    
    print("\n" + "=" * 50)
    print("💡 To test search functionality:")
    print("1. Go to http://localhost:3000")
    print("2. Login with your account")
    print("3. Try searching for: 'jules', 'reddit', 'getting started'")
    print("4. The search should work with keyword matching")

if __name__ == "__main__":
    test_search_api()