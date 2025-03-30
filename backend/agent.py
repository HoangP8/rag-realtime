from __future__ import annotations
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Annotated
import re
import asyncio

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.multimodal import MultimodalAgent, AgentTranscriptionOptions
from livekit.plugins import openai
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Basic setup
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)


def load_vectorstore(model_name: str):
    """Load FAISS vector store from disk."""
    
    backend_dir = Path(__file__).parent.absolute()
    model_folder = backend_dir / "faiss" / model_name
    if not os.path.exists(model_folder):
        logger.error(f"Vector store not found: {model_folder}")
        return None
    embeddings = OpenAIEmbeddings(model=model_name)
    return FAISS.load_local(str(model_folder), embeddings, allow_dangerous_deserialization=True)


class MedicalFunctionContext(llm.FunctionContext):
    """Function context for medical RAG capabilities."""
    
    def __init__(self, vectorstore):
        super().__init__()
        self.vectorstore = vectorstore
    
    @llm.ai_callable()
    async def search_medical_info(
        self,
        query: Annotated[str, llm.TypeInfo(description="Medical query to search within the documents")],
        k: Annotated[int, llm.TypeInfo(description="Number of relevant documents to retrieve")] = 3,
    ) -> str:
        """
        Search the medical document database for information relevant to health-related queries.
        Uses GPT-4o to synthesize the information into a coherent response.
        """
        
        if not self.vectorstore:
            return "I couldn't access the medical database. Please try again later."
        
        # Get relevant documents
        logger.info(f"Searching medical info for: '{query}' with k={k}")
        docs = self.vectorstore.similarity_search(query, k=k)
        
        if not docs:
            return "I couldn't find any relevant medical information in our database."
        
        # Combine the document content
        context = "\n\n---\n\n".join([
            f"Document {i+1}:\n{doc.page_content}" 
            for i, doc in enumerate(docs)
        ])
        
        # Use GPT-4o to generate a response
        llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        
        # Template prompt
        prompt = f"""
        MEDICAL INFORMATION REQUEST
        
        Query: {query}
        
        Context from medical database:
        {context}
        
        Instructions:
        1. Generate a truthful and accurate response based ONLY on the provided context
        2. If the information in the context is insufficient, acknowledge limitations
        3. Format the response in the same language as the query
        4. Focus on providing clinically accurate information
        5. Be clear, concise, and patient-friendly in your explanation
        6. Do not reference the source documents or say things like "according to the documents"
        
        Response:
        """
        
        logger.info("Requesting GPT-4o synthesis of medical information")
        response = await llm.ainvoke(prompt)
        logger.info(f"GPT-4o synthesized response:\n{response.content}")
        return response.content


