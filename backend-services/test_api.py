#!/usr/bin/env python3
"""
Test the API Gateway
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Gateway URL
API_URL = "http://localhost:8000"

# Test the root endpoint
def test_root():
    try:
        response = requests.get(f"{API_URL}/")
        print(f"Root endpoint: {response.status_code}")
        print(response.json())
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing root endpoint: {str(e)}")
        return False

# Test the OpenAPI documentation
def test_openapi():
    try:
        response = requests.get(f"{API_URL}/api/v1/openapi.json")
        print(f"OpenAPI endpoint: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing OpenAPI endpoint: {str(e)}")
        return False

# Run tests
if __name__ == "__main__":
    print("Testing API Gateway...")
    
    # Test root endpoint
    root_success = test_root()
    
    # Test OpenAPI documentation
    openapi_success = test_openapi()
    
    # Print results
    print("\nTest results:")
    print(f"Root endpoint: {'Success' if root_success else 'Failure'}")
    print(f"OpenAPI endpoint: {'Success' if openapi_success else 'Failure'}")
    
    # Exit with success or failure
    if root_success and openapi_success:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)
