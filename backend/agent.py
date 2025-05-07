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
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
log_dir = Path(__file__).parent / "logs" / "talk_logs"
log_dir.mkdir(parents=True, exist_ok=True) 
log_file_path = log_dir / "medical_assistant.log"
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
root_logger.addHandler(file_handler)

def log_with_separator(logger, type_label, content, separator_length=80):
    """Logging function."""
    separator = "=" * separator_length
    logger.info(f"{separator}")
    logger.info(f"{type_label}")
    if isinstance(content, str):
        logger.info(json.dumps(content, ensure_ascii=False))
    else:
        logger.info(json.dumps(content, ensure_ascii=False, default=str))
    logger.info(f"{separator}")

def load_vectorstore(model_name: str, chunk_size: int = 1024):
    """Load FAISS vector store from disk with embedding model and chunk size."""
    
    start_time = time.time()
    backend_dir = Path(__file__).parent.absolute()
    model_base_folder = os.path.join(backend_dir, "faiss", f"{model_name}")
    model_folder = os.path.join(model_base_folder, f"chunk_size_{chunk_size}")

    logger.info(f"Loading vectorstore from: {model_folder}")
    embeddings = OpenAIEmbeddings(model=model_name)
    vectorstore = FAISS.load_local(model_folder, embeddings, allow_dangerous_deserialization=True)
    load_time = time.time() - start_time
    log_with_separator(root_logger, "SYSTEM", f"Vector store loaded in {load_time:.4f} seconds")
    return vectorstore

class MedicalFunctionContext(llm.FunctionContext):
    """Function context for RAG capabilities."""
    
    def __init__(self, vectorstore):
        super().__init__()
        self.vectorstore = vectorstore
        self.query_metrics: List[Dict] = []
    
    @llm.ai_callable()
    async def rag_search(
        self,
        query: Annotated[str, llm.TypeInfo(description="Query to search within the documents")],
        language: Annotated[str, llm.TypeInfo(description="Language of the query (en or vi)")] = "vi",
        k: Annotated[int, llm.TypeInfo(description="Number of relevant documents to retrieve")] = 3,
        score_threshold: Annotated[float, llm.TypeInfo(description="Minimum relevance score (0-1, higher is better) to consider a document relevant")] = 0.35,
    ) -> str:
        """RAG search for medical information, filtering by relevance score."""

        metrics = {
            "query": query,
            "language": language,
            "k": k,
            "score_threshold": score_threshold,
            "timestamp": time.time(),
        }
        total_start_time = time.time()
        log_with_separator(root_logger, "USER QUERY", f"Query: {query}\nLanguage: {language}")

        # Get relevant documents - measure retrieval time
        logger.info(f"Searching medical info for: '{query}' with k={k} and relevance score threshold={score_threshold}")
        retrieval_start = time.time()
        filtered_docs = self.vectorstore.similarity_search_with_relevance_scores(
            query, k=k, score_threshold=score_threshold
        )
        retrieval_time = time.time() - retrieval_start
        metrics["retrieval_time"] = retrieval_time
        metrics["filtered_docs"] = len(filtered_docs)
        if not filtered_docs:
            metrics["error"] = "No documents found meeting the relevance score threshold"
            metrics["total_time"] = time.time() - total_start_time
            log_with_separator(root_logger, "RAG RESULTS", f"No documents found meeting relevance threshold {score_threshold} for query: '{query}'")
            logger.info(f"No documents above threshold for query: '{query}'. Model will answer normally.")
            return ""

        # Format results for user
        metrics["doc_count"] = len(filtered_docs)
        doc_sources = [getattr(doc, 'metadata', {}).get('source', 'Unknown source') for doc, _ in filtered_docs]
        metrics["doc_sources"] = doc_sources
        metrics["relevance_scores"] = [float(score) for _, score in filtered_docs]
        
        # Log found documents
        doc_info = [f"Document {i+1}: {source}, relevance score: {float(filtered_docs[i][1]):.4f}" 
                   for i, source in enumerate(doc_sources)]
        doc_info_str = "\n".join(doc_info)
        log_with_separator(root_logger, "DOCUMENTS FOUND", f"Count: {len(filtered_docs)}\n{doc_info_str}")
        
        # Add RAG information to response
        response_parts = []
        doc_contents = []
        for i, (doc, score) in enumerate(filtered_docs):
            content = doc.page_content.strip()
            response_parts.append(f"RAG Information {i+1}:\n{content}")
            doc_contents.append(f"Document {i+1} Content:\n{content}")
        response = "\n\n---\n\n".join(response_parts)
        log_with_separator(root_logger, "DOCUMENT CONTENTS", "\n\n".join(doc_contents))
        metrics["rag_response"] = response
        
        # Add RAG instructions based on language
        if language == "vi":
            rag_instructions = """
            Hướng dẫn: Đây là thông tin từ cơ sở dữ liệu y tế Việt Nam. 
            Hãy sử dụng thông tin này để trả lời câu hỏi của người dùng một cách ngắn gọn, chính xác và dễ hiểu bằng tiếng Việt.
            Có một vài thông tin từ RAG có thể không liên quan đến câu hỏi của người dùng, bạn hãy bỏ qua nó.
            Hãy chọn lọc thông tin từ RAG mà liên quan đến câu hỏi của người dùng."""
        else:
            rag_instructions = """
            Instructions: This is information from the Vietnamese medical database.
            Please translate this information and answer to the user's question concisely, accurately, and clearly in English.
            There may be some information from RAG that is not relevant to the user's question, please ignore it.
            Please choose the information from RAG that is relevant to the user's question."""
        response = response + rag_instructions
        
        # Log metrics
        total_time = time.time() - total_start_time
        metrics["total_time"] = total_time
        log_with_separator(root_logger, "RAG METRICS", f"Performance: Retrieval={retrieval_time:.3f}s, Total={total_time:.3f}s")
        logger.info(f"Performance: Retrieval={retrieval_time:.3f}s, Total={total_time:.3f}s")
        self.query_metrics.append(metrics)
        
        return response

