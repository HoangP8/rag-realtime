import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM
from google.cloud import speech, texttospeech
from deepgram import DeepgramClient
import torch

# Get constants
load_dotenv()
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

def load_stt_model(STT_type):
    if STT_type == "Google":
        return speech.SpeechClient()
    elif STT_type == "Deepgram":
        return DeepgramClient(DEEPGRAM_API_KEY)
    
def load_llm_model(LLM_type):
    if LLM_type == 'gpt2':
        tokenizer = AutoTokenizer.from_pretrained('gpt2')
        model = AutoModelForCausalLM.from_pretrained('gpt2', torch_dtype=torch.float16).to(device)
        return model, tokenizer

def load_tts_model(TTS_type):
    if TTS_type == "Google":
        return texttospeech.TextToSpeechClient()