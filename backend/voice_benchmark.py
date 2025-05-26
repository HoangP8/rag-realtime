import logging
import os
import time
from dotenv import load_dotenv
from pathlib import Path
import asyncio
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai, deepgram, silero

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
AGENT_TYPE = "voice_pipeline"  # "voice_pipeline" or "multimodal"

# Set up logging
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)
log_dir = Path(__file__).parent / "logs" / "voice_benchmark_logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"latency_{AGENT_TYPE}.log"
file_handler = logging.FileHandler(log_file, encoding='utf-8')
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Agent instructions
INSTRUCTIONS = """
    You are a HEALTHCARE ASSISTANT.
    
    PURPOSE: 
    1. Provide medical and healthcare information.
    2. For NON-medical topics: Politely refuse and redirect to health topics
        
        IMPORTANT RULES:
        1. Respond in Vietnamese if user speaks Vietnamese
        2. Respond in English if user speaks English
    
    LANGUAGE AND STYLE:
       1. ONLY Vietnamese and English
        2. Respond in Vietnamese if user speaks Vietnamese.
        3. Respond in English if user speaks English.
        4. Style: Concise, clear, easy to understand     
    """

def setup_latency_tracking(agent, state):
    """Set up event handlers for latency tracking on the given agent."""
    
    @agent.on("agent_stopped_speaking")
    def on_agent_stopped_speaking():
        if not state["warmup_done"]:
            state["warmup_done"] = True
            logger.info("Warmup completed via event")
    
    @agent.on("user_started_speaking")
    def on_user_started_speaking():
        if state["warmup_done"]:
            logger.debug("User speech detected")
    
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
    
    @agent.on("user_speech_committed")
    def on_user_speech_committed(text):
        if state["warmup_done"]:
            logger.info(f"User Question: {text}")
    
    @agent.on("agent_speech_committed")
    def on_agent_speech_committed(text):
        if state["warmup_done"]:
            logger.info(f"AI Response: {text}")


async def voice_entrypoint(ctx: JobContext):
    # Initialize chat context
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=INSTRUCTIONS,
    )
    
    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice pipeline assistant for {participant.identity}")
    
    # Set up voice pipeline agent
    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=openai.STT(model="whisper-1", detect_language=True), # whisper-1, gpt-4o-mini-transcribe, gpt-4o-transcribe
        llm=openai.LLM(model="gpt-4o"), # gpt-4o-mini, gpt-4o
        tts=openai.TTS(
            model="gpt-4o-mini-tts", # tts-1, tts-1-hd
            voice="coral"),
        chat_ctx=initial_ctx,
    )
    
    # Initialize state for latency measurement and conversation tracking
    state = {
        "warmup_done": False, 
        "question_end": None,
        "current_question": None,
        "current_response": None
    }    
    setup_latency_tracking(agent, state)
    
    # Connect and warm-up
    agent.start(room=ctx.room, participant=participant)


async def multimodal_entrypoint(ctx: JobContext):
    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting multimodal assistant for {participant.identity}")
    
    # Agent setup
    model = openai.realtime.RealtimeModel(
        model="gpt-4o-realtime-preview",
        modalities=["text", "audio"],
        voice="coral",
        instructions=INSTRUCTIONS,
    )
    agent = MultimodalAgent(model=model)
    
    # Initialize state for latency measurement and conversation tracking
    state = {
        "warmup_done": False, 
        "question_end": None,
        "current_question": None,
        "current_response": None
    }    
    setup_latency_tracking(agent, state)
    
    # Connect and warm-up
    agent.start(room=ctx.room, participant=participant)

if __name__ == "__main__":
    
    # Select the agent entrypoint based on configuration
    entrypoints = {
        "voice_pipeline": voice_entrypoint,
        "multimodal": multimodal_entrypoint
    }

    if AGENT_TYPE not in entrypoints:
        raise ValueError(f"Unknown agent type: {AGENT_TYPE}")
        
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoints[AGENT_TYPE]))