from __future__ import annotations
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Annotated
import re

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.multimodal import MultimodalAgent
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


class AssistantFnc(llm.FunctionContext):
    def __init__(self, vectorstore):
        super().__init__()
        self.vectorstore = vectorstore

    @llm.ai_callable()
    async def process_pdf(
        self,
        query: Annotated[str, llm.TypeInfo(description="Query to search within the PDFs")],
    ) -> str:
        """Find relevant medical info in documents and return an answer."""
        if not self.vectorstore:
            return "Failed to load the vector store."
        
        # Get relevant documents
        docs = self.vectorstore.similarity_search(query, k=2)
        if not docs:
            return "No relevant information found."
        
        # Prepare context and generate response
        context = "\n\n".join(doc.page_content for doc in docs)
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        prompt = f"""Context: {context}\n\nQuery: {query}\n\nAnswer based on the context in the same language as the query:"""
        
        try:
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm sorry, there was an error retrieving the medical information."


class MedicalAssistant(MultimodalAgent):
    """Custom assistant that adds RAG capabilities to voice interactions."""
    
    def __init__(self, model, fnc_ctx):
        super().__init__(model=model, fnc_ctx=fnc_ctx)
        # Medical terms that trigger RAG
        self.medical_terms = [
            "lao", "tuberculosis", "tb", "cough", "fever",
            "đau", "sốt", "ho", "sụt cân", "khó thở"
        ]
        self.conversation_history = []
    
    def extract_relevant_sentence(self, transcript):
        """Extract the sentence containing a medical term."""
        
        sentences = re.split(r'(?<=[.?!])\s+', transcript)
        for sentence in sentences:
            if any(term.lower() in sentence.lower() for term in self.medical_terms):
                return sentence
        return transcript  # Fallback to full transcript if no specific sentence found

    async def on_transcript(self, transcript, participant_identity=None):
        """Process user speech and trigger RAG when medical terms are detected."""
        
        if transcript:
            # Log user message and add to conversation history
            logger.info(f"User: {transcript}")
            self.conversation_history.append({"role": "user", "content": transcript})
            
            # Check for medical to RAG
            if any(term in transcript.lower() for term in self.medical_terms):
                relevant_query = self.extract_relevant_sentence(transcript)
                logger.info(f"Medical term detected in: '{transcript}', performing RAG with query: '{relevant_query}'")
                result = await self.fnc_ctx.process_pdf(query=relevant_query)
                
                if result:
                    rag_info = f"📚 Medical information: {result}"
                    logger.info(f"System: {rag_info}")
                    self.conversation_history.append({"role": "system", "content": rag_info})
                    
                    # Add to the conversation in the model
                    session = self.model.sessions[0]
                    session.conversation.item.create(
                        llm.ChatMessage(
                            role="system",
                            content=rag_info
                        )
                    )
        await super().on_transcript(transcript, participant_identity)

    async def on_message(self, message, participant_identity=None):
        """Capture assistant's responses."""
        
        if message and message.role == "assistant":
            logger.info(f"Assistant: {message.content}")
            self.conversation_history.append({"role": "assistant", "content": message.content})
        await super().on_message(message, participant_identity)

    def get_conversation_history(self):
        """Return the conversation history for the frontend."""
        
        return self.conversation_history


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

    # Function context
    fnc_ctx = AssistantFnc(vectorstore=vectorstore)
    
    # Initialize voice model
    model = openai.realtime.RealtimeModel(
        instructions="""You are a medical assistant specializing in tuberculosis.
        IMPORTANT - LANGUAGE SELECTION:
        - If the user speaks in Vietnamese, respond ONLY in Vietnamese.
        - If the user speaks in English, respond ONLY in English.
        - Never mix languages in the same response.
        - Never translate your response to both languages.
        Keep responses concise and accurate. Provide medical information clearly and with confidence.""",
        voice="coral",
        temperature=0.7,
        modalities=["audio", "text"],
    )
    
    # Custom assistant with RAG
    assistant = MedicalAssistant(model=model, fnc_ctx=fnc_ctx)
    assistant.start(ctx.room)

    ctx.assistant = assistant

    # System message
    session = model.sessions[0]
    session.conversation.item.create(
        llm.ChatMessage(
            role="system",
            content="""You are a medical voice assistant specializing in tuberculosis, be concise and straightforward.
            RULE: Respond ONLY in the language the user is using. Do not provide translations.
            - If user speaks Vietnamese → respond in Vietnamese
            - If user speaks English → respond in English
            First message to user should be a greeting that works in both languages, like: "Hello! How can I help you today? Xin chào! Bạn có khỏe không?"
            After the greeting, strictly stick to the user's language.
            """
        )
    )
    session.response.create()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))