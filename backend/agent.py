from __future__ import annotations
import logging
import os
import time
from dotenv import load_dotenv
from pathlib import Path
from typing import Annotated, Dict, List, Optional, Any
import asyncio
import langid
import json

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.multimodal import MultimodalAgent, AgentTranscriptionOptions
from livekit.plugins import openai
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Basic setup
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)
log_dir = Path(__file__).parent / "logs" / "talk_logs"
log_dir.mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(log_dir / "medical_assistant.log", encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

def log_event(event_type, content):
    """Logging function"""
    if isinstance(content, (dict, list)):
        logger.info(f"{event_type}: {json.dumps(content, ensure_ascii=False, default=str)}")
    else:
        logger.info(f"{event_type}: {content}")

def load_vectorstore(model_name: str, chunk_size: int = 1024):
    """Load FAISS vector store from disk"""
    start_time = time.time()
    backend_dir = Path(__file__).parent.absolute()
    model_folder = os.path.join(backend_dir, "faiss", f"{model_name}", f"chunk_size_{chunk_size}")

    logger.info(f"Loading vectorstore from: {model_folder}")
    embeddings = OpenAIEmbeddings(model=model_name)
    vectorstore = FAISS.load_local(model_folder, embeddings, allow_dangerous_deserialization=True)
    logger.info(f"Vector store loaded in {time.time() - start_time:.2f}s")
    return vectorstore, embeddings

class MedicalFunctionContext(llm.FunctionContext):
    """Function context for RAG capabilities"""
    
    def __init__(self, vectorstore):
        super().__init__()
        self.vectorstore = vectorstore
        self.query_metrics = []
    
    @llm.ai_callable()
    async def rag_search(
        self,
        query: Annotated[str, llm.TypeInfo(description="Query to search within the documents")],
        language: Annotated[str, llm.TypeInfo(description="Language of the query (en or vi)")] = "vi",
        k: Annotated[int, llm.TypeInfo(description="Number of relevant documents to retrieve")] = 3,
        score_threshold: Annotated[float, llm.TypeInfo(description="Minimum relevance score threshold")] = 0.35,
    ) -> str:
        """RAG search for medical information"""
        
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
        instructions = """
        Hướng dẫn: Đây là thông tin từ cơ sở dữ liệu y tế Việt Nam. 
        Hãy sử dụng thông tin này để trả lời câu hỏi của người dùng một cách ngắn gọn bằng tiếng Việt.
        """ if language == "vi" else """
        Instructions: This is information from the Vietnamese medical database.
        Please translate this information and answer the user's question concisely in English.
        """
        
        response = "\n\n---\n\n".join(response_parts) + instructions
        
        # Log metrics and return
        metrics["total_time"] = time.time() - total_start
        log_event("RAG METRICS", f"Total: {metrics['total_time']:.2f}s")
        self.query_metrics.append(metrics)
        
        return response

class MedicalMultimodalAgent(MultimodalAgent):
    """Custom MultimodalAgent with RAG capabilities and chat history"""
    
    def __init__(
        self,
        *,
        model: openai.realtime.RealtimeModel,
        vectorstore: FAISS,
        vad: Optional[Any] = None,
        transcription=AgentTranscriptionOptions(),
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        # Initialize RAG function context
        self.med_fnc_ctx = MedicalFunctionContext(vectorstore=vectorstore)
        
        super().__init__(
            model=model,
            vad=vad,
            chat_ctx=llm.ChatContext(),
            fnc_ctx=self.med_fnc_ctx,
            transcription=transcription,
            loop=loop,
        )
        
        # State tracking
        self.conversation_history = {}
        self.current_language = "en"
        self.active_user_id = None
        self.active_chat_id = None
        self.max_history_turns = 5
        
        # Initialize test data and listeners
        self._initialize_dummy_chat_history()
        self.setup_event_listeners()
    
    def _initialize_dummy_chat_history(self):
        """Initialize dummy chat history for testing"""
        
        test_user_id = "user_test_123"
        test_chat_id = "chat_medical_history"
        
        dummy_history = [
            {"role": "user", "content": "Tôi tên là Hoàng, hãy gọi tên tôi mỗi khi bạn nói chuyện với tôi.", "timestamp": time.time() - 3600},
            {"role": "assistant", "content": "Xin chào anh Hoàng! Tôi là trợ lý y tế của anh.", "timestamp": time.time() - 3590},
            {"role": "user", "content": "Tôi vừa được chẩn đoán mắc bệnh tiểu đường 2 tháng trước. Đường huyết của tôi khoảng 180-200 mg/dL.", "timestamp": time.time() - 3580},
            {"role": "assistant", "content": "Cảm ơn anh Hoàng đã chia sẻ thông tin. Mức đường huyết của anh cao hơn mức mục tiêu.", "timestamp": time.time() - 3570},
        ]
        
        # Initialize the history
        if test_user_id not in self.conversation_history:
            self.conversation_history[test_user_id] = {}
        self.conversation_history[test_user_id][test_chat_id] = dummy_history
        log_event("SETUP", f"Initialized chat history for test user {test_user_id}")
    
    def setup_event_listeners(self):
        """Configure speech event handlers"""
        @self.on("user_speech_committed")
        def on_user_speech_committed(msg):
            user_id = "user_test_123"
            chat_id = "chat_medical_history"
            
            self.active_user_id = user_id
            self.active_chat_id = chat_id
            
            # Get or create chat history and record speech
            chat_history, _ = self.load_chat_history(user_id, chat_id)
            chat_history.append({"role": "user", "content": msg, "timestamp": time.time()})
            
            log_event("USER TALK", f"User ID: {user_id}, Chat ID: {chat_id}, Message: {msg}")
            asyncio.create_task(self.process_committed_transcript(msg, user_id, chat_id))
        
        @self.on("agent_speech_committed")
        def on_agent_speech_committed(speech_data):
            """Capture agent's speech responses"""
            if not self.active_user_id or not self.active_chat_id:
                logger.warning("Agent speech committed but no active user/chat")
                return
                
            # Get chat history and add response
            chat_history, _ = self.load_chat_history(
                self.active_user_id, self.active_chat_id
            )
            chat_history.append({
                "role": "assistant", 
                "content": speech_data, 
                "timestamp": time.time()
            })
            log_event("AI RESPONSE", f"User ID: {self.active_user_id}, Chat ID: {self.active_chat_id}, Response: {speech_data}")

    def load_chat_history(self, user_id, chat_id=None):
        """Get or create chat history for a user and specific chat"""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = {}
        
        # If no chat_id provided, create a new one
        if not chat_id:
            chat_id = f"chat_{int(time.time())}"
            self.conversation_history[user_id][chat_id] = []
        elif chat_id not in self.conversation_history[user_id]:
            self.conversation_history[user_id][chat_id] = []
            
        return self.conversation_history[user_id][chat_id], chat_id

    def format_chat_history(self, chat_history, max_turns=5):
        """Format chat history to include in the prompt"""
        history_to_format = chat_history.copy()
        if history_to_format and history_to_format[-1]["role"] == "user":
            history_to_format = history_to_format[:-1]
        
        # Only keep the last N turns of chat history
        recent_history = history_to_format[-max_turns*2:] if len(history_to_format) > max_turns*2 else history_to_format
        
        formatted_lines = []
        for entry in recent_history:
            role = "User" if entry["role"] == "user" else "Assistant"
            formatted_lines.append(f"{role}: {entry['content']}")
        
        return "\n".join(formatted_lines)
    
    def detect_language(self, text):
        """Detect language of the text"""
        lang, _ = langid.classify(text)
        return "vi" if lang == 'vi' else "en"
    
    async def process_committed_transcript(self, msg, user_id, chat_id):
        """Apply RAG to user's utterance and update conversation context"""
        # Skip processing for empty messages
        if not msg or msg.strip() == "":
            log_event("PROCESS", "Skipping empty message")
            return

        # Detect language
        self.current_language = self.detect_language(msg)
        log_event("PROCESS", f"Query: {msg}, Language: {self.current_language}")
        
        # Perform RAG search
        result = ""
        if len(msg.split()) > 5:
            result = await self.med_fnc_ctx.rag_search(query=msg, language=self.current_language)
        
        # Get chat history
        chat_history, _ = self.load_chat_history(user_id, chat_id)    
        formatted_history = self.format_chat_history(chat_history, self.max_history_turns)
        
        # Add RAG results and chat history to conversation context
        if hasattr(self._model, 'sessions') and self._model.sessions:
            session = self._model.sessions[0]
            prompt_parts = []
            
            # Add conversation history if it exists
            if formatted_history:
                prompt_parts.append(f"CONVERSATION HISTORY:\n{formatted_history}")
            
            # Add RAG context if available
            if result and len(result.strip()) > 0:
                prompt_parts.append(f"RAG MEDICAL CONTEXT:\n{result}")
            
            # Add current query
            prompt_parts.append(f"CURRENT USER QUERY:\n{msg}")
            
            # Finalize the prompt
            combined_query = "\n\n".join(prompt_parts)
            
            # Update the session
            session.conversation.item.create(
                llm.ChatMessage(role="user", content=combined_query)
            )
            log_event("PROMPT", "Combined query with history and RAG sent to model")
        
        log_event("HISTORY", f"Active chat history has {len(chat_history)} messages")
        
    async def on_transcript(self, transcript, participant_identity=None):
        """Process user speech transcript"""
        if hasattr(self._model, 'on_transcript'):
            await self._model.on_transcript(transcript, participant_identity)


async def entrypoint(ctx: JobContext):
    """Main entry point for the medical assistant"""
    
    # Initialize connection
    start_time = time.time()
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    await ctx.wait_for_participant()
    log_event("STARTUP", f"Connection established in {time.time() - start_time:.2f}s")
    
    # Load vectorstore
    vectorstore, _ = load_vectorstore("text-embedding-3-small", 1024)
    
    # Initialize voice model
    model = openai.realtime.RealtimeModel(
        model="gpt-4o-realtime-preview-2024-12-17",
        instructions="""You are a HEALTHCARE ASSISTANT.
        Your ONLY purpose is to provide healthcare and medical information.
        You can ONLY work (understand, speak, and answer) in two languages: Vietnamese or English. 
        Do NOT work on other languages, they are maybe noise from the user that you mistranslate.
        Be CONCISE and SMOOTH in your responses without hesitation, no need to repeat the same thing over and over again.
        
        IMPORTANT RULES:
        1. ONLY answer healthcare/medical questions. For ANY other topics, politely refuse and remind the user
           that you are a dedicated healthcare assistant, EVEN they ask about your health or other conditions.
        2. If the user speaks in Vietnamese, respond ONLY in Vietnamese.
        3. If the user speaks in English, respond ONLY in English.
        4. Be clear, accessible, and concise in your explanations.
        5. Start every conversation by saying: 'Hello! Xin chào! Tôi có thể giúp gì cho bạn?'
        """,
        voice="coral",
        temperature=0.6,
        modalities=["audio", "text"],
        turn_detection=openai.realtime.ServerVadOptions(
            threshold=0.5, prefix_padding_ms=200, silence_duration_ms=1000
        ),
    )
    
    # Initialize the assistant
    assistant = MedicalMultimodalAgent(model=model, vectorstore=vectorstore)
    assistant.start(ctx.room)
    ctx.assistant = assistant
    log_event("STARTUP", "Assistant started")
    
    # Warm-up RAG system
    await assistant.med_fnc_ctx.rag_search(query="How are you today?", language="en")
    log_event("WARMUP", "RAG system warmed up")
        
    # Initial greeting
    session = model.sessions[0]
    session.response.create()
    logger.info("Assistant initialized and ready")

if __name__ == "__main__":  
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))