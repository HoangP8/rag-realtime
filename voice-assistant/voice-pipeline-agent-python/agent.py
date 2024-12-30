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

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

async def entrypoint(ctx: JobContext):
    logger.info("starting entrypoint")

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()

    model = openai.realtime.RealtimeModel(
        instructions="You are a helpful assistant that is specialized for medical queries. Please start the conversation with the user by asking them how they are feeling.",
        voice="echo",
        temperature=0.8,
        modalities=["audio", "text"],
    )
    assistant = MultimodalAgent(model=model)
    assistant.start(ctx.room)

    logger.info("starting agent")

    session = model.sessions[0]
    session.conversation.item.create(
      llm.ChatMessage(
        role="system",
        content="You are a voice assistant created for medical purposes. You should be able to speak fluent English and Vietnamese. You should use short and concise responses, and avoiding usage of unpronouncable punctuation. You should give precise diagnoses and treatment suggestions because medical advices are sensitive and very important."
      )
    )
    session.response.create()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))