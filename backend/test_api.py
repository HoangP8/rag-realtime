#!/usr/bin/env python3
"""
API Testing Script for Medical Chatbot Backend

This script provides a simple way to test the API endpoints of the Medical Chatbot backend.
It uses the requests library to make HTTP requests to the API endpoints.

Usage:
    python test_api.py

Requirements:
    - requests
    - python-dotenv
"""
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env and .env.local files
load_dotenv()
load_dotenv(".env.local")

# Base URL for the API
BASE_URL = "http://localhost:8000"
# BASE_URL = "https://medbot-backend.fly.dev"

# Authentication token
TOKEN = None
REFRESH_TOKEN = None

def print_response(response):
    """Print the response in a formatted way"""
    print(f"Status Code: {response.status_code}")
    print("Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    print("Response Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print("\n" + "-" * 80 + "\n")

def login(email, password):
    """Login to the API and get a token"""
    global TOKEN
    global REFRESH_TOKEN
    url = f"{BASE_URL}/api/v1/auth/login"
    data = {
        "email": email,
        "password": password
    }
    response = requests.post(url, json=data)
    print("Login Response:")
    print_response(response)

    if response.status_code == 200:
        TOKEN = response.json().get("access_token")
        REFRESH_TOKEN = response.json().get("refresh_token")
        print(f"Token: {TOKEN} \n")
    return response

def refresh_token():
    """Refresh the authentication token"""
    global REFRESH_TOKEN
    
    url = f"{BASE_URL}/api/v1/auth/refresh"
    response = requests.post(url, json={"refresh_token": REFRESH_TOKEN})
    print("Refresh Token Response:")
    print_response(response)
    
    if response.status_code == 200:
        TOKEN = response.json().get("access_token")
        REFRESH_TOKEN = response.json().get("refresh_token")
        print(f"New Token: {TOKEN} \n")
    return response

def get_conversations():
    """Get all conversations"""
    url = f"{BASE_URL}/api/v1/conversations"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-API-Auth": f"Bearer {TOKEN}",
    }
    response = requests.get(url, headers=headers)
    print("Get Conversations Response:")
    print_response(response)
    return response

def create_conversation(title="Test Conversation"):
    """Create a new conversation"""
    url = f"{BASE_URL}/api/v1/conversations"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-API-Auth": f"Bearer {TOKEN}",
    }
    data = {
        "title": title,
        "metadata": {},
        "tags": ["test"]
    }
    response = requests.post(url, json=data, headers=headers)
    print("Create Conversation Response:")
    print_response(response)
    return response

def get_conversation(conversation_id):
    """Get a specific conversation"""
    url = f"{BASE_URL}/api/v1/conversations/{conversation_id}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-API-Auth": f"Bearer {TOKEN}"
    }
    response = requests.get(url, headers=headers)
    print("Get Conversation Response:")
    print_response(response)
    return response

def create_message(conversation_id, content="Hello, this is a test message"):
    """Create a new message in a conversation"""
    url = f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-API-Auth": f"Bearer {TOKEN}"
    }
    data = {
        "role": "user",
        "content": content,
        "message_type": "text"
    }
    response = requests.post(url, json=data, headers=headers)
    print("Create Message Response:")
    print_response(response)
    return response

def get_messages(conversation_id):
    """Get all messages in a conversation"""
    url = f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-API-Auth": f"Bearer {TOKEN}"
    }
    response = requests.get(url, headers=headers)
    print("Get Messages Response:")
    print_response(response)
    return response

def create_voice_session(conversation_id):
    """Create a new voice session"""
    url = f"{BASE_URL}/api/v1/voice/session/create"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-API-Auth": f"Bearer {TOKEN}"
    }
    data = {
        "conversation_id": conversation_id,
        "metadata": {
            "instructions": "You are a helpful medical assistant."
        }
    }
    response = requests.post(url, json=data, headers=headers)
    print("Create Voice Session Response:")
    print_response(response)
    return response

