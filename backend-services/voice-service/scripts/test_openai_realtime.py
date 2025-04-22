#!/usr/bin/env python3
"""
Test script for OpenAI Realtime API integration
"""
import argparse
import asyncio
import base64
import json
import os
import sys
import time
import uuid
from pathlib import Path

import httpx
import websockets

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


async def create_session(api_url, auth_token=None):
    """Create a voice session"""
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{api_url}/api/v1/voice/session/create",
            json={
                "metadata": {
                    "instructions": "You are a helpful medical assistant. Answer the user's questions about health and medical topics."
                }
            },
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Error creating session: {response.text}")
            return None
        
        return response.json()


async def delete_session(api_url, session_id, auth_token=None):
    """Delete a voice session"""
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{api_url}/api/v1/voice/session/{session_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Error deleting session: {response.text}")
            return False
        
        return True


async def test_websocket(api_url, session_id):
    """Test WebSocket communication"""
    ws_url = f"{api_url.replace('http://', 'ws://').replace('https://', 'wss://')}/api/v1/realtime/ws/{session_id}"
    
    print(f"Connecting to WebSocket: {ws_url}")
    
    async with websockets.connect(ws_url) as websocket:
        print("Connected to WebSocket")
        
        # Start conversation
        await websocket.send(json.dumps({
            "type": "control",
            "action": "start"
        }))
        
        print("Sent start command")
        
        # Wait for response
        response = await websocket.recv()
        print(f"Received: {response}")
        
        # Send a text message
        await websocket.send(json.dumps({
            "type": "text",
            "text": "Hello, how can you help me with medical questions?"
        }))
        
        print("Sent text message")
        
        # Wait for responses
        for _ in range(5):  # Wait for up to 5 messages
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                print(f"Received: {response}")
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                break
        
        # Interactive mode
        print("\nEntering interactive mode. Type 'exit' to quit.")
        while True:
            user_input = input("> ")
            if user_input.lower() == "exit":
                break
            
            # Send text message
            await websocket.send(json.dumps({
                "type": "text",
                "text": user_input
            }))
            
            # Wait for responses
            for _ in range(5):  # Wait for up to 5 messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    print(f"Received: {response}")
                except asyncio.TimeoutError:
                    break
        
        # Stop conversation
        await websocket.send(json.dumps({
            "type": "control",
            "action": "stop"
        }))
        
        print("Sent stop command")
        
        # Wait for response
        response = await websocket.recv()
        print(f"Received: {response}")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test OpenAI Realtime API integration")
    parser.add_argument("--url", default="http://localhost:8003", help="API URL")
    parser.add_argument("--token", help="Authentication token")
    parser.add_argument("--session-id", help="Existing session ID (skip creation)")
    parser.add_argument("--keep", action="store_true", help="Keep session after test")
    args = parser.parse_args()
    
    session_id = args.session_id
    session_created = False
    
    try:
        if not session_id:
            print("Creating voice session...")
            session = await create_session(args.url, args.token)
            if not session:
                print("Failed to create session")
                return
            
            session_id = session["id"]
            session_created = True
            print(f"Created session: {session_id}")
            print(f"Token: {session['token']}")
            
            # Wait for session to initialize
            print("Waiting for session to initialize...")
            time.sleep(2)
        
        print(f"Testing WebSocket communication for session {session_id}...")
        await test_websocket(args.url, session_id)
    
    finally:
        if session_created and not args.keep:
            print(f"Deleting session {session_id}...")
            await delete_session(args.url, session_id, args.token)
            print("Session deleted")


if __name__ == "__main__":
    asyncio.run(main())
