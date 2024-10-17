import os
from dotenv import load_dotenv
from flask import Flask, request, send_file, jsonify, Response
from helpers import read_audio_file, transcribe_audio, process_with_llm, convert_text_to_speech, inference, streaming_process_with_llm
from loaders import load_llm_model, load_stt_model, load_tts_model

# Framework Settings

load_dotenv()
INPUT_AUDIO_DIR = os.getenv("INPUT_AUDIO_DIR")
OUTPUT_AUDIO_DIR = os.getenv("OUTPUT_AUDIO_DIR")

input_audio_path = INPUT_AUDIO_DIR + "/input_audio.wav"
output_audio_path = OUTPUT_AUDIO_DIR + "/output_audio.wav"

STT_model = load_stt_model("Google")
LLM_model, LLM_tokenizer = load_llm_model("gpt2")
TTS_model = load_tts_model("Google")

STT_type = "Google"
LLM_type = "gpt2"
TTS_type = "Google"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "recordings/"

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "API is working!"})

@app.route('/upload', methods=['POST'])
def upload():
    if 'audio' not in request.files:
        return "No audio file uploaded", 400

    audio = request.files['audio']
    STT_type = request.form.get('STT_type')
    LLM_type = request.form.get('LLM_type')
    TTS_type = request.form.get('TTS_type')
    
    audio.save(input_audio_path)
    inference(read_audio_file(input_audio_path), output_audio_path, STT_type, LLM_type, TTS_type, STT_model, LLM_model, TTS_model, LLM_tokenizer)
    return send_file(output_audio_path, mimetype='audio/wav')

@app.route('/setting', methods=['POST'])
def saveSetting():
    global STT_model, LLM_model, TTS_model, LLM_tokenizer
    global STT_type, LLM_type, TTS_type

    data = request.get_json()
    STT_type = data['STT_type']
    LLM_type = data['LLM_type']
    TTS_type = data['TTS_type']

    STT_model = load_stt_model(STT_type)
    LLM_model, LLM_tokenizer = load_llm_model(LLM_type)
    TTS_model = load_tts_model(TTS_type)
    return "success", 200

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return "No audio file uploaded", 400

    audio = request.files['audio']
    STT_type = request.form.get('STT_type')
    
    audio.save(input_audio_path)
    transcript = transcribe_audio(read_audio_file(input_audio_path), STT_type, STT_model)
    return jsonify({"transcript": transcript})

@app.route('/llmresponse', methods=['POST'])
def llmresponse():
    data = request.get_json()
    transcript = data['transcript']
    LLM_type = data['LLM_type']

    response = process_with_llm(transcript, LLM_type, LLM_model, LLM_tokenizer)
    return jsonify({"response": response})

@app.route('/llmresponse/stream', methods=['POST'])
def llmStreamingResponse():
    data = request.get_json()
    transcript = data['transcript']
    LLM_type = data['LLM_type']

    response = streaming_process_with_llm(transcript, LLM_type, LLM_model)
    return Response(response, content_type='text/plain')

@app.route('/voiceresponse', methods=['POST'])
def voiceresponse():
    data = request.get_json()
    response = data['response']
    TTS_type = data['TTS_type']

    convert_text_to_speech(response, output_audio_path, TTS_type, TTS_model)
    return send_file(output_audio_path, mimetype='audio/wav')

if __name__ == '__main__':
    app.run(port=5000, debug=True)
