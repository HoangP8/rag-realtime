"""
Session manager for handling multiple concurrent voice sessions
"""
import asyncio
import json
import logging
from typing import Dict, Optional, Set, Any
from uuid import UUID

import httpx
from livekit import api

from app.config import settings
from app.models import VoiceSessionConfig
from app.livekit.connection import LiveKitConnection


class SessionManager:
    """
    Manages multiple concurrent voice sessions
    Handles creation, tracking, and cleanup of voice sessions
    """

    def __init__(self):
        """Initialize session manager"""
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_tasks: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger(__name__)
        self.livekit_connection = LiveKitConnection()

    async def create_session(
        self,
        session_id: str,
        user_id: UUID,
        room_name: str,
        token: str,
        config: VoiceSessionConfig,
        conversation_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new voice session

        Args:
            session_id: Unique session identifier
            user_id: User ID
            room_name: LiveKit room name
            token: Token for the AI assistant identity
            config: Voice session configuration
            conversation_id: Optional conversation ID
            metadata: Optional metadata

        Returns:
            Session information dictionary
        """
        if session_id in self.active_sessions:
            self.logger.warning(f"Session {session_id} already exists, returning existing session")
            return self.active_sessions[session_id]

        try:
            # Prepare room metadata for the agent worker
            room_metadata = {
                "session_id": session_id,
                "user_id": str(user_id),
                "conversation_id": str(conversation_id) if conversation_id else None,
                "config": config.model_dump() if config else {},
                "metadata": metadata or {}
            }

            # Create a LiveKit API client
            livekit_api = api.LiveKitAPI(
                url=settings.LIVEKIT_URL,
                api_key=settings.LIVEKIT_API_KEY,
                api_secret=settings.LIVEKIT_API_SECRET
            )

            # Update room metadata to include our session information
            await livekit_api.room.update_room_metadata(
                room_name=room_name,
                metadata=json.dumps(room_metadata)
            )

            # Create a session info dictionary
            session_info = {
                "id": session_id,
                "user_id": str(user_id),
                "room_name": room_name,
                "conversation_id": str(conversation_id) if conversation_id else None,
                "status": "created",
                "metadata": metadata or {}
            }

            # Store in active sessions
            self.active_sessions[session_id] = session_info

            # Create monitoring task
            self.session_tasks[session_id] = asyncio.create_task(
                self._monitor_session(session_id)
            )

            self.logger.info(f"Created voice session {session_id} for user {user_id}")
            return session_info

        except Exception as e:
            self.logger.error(f"Error creating voice session: {str(e)}")
            raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an active voice session

        Args:
            session_id: Session ID

        Returns:
            Session information dictionary if found, None otherwise
        """
        return self.active_sessions.get(session_id)

    async def update_session_config(
        self, session_id: str, config: VoiceSessionConfig
    ) -> bool:
        """
        Update session configuration

        Args:
            session_id: Session ID
            config: New configuration

        Returns:
            True if successful, False otherwise
        """
        session_info = await self.get_session(session_id)
        if not session_info:
            return False

        try:
            # Get room name from session info
            room_name = session_info.get("room_name")
            if not room_name:
                return False

            # Create a LiveKit API client
            livekit_api = api.LiveKitAPI(
                url=settings.LIVEKIT_URL,
                api_key=settings.LIVEKIT_API_KEY,
                api_secret=settings.LIVEKIT_API_SECRET
            )

            # Get current room metadata
            room_info = await livekit_api.room.get_room(room_name)
            if not room_info or not room_info.metadata:
                return False

            # Parse current metadata
            try:
                room_metadata = json.loads(room_info.metadata)
            except json.JSONDecodeError:
                room_metadata = {}

            # Update config in metadata
            room_metadata["config"] = config.model_dump() if config else {}

            # Update room metadata
            await livekit_api.room.update_room_metadata(
                room_name=room_name,
                metadata=json.dumps(room_metadata)
            )

            # Update session info
            session_info["config"] = config.model_dump() if config else {}

            self.logger.info(f"Updated session {session_id} configuration")
            return True

        except Exception as e:
            self.logger.error(f"Error updating session configuration: {str(e)}")
            return False

    async def end_session(self, session_id: str) -> bool:
        """
        End a voice session

        Args:
            session_id: Session ID

        Returns:
            True if successful, False otherwise
        """
        session_info = self.active_sessions.pop(session_id, None)
        if not session_info:
            return False

        try:
            # Cancel monitoring task
            task = self.session_tasks.pop(session_id, None)
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Get room name from session info
            room_name = session_info.get("room_name")
            if room_name:
                # Delete the LiveKit room
                try:
                    await self.livekit_connection.delete_room(room_name)
                except Exception as e:
                    self.logger.warning(f"Error deleting LiveKit room: {str(e)}")

            self.logger.info(f"Ended voice session {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error ending session: {str(e)}")
            return False

    async def _monitor_session(self, session_id: str):
        """
        Monitor a session for inactivity or errors

        Args:
            session_id: Session ID
        """
        try:
            session_info = self.active_sessions.get(session_id)
            if not session_info:
                return

            room_name = session_info.get("room_name")
            if not room_name:
                return

            # Create a LiveKit API client
            livekit_api = api.LiveKitAPI(
                url=settings.LIVEKIT_URL,
                api_key=settings.LIVEKIT_API_KEY,
                api_secret=settings.LIVEKIT_API_SECRET
            )

            while True:
                try:
                    # Check if room still exists and has participants
                    room_info = await livekit_api.room.get_room(room_name)

                    # If room doesn't exist or has no participants for a while, end the session
                    if not room_info or (room_info.num_participants == 0 and room_info.empty_timeout > 0):
                        self.logger.info(f"Session {session_id} is no longer active, cleaning up")
                        await self.end_session(session_id)
                        break

                except Exception as e:
                    self.logger.warning(f"Error checking room status: {str(e)}")
                    # If we can't get room info, assume it's gone
                    await self.end_session(session_id)
                    break

                # Wait before checking again
                await asyncio.sleep(30)  # Check every 30 seconds

        except asyncio.CancelledError:
            # Task was cancelled, clean up
            self.logger.info(f"Session monitoring for {session_id} cancelled")
            raise

        except Exception as e:
            self.logger.error(f"Error monitoring session {session_id}: {str(e)}")
            # Try to clean up
            await self.end_session(session_id)

    async def shutdown(self):
        """Shutdown all active sessions"""
        session_ids = list(self.active_sessions.keys())
        for session_id in session_ids:
            await self.end_session(session_id)

        self.logger.info("All voice sessions shut down")
