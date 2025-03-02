from __future__ import annotations

import logging
from dotenv import load_dotenv

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

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

async def entrypoint(ctx: JobContext):
    logger.info("starting entrypoint")

    # Load PDFs directly from your repo
    pdf_folder = "medical_pdfs"
    print(f"Loading PDFs from {pdf_folder}")
    loader = PyPDFDirectoryLoader(pdf_folder)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} PDFs into {len(chunks)} chunks")

    # Create in-memory vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    def retrieve_medical_info(query: str) -> str:
        docs = retriever.get_relevant_documents(query)
        print(f"Retrieved {len(docs)} documents for query: '{query}'")
        for i, doc in enumerate(docs, 1):
            print(f"Document {i}: {doc.page_content[:500]}...")
        return "\n\n".join([doc.page_content for doc in docs])

    retrieve_medical_info_func = llm.FunctionDefinition(
        name="retrieve_medical_info",
        description="Retrieve relevant medical information based on the user's query.",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        call=retrieve_medical_info
    )

    model = openai.realtime.RealtimeModel(
        instructions="You are a helpful assistant specialized in medical queries. Start by asking the user how they are feeling.",
        voice="echo",
        temperature=0.8,
        modalities=["audio", "text"],
        functions=[retrieve_medical_info_func]
    )

    assistant = MultimodalAgent(model=model)
    assistant.start(ctx.room)
    logger.info("starting agent")

    session = model.sessions[0]
    session.conversation.item.create(
        llm.ChatMessage(
            role="system",
            content="You are a voice assistant for medical purposes. Speak fluent English and Vietnamese. Use short, concise responses without unpronounceable punctuation. Provide precise diagnoses and treatment suggestions. Use 'retrieve_medical_info' for specific queries."
        )
    )
    session.response.create()

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))