"""
Voice agent for real-time speech-to-speech communication using OpenAI Realtime API
"""
import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from typing import Dict, Optional, Any, List, Set
from uuid import UUID

from fastapi import WebSocket
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai as lk_openai
from openai import OpenAI

from app.config import settings
from app.models import VoiceSessionConfig
from app.services.llm import LLMService
from app.livekit.connection import LiveKitConnection


@dataclass
class RealtimeConfig:
    """Configuration for real-time voice processing"""
    openai_api_key: str
    instructions: str
    voice: str
    temperature: float
    max_response_output_tokens: int
    modalities: List[str]
    turn_detection: Dict[str, Any]

    def __post_init__(self):
        if self.modalities is None:
            self.modalities = self._modalities_from_string("text_and_audio")

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if k != "openai_api_key"}

    @staticmethod
    def _modalities_from_string(modalities: str) -> List[str]:
        modalities_map = {
            "text_and_audio": ["text", "audio"],
            "text_only": ["text"],
        }
        return modalities_map.get(modalities, ["text", "audio"])


class VoiceAgent:
    """
    Voice agent for real-time speech-to-speech communication
    Handles WebRTC communication with LiveKit and WebSocket connections
    Uses OpenAI Realtime API for speech-to-speech capabilities
    """

    def __init__(
        self,
        session_id: str,
        user_id: UUID,
        room_name: str,
        config: VoiceSessionConfig,
        conversation_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize voice agent

        Args:
            session_id: Unique session identifier
            user_id: User ID
            room_name: LiveKit room name
            config: Voice session configuration
            conversation_id: Optional conversation ID
            metadata: Optional metadata
        """
        self.session_id = session_id
        self.user_id = user_id
        self.room_name = room_name
        self.config = config
        self.conversation_id = conversation_id
        self.metadata = metadata or {}

        self.livekit_connection = LiveKitConnection()
        self.llm_service = LLMService()
        self.logger = logging.getLogger(__name__)

        self.room = rtc.Room()
        self.is_running = False
        self.last_activity = asyncio.get_event_loop().time()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # WebSocket connections
        self.websockets = set()
        self.is_conversation_active = False

        # OpenAI Realtime API components
        self.assistant = None
        self.model = None
        self.session = None
        self.last_transcript_id = None

    async def start(self):
        """Start the voice agent"""
        if self.is_running:
            return

        try:
            # Connect to LiveKit room
            token = self.livekit_connection.generate_token(
                room_name=self.room_name,
                identity=f"ai-{self.session_id}",
                name="AI Assistant"
            )

            # Connect to room
            await self.room.connect(settings.LIVEKIT_URL, token, auto_subscribe=AutoSubscribe.AUDIO_ONLY)

            # Set up event handlers
            self._setup_event_handlers()

            # Start real-time processing
            await self._start_realtime_processing()

            self.is_running = True
            self.last_activity = asyncio.get_event_loop().time()
            self.logger.info(f"Voice agent started for session {self.session_id}")

        except Exception as e:
            self.logger.error(f"Error starting voice agent: {str(e)}")
            await self.stop()
            raise

    async def stop(self):
        """Stop the voice agent"""
        if not self.is_running:
            return

        try:
            # Disconnect from room
            await self.room.disconnect()

            self.is_running = False
            self.logger.info(f"Voice agent stopped for session {self.session_id}")

        except Exception as e:
            self.logger.error(f"Error stopping voice agent: {str(e)}")
            raise

    async def update_config(self, config: VoiceSessionConfig):
        """
        Update agent configuration

        Args:
            config: New configuration
        """
        self.config = config
        self.last_activity = asyncio.get_event_loop().time()

        # Update real-time processing if running
        if self.is_running and self.session:
            try:
                # Create new config
                realtime_config = self._create_realtime_config()

                # Update session configuration
                self.session.session_update(
                    instructions=realtime_config.instructions,
                    voice=realtime_config.voice,
                    temperature=realtime_config.temperature,
                    max_response_output_tokens=realtime_config.max_response_output_tokens,
                    turn_detection=lk_openai.realtime.ServerVadOptions(
                        threshold=realtime_config.turn_detection.get("threshold", 0.5),
                        prefix_padding_ms=realtime_config.turn_detection.get("prefix_padding_ms", 200),
                        silence_duration_ms=realtime_config.turn_detection.get("silence_duration_ms", 300),
                    ),
                    modalities=realtime_config.modalities
                )

                self.logger.info(f"Updated real-time processing config for session {self.session_id}")
            except Exception as e:
                self.logger.error(f"Error updating real-time processing config: {str(e)}")

    async def is_active(self) -> bool:
        """
        Check if the session is still active

        Returns:
            True if active, False otherwise
        """
        # Check if room is connected
        if not self.room.connected:
            return False

        # Check for recent activity
        current_time = asyncio.get_event_loop().time()
        if current_time - self.last_activity > 300:  # 5 minutes of inactivity
            return False

        return True

    def _setup_event_handlers(self):
        """Set up event handlers for the room"""

        @self.room.on("participant_connected")
        def on_participant_connected(participant: rtc.Participant):
            self.logger.info(f"Participant connected: {participant.identity}")
            self.last_activity = asyncio.get_event_loop().time()

        @self.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.Participant):
            self.logger.info(f"Participant disconnected: {participant.identity}")

        @self.room.on("track_subscribed")
        def on_track_subscribed(track, publication, participant):
            self.logger.info(f"Track subscribed: {track.kind} from {participant.identity}")
            self.last_activity = asyncio.get_event_loop().time()

    async def _start_realtime_processing(self):
        """Start real-time processing with OpenAI Realtime API"""
        try:
            # Convert config to OpenAI realtime format
            realtime_config = self._create_realtime_config()

            # Create OpenAI Realtime model
            self.model = lk_openai.realtime.RealtimeModel(
                api_key=realtime_config.openai_api_key,
                instructions=realtime_config.instructions,
                voice=realtime_config.voice,
                temperature=realtime_config.temperature,
                max_response_output_tokens=realtime_config.max_response_output_tokens,
                modalities=realtime_config.modalities,
                turn_detection=lk_openai.realtime.ServerVadOptions(
                    threshold=realtime_config.turn_detection.get("threshold", 0.5),
                    prefix_padding_ms=realtime_config.turn_detection.get("prefix_padding_ms", 200),
                    silence_duration_ms=realtime_config.turn_detection.get("silence_duration_ms", 300),
                ),
            )

            # Create multimodal agent
            self.assistant = MultimodalAgent(model=self.model)
            self.assistant.start(self.room)

            # Get the session
            self.session = self.model.sessions[0]

            # Set up event handlers
            self._setup_realtime_event_handlers()

            # Start the conversation if modalities include text and audio
            if realtime_config.modalities == ["text", "audio"]:
                self.session.conversation.item.create(
                    lk_openai.llm.ChatMessage(
                        role="user",
                        content="Please begin the interaction with the user in a manner consistent with your instructions.",
                    )
                )
                self.session.response.create()

            self.logger.info(f"Started real-time processing for session {self.session_id}")

        except Exception as e:
            self.logger.error(f"Error starting real-time processing: {str(e)}")
            raise

    def _setup_realtime_event_handlers(self):
        """
        Set up event handlers for the OpenAI Realtime API
        Based on the example code provided
        """
        session = self.session
        self.last_transcript_id = None

        # Handle response completion
        @session.on("response_done")
        def on_response_done(response: lk_openai.realtime.RealtimeResponse):
            message = None
            if response.status == "incomplete":
                if response.status_details and response.status_details['reason']:
                    reason = response.status_details['reason']
                    if reason == "max_output_tokens":
                        message = "🚫 Max output tokens reached"
                    elif reason == "content_filter":
                        message = "🚫 Content filter applied"
                    else:
                        message = f"🚫 Response incomplete: {reason}"
                else:
                    message = "🚫 Response incomplete"
            elif response.status == "failed":
                if response.status_details and response.status_details['error']:
                    error_code = response.status_details['error']['code']
                    if error_code == "server_error":
                        message = "⚠️ Server error"
                    elif error_code == "rate_limit_exceeded":
                        message = "⚠️ Rate limit exceeded"
                    else:
                        message = "⚠️ Response failed"
                else:
                    message = "⚠️ Response failed"
            else:
                return

            # Send status message to WebSockets
            asyncio.create_task(self.broadcast_message({
                "type": "error",
                "message": message
            }))

            # Send status message to LiveKit
            local_participant = self.room.local_participant
            track_sid = next(
                (track.sid for track in local_participant.track_publications.values()
                 if track.source == rtc.TrackSource.SOURCE_MICROPHONE),
                None
            )

            if track_sid:
                asyncio.create_task(
                    self.send_transcription(
                        local_participant, track_sid, message
                    )
                )

        # Handle speech input start
        @session.on("input_speech_started")
        def on_input_speech_started():
            self.last_activity = asyncio.get_event_loop().time()

            # Send "listening" indicator
            remote_participant = next(iter(self.room.remote_participants.values()), None)
            if not remote_participant:
                return

            track_sid = next(
                (track.sid for track in remote_participant.track_publications.values()
                 if track.source == rtc.TrackSource.SOURCE_MICROPHONE),
                None
            )

            if not track_sid:
                return

            # Clear previous transcript if exists
            if self.last_transcript_id:
                asyncio.create_task(
                    self.send_transcription(
                        remote_participant, track_sid, "", is_final=True
                    )
                )

            # Send "listening" indicator
            new_id = str(uuid.uuid4())
            self.last_transcript_id = new_id
            asyncio.create_task(
                self.send_transcription(
                    remote_participant, track_sid, "…", is_final=False
                )
            )

            # Also broadcast to WebSockets
            asyncio.create_task(self.broadcast_message({
                "type": "status",
                "status": "listening",
                "message": "Listening..."
            }))

        # Handle speech transcription completion
        @session.on("input_speech_transcription_completed")
        def on_input_speech_transcription_completed(event: lk_openai.realtime.InputTranscriptionCompleted):
            self.last_activity = asyncio.get_event_loop().time()

            # Clear "listening" indicator
            if self.last_transcript_id:
                remote_participant = next(iter(self.room.remote_participants.values()), None)
                if not remote_participant:
                    return

                track_sid = next(
                    (track.sid for track in remote_participant.track_publications.values()
                     if track.source == rtc.TrackSource.SOURCE_MICROPHONE),
                    None
                )

                if track_sid:
                    asyncio.create_task(
                        self.send_transcription(
                            remote_participant, track_sid, ""
                        )
                    )

                self.last_transcript_id = None

            # Broadcast transcription to WebSockets
            if hasattr(event, 'text') and event.text:
                asyncio.create_task(self.broadcast_message({
                    "type": "transcription",
                    "text": event.text,
                    "is_final": True
                }))

        # Handle speech transcription failure
        @session.on("input_speech_transcription_failed")
        def on_input_speech_transcription_failed(event: lk_openai.realtime.InputTranscriptionFailed):
            # Clear "listening" indicator
            if self.last_transcript_id:
                remote_participant = next(iter(self.room.remote_participants.values()), None)
                if not remote_participant:
                    return

                track_sid = next(
                    (track.sid for track in remote_participant.track_publications.values()
                     if track.source == rtc.TrackSource.SOURCE_MICROPHONE),
                    None
                )

                if track_sid:
                    error_message = "⚠️ Transcription failed"
                    asyncio.create_task(
                        self.send_transcription(
                            remote_participant, track_sid, error_message
                        )
                    )

                self.last_transcript_id = None

            # Broadcast error to WebSockets
            asyncio.create_task(self.broadcast_message({
                "type": "error",
                "message": "Transcription failed"
            }))

    def _create_realtime_config(self) -> RealtimeConfig:
        """
        Create real-time configuration from session config

        Returns:
            RealtimeConfig instance
        """
        voice_settings = self.config.voice_settings or {}
        transcription_settings = self.config.transcription_settings or {}

        # Default turn detection settings
        turn_detection = {
            "threshold": 0.5,
            "prefix_padding_ms": 200,
            "silence_duration_ms": 300
        }

        # Get instructions from metadata or use default
        instructions = self.metadata.get("instructions", "You are a medical assistant. Help the user with their medical questions.")

        return RealtimeConfig(
            openai_api_key=settings.OPENAI_API_KEY,
            instructions=instructions,
            voice=voice_settings.get("voice_id", "alloy"),
            temperature=float(voice_settings.get("temperature", 0.8)),
            max_response_output_tokens=int(voice_settings.get("max_output_tokens", 2048)),
            modalities=["text", "audio"],
            turn_detection=turn_detection
        )

    async def register_websocket(self, websocket):
        """
        Register a WebSocket connection

        Args:
            websocket: WebSocket connection
        """
        self.websockets.add(websocket)
        self.last_activity = asyncio.get_event_loop().time()
        self.logger.info(f"WebSocket registered for session {self.session_id}")

    async def unregister_websocket(self, websocket):
        """
        Unregister a WebSocket connection

        Args:
            websocket: WebSocket connection
        """
        if websocket in self.websockets:
            self.websockets.remove(websocket)
            self.logger.info(f"WebSocket unregistered for session {self.session_id}")

    async def broadcast_message(self, message: Dict):
        """
        Broadcast a message to all connected WebSockets

        Args:
            message: Message to broadcast
        """
        if not self.websockets:
            return

        # Convert message to JSON
        message_json = json.dumps(message)

        # Send to all WebSockets
        for websocket in list(self.websockets):
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                self.logger.error(f"Error sending message to WebSocket: {str(e)}")
                # Remove WebSocket if it's closed
                await self.unregister_websocket(websocket)

    async def process_audio(self, audio_data: str):
        """
        Process audio data from WebSocket

        Args:
            audio_data: Base64-encoded audio data
        """
        self.last_activity = asyncio.get_event_loop().time()

        if not self.is_conversation_active or not self.session:
            await self.broadcast_message({
                "type": "error",
                "message": "Conversation is not active"
            })
            return

        try:
            # Process audio data using OpenAI Realtime API
            # The audio data is already being processed by LiveKit and OpenAI Realtime API
            # through the WebRTC connection, so we don't need to do anything here

            # Just update the last activity time
            self.last_activity = asyncio.get_event_loop().time()

            # Send acknowledgment to client
            await self.broadcast_message({
                "type": "status",
                "status": "processing",
                "message": "Processing audio..."
            })

        except Exception as e:
            self.logger.error(f"Error processing audio: {str(e)}")
            await self.broadcast_message({
                "type": "error",
                "message": f"Error processing audio: {str(e)}"
            })

    async def process_text(self, text: str):
        """
        Process text message from WebSocket

        Args:
            text: Text message
        """
        self.last_activity = asyncio.get_event_loop().time()

        if not self.is_conversation_active or not self.session:
            await self.broadcast_message({
                "type": "error",
                "message": "Conversation is not active"
            })
            return

        try:
            # Process text message using OpenAI Realtime API
            # Create a chat message in the conversation
            self.session.conversation.item.create(
                lk_openai.llm.ChatMessage(
                    role="user",
                    content=text
                )
            )

            # Generate a response
            self.session.response.create()

            # The response will be handled by the event handlers
            # set up in _setup_realtime_event_handlers

            # Send acknowledgment to client
            await self.broadcast_message({
                "type": "status",
                "status": "processing",
                "message": "Processing message..."
            })

        except Exception as e:
            self.logger.error(f"Error processing text: {str(e)}")
            await self.broadcast_message({
                "type": "error",
                "message": f"Error processing text: {str(e)}"
            })

    async def start_conversation(self):
        """
        Start a conversation
        """
        self.is_conversation_active = True
        self.last_activity = asyncio.get_event_loop().time()

        # If we have a session, start the conversation
        if self.session:
            try:
                # Create a welcome message
                self.session.conversation.item.create(
                    lk_openai.llm.ChatMessage(
                        role="user",
                        content="Please begin the interaction with the user in a manner consistent with your instructions."
                    )
                )

                # Generate a response
                self.session.response.create()
            except Exception as e:
                self.logger.error(f"Error starting conversation: {str(e)}")

        await self.broadcast_message({
            "type": "status",
            "status": "started",
            "message": "Conversation started"
        })

    async def stop_conversation(self):
        """
        Stop a conversation
        """
        self.is_conversation_active = False

        # If we have a session, stop any ongoing responses
        if self.session and self.session.response.active:
            try:
                # Stop the response
                self.session.response.stop()
            except Exception as e:
                self.logger.error(f"Error stopping conversation: {str(e)}")

        await self.broadcast_message({
            "type": "status",
            "status": "stopped",
            "message": "Conversation stopped"
        })

    async def pause_conversation(self):
        """
        Pause a conversation
        """
        self.is_conversation_active = False

        # If we have a session, pause any ongoing responses
        if self.session and self.session.response.active:
            try:
                # Stop the response
                self.session.response.stop()
            except Exception as e:
                self.logger.error(f"Error pausing conversation: {str(e)}")

        await self.broadcast_message({
            "type": "status",
            "status": "paused",
            "message": "Conversation paused"
        })

    async def resume_conversation(self):
        """
        Resume a conversation
        """
        self.is_conversation_active = True
        self.last_activity = asyncio.get_event_loop().time()

        # If we have a session, resume the conversation
        if self.session:
            try:
                # Create a resume message
                self.session.conversation.item.create(
                    lk_openai.llm.ChatMessage(
                        role="user",
                        content="The conversation is resuming. Please continue where we left off."
                    )
                )

                # Generate a response
                self.session.response.create()
            except Exception as e:
                self.logger.error(f"Error resuming conversation: {str(e)}")

        await self.broadcast_message({
            "type": "status",
            "status": "resumed",
            "message": "Conversation resumed"
        })

    async def send_transcription(self, participant: rtc.Participant, track_sid: str, text: str, is_final: bool = True):
        """
        Send transcription to the room

        Args:
            participant: Participant
            track_sid: Track SID
            text: Transcription text
            is_final: Whether this is a final transcription
        """
        segment_id = str(uuid.uuid4())

        transcription = rtc.Transcription(
            participant_identity=participant.identity,
            track_sid=track_sid,
            segments=[
                rtc.TranscriptionSegment(
                    id=segment_id,
                    text=text,
                    start_time=0,
                    end_time=0,
                    language="en",
                    final=is_final
                )
            ]
        )

        await self.room.local_participant.publish_transcription(transcription)

        # Also broadcast to WebSockets
        await self.broadcast_message({
            "type": "transcription",
            "text": text,
            "is_final": is_final
        })
