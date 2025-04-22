#!/usr/bin/env python3
"""
WebSocket client for testing voice mode
"""
import asyncio
import json
import sys
import argparse
import logging
from typing import Optional

import websockets


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


async def send_message(websocket, message_type: str, **kwargs):
    """Send a message to the WebSocket server"""
    message = {"type": message_type, **kwargs}
    message_json = json.dumps(message)
    logger.info(f"Sending: {message_json}")
    await websocket.send(message_json)


async def test_voice_websocket(session_id: str, server_url: str):
    """Test voice WebSocket connection"""
    ws_url = f"{server_url}/api/v1/realtime/ws/{session_id}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            logger.info(f"Connected to {ws_url}")
            
            # Start conversation
            await send_message(websocket, "control", action="start")
            
            # Wait for response
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
            # Send a text message
            await send_message(websocket, "text", text="Hello, I have a question about my medication.")
            
            # Wait for response
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
            # Interactive mode
            print("\n--- Interactive Mode ---")
            print("Type your messages. Type 'exit' to quit.")
            
            while True:
                user_input = input("> ")
                
                if user_input.lower() == "exit":
                    break
                
                # Send user input as text
                await send_message(websocket, "text", text=user_input)
                
                # Wait for response
                response = await websocket.recv()
                logger.info(f"Received: {response}")
                
                # Parse response
                try:
                    response_data = json.loads(response)
                    if response_data.get("type") == "response":
                        print(f"AI: {response_data.get('text', 'No response text')}")
                    elif response_data.get("type") == "error":
                        print(f"Error: {response_data.get('message', 'Unknown error')}")
                except json.JSONDecodeError:
                    print(f"Received non-JSON response: {response}")
            
            # Stop conversation
            await send_message(websocket, "control", action="stop")
            
            # Wait for response
            response = await websocket.recv()
            logger.info(f"Received: {response}")
            
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"WebSocket connection closed: {e}")
    except Exception as e:
        logger.error(f"Error: {str(e)}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test voice WebSocket connection")
    parser.add_argument("session_id", help="Voice session ID")
    parser.add_argument("--url", default="ws://localhost:8000", help="WebSocket server URL")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(test_voice_websocket(args.session_id, args.url))
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
