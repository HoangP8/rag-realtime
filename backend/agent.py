"""
AGENT PIPELINE FLOW

=== INITIALIZATION PHASE ===
1. Load environment variables and setup logging
2. Connect to LiveKit room (LATENCY: ~connection time)
3. Load FAISS vectorstore for RAG (LATENCY: ~vector store loading time)
4. Initialize OpenAI Realtime model with Vietnamese default
5. Setup event listeners for speech detection

=== REAL-TIME CONVERSATION LOOP ===

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
│   └── Trigger: add_rag_to_query(message) [ASYNC]
│
└── add_rag_to_query() Processing:
    ├── Language detection (LATENCY: ~language detection time)
    ├── Session language update if changed (LATENCY: ~session update time)  
    ├── RAG search in vectorstore (LATENCY: ~RAG search time)
    ├── Update session instructions with RAG context
    ├── Call generate_reply() to trigger LLM response
    └── LATENCY MEASURED: Total RAG query processing time

Agent Response:
├── [EVENT] agent_started_speaking
│   ├── LATENCY MEASURED: Total response latency (user_stopped → agent_started)
│   └── LATENCY MEASURED: Processing latency (transcription_ready → agent_started)
│
└── [EVENT] agent_speech_committed
    └── Log final assistant response

=== KEY LATENCY MEASUREMENTS ===
- Speech-to-text: User stops talking → Transcription ready
- RAG processing: Message received → Response generation triggered  
- Total response: User stops talking → Agent starts speaking
- Processing: Transcription ready → Agent starts speaking
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Annotated, Any, Optional

import langid
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.multimodal import AgentTranscriptionOptions, MultimodalAgent
from livekit.plugins import openai

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
    """Function context for RAG capabilities."""

    def __init__(self, vectorstore: FAISS):
        super().__init__()
        self.vectorstore = vectorstore

    @llm.ai_callable()
    async def rag_search(
        self,
        query: Annotated[str, llm.TypeInfo(description="Query to search within the documents")],
        language: Annotated[str, llm.TypeInfo(description="Language of the query (en or vi)")] = "vi",
        k: Annotated[int, llm.TypeInfo(description="Number of relevant documents to retrieve")] = 1,
        score_threshold: Annotated[
            float, llm.TypeInfo(description="Minimum relevance score threshold")
        ] = 0.35,
    ) -> str:
        """RAG search for medical information."""
        search_start = time.time()

        # Get relevant documents
        filtered_docs = self.vectorstore.similarity_search_with_relevance_scores(
            query, k=k, score_threshold=score_threshold
        )

        # Early return if no results
        if not filtered_docs:
            log_timing("RAG search (no results)", time.time() - search_start)
            log_event("RAG RELEVANT DOCUMENTS", f"No documents found")
            return ""
        
        log_timing("RAG search", time.time() - search_start)
        log_event("RAG", f"Found {len(filtered_docs)} documents")

        # Prepare response (optimized string building)
        response_parts = [f"RAG Information {i+1}:\n{doc.page_content.strip()}" 
                         for i, (doc, score) in enumerate(filtered_docs)]

        # Pre-defined instructions to avoid repeated string operations
        instructions = (
            "\n\nHướng dẫn: Đây là thông tin từ cơ sở dữ liệu y tế Việt Nam. "
            "Hãy sử dụng thông tin này để trả lời câu hỏi của người dùng một cách ngắn gọn bằng tiếng Việt."
            if language == "vi"
            else "\n\nInstructions: This is information from the Vietnamese medical database. "
            "Please translate this information and answer the user's question concisely in English."
        )

        response = "\n\n".join(response_parts) + instructions
        return response


class MedicalMultimodalAgent(MultimodalAgent):
    """Custom MultimodalAgent with RAG capabilities and chat history."""

    instruction_format = """You are a HEALTHCARE ASSISTANT.
        Your ONLY purpose is to provide healthcare and medical information. For ANY other topics, politely refuse.
        Languages: Vietnamese and English only. Ignore other languages.
        Style: Be concise, clear, and avoid repetition.
        
        IMPORTANT RULES:
        1. Respond in Vietnamese if user speaks Vietnamese.
        2. Respond in English if user speaks English.
        3. Follow EXACTLY the RAG information provided below if it DIRECTLY answers the user's question. 
        If not, rely on your general knowledge instead.

    RAG CONTEXT (ONLY USE IF DIRECTLY RELEVANT): {RAG_context}
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

        # State tracking with optimizations
        self.current_language = "vi"
        self.query_count = 0
        
        # Cache for language detection to reduce overhead
        self._lang_cache = {}
        self._cache_max_size = 100

    def start(self, room: rtc.Room, participant: rtc.RemoteParticipant | str | None = None):
        """Start the agent with timing logs."""
        self.setup_event_listeners()
        super().start(room, participant)

    async def add_rag_to_query(self, msg: str | None):
        """Detects language, performs RAG search, and updates instructions."""
        
        if not msg or not msg.strip():
            return

        total_start = time.time()

        # Detect language with caching and cooldown
        lang_start = time.time()
        detected_lang = self.detect_language(msg)
        log_timing("Language detection", time.time() - lang_start)

        # Only update session if language changed
        if detected_lang != self.current_language:
            session_start = time.time()
            self.current_language = detected_lang
            self._session.session_update(
                input_audio_transcription=openai.realtime.InputTranscriptionOptions(
                    model="gpt-4o-transcribe",
                    language=self.current_language,
                )
            )
            log_timing("Session language update", time.time() - session_start)

        # Get RAG results
        rag_start = time.time()
        result = await self.med_fnc_ctx.rag_search(query=msg, language=self.current_language)
        log_timing("RAG search total", time.time() - rag_start)
        
        # Update instructions with RAG context
        new_instruction = self.instruction_format.format(RAG_context=result)
        self._session.session_update(instructions=new_instruction)
        
        # Generate reply
        self.generate_reply()
        
        # Measure total time from  the transcribed message is received until the response generation is initiated
        log_timing("Total RAG query processing", time.time() - total_start)

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
            
            # Use asyncio.create_task for non-blocking execution
            asyncio.create_task(self.add_rag_to_query(message))
        
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

    def detect_language(self, text: str) -> str:
        """Optimized language detection with caching and cooldown."""
        
        text_hash = hash(text[:30])  # Use first 30 chars for cache key
        if text_hash in self._lang_cache:
            return self._lang_cache[text_hash]
        
        # Perform detection
        lang, confidence = langid.classify(text)
        detected_lang = "vi" if lang == "vi" else "en"
        
        # Cache management
        if len(self._lang_cache) >= self._cache_max_size:
            # Remove oldest entries
            oldest_key = next(iter(self._lang_cache))
            del self._lang_cache[oldest_key]
        
        self._lang_cache[text_hash] = detected_lang
        return detected_lang


