import json
import os
import torch
from transformers import GPT2Tokenizer, GPT2Model, AutoTokenizer, AutoModelForCausalLM, AutoModelForMaskedLM
from google.cloud import speech, texttospeech
from helpers import read_audio_file, transcribe_audio, process_with_llm, convert_text_to_speech
import torch    
import time

def safe_json_read(filepath):
    """Safely reads a JSON file, returning None if the file is empty or invalid."""
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def initialize_model(model_id, device):
    """Helper to initialize tokenizer and model based on the model ID"""
    if model_id == 'gpt2':
        tokenizer = AutoTokenizer.from_pretrained('gpt2')
        model = AutoModelForCausalLM.from_pretrained('gpt2', torch_dtype=torch.float16)
    elif model_id == 'phi-2':
        tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-2", trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained("microsoft/phi-2", torch_dtype=torch.float16, trust_remote_code=True)
    elif model_id == 'StableMed':
        tokenizer = AutoTokenizer.from_pretrained("cxllin/StableMed-3b")
        model = AutoModelForCausalLM.from_pretrained("stabilityai/stablelm-3b-4e1t", torch_dtype=torch.float16)
    elif model_id == 'H2O':
        tokenizer = AutoTokenizer.from_pretrained("h2oai/h2o-danube-1.8b-base")
        model = AutoModelForCausalLM.from_pretrained("h2oai/h2o-danube-1.8b-base", torch_dtype=torch.float16)
    elif model_id == 'Llama3':
        tokenizer = AutoTokenizer.from_pretrained("aaditya/OpenBioLLM-Llama3-8B")    
        model = AutoModelForCausalLM.from_pretrained("aaditya/OpenBioLLM-Llama3-8B", torch_dtype=torch.float16)
    elif model_id == 'Camel':
        tokenizer = AutoTokenizer.from_pretrained("Writer/camel-5b-hf")
        model = AutoModelForCausalLM.from_pretrained("Writer/camel-5b-hf", torch_dtype=torch.float16)
    else:
        raise ValueError("Invalid model ID")
    
    model.to(device)
    return tokenizer, model

def process_task(device, args):
    """Process the task, perform transcription and text-to-speech, and log results."""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = args.credentials_file
    speech_client = speech.SpeechClient()
    tts_client = texttospeech.TextToSpeechClient()

    tokenizer, model = initialize_model(args.model_id, device)

    primary_device = torch.device(f"cuda:{device}" if torch.cuda.is_available() else "cpu")

    start_time = time.time()

    transcript = transcribe_audio(args.input_file, speech_client)    
    processed_text = process_with_llm(transcript, model, tokenizer, primary_device)

    output_audio_path = f"latency_test/output_audio/output_{args.model_id}.wav"
    convert_text_to_speech(processed_text, output_audio_path, tts_client, primary_device)
    end_time = time.time()

    results = {
        "model_id": args.model_id,
        "latency_seconds": end_time - start_time,
        "model_params": model.num_parameters(),
        "processed_text": processed_text 
    }

    log_path = "latency_test/performance_log_one_gpu_A5000.json"

    data = safe_json_read(log_path)
    if data is None:
        data = [] 

    data.append(results)

    with open(log_path, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Processed on {device}, output at {output_audio_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Speech to speech processing.")
    parser.add_argument("--credentials_file", type=str, default="serviceAcc.json", help="Google API credentials file")
    parser.add_argument("--input_file", type=str, default="record_google.wav", help="Input audio file path")
    parser.add_argument("--model_id", type=str, default="AdaptLLM", help="Hugging Face model ID")
    parser.add_argument("--device", type=int, default=0, help="GPU device number")
    args = parser.parse_args()

    process_task(args.device, args)