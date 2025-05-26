"""
AGENT PIPELINE:

====== INITIALIZATION PHASE ======
1. Load environment variables and setup logging
2. Connect to LiveKit room (LATENCY: ~connection time)
3. Load FAISS vectorstore for RAG (LATENCY: ~vector store loading time)
4. Initialize OpenAI Realtime model with function calling
5. Setup event listeners for speech detection

====== REAL-TIME CONVERSATION LOOP ======
User Speech Input:
├── [EVENT] user_started_speaking
│   └── Reset timing variables
│
├── [EVENT] user_stopped_speaking  
│   └── Mark timestamp: user_stopped_speaking_time
│
├── [EVENT] user_speech_committed (transcription ready)
│   ├── Mark timestamp: user_speech_committed_time
│   ├── LATENCY MEASURED: Speech-to-text transcription time
│   └── LLM processes and decides if function calling needed
│
├── LLM Processing:
│   ├── If medical query detected → calls rag_medical_search()
│   ├── Function executes RAG search (LATENCY: ~RAG search time)
│   ├── LLM receives results and generates response
│   └── LATENCY MEASURED: Total processing time
│
└── Agent Response:
    ├── [EVENT] agent_started_speaking
    │   ├── LATENCY MEASURED: Total response latency
    │   └── LATENCY MEASURED: Processing latency
    │
    └── [EVENT] agent_speech_committed
        └── Log final assistant response
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Annotated, Any, Optional
import uuid
from uuid import UUID

import langid
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.multimodal import AgentTranscriptionOptions, MultimodalAgent
from livekit.plugins import openai

from app.services.storage import StorageService

# Basic setup
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

# Logging setup
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)
log_dir = Path(__file__).parent / "logs" / "talk_logs"
log_dir.mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(log_dir / "medical_assistant.log", encoding="utf-8")
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def log_event(event_type: str, content: Any):
    """Logs events with structured content."""
    if isinstance(content, (dict, list)):
        logger.info(f"{event_type}: {json.dumps(content, ensure_ascii=False, default=str)}")
    else:
        logger.info(f"{event_type}: {content}")


def log_timing(operation: str, duration: float):
    """Logs timing information for operations."""
    logger.info(f"TIMING | {operation}: {duration:.3f}s")


def load_vectorstore(model_name: str, chunk_size: int = 1024) -> tuple[FAISS, OpenAIEmbeddings]:
    """Loads a FAISS vector store from disk."""
    start_time = time.time()
    backend_dir = Path(__file__).parent.absolute()
    model_folder = os.path.join(backend_dir, "faiss", f"{model_name}", f"chunk_size_{chunk_size}")

    logger.info(f"Loading vectorstore from: {model_folder}")
    embeddings = OpenAIEmbeddings(model=model_name)
    vectorstore = FAISS.load_local(model_folder, embeddings, allow_dangerous_deserialization=True)
    log_timing("Vector store loading", time.time() - start_time)
    return vectorstore, embeddings


class MedicalFunctionContext(llm.FunctionContext):
    """Function context for RAG capabilities following LiveKit best practices."""

    def __init__(self, vectorstore: FAISS):
        super().__init__()
        self.vectorstore = vectorstore
        self.current_language = "vi"  # Default to Vietnamese

    @llm.ai_callable()
    async def detect_user_language(
        self,
        text: Annotated[str, llm.TypeInfo(description="User's text to analyze for language detection")],
    ) -> str:
        """
        Detect user language and set it for the session.
        """
        lang, confidence = langid.classify(text)
        
        # Check for Vietnamese characters
        has_vietnamese = any(char in text.lower() for char in 'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ')
        
        if has_vietnamese or (lang == "vi" and confidence > 0.5):
            self.current_language = "vi"
        else:
            self.current_language = "en"
            
        log_event("Language Detection", f"Detected: {self.current_language}")
        return self.current_language

    @llm.ai_callable()
    async def rag_medical_search(
        self,
        query: Annotated[str, llm.TypeInfo(description="Medical question to search for in the knowledge base")],
        num_results: Annotated[int, llm.TypeInfo(description="Number of documents to retrieve")] = 3,
    ) -> str:
        """
        Search medical knowledge base for relevant information.
        """
        search_start = time.time()
        
        # Perform similarity search
        filtered_docs = self.vectorstore.similarity_search_with_relevance_scores(
            query, k=num_results, score_threshold=0.35
        )

        if not filtered_docs:
            log_timing("RAG search (no results)", time.time() - search_start)
            log_event("RAG", "No documents found")
            return ""
        
        log_timing("RAG search", time.time() - search_start)
        log_event("RAG", f"Found {len(filtered_docs)} documents for: {query}")

        # Format results
        results = []
        for i, (doc, score) in enumerate(filtered_docs):
            results.append(f"Medical Information {i+1}:\n{doc.page_content.strip()}")

        # Add language-specific instructions
        instruction = (
            "\n\nHướng dẫn: Đây là thông tin từ cơ sở dữ liệu y tế Việt Nam. "
            "Hãy sử dụng thông tin này để trả lời câu hỏi của người dùng một cách ngắn gọn bằng tiếng Việt."
            if self.current_language == "vi"
            else "\n\nInstructions: This is information from the Vietnamese medical database. "
            "Please translate this information and answer the user's question concisely in English."
        )
        
        return "\n\n".join(results) + instruction


class MedicalMultimodalAgent(MultimodalAgent):
    """Customized MultimodalAgent with RAG."""

    # Static instructions - no need to constantly update
    INSTRUCTIONS = """You are a HEALTHCARE ASSISTANT.
    
    PURPOSE: 
        1. Provide medical and healthcare information.
        2. For NON-medical topics: Politely refuse and redirect to health topics
    
    IMPORTANT RULES:
        1. For ANY medical/health question, you MUST call rag_medical_search() function.
        2. Follow EXACTLY the RAG information provided below if it DIRECTLY answers the user's question.  If not, rely on your general knowledge instead.
    
    LANGUAGE AND STYLE:
        1. Call detect_user_language() to identify user's language if you're unsure
        2. ONLY Vietnamese and English
        3. Respond in Vietnamese if user speaks Vietnamese.
        4. Respond in English if user speaks English.
        5. Style: Concise, clear, easy to understand
    
    """

    def __init__(
        self,
        *,
        model: openai.realtime.RealtimeModel,
        vectorstore: FAISS,
        vad: Optional[Any] = None,
        transcription: AgentTranscriptionOptions = AgentTranscriptionOptions(),
        loop: Optional[asyncio.AbstractEventLoop] = None,
        chat_ctx: Optional[llm.ChatContext] = None,
    ):
        # Initialize RAG function context
        self.med_fnc_ctx = MedicalFunctionContext(vectorstore=vectorstore)

        super().__init__(
            model=model,
            vad=vad,
            chat_ctx=chat_ctx,
            fnc_ctx=self.med_fnc_ctx,
            transcription=transcription,
            loop=loop,
        )

        # State tracking
        self.query_count = 0
        
    def start(self, room: rtc.Room, participant: rtc.RemoteParticipant | str | None = None):
        """Start the agent with event listeners."""
        self.setup_event_listeners()
        super().start(room, participant)

    def setup_event_listeners(self):
        """Configures speech event handlers."""
        # Timing tracking variables
        self.user_stopped_speaking_time = None  # When user finished talking
        self.user_speech_committed_time = None  # When transcription is ready
        
        @self.on("user_started_speaking")
        def on_user_started_speaking():
            # Reset timing variables for new query
            self.user_stopped_speaking_time = None
            self.user_speech_committed_time = None
        
        @self.on("user_stopped_speaking")
        def on_user_stopped_speaking():
            # User finished talking - mark this time
            self.user_stopped_speaking_time = time.time()
        
        @self.on("user_speech_committed")
        def on_user_speech_committed(message):
            self.query_count += 1
            logger.info(f"----- Query {self.query_count} -----")
            
            # Mark when transcription is ready
            self.user_speech_committed_time = time.time()
            
            # Speech to text transcription time: from when user stopped talking to when transcription is ready
            if self.user_stopped_speaking_time:
                transcription_time = self.user_speech_committed_time - self.user_stopped_speaking_time
                log_timing("User speech to text transcription", transcription_time)
            
            log_event("USER TRANSCRIPT", f"{message}")
        
        @self.on("agent_started_speaking")
        def on_agent_started_speaking():
            # Total response latency (from when user stopped talking to when agent starts speaking)
            if self.user_stopped_speaking_time:
                response_latency = time.time() - self.user_stopped_speaking_time
                log_timing("Total response latency", response_latency)
                
                # Processing latency: from transcription ready to agent starts speaking
                if self.user_speech_committed_time:
                    processing_latency = time.time() - self.user_speech_committed_time
                    log_timing("Processing latency (post-transcription)", processing_latency)
        
        @self.on("agent_speech_committed")
        def on_agent_speech_committed(response):
            log_event("ASSISTANT RESPONSE", f"{response}\n\n")    


def get_user_active_chat_history(auth_token: str, user_id: str = "user_test_123", conversation_id: str = "conversation_test_123") -> Optional[llm.ChatContext]:
    """Initializes chat history for user."""
    storage_service = StorageService()

    messages = storage_service.get_conversation_history(user_id, conversation_id, auth_token)
    messages = [llm.ChatMessage(role=item.role, content=item.content) for item in messages]

    if user_id == "user_test_123" or not messages: # Get dummy history 
        # Pre-create messages to avoid repeated object creation
        # dummy_history = [
        #     {"role": "user", "content": "Tôi tên là Hoàng, hãy gọi tên tôi mỗi khi bạn nói chuyện với tôi."},
        #     {"role": "user", "content": "Dạo này tôi bị đau đầu và căng thẳng trong công việc. Tôi cần được hỗ trợ về sức khỏe và tâm lý."}, 
        # ]
        dummy_history = [
            {"role": "user", "content": "Tôi tên là Hoàng, hãy bắt đầu gợi ý các câu hỏi về sức khỏe và tâm lý của tôi."},
        ]
        messages = [llm.ChatMessage(role=item["role"], content=item["content"]) for item in dummy_history]
    
    return llm.ChatContext(messages=messages)


async def entrypoint(ctx: JobContext):
    """Main entry point for the medical assistant."""
    
    # Initialize connection
    start_time = time.time()
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    log_timing("LiveKit connection", time.time() - start_time)

    # Extract metadata from the room
    metadata_str = ctx.room.metadata
    try:
        metadata = json.loads(metadata_str)
    except json.JSONDecodeError:
        metadata = {}
    
    # Extract session information
    session_id = metadata.get("session_id")
    user_id_str = metadata.get("user_id")
    conversation_id_str = metadata.get("conversation_id")
    voice_settings = metadata.get("voice_settings", {})
    agent_metadata = metadata.get("metadata", {})

    # Get auth token from metadata if available
    auth_token = agent_metadata.get("auth_token")

    # Convert IDs to proper types
    user_id = UUID(user_id_str)
    conversation_id = UUID(conversation_id_str) if conversation_id_str else None

    # Load vectorstore
    vectorstore, _ = load_vectorstore("text-embedding-3-small", 1024)

    # Initialize voice model with optimized settings
    model = openai.realtime.RealtimeModel(
        model="gpt-4o-realtime-preview",
        modalities=["text", "audio"],
        voice="coral",
        instructions=MedicalMultimodalAgent.INSTRUCTIONS,
        turn_detection=openai.realtime.ServerVadOptions(
            threshold=0.5, 
            prefix_padding_ms=200,  
            silence_duration_ms=1000, 
            create_response=True
        ),
        input_audio_transcription=openai.realtime.InputTranscriptionOptions(
            model="gpt-4o-transcribe",
        )
    )
    
    # Load initial chat context
    chat_ctx = get_user_active_chat_history(auth_token, user_id, conversation_id)

    # Initialize the assistant
    assistant = MedicalMultimodalAgent(model=model, chat_ctx=chat_ctx, vectorstore=vectorstore)
    assistant.start(ctx.room, participant)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))