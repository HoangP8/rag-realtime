import os
import soundfile as sf
from pydub import AudioSegment
from google.cloud import speech, texttospeech
from transformers import pipeline

def read_audio_file(file_path):
    # Convert audio to WAV if it's not in WAV format (Google API works best with WAV)
    audio = AudioSegment.from_file(file_path)
    wav_path = "temp_audio.wav"
    audio.export(wav_path, format="wav")

    return wav_path

def transcribe_audio(file_path, speech_client):
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
    response = speech_client.recognize(config=config, audio=audio)
    transcript = " ".join([result.alternatives[0].transcript for result in response.results])
    
    return transcript

def process_with_llm(transcript, llm, tokenizer, device):
    # Ensure the transcript is tokenized correctly
    input_ids = tokenizer.encode(transcript, return_tensors="pt").to(device)
    
    # Generate response using the language model
    response_ids = llm.generate(
        input_ids,
        max_length=128,
        num_return_sequences=1,
        no_repeat_ngram_size=2,
        do_sample=True,
        top_k=50,
        top_p=0.95,
        temperature=1.0,
    )
    
    response = tokenizer.decode(response_ids[0], skip_special_tokens=True)
    
    return response

def convert_text_to_speech(text, output_audio_file, tts_client, device):
    # Prepare the input for Google Text-to-Speech API
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Config
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", name="en-US-Wavenet-D"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Generate the speech
    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Write the output audio to a file
    with open(output_audio_file, "wb") as out:
        out.write(response.audio_content)
    
    print(f"Audio content written to file {output_audio_file}")