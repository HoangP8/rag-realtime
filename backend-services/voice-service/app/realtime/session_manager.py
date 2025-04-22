"""
Session manager for handling multiple concurrent voice sessions
"""
import asyncio
import logging
from typing import Dict, Optional, Set, Any
from uuid import UUID

from app.models import VoiceSessionConfig
from app.realtime.voice_agent import VoiceAgent


class SessionManager:
    """
    Manages multiple concurrent voice sessions
    Handles creation, tracking, and cleanup of voice sessions
    """
    
    def __init__(self):
        """Initialize session manager"""
        self.active_sessions: Dict[str, VoiceAgent] = {}
        self.session_tasks: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger(__name__)
    
    async def create_session(
        self, 
        session_id: str, 
        user_id: UUID, 
        room_name: str,
        config: VoiceSessionConfig,
        conversation_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> VoiceAgent:
        """
        Create a new voice session
        
        Args:
            session_id: Unique session identifier
            user_id: User ID
            room_name: LiveKit room name
            config: Voice session configuration
            conversation_id: Optional conversation ID
            metadata: Optional metadata
            
        Returns:
            VoiceAgent instance
        """
        if session_id in self.active_sessions:
            self.logger.warning(f"Session {session_id} already exists, returning existing session")
            return self.active_sessions[session_id]
        
        # Create voice agent
        agent = VoiceAgent(
            session_id=session_id,
            user_id=user_id,
            room_name=room_name,
            config=config,
            conversation_id=conversation_id,
            metadata=metadata
        )
        
        # Start agent
        await agent.start()
        
        # Store in active sessions
        self.active_sessions[session_id] = agent
        
        # Create monitoring task
        self.session_tasks[session_id] = asyncio.create_task(
            self._monitor_session(session_id)
        )
        
        self.logger.info(f"Created voice session {session_id} for user {user_id}")
        return agent
    
    async def get_session(self, session_id: str) -> Optional[VoiceAgent]:
        """
        Get an active voice session
        
        Args:
            session_id: Session ID
            
        Returns:
            VoiceAgent if found, None otherwise
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
        agent = await self.get_session(session_id)
        if not agent:
            return False
        
        await agent.update_config(config)
        return True
    
    async def end_session(self, session_id: str) -> bool:
        """
        End a voice session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        agent = self.active_sessions.pop(session_id, None)
        if not agent:
            return False
        
        # Cancel monitoring task
        task = self.session_tasks.pop(session_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Stop agent
        await agent.stop()
        
        self.logger.info(f"Ended voice session {session_id}")
        return True
    
    async def _monitor_session(self, session_id: str):
        """
        Monitor a session for inactivity or errors
        
        Args:
            session_id: Session ID
        """
        try:
            agent = self.active_sessions.get(session_id)
            if not agent:
                return
            
            while True:
                # Check if session is still active
                if not await agent.is_active():
                    self.logger.info(f"Session {session_id} is no longer active, cleaning up")
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
