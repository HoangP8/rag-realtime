import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM
from google.cloud import speech, texttospeech
from deepgram import DeepgramClient
import openai
import torch

# Get constants
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
OPENAI_PROJ_ID = os.getenv("OPENAI_PROJ_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

def load_stt_model(STT_type):
    if STT_type == "Google":
        return speech.SpeechClient()
    elif STT_type == "Deepgram":
        return DeepgramClient(DEEPGRAM_API_KEY)
    
def load_llm_model(LLM_type):
    if LLM_type == 'gpt2':
        tokenizer = AutoTokenizer.from_pretrained('gpt2')
        model = AutoModelForCausalLM.from_pretrained('gpt2', torch_dtype=torch.float16).to(device)
        tokenizer.pad_token_id = tokenizer.eos_token_id
        return model, tokenizer
    elif LLM_type == 'gpt-4o-mini': 
        client = openai.OpenAI()
        return client, None
        
def load_tts_model(TTS_type):
    if TTS_type == "Google":
        return texttospeech.TextToSpeechClient()