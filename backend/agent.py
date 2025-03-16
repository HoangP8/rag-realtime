from __future__ import annotations

import logging
import os
from dotenv import load_dotenv
from pathlib import Path
import openai

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai
from livekit.plugins.rag.annoy import AnnoyIndex, IndexBuilder, Item
from openai import AsyncClient

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
api_key = os.getenv("OPENAI_API_KEY")
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

async def entrypoint(ctx: JobContext):
    logger.info("starting entrypoint")

    # Connect to the LiveKit room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()

    # Set up OpenAI async client for embeddings
    client = AsyncClient(api_key=api_key)

    async def get_embedding(text):
        """Generate an embedding for the given text using OpenAI's embedding model."""
        response = await client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    # Build the vector index with medical documents
    logger.info("setting up vector index")
    builder = IndexBuilder()
    medical_docs_path = Path(__file__).parent / "medical_docs"
    if medical_docs_path.exists():
        logger.info("loading medical documents into vector index")
        for doc_path in medical_docs_path.glob("*.txt"):
            with open(doc_path, "r") as f:
                text = f.read()
            vector = await get_embedding(text)
            item = Item(i=str(doc_path), vector=vector, userdata={"text": text})
            builder.add_item(item)
        index = builder.build()
    else:
        logger.warning("medical_docs directory not found")
        index = None

    # Define the retrieval function for RAG
    async def retrieve_documents(query: str) -> str:
        """Retrieve relevant medical documents based on the query."""
        if index is None:
            return "No medical documents available."
        query_vector = await get_embedding(query)
        similar_items = index.query(query_vector, top_k=3)
        context = "\n".join([item.userdata["text"] for item in similar_items])
        return context

    # Define the tool for OpenAI's function-calling
    tools = [
        {
            "type": "function",
            "function": {
                "name": "retrieve_documents",
                "description": "Retrieve relevant medical documents based on the query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    # Configure the model with tools
    model = openai.realtime.RealtimeModel(
        api_key=api_key,
        instructions=(
            "You are a helpful assistant specialized in medical queries. "
            "Use the retrieve_documents function to access relevant medical information before responding. "
            "Please start the conversation by asking the user how they are feeling."
        ),
        voice="echo",
        temperature=0.8,
        modalities=["audio", "text"],
        tools=tools,
    )

    # Start the multimodal agent
    assistant = MultimodalAgent(model=model)
    assistant.start(ctx.room)

    logger.info("starting agent")

    # Initialize the conversation
    session = model.sessions[0]
    session.conversation.item.create(
        llm.ChatMessage(
            role="system",
            content=(
                "You are a voice assistant created for medical purposes. "
                "You should speak fluent English and Vietnamese. "
                "Use short, concise responses without unpronounceable punctuation. "
                "Provide precise diagnoses and treatment suggestions, as medical advice is sensitive and critical. "
                "Always cite your sources when providing medical information."
            )
        )
    )
    session.response.create()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))