import soundfile as sf
from pydub import AudioSegment
from transformers import pipeline
from google.cloud import speech, texttospeech
import torch

from deepgram import (
    PrerecordedOptions,
    FileSource,
)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def read_audio_file(file_path):
    # Convert audio to WAV if it's not in WAV format (Google API works best with WAV)
    audio = AudioSegment.from_file(file_path)
    wav_path = "temp_audio.wav"
    audio.export(wav_path, format="wav")

    return wav_path

def transcribe_audio(file_path, STT_type, STT_model):
    if (STT_type == "Google"):
        # Read audio data
        with sf.SoundFile(file_path) as audio_file:
            audio_content = audio_file.read(dtype="int16").tobytes()
            sample_rate = audio_file.samplerate

        # Prepare the audio for Google Speech API
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code="en-US"
        )

        # Perform transcription
        response = STT_model.recognize(config=config, audio=audio)
        transcript = " ".join([result.alternatives[0].transcript for result in response.results])
        
        return transcript
    elif (STT_type == "Deepgram"):
        with open(file_path, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
        )
        response = STT_model.listen.prerecorded.v("1").transcribe_file(payload, options)
        transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
        return transcript
    return 404

def process_with_llm(transcript, LLM_type, LLM_model, LLM_tokenizer):
    if (LLM_type == "gpt2"):
        transcript_tokens = LLM_tokenizer.encode(transcript, return_tensors='pt').to(device)
        response = LLM_model.generate(
            transcript_tokens,
            max_length=50,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=1.0,
        )    
        processed_text = LLM_tokenizer.decode(response[0], skip_special_tokens=True)
        return processed_text
    
def convert_text_to_speech(text, output_audio_file, TTS_type, TTS_model):
    if TTS_type == "Google":
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Config
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", name="en-US-Wavenet-D"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Generate the speech
        response = TTS_model.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Write the output audio to a file
        with open(output_audio_file, "wb") as out:
            out.write(response.audio_content)
        
        print(f"Audio content written to file {output_audio_file}")
        return response


def inference(input_audio_file, output_audio_file, STT_type, LLM_type, TTS_type, STT_model, LLM_model, TTS_model, LLM_tokenizer):
    transcript = transcribe_audio(input_audio_file, STT_type, STT_model)
    processed_text = process_with_llm(transcript, LLM_type, LLM_model, LLM_tokenizer)
    return convert_text_to_speech(processed_text, output_audio_file, TTS_type, TTS_model)