def get_voice_session_status(session_id):
    """Get the status of a voice session"""
    url = f"{BASE_URL}/api/v1/voice/session/{session_id}/status"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-API-Auth": f"Bearer {TOKEN}"
    }
    response = requests.get(url, headers=headers)
    print("Get Voice Session Status Response:")
    print_response(response)
    return response

def get_user_profile():
    """Get the user profile"""
    url = f"{BASE_URL}/api/v1/profile"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-API-Auth": f"Bearer {TOKEN}"
    }
    response = requests.get(url, headers=headers)
    print("Get User Profile Response:")
    print_response(response)
    return response

def register_user(email, password, first_name="Test", last_name="User"):
    """Register a new user"""
    url = f"{BASE_URL}/api/v1/auth/register"
    data = {
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name
    }
    response = requests.post(url, json=data)
    print("Register User Response:")
    print_response(response)
    return response

def run_tests():
    """Run all tests"""
    # Get email and password from environment variables or prompt user
    email = os.getenv("TEST_EMAIL")
    password = os.getenv("TEST_PASSWORD")

    if not email or not password:
        email = input("Enter your email: ")
        password = input("Enter your password: ")

    # Try to register first (this might fail if the user already exists)
    # email = "register@test.com"
    # password = "Password123!"
    # register_response = register_user(email, password)

    # Login
    login_response = login(email, password)
    if login_response.status_code != 200:
        print(f"Email: {email}, Password: {password}")
        print("Login failed. Exiting.")
        return

    # Refresh token
    # refresh_token()

    # Get conversations
    # get_conversations()

    # Create a conversation
    create_response = create_conversation()
    if create_response.status_code != 201:
        print("Failed to create conversation. Exiting.")
        return

    conversation_id = create_response.json().get("id")

    # Get the created conversation
    get_conversation(conversation_id)

    # # Create a message
    # create_message(conversation_id)

    # # Get messages
    # get_messages(conversation_id)

    # Create a voice session
    voice_response = create_voice_session(conversation_id)
    if voice_response.status_code == 200:
        session_id = voice_response.json().get("id")
        # Get voice session status
        get_voice_session_status(session_id)

        # Delete voice session
        delete_voice_response = requests.delete(
            f"{BASE_URL}/api/v1/voice/session/{session_id}", 
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "X-API-Auth": f"Bearer {TOKEN}"
            }
        )
        print(f"Delete Voice Session Response:")
        print_response(delete_voice_response)

    # Delete test conversation
    # delete_response = requests.delete(
    #     f"{BASE_URL}/api/v1/conversations/{conversation_id}", 
    #     headers={
    #         "Authorization": f"Bearer {TOKEN}",
    #         "X-API-Auth": f"Bearer {TOKEN}"
    #     }
    # )
    # print(f"Delete Conversation Response:")
    # print_response(delete_response)

    # Get user profile
    # get_user_profile()

if __name__ == "__main__":
    run_tests()


# curl -X POST https://medbot-backend.fly.dev/api/v1/auth/login \
#     -H "Content-Type: application/json" \
#     -d '{"email":"alice@demo.com","password":"Password123!"}'
# flyctl ssh console
# curl http://localhost:8001/api/v1/auth/validate \
#     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6Ik9hZkR2TXR6Uk40N1hVTEciLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL213anpxeWJkb2V4d3JmenBwZGdvLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIyZDhiMmExYS1jNmYzLTRiMDQtOWRhZi0wNTcwZTU4MzhkYzQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzQ3MDg0Nzc2LCJpYXQiOjE3NDcwODExNzYsImVtYWlsIjoiYWxpY2VAZGVtby5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsX3ZlcmlmaWVkIjp0cnVlfSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc0NzA4MTE3Nn1dLCJzZXNzaW9uX2lkIjoiZjM3ODg1NWUtOTQ2Yi00Yjc0LTlmNzktYjk0YjQ3OTgyY2Q3IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.9B150TNAdFHbn3hAm_IVzgTa-trrYPGSkWZcpBqk66c"
