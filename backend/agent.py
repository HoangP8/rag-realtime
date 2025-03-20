from __future__ import annotations
import logging
import os
import pickle
from dotenv import load_dotenv
from pathlib import Path
from typing import Annotated
import numpy as np
import faiss
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

# Load FAISS index and text chunks from pre-existing files
def load_vectorstore(index_path: str, texts_path: str):
    """Load FAISS index and text chunks from disk."""
    if not os.path.exists(index_path) or not os.path.exists(texts_path):
        raise FileNotFoundError("FAISS index or texts file not found.")
    
    faiss_index = faiss.read_index(index_path)
    with open(texts_path, "rb") as f:
        texts = pickle.load(f)
    
    return faiss_index, texts

# Function Context with RAG for PDF processing
class AssistantFnc(llm.FunctionContext):
    
    @llm.ai_callable()
    async def process_pdf(
        self,
        query: Annotated[str, llm.TypeInfo(description="Query to search within the PDFs")],
    ) -> str:
        """Query FAISS index and return relevant text."""
        index_path = "faiss_index.bin"
        texts_path = "texts.pkl"
        
        faiss_index, texts = load_vectorstore(index_path, texts_path)
        query_embedding_response = await openai.create_embeddings(input=[query], model="text-embedding-ada-002")
        query_embedding = np.array(query_embedding_response[0].embedding).astype('float32')

        
        # Search for the most relevant chunk
        D, I = faiss_index.search(query_embedding.reshape(1, -1), k=1)
        relevant_text = texts[I[0][0]]
        
        # Generate a response based on the relevant context
        response = openai.realtime.RealtimeModel.generate(
            prompt=f"Context: {relevant_text}\n\nUser's Query: {query}\nAnswer:",
            max_tokens=150
        )
        return response['text']

# Main Worker EntryPoint
async def entrypoint(ctx: JobContext):
    logger.info("starting entrypoint")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()

    fnc_ctx = AssistantFnc()

    query = "What is the main topic of these documents?"
    
    # Call the process_pdf function with the query
    result = await fnc_ctx.process_pdf(query=query)
    logger.info(f"Generated response: {result}")

    # Initialize and start the assistant
    model = openai.realtime.RealtimeModel(
        instructions="You are a helpful assistant that is specialized for medical queries. Please start the conversation with the user by asking them how they are feeling.",
        voice="echo",
        temperature=0.8,
        modalities=["audio", "text"],
    )
    assistant = MultimodalAgent(model=model, fnc_ctx=fnc_ctx)
    assistant.start(ctx.room)

    logger.info("starting agent")

    session = model.sessions[0]
    session.conversation.item.create(
        llm.ChatMessage(
            role="system",
            content="You are a voice assistant created for medical purposes. You should be able to speak fluent English and Vietnamese. You should use short and concise responses, avoiding unpronounceable punctuation. You should give precise diagnoses and treatment suggestions because medical advice is sensitive and very important."
        )
    )
    session.response.create()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))