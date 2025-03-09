from __future__ import annotations
import os
import logging
import asyncio
import openai
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai as livekit_openai

# Load environment variables and configure logging
load_dotenv(dotenv_path=".env.local")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

# Function to transcribe audio using Whisper
async def transcribe_audio(audio_data):
    try:
        client = openai.AsyncOpenAI()
        # Note: audio_data should be bytes; adjust for real audio input as needed
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_data,  # Placeholder; replace with actual audio handling
            response_format="text"
        )
        return response
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return None

# Main voice agent function
async def voice_agent(ctx: JobContext):
    logger.info("Starting voice agent")

    # Connect to the LiveKit room with audio-only subscription
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info("Connected to LiveKit room")

    # Wait for a participant to join
    participant = await ctx.wait_for_participant()
    if not participant:
        logger.warning("No participant joined.")
        return

    logger.info(f"Participant {participant.identity} joined")

    # Initialize the real-time model
    model = livekit_openai.realtime.RealtimeModel(
        instructions="You are a helpful assistant specialized in medical queries. Start the conversation by asking the user how they are feeling.",
        voice="echo",
        temperature=0.8,
        modalities=["audio", "text"],
    )

    # Set up Chroma for RAG
    embedding_model = "text-embedding-3-small"
    chroma_path = f"chroma/{embedding_model}"
    embedding_function = OpenAIEmbeddings(model=embedding_model)
    chroma_db = Chroma(persist_directory=chroma_path, embedding_function=embedding_function)
    logger.info(f"Loaded Chroma database at {chroma_path}")

    # Start the multimodal agent
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

            # Retrieve relevant documents from Chroma
            results = chroma_db.similarity_search(transcribed_text, k=3)
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

    # Function to handle track publication
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

if __name__ == "__main__":
    # Wrap the voice_agent function in WorkerOptions
    worker_options = WorkerOptions(entrypoint_fnc=voice_agent)
    cli.run_app(worker_options)