class MedicalMultimodalAgent(MultimodalAgent):
    """Custom MultimodalAgent with medical keyword detection and RAG capabilities."""
    
    def __init__(
        self,
        *,
        model,
        vectorstore,
        vad=None,
        chat_ctx=None,
        fnc_ctx=None,
        transcription=AgentTranscriptionOptions(),
        max_text_response_retries=5,
        loop=None,
        noise_cancellation=None,
    ):
        # Create our medical function context
        self.med_fnc_ctx = MedicalFunctionContext(vectorstore=vectorstore)
        
        # If no function context is provided, use our medical one
        if fnc_ctx is None:
            fnc_ctx = self.med_fnc_ctx
        
        # Initialize the parent MultimodalAgent with all parameters
        super().__init__(
            model=model,
            vad=vad,
            chat_ctx=chat_ctx,
            fnc_ctx=fnc_ctx,
            transcription=transcription,
            max_text_response_retries=max_text_response_retries,
            loop=loop,
            noise_cancellation=noise_cancellation,
        )
        
        # Medical terms that trigger RAG (both English and Vietnamese)
        self.medical_terms = [
            # English terms
            "tuberculosis", "tb", "cough", "fever", "weight loss", "shortness of breath",
            "pain", "infection", "symptoms", "treatment", "medicine", "diagnosis",
            "disease", "vaccine", "blood pressure", "diabetes", "cancer", "virus",
            
            # Vietnamese terms
            "lao", "ho", "sốt", "sụt cân", "khó thở", "đau", "nhiễm trùng", 
            "triệu chứng", "điều trị", "thuốc", "chẩn đoán", "bệnh", "vắc-xin",
            "huyết áp", "tiểu đường", "ung thư", "vi rút"
        ]
        
        self.conversation_history = []
        self.current_language = "en"
        self.committed_transcript = None
        self.setup_event_listeners()
    
    async def process_committed_transcript(self, msg):
        """Process the committed transcript with RAG capabilities."""

        if not msg or not any(term.lower() in msg.lower() for term in self.medical_terms):
            logger.info("No medical terms detected in committed transcript.")
            return
            
        # Detect language + extract relevant query
        self.current_language = self.detect_language(msg)
        relevant_query = self.extract_relevant_sentence(msg)
        logger.info(f"Medical term detected in committed transcript: '{msg}', performing RAG")
        
        try:
            # Perform RAG search using the relevant query
            result = await self.med_fnc_ctx.search_medical_info(query=relevant_query)
            
            if result:

                system_template = """
                As a medical assistant specializing in tuberculosis, provide this information to the user:
                
                {result}
                
                IMPORTANT RULES:
                - Respond only in {language}
                - Be concise and straightforward
                - You specialize in tuberculosis but can answer related health questions
                - For non-medical topics (hobbies, history, etc.), politely explain you're a medical assistant
                """
                
                language = "Vietnamese" if self.current_language == "vi" else "English"
                system_message = system_template.format(result=result, language=language)
                
                logger.info(f"Adding RAG information to conversation context")
                logger.info(f"System message added to agent:\n{system_message}")
                
                # Add RAG information to model's conversation context
                if hasattr(self._model, 'sessions') and self._model.sessions:
                    session = self._model.sessions[0]
                    session.conversation.item.create(
                        llm.ChatMessage(role="system", content=system_message)
                    )
                    logger.info("Successfully added RAG information to conversation")
        except Exception as e:
            logger.error(f"Error processing medical query: {e}")
            
    def setup_event_listeners(self):
        """Setup event listeners for agent events"""
        @self.on("user_speech_committed")
        def on_user_speech_committed(msg):
            logger.info(f"User speech committed: {msg}")
            self.conversation_history.append({"role": "user", "content": msg})
            self.committed_transcript = msg
            # asyncio.create_task(self.process_committed_transcript(msg))
    
    def extract_relevant_sentence(self, transcript):
        """Extract the sentence containing a medical term."""
        sentences = re.split(r'(?<=[.?!])\s+', transcript)
        for sentence in sentences:
            if any(term.lower() in sentence.lower() for term in self.medical_terms):
                return sentence
        return transcript
    
    def detect_language(self, text):
        """Simple language detection for Vietnamese vs English."""
        vietnamese_chars = set('àáâãèéêìíòóôõùúýăđĩũơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ')
        if any(char.lower() in vietnamese_chars for char in text):
            return "vi"
        return "en"
    
    async def on_transcript(self, transcript, participant_identity=None):
        """Process user speech transcript."""
        await super().on_transcript(transcript, participant_identity)



async def entrypoint(ctx: JobContext):
    """Main entry point for the medical assistant."""
    
    # Initialize connection
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    await ctx.wait_for_participant()

    # Load vectorstore
    model_name = "text-embedding-3-small"
    vectorstore = load_vectorstore(model_name)
    if not vectorstore:
        logger.error("Failed to load vectorstore, exiting.")
        return
    
    # Initialize voice model
    model = openai.realtime.RealtimeModel(
        instructions="""You are a medical assistant specializing in tuberculosis.
        IMPORTANT - LANGUAGE SELECTION:
        - If the user speaks in Vietnamese, respond ONLY in Vietnamese.
        - If the user speaks in English, respond ONLY in English.
        - You specialize in tuberculosis but can assist with related health questions.
        - For non-medical topics (like hobbies or history), politely explain you're a medical assistant.
        Be concise, accurate, and approachable in your responses.""",
        voice="coral",
        temperature=0.7,
        modalities=["audio", "text"],
    )
    
    # Create and start the assistant
    assistant = MedicalMultimodalAgent(model=model, vectorstore=vectorstore)
    assistant.start(ctx.room)
    ctx.assistant = assistant
    
    # Add initial system message
    try:
        session = model.sessions[0]
        session.conversation.item.create(
            llm.ChatMessage(
                role="system",
                content="""Welcome the user in both English and Vietnamese. After the initial greeting, 
                detect their language and respond only in that language. Focus on helping with tuberculosis questions.
                First message to user should be a greeting that works in both languages, like: "Hello! How can I help you today? Xin chào! Bạn có khỏe không?"
                """
            )
        )
        session.response.create()
        logger.info("Assistant initialized and ready")
    except Exception as e:
        logger.error(f"Error initializing assistant session: {e}")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))