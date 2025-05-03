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
AGENT_TYPE = "multimodal"

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
INSTRUCTIONS = """You are a HEALTHCARE ASSISTANT.
        Your ONLY purpose is to provide healthcare and medical information.
        You can ONLY work (understand, speak, and answer) in two languages: Vietnamese or English.
        Do NOT work on other languages, they are maybe noise from the user that you mistranslate.
        Be CONCISE and SMOOTH in your responses without hesitation, no need to repeat the same thing over and over again.
        IMPORTANT RULES:
        1. ONLY answer healthcare/medical questions. For ANY other topics, politely refuse and remind the user
            that you are a dedicated healthcare assistant, EVEN they ask about your health or other conditions.
        2. If the user speaks in Vietnamese, respond ONLY in Vietnamese.
        3. If the user speaks in English, respond ONLY in English.
        4. Be clear, accessible, and concise in your explanations.
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
    chat_ctx = llm.ChatContext().append(role="system", text=INSTRUCTIONS)
    
    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    
    # Set up voice pipeline agent
    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=deepgram.STT(
            model="nova-2-general",  # whisper-base, nova-2-general, whisper-medium
        ),
        llm=openai.LLM(model="gpt-4o"),
        tts=openai.TTS(
            model="tts-1",  # tts-1-hd
            voice="coral"),  # automatically recognize input language
        chat_ctx=chat_ctx,
    )
    
    # State for latency measurement and conversation tracking
    state = {
        "warmup_done": False, 
        "question_end": None,
        "current_question": None,
        "current_response": None
    }
    
    # Set up event handlers for latency tracking
    setup_latency_tracking(agent, state)
    
    # Connect and perform warm-up
    agent.start(room=ctx.room, participant=participant)
    await agent.say("Xin chào! Bạn có khỏe không? Hello! How are you?", allow_interruptions=True)
    await asyncio.sleep(1)
    state["warmup_done"] = True
    logger.info("Warmup completed (fallback after delay)")


async def multimodal_entrypoint(ctx: JobContext):
    # Connect to room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting multimodal assistant for {participant.identity}")
    
    # Real-time model configuration
    model = openai.realtime.RealtimeModel(
        model="gpt-4o-realtime-preview-2024-12-17",
        instructions=INSTRUCTIONS,
        modalities=["text", "audio"],
        voice="coral",
    )
    
    # Chat context and agent setup
    chat_ctx = llm.ChatContext().append(
        text="Greetings strictly with this text: `Xin chào! Bạn có khỏe không? Hello! How are you?`",
        role="system",
    )
    agent = MultimodalAgent(model=model, chat_ctx=chat_ctx)
    
    # State for latency measurement and conversation tracking
    state = {
        "warmup_done": False, 
        "question_end": None,
        "current_question": None,
        "current_response": None
    }
    
    # Set up event handlers for latency tracking
    setup_latency_tracking(agent, state)
    
    # Connect and perform warm-up
    agent.start(room=ctx.room, participant=participant)
    agent.generate_reply(on_duplicate="cancel_existing")
    await asyncio.sleep(1)
    state["warmup_done"] = True
    logger.info("Warmup completed (fallback after delay)")


def select_entrypoint():
    # Select the appropriate agent entrypoint based on configuration
    if AGENT_TYPE == "voice_pipeline":
        return voice_entrypoint
    elif AGENT_TYPE == "multimodal":
        return multimodal_entrypoint
    else:
        raise ValueError(f"Unknown agent type: {AGENT_TYPE}")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=select_entrypoint()))