def get_user_active_chat_history(user_id: str = "user_test_123") -> Optional[llm.ChatContext]:
    """Initializes dummy chat history for testing."""
    if user_id != "user_test_123":
        return None

    # Pre-create messages to avoid repeated object creation
    dummy_history = [
        {"role": "user", "content": "Tôi tên là Hoàng, hãy gọi tên tôi mỗi khi bạn nói chuyện với tôi."},
        {"role": "user", "content": "Dạo này tôi bị đau đầu và căng thẳng trong công việc. Tôi cần được hỗ trợ về sức khỏe và tâm lý."}, 
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

    # Load vectorstore
    vectorstore, _ = load_vectorstore("text-embedding-3-small", 1024)

    # Initialize voice model with optimized settings
    model = openai.realtime.RealtimeModel(
        model="gpt-4o-realtime-preview",
        modalities=["text", "audio"],
        voice="coral",
        instructions=MedicalMultimodalAgent.instruction_format.format(RAG_context=""),
        turn_detection=openai.realtime.ServerVadOptions(
            threshold=0.5, 
            prefix_padding_ms=200,  
            silence_duration_ms=1000, 
            create_response=False
        ),
        input_audio_transcription=openai.realtime.InputTranscriptionOptions(
            model="gpt-4o-transcribe",
            language="vi",
        )
    )
    
    # Load chat context
    chat_ctx = get_user_active_chat_history()

    # Initialize the assistant
    assistant = MedicalMultimodalAgent(model=model, chat_ctx=chat_ctx, vectorstore=vectorstore)
    assistant.start(ctx.room, participant)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))