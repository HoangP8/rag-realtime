from __future__ import annotations
import os
import logging
import asyncio
import openai
import sys
from pathlib import Path
from dotenv import load_dotenv
from functools import partial
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai as livekit_openai

# load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("voice-agent")
FAISS_PATH = os.path.join(os.path.dirname(__file__), "..", "rag", "faiss")

# transcribe audio using Whisper
async def transcribe_audio(audio_data):
    try:
        client = openai.AsyncOpenAI()
        # Note: audio_data should be bytes; adjust for real audio input as needed
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_data,
            response_format="text"
        )
        return response
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return None
    
# Main voice agent function
async def voice_agent(ctx: JobContext, embedding_model: str, model_type: str):
    logger.info("Starting voice agent")

    # connect to the LiveKit room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info("Connected to LiveKit room")

    # Wait for a participant to join
    participant = await ctx.wait_for_participant()
    if not participant:
        logger.warning("No participant joined.")
        return
    logger.info(f"Participant {participant.identity} joined")

    # initialize real-time model
    model = livekit_openai.realtime.RealtimeModel(
        instructions="You are a helpful assistant specialized in medical queries. Start the conversation by asking the user how they are feeling.",
        voice="echo",
        temperature=0.8,
        modalities=["audio", "text"],
    )

    # FAISS for RAG
    faiss_path = os.path.join(FAISS_PATH, embedding_model.replace('/', '_'))
    if model_type == "openai":
        embedding_function = OpenAIEmbeddings(model=embedding_model)
    elif model_type == "huggingface":
        embedding_function = HuggingFaceEmbeddings(model_name=embedding_model)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    faiss_db = FAISS.load_local(faiss_path, embedding_function, allow_dangerous_deserialization=True)
    logger.info(f"Loaded FAISS database at {faiss_path}")

    # multimodal agent
    assistant = MultimodalAgent(model=model)
    assistant.start(ctx.room)
    logger.info("Multimodal agent started")

    # Handle user audio input
    async def handle_user_input(audio_track: rtc.AudioTrack):
        logger.info("Handling user audio input")
        async for audio_frame in audio_track:
            # Transcribe audio to text
            transcribed_text = await transcribe_audio(audio_frame.data)
            if not transcribed_text:
                logger.warning("No transcription result")
                continue

            logger.info(f"User said: {transcribed_text}")

            # Retrieve relevant documents from FAISS
            results = faiss_db.similarity_search(transcribed_text, k=3)
            context = "\n".join([doc.page_content for doc in results])
            logger.info(f"Retrieved context: {context[:100]}...")  # Log first 100 chars

            # Augment the prompt with retrieved context
            augmented_prompt = (
                f"Based on the following medical documents:\n{context}\n\n"
                f"Answer the question: {transcribed_text}"
            )

            # Add the augmented prompt to the model's session
            session = model.sessions[0]
            session.conversation.item.create(
                {"role": "user", "content": augmented_prompt}
            )

            # Generate and stream the response
            response_stream = session.response.create()
            async for chunk in response_stream:
                if chunk.get("audio"):
                    await ctx.room.local_participant.publish_audio(chunk["audio"])
                    logger.info("Published audio response")
                elif chunk.get("text"):
                    logger.info(f"Assistant text response: {chunk['text']}")

    # handle track publication
    def on_track_published(publication, participant):
        if publication.kind == rtc.TrackKind.KIND_AUDIO:
            audio_track = publication.track
            if audio_track:
                logger.info("Subscribed to participant's audio track")
                asyncio.create_task(handle_user_input(audio_track))
            else:
                logger.warning("Audio track not available yet")

    # Attach the event listener to the participant
    participant.on_track_published = on_track_published

    # Check for existing audio tracks
    audio_publications = [pub for pub in participant.get_tracks() if pub.kind == rtc.TrackKind.KIND_AUDIO]
    if audio_publications and audio_publications[0].track:
        audio_track = audio_publications[0].track
        logger.info("Subscribed to existing audio track")
        asyncio.create_task(handle_user_input(audio_track))
    else:
        logger.warning("No audio track available from participant initially")

    # Keep the agent running
    while True:
        await asyncio.sleep(1)

# Entrypoint function defined at module level
async def entrypoint(ctx: JobContext, embedding_model: str, model_type: str):
    await voice_agent(ctx, embedding_model=embedding_model, model_type=model_type)


if __name__ == "__main__":
    # Parse custom arguments manually without interfering with cli.run_app
    embedding_model = "text-embedding-3-small" 
    model_type = "openai"  
    args = sys.argv[1:]  
    
    # manual parsing for --embedding-model and --model-type
    i = 0
    while i < len(args):
        if args[i] == "--embedding-model" and i + 1 < len(args):
            i += 2
        elif args[i] == "--model-type" and i + 1 < len(args):
            model_type = args[i + 1]
            i += 2
        else:
            i += 1

    # Use functools.partial to bind arguments to entrypoint
    entrypoint_with_args = partial(entrypoint, embedding_model=embedding_model, model_type=model_type)

    # Create WorkerOptions with the bound entrypoint
    worker_options = WorkerOptions(
        entrypoint_fnc=entrypoint_with_args,
        ws_url=os.getenv("LIVEKIT_URL"),
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET")
    )
    cli.run_app(worker_options)