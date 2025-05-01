import logging
import os
import time
from dotenv import load_dotenv
from pathlib import Path

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai, deepgram, silero

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
AGENT_TYPE = os.getenv("AGENT_TYPE", "voice_pipeline")

# Set up logging
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"{AGENT_TYPE}.log"
file_handler = logging.FileHandler(log_file)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Agent instructions
INSTRUCTIONS = (
    "You are a friendly voice assistant created by LiveKit. Your interface with users will be voice. "
    "Use short, concise responses without unpronounceable punctuation."
)

async def voice_entrypoint(ctx: JobContext):
    # Initialize chat context
    chat_ctx = llm.ChatContext().append(role="system", text=INSTRUCTIONS)
    
    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for {participant.identity}")

    # Set up agent
    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o"),
        tts=openai.TTS(voice="coral"),
        chat_ctx=chat_ctx,
    )

    # State for latency measurement
    state = {"warmup_done": False, "question_end": None}

    @agent.on("agent_stopped_speaking")
    def on_agent_stopped_speaking():
        if not state["warmup_done"]:
            state["warmup_done"] = True
            logger.info("Warmup completed")

    @agent.on("user_stopped_speaking")
    def on_user_stopped_speaking():
        if state["warmup_done"] and state["question_end"] is None:
            state["question_end"] = time.time()
            logger.info("User asked a question")

    @agent.on("agent_started_speaking")
    def on_agent_started_speaking():
        if state["question_end"] is not None:
            latency = time.time() - state["question_end"]
            logger.info(f"Response latency: {latency:.3f} seconds")
            state["question_end"] = None

    # Start agent and send warmup message
    agent.start(ctx.room, participant)
    await agent.say("How are you feeling today?", allow_interruptions=True)

async def multimodal_entrypoint(ctx: JobContext):
    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting multimodal assistant for {participant.identity}")

    # Set up agent
    agent = MultimodalAgent(
        model=openai.RealtimeModel(model="gpt-4o-realtime-preview-2024-12-17"),
        instructions=INSTRUCTIONS,
    )

    # State for latency measurement
    state = {"warmup_done": False, "question_end": None}

    # Assuming similar event handlers
    @agent.on("agent_stopped_speaking")
    def on_agent_stopped_speaking():
        if not state["warmup_done"]:
            state["warmup_done"] = True
            logger.info("Warmup completed")

    @agent.on("user_stopped_speaking")
    def on_user_stopped_speaking():
        if state["warmup_done"] and state["question_end"] is None:
            state["question_end"] = time.time()
            logger.info("User asked a question")

    @agent.on("agent_started_speaking")
    def on_agent_started_speaking():
        if state["question_end"] is not None:
            latency = time.time() - state["question_end"]
            logger.info(f"Response latency: {latency:.3f} seconds")
            state["question_end"] = None

    # Connect and send warmup message
    await agent.connect(room=ctx.room)
    await agent.say("How are you feeling today?")

def select_entrypoint():
    if AGENT_TYPE == "voice_pipeline":
        return voice_entrypoint
    elif AGENT_TYPE == "multimodal":
        return multimodal_entrypoint
    else:
        raise ValueError(f"Unknown agent type: {AGENT_TYPE}")

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=select_entrypoint()))