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
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(file_handler)


def log_event(event_type: str, content: Any):
    """Logs events with structured content."""
    if isinstance(content, (dict, list)):
        logger.info(f"{event_type}: {json.dumps(content, ensure_ascii=False, default=str)}")
    else:
        logger.info(f"{event_type}: {content}")

def load_vectorstore(model_name: str, chunk_size: int = 1024) -> tuple[FAISS, OpenAIEmbeddings]:
    """Loads a FAISS vector store from disk."""
    start_time = time.time()
    backend_dir = Path(__file__).parent.absolute()
    model_folder = os.path.join(backend_dir, "faiss", f"{model_name}", f"chunk_size_{chunk_size}")

    logger.info(f"Loading vectorstore from: {model_folder}")
    embeddings = OpenAIEmbeddings(model=model_name)
    vectorstore = FAISS.load_local(model_folder, embeddings, allow_dangerous_deserialization=True)
    logger.info(f"Vector store loaded in {time.time() - start_time:.2f}s")
    return vectorstore, embeddings


class MedicalFunctionContext(llm.FunctionContext):
    """Function context for RAG capabilities."""

    def __init__(self, vectorstore: FAISS):
        super().__init__()
        self.vectorstore = vectorstore
        self.query_metrics = []

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

        metrics = {"query": query, "language": language, "k": k, "threshold": score_threshold}
        total_start = time.time()
        log_event("QUERY", f"{query} ({language})")

        # Get relevant documents
        filtered_docs = self.vectorstore.similarity_search_with_relevance_scores(
            query, k=k, score_threshold=score_threshold
        )

        # Early return if no results
        if not filtered_docs:
            log_event("RAG", f"No documents found for query: '{query}'")
            metrics["total_time"] = time.time() - total_start
            self.query_metrics.append(metrics)
            return ""

        # Format results
        metrics["doc_count"] = len(filtered_docs)
        metrics["scores"] = [float(score) for _, score in filtered_docs]
        log_event("FOUND", f"{len(filtered_docs)} documents")

        # Prepare response
        response_parts = []
        for i, (doc, score) in enumerate(filtered_docs):
            content = doc.page_content.strip()
            response_parts.append(f"RAG Information {i+1}:\n{content}")

        # Add language-specific instructions
        instructions = (
            """
        Hướng dẫn: Đây là thông tin từ cơ sở dữ liệu y tế Việt Nam.
        Hãy sử dụng thông tin này để trả lời câu hỏi của người dùng một cách ngắn gọn bằng tiếng Việt.
        """
            if language == "vi"
            else """
        Instructions: This is information from the Vietnamese medical database.
        Please translate this information and answer the user's question concisely in English.
        """
        )

        response = "\n\n---\n\n".join(response_parts) + instructions

        # Log metrics and return
        metrics["total_time"] = time.time() - total_start
        self.query_metrics.append(metrics)

        return response


class MedicalMultimodalAgent(MultimodalAgent):
    """Custom MultimodalAgent with RAG capabilities and chat history."""

    instruction_format = """You are a HEALTHCARE ASSISTANT.
    Your ONLY purpose is to provide healthcare and medical information.
    You can ONLY work (understand, speak, and answer) in two languages: Vietnamese or English.
    Do NOT work on other languages, maybe there are noise in transcription.
    Be CONCISE and SMOOTH in your responses without hesitation, no need to repeat the same thing over and over again.

    IMPORTANT RULES:
    1. ONLY answer healthcare/medical questions. For ANY other topics, politely refuse and remind the user
       that you are a dedicated healthcare assistant, EVEN they ask about your health or other conditions.
    2. If the user speaks in Vietnamese, respond ONLY in Vietnamese.
    3. If the user speaks in English, respond ONLY in English.
    4. Be clear, accessible, and concise in your explanations.
    5. Start every conversation by saying: 'Hello! Xin chào! Tôi có thể giúp gì cho bạn?'

    RESPONSE BASED ON RAG CONTEXT HERE IF RELAVANT AND NOT EMPTY: {RAG_context}
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
        self.current_language = "en"

    def start(self, room: rtc.Room, participant: rtc.RemoteParticipant | str | None = None):
        """Start the agent with timing logs."""
        start_time = time.time()
        super().start(room, participant)
        self.setup_event_listeners()
        log_event("TIMING", f"Agent start completed in {time.time() - start_time:.3f}s")

    async def add_rag_to_query(self, msg: str | None):
        """Detects language, performs RAG search, and updates instructions."""
        
        total_start_time = time.time()
        if not msg or msg.strip() == "":
            log_event("PROCESS", "Skipping empty message")
            return

        # Detect language
        lang_start_time = time.time()
        self.current_language = self.detect_language(msg)
        lang_time = time.time() - lang_start_time
        log_event("TIMING", f"Language detection completed in {lang_time:.3f}s")
        log_event("PROCESS", f"Query: {msg}, Language: {self.current_language}")

        # Add user message to chat context
        if hasattr(self, '_chat_ctx') and self._chat_ctx is not None:
            self._chat_ctx.append(text=msg, role="user")
            log_event("DEBUG", f"CHAT CONTEXT: {len(self._chat_ctx.messages)} messages")
            
        # Get RAG results
        rag_start_time = time.time()
        result = await self.med_fnc_ctx.rag_search(query=msg, language=self.current_language)
        rag_time = time.time() - rag_start_time
        log_event("RAG", f"Rag results: {result}")
        log_event("TIMING", f"RAG search completed in {rag_time:.3f}s")
        
        # Update instructions with RAG context
        update_start_time = time.time()
        new_instruction = self.instruction_format.format(RAG_context=result)
        self._session.session_update(instructions=new_instruction)
        update_time = time.time() - update_start_time
        log_event("TIMING", f"Instruction update completed in {update_time:.3f}s")
        
        # Generate reply
        self.generate_reply()
        
        total_time = time.time() - total_start_time
        log_event("TIMING", f"Total add_rag_to_query process completed in {total_time:.3f}s")

    def setup_event_listeners(self):
        """Configures speech event handlers."""
        self.user_speech_end_time = None
        
        @self._session.on("input_speech_transcription_completed")
        def _input_speech_transcription_completed(ev):
            self.user_speech_end_time = time.time()
            log_event("TIMING", f"User finished speaking")
            asyncio.create_task(self.add_rag_to_query(ev.transcript))
        
        @self._session.on("response_content_added")
        def _response_content_added(message):
            if self.user_speech_end_time:
                response_time = time.time() - self.user_speech_end_time
                log_event("RESPONSE", f"Agent started responding after {response_time:.3f}s")
                self.user_speech_end_time = None
            else:
                log_event("RESPONSE", "Agent started responding")                

    def detect_language(self, text: str) -> str:
        """Detects the language of the text."""
        lang, confidence = langid.classify(text)
        result = "vi" if lang == "vi" else "en"
        return result

def get_user_active_chat_history(user_id: str = "user_test_123") -> Optional[llm.ChatContext]:
    """Initializes dummy chat history for testing."""

    if user_id != "user_test_123":
        return None

    dummy_history = [
        {"role": "user", "content": "Tôi tên là Hoàng, hãy gọi tên tôi mỗi khi bạn nói chuyện với tôi."},
    ]

    messages = [llm.ChatMessage(role=item["role"], content=item["content"]) for item in dummy_history]
    return llm.ChatContext(messages=messages)


async def entrypoint(ctx: JobContext):
    """Main entry point for the medical assistant."""

    # Initialize connection
    start_time = time.time()
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    log_event("STARTUP", f"Connection established in {time.time() - start_time:.2f}s")

    # Load vectorstore
    vectorstore, _ = load_vectorstore("text-embedding-3-small", 1024)

    # Initialize voice model
    model = openai.realtime.RealtimeModel(
        model="gpt-4o-realtime-preview-2024-12-17",
        instructions=MedicalMultimodalAgent.instruction_format.format(RAG_context=""),
        voice="coral",
        temperature=0.6,
        modalities=["audio", "text"],
        turn_detection=openai.realtime.ServerVadOptions(
            threshold=0.5, prefix_padding_ms=200, silence_duration_ms=1000, create_response=False
        ),
    )
    chat_ctx = get_user_active_chat_history()

    # Initialize the assistant
    assistant = MedicalMultimodalAgent(model=model, chat_ctx=chat_ctx, vectorstore=vectorstore)
    assistant.start(ctx.room, participant)
    logger.info("Assistant initialized and ready")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))