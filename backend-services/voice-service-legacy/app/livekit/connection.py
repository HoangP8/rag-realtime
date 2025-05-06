"""
LiveKit connection management
"""
import logging
from functools import lru_cache
from datetime import timedelta

from livekit import api
from livekit.api import CreateRoomRequest, DeleteRoomRequest

from app.livekit.config import LiveKitConfig


@lru_cache()
def get_livekit_client():
    """
    Create and return a LiveKit client
    Uses LRU cache to avoid creating multiple clients
    """
    if not LiveKitConfig.API_KEY or not LiveKitConfig.API_SECRET or not LiveKitConfig.URL:
        raise ValueError("LiveKit API key, secret, and URL must be provided")

    # Create LiveKit API client with proper authentication
    livekit_api = api.LiveKitAPI(
        url=LiveKitConfig.URL,
        api_key=LiveKitConfig.API_KEY,
        api_secret=LiveKitConfig.API_SECRET
    )

    return livekit_api.room


class LiveKitConnection:
    """LiveKit connection management"""

    def __init__(self):
        """Initialize LiveKit connection"""
        self.client = get_livekit_client()
        self.logger = logging.getLogger(__name__)

    def create_room(self, room_name: str, **kwargs) -> bool:
        """Create a LiveKit room"""
        try:
            # Merge default settings with provided kwargs
            settings = {**LiveKitConfig.DEFAULT_ROOM_SETTINGS, **kwargs}

            # Create the request object
            request = CreateRoomRequest(
                name=room_name,
                empty_timeout=settings.get("empty_timeout"),
                max_participants=settings.get("max_participants")
            )

            # Create room
            self.client.create_room(request)

            return True

        except Exception as e:
            self.logger.error(f"Error creating LiveKit room '{room_name}': {str(e)}")
            raise

    def delete_room(self, room_name: str) -> bool:
        """Delete a LiveKit room"""
        try:
            # Create the request object
            request = DeleteRoomRequest(room=room_name)

            # Delete the room
            self.client.delete_room(request)
            self.logger.info(f"Successfully deleted LiveKit room: {room_name}")

            return True

        except Exception as e:
            self.logger.error(f"Error deleting LiveKit room '{room_name}': {str(e)}")
            raise

    def generate_token(self, room_name: str, identity: str, name: str = None, **kwargs) -> str:
        """Generate a LiveKit token"""
        try:
            # Merge default settings with provided kwargs
            settings = {**LiveKitConfig.DEFAULT_TOKEN_SETTINGS, **kwargs}

            # Create an AccessToken
            token = api.AccessToken(
                api_key=LiveKitConfig.API_KEY,
                api_secret=LiveKitConfig.API_SECRET
            )

            # Create a VideoGrant
            grant = api.VideoGrants(
                room_join=True,
                room=room_name,
                # can_publish=True,
                # can_subscribe=True
            )

            # Set identity, name and add grant
            token.with_identity(identity)
            token.with_name(name or f"User {identity}")
            token.with_grants(grant)

            # Set TTL if provided
            if "ttl" in settings:
                # Convert seconds to timedelta
                ttl_seconds = settings["ttl"]
                ttl_delta = timedelta(seconds=ttl_seconds)
                token.with_ttl(ttl_delta)

            # Convert to JWT
            jwt_token = token.to_jwt()

            return jwt_token

        except Exception as e:
            self.logger.error(f"Error generating LiveKit token: {str(e)}")
            raise
