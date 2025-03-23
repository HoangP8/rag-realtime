from __future__ import annotations
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Annotated

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
    @llm.ai_callable()
    async def process_pdf(
        self,
        query: Annotated[str, llm.TypeInfo(description="Query to search within the PDFs")],
        model_name: Annotated[str, llm.TypeInfo(description="The model name to use for embeddings")],
    ) -> str:
        """Find relevant medical info in documents and return an answer."""
        
        vectorstore = load_vectorstore(model_name)
        if not vectorstore:
            return "Failed to load the vector store."
        
        # get relevant documents
        docs = vectorstore.similarity_search(query, k=2)
        if not docs:
            return "No relevant information found."
        
        # prepare context and generate response
        context = "\n\n".join(doc.page_content for doc in docs)
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        prompt = f"""Context: {context}\n\nQuery: {query}\n\nAnswer based on the context:"""
        
        response = llm.invoke(prompt)
        return response.content


class MedicalAssistant(MultimodalAgent):
    """Custom assistant that adds RAG capabilities to voice interactions."""
    
    def __init__(self, model, fnc_ctx):
        super().__init__(model=model, fnc_ctx=fnc_ctx)
        self.model_name = "text-embedding-3-small"
        
        # medical terms that trigger RAG
        self.medical_terms = [
            "lao", "tuberculosis", "tb", "cough", "fever", 
            "đau", "sốt", "ho", "sụt cân", "khó thở"
        ]
    
    async def on_transcript(self, transcript, participant_identity=None):
        """Process user speech and trigger RAG when medical terms are detected."""
        if transcript and any(term in transcript.lower() for term in self.medical_terms):
            
            logger.info(f"Medical term detected in: '{transcript}', performing RAG")
            
            # perform RAG for medical queries
            result = await self.fnc_ctx.process_pdf(query=transcript, model_name=self.model_name)
            
            # add RAG context to the conversation
            session = self.model.sessions[0]
            session.conversation.item.create(
                llm.ChatMessage(
                    role="system",
                    content=f"Medical information: {result}"
                )
            )
        
        await super().on_transcript(transcript, participant_identity)


async def entrypoint(ctx: JobContext):
    """Main entry point for the medical assistant."""
    
    # initialize connection
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    await ctx.wait_for_participant()

    # function context
    fnc_ctx = AssistantFnc()
    
    # initialize voice model
    model = openai.realtime.RealtimeModel(
        instructions="""You are a medical assistant specializing in tuberculosis.
        
        IMPORTANT - LANGUAGE SELECTION:
        - If the user speaks in Vietnamese, respond ONLY in Vietnamese.
        - If the user speaks in English, respond ONLY in English.
        - Never mix languages in the same response.
        - Never translate your response to both languages.
        
        Keep responses concise and accurate. Provide medical information clearly and with confidence.""",
        voice="echo",
        temperature=0.7,
        modalities=["audio", "text"],
    )
    
    # custom assistant with RAG
    assistant = MedicalAssistant(model=model, fnc_ctx=fnc_ctx)
    assistant.start(ctx.room)

    # system message
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