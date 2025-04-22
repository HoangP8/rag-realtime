#!/usr/bin/env python3
"""
Test LiveKit connection for voice mode
"""
import asyncio
import argparse
import logging
import sys
from typing import Optional

from livekit import rtc
from livekit.agents import AutoSubscribe


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


async def test_livekit_connection(token: str, url: str):
    """Test LiveKit connection"""
    logger.info(f"Connecting to LiveKit server at {url}")
    
    # Create room
    room = rtc.Room()
    
    try:
        # Connect to room
        await room.connect(url, token, auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        logger.info(f"Connected to room: {room.name}")
        
        # Log local participant info
        local_participant = room.local_participant
        logger.info(f"Local participant: {local_participant.identity} ({local_participant.sid})")
        
        # Log remote participants
        logger.info(f"Remote participants: {len(room.remote_participants)}")
        for participant in room.remote_participants.values():
            logger.info(f"- {participant.identity} ({participant.sid})")
        
        # Set up event handlers
        @room.on("participant_connected")
        def on_participant_connected(participant: rtc.Participant):
            logger.info(f"Participant connected: {participant.identity}")
        
        @room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.Participant):
            logger.info(f"Participant disconnected: {participant.identity}")
        
        @room.on("track_subscribed")
        def on_track_subscribed(track, publication, participant):
            logger.info(f"Track subscribed: {track.kind} from {participant.identity}")
        
        @room.on("track_unsubscribed")
        def on_track_unsubscribed(track, publication, participant):
            logger.info(f"Track unsubscribed: {track.kind} from {participant.identity}")
        
        @room.on("data_received")
        def on_data_received(data, participant):
            logger.info(f"Data received from {participant.identity}: {data.decode()}")
        
        # Wait for user to press Ctrl+C
        logger.info("Connected to LiveKit. Press Ctrl+C to disconnect.")
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    
    finally:
        # Disconnect from room
        if room.connected:
            await room.disconnect()
            logger.info("Disconnected from room")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test LiveKit connection")
    parser.add_argument("token", help="LiveKit token")
    parser.add_argument("--url", default="wss://your-livekit-server", help="LiveKit server URL")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(test_livekit_connection(args.token, args.url))
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