class MedicalMultimodalAgent(MultimodalAgent):
    """Custom MultimodalAgent with RAG capabilities and user-based chat history."""
    
    def __init__(
        self,
        *,
        model: openai.realtime.RealtimeModel,
        vectorstore: FAISS,
        vad: Optional[Any] = None,
        chat_ctx: Optional[llm.ChatContext] = None,
        fnc_ctx: Optional[llm.FunctionContext] = None,
        transcription=AgentTranscriptionOptions(),
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        # Initialize RAG function context
        self.med_fnc_ctx = MedicalFunctionContext(vectorstore=vectorstore)
        if fnc_ctx is None:
            fnc_ctx = self.med_fnc_ctx
        
        super().__init__(
            model=model,
            vad=vad,
            chat_ctx=chat_ctx,
            fnc_ctx=fnc_ctx,
            transcription=transcription,
            loop=loop,
        )
        
        # State tracking variables
        self.conversation_history = {}
        self.current_language: str = "en"
        
        # User and chat tracking
        self.active_user_id = None  
        self.active_chat_id = None  
        
        # Chat history retrieval settings
        self.max_history_turns = 5 
        self._initialize_dummy_chat_history()
        self.setup_event_listeners()
    
    def _initialize_dummy_chat_history(self):
        """Initialize dummy chat history for testing purposes."""
        
        test_user_id = "user_test_123"
        test_chat_id = "chat_medical_history"
        
        dummy_history = [
            {"role": "user", "content": "Tôi tên là Hoàng, hãy gọi tên tôi mỗi khi bạn nói chuyện với tôi.", "timestamp": time.time() - 3600},
            {"role": "assistant", "content": "Xin chào anh Hoàng! Tôi là trợ lý y tế của anh.", "timestamp": time.time() - 3590},
            {"role": "user", "content": "Tôi vừa được chẩn đoán mắc bệnh tiểu đường 2 tháng trước. Đường huyết của tôi khoảng 180-200 mg/dL.", "timestamp": time.time() - 3580},
            {"role": "assistant", "content": "Cảm ơn anh Hoàng đã chia sẻ thông tin. Mức đường huyết của anh cao hơn mức mục tiêu. Đối với hầu hết người lớn mắc bệnh tiểu đường, mục tiêu thường là từ 80-130 mg/dL trước bữa ăn và dưới 180 mg/dL sau bữa ăn.", "timestamp": time.time() - 3570},
        ]
        
        # Initialize the history
        if test_user_id not in self.conversation_history:
            self.conversation_history[test_user_id] = {}
        self.conversation_history[test_user_id][test_chat_id] = dummy_history
        log_with_separator(root_logger, "SYSTEM SETUP", f"Initialized dummy chat history for test user {test_user_id}")
    
    def get_or_create_chat_history(self, user_id, chat_id=None):
        """Get or create chat history for a user and specific chat."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = {}
        
        # If no chat_id provided, create a new one
        if not chat_id:
            chat_id = f"chat_{int(time.time())}"
            self.conversation_history[user_id][chat_id] = []
        elif chat_id not in self.conversation_history[user_id]:
            self.conversation_history[user_id][chat_id] = []
            
        return self.conversation_history[user_id][chat_id], chat_id
    
    def setup_event_listeners(self):
        """Configure speech event handlers"""
        @self.on("user_speech_committed")
        def on_user_speech_committed(msg):
            
            user_id = "user_test_123"
            chat_id = "chat_medical_history"
            
            self.active_user_id = user_id
            self.active_chat_id = chat_id
            
            chat_history, chat_id = self.get_or_create_chat_history(user_id, chat_id)
            self.active_chat_id = chat_id
            
            # Get or create chat history
            chat_history, chat_id = self.get_or_create_chat_history(user_id, chat_id)
            
            # Record speech in chat history
            speech_time = time.time()
            chat_history.append({"role": "user", "content": msg, "timestamp": speech_time})
            
            # Log the event
            logger.info(f"User speech committed: {json.dumps(msg, ensure_ascii=False)}")
            log_with_separator(root_logger, "SPEECH FRAGMENT", 
                              f"User ID: {user_id}, Chat ID: {chat_id}, Message: {msg}")
            
            # Process the transcript
            asyncio.create_task(self.process_committed_transcript(msg, user_id, chat_id))
        
        @self.on("agent_speech_committed")
        def on_agent_speech_committed(speech_data):
            """Capture agent's speech responses"""
            if not self.active_user_id or not self.active_chat_id:
                logger.warning("Agent speech committed but no active user/chat")
                return
                
            # Get chat history
            chat_history, _ = self.get_or_create_chat_history(
                self.active_user_id, self.active_chat_id
            )
            
            # Add to conversation history
            speech_time = time.time()
            chat_history.append({
                "role": "assistant", 
                "content": speech_data, 
                "timestamp": speech_time
            })
            
            log_with_separator(root_logger, "AI RESPONSE", 
                              f"User ID: {self.active_user_id}, Chat ID: {self.active_chat_id}, Response: {speech_data}")
    
    async def process_committed_transcript(self, msg, user_id, chat_id):
        """Apply RAG to user's complete utterance and update conversation context."""
        process_start = time.time()
        transcript_metrics = {"transcript": msg, "timestamp": process_start}
        
        # Detect language + extract relevant query
        self.current_language = self.detect_language(msg)
        transcript_metrics["language"] = self.current_language
        
        logger.info(f"Processing transcript for RAG: {json.dumps(msg, ensure_ascii=False)} in {self.current_language}")
        log_with_separator(root_logger, "COMPLETE USER SPEECH",
                        f"User ID: {user_id}, Chat ID: {chat_id}, Query: {msg}, Language: {self.current_language}")
        
        # Perform RAG search
        result = await self.med_fnc_ctx.rag_search(
            query=msg,
            language=self.current_language
        )
        transcript_metrics["rag_time"] = time.time() - process_start
        
        # Get relevant chat history
        chat_history, _ = self.get_or_create_chat_history(user_id, chat_id)    
        formatted_history = self.format_chat_history(chat_history, self.max_history_turns)
        
        # Add RAG results and chat history to conversation context
        if hasattr(self._model, 'sessions') and self._model.sessions:
            session = self._model.sessions[0]
            
            # Create the context with history
            context_parts = [
                "CHAT HISTORY (FOR REFERENCES TO EXTRACT CONTEXT):",
                formatted_history
            ]
            
            # Add RAG results if available
            if result and len(result.strip()) > 0:
                logger.info("Adding RAG results to conversation context")
                log_with_separator(root_logger, "RAG STATUS", "RAG results found and added to conversation")
                context_parts.extend([
                    "",
                    "MEDICAL CONTEXT:",
                    result
                ])
                transcript_metrics["rag_content"] = result
            else:
                logger.info("No relevant documents found, using base knowledge")
                log_with_separator(root_logger, "RAG STATUS", "No relevant documents found. Using base knowledge.")
                transcript_metrics["no_relevant_info"] = True
            
            # Add current query from user
            context_parts.extend([
                "",
                f"CURRENT QUERY: {msg}"
            ])
            formatted_result = "\n".join(context_parts)
            
            # Update the session with the new context
            log_with_separator(root_logger, "FULL PROMPT CONTEXT TO LLM", formatted_result)
            session.conversation.item.create(
                llm.ChatMessage(role="system", content=formatted_result)
            )
            logger.info(f"Context updated for user {user_id}, chat {chat_id}")
        
        # Log completion and metrics
        transcript_metrics["total_process_time"] = time.time() - process_start
        logger.info(f"Processing completed in {transcript_metrics['total_process_time']:.3f}s")
        log_with_separator(root_logger, "WAITING FOR AI RESPONSE",
                        f"User ID: {user_id}, Chat ID: {chat_id}, Query: {msg}")
    
    
    def format_chat_history(self, chat_history, max_turns=5):
        """Format chat history to include in the prompt."""
        
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
        """Detect language of the text."""
        lang, _ = langid.classify(text)
        if lang == 'vi':
            return "vi"
        return "en"
    
    async def on_transcript(self, transcript, participant_identity=None):
        """Process user speech transcript."""
        await super().on_transcript(transcript, participant_identity)


async def entrypoint(ctx: JobContext):
    """Main entry point for the medical assistant."""
    
    # Initialize connection
    start_time = time.time()
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    await ctx.wait_for_participant()
    connect_time = time.time() - start_time
    log_with_separator(root_logger, "SYSTEM STARTUP", f"Connection established in {connect_time:.4f} seconds")
    
    # Load vectorstore
    vectorstore_start = time.time()
    model_name = "text-embedding-3-small"
    chunk_size = 1024
    vectorstore = load_vectorstore(model_name, chunk_size)
    vectorstore_time = time.time() - vectorstore_start
    log_with_separator(root_logger, "SYSTEM STARTUP", f"Vector store loaded in {vectorstore_time:.4f} seconds")
    
    # Initialize voice model
    model_start = time.time()
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
        """,
        voice="coral",
        temperature=0.6,
        modalities=["audio", "text"],
        turn_detection=openai.realtime.ServerVadOptions(
            threshold=0.5, prefix_padding_ms=200, silence_duration_ms=1000
            ),
    )
    model_time = time.time() - model_start
    log_with_separator(root_logger, "SYSTEM STARTUP", f"Voice model initialized in {model_time:.4f} seconds")
    
    # Initialize the assistant
    assistant_start = time.time()
    assistant = MedicalMultimodalAgent(model=model, vectorstore=vectorstore)
    assistant.start(ctx.room)
    ctx.assistant = assistant
    assistant_time = time.time() - assistant_start
    log_with_separator(root_logger, "SYSTEM STARTUP", f"Assistant started in {assistant_time:.4f} seconds")
    
    # Warm-up RAG system with dummy query (important to reduce latency at first query)
    warmup_start = time.time()
    log_with_separator(root_logger, "SYSTEM WARMUP", "Starting RAG warm-up...")
    await assistant.med_fnc_ctx.rag_search(query="How are you today?", language="en", k=3, score_threshold=0.35)
    warmup_time = time.time() - warmup_start
    log_with_separator(root_logger, "SYSTEM WARMUP", f"RAG warm-up completed in {warmup_time:.4f} seconds.")
    
    # Initial system message
    session = model.sessions[0]
    session.conversation.item.create(
        llm.ChatMessage(
            role="system",
            content="""You are a healthcare assistant in both English and Vietnamese.
            
            Your initial greeting should have ONLY this content, then stop to hear the user's response:
            "Hello! Xin chào!"
            
            After this greeting, detect the user's language and respond only in that language.
            """
        )
    )
    session.response.create()
    logger.info("Assistant initialized and ready")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))