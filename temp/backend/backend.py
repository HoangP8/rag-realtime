from flask import Flask, request, send_file, jsonify
from helpers import read_audio_file, transcribe_audio, process_with_llm, convert_text_to_speech, inference
from loaders import load_llm_model, load_stt_model, load_tts_model
import ffmpeg

# Framework Settings
input_audio_path = "/home/LENOVO/capstone/backend/input_audio/input_audio.wav"
fixed_audio_path = "/home/LENOVO/capstone/backend/input_audio/fixed_audio.wav"
output_audio_path = "/home/LENOVO/capstone/backend/output_audio/output_audio.wav"

STT_model = load_stt_model("Google")
LLM_model, LLM_tokenizer = load_llm_model("gpt2")
TTS_model = load_tts_model("Google")

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
    ffmpeg.input(input_audio_path).output(fixed_audio_path, format='wav').run(overwrite_output=True)
    inference(fixed_audio_path, output_audio_path, STT_type, LLM_type, TTS_type, STT_model, LLM_model, TTS_model, LLM_tokenizer)
    return send_file(output_audio_path, mimetype='audio/wav')


@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return "No audio file uploaded", 400

    audio = request.files['audio']
    STT_type = request.form.get('STT_type')
    
    audio.save(input_audio_path)
    ffmpeg.input(input_audio_path).output(fixed_audio_path, format='wav').run(overwrite_output=True)
    transcript = transcribe_audio(fixed_audio_path, STT_type, STT_model)
    return jsonify({"transcript": transcript})

@app.route('/llmresponse', methods=['POST'])
def llmresponse():
    data = request.get_json()
    transcript = data['transcript']
    LLM_type = data['LLM_type']

    response = process_with_llm(transcript, LLM_type, LLM_model, LLM_tokenizer)
    return jsonify({"response": response})

@app.route('/voiceresponse', methods=['POST'])
def voiceresponse():
    data = request.get_json()
    response = data['response']
    TTS_type = data['TTS_type']

    convert_text_to_speech(response, output_audio_path, TTS_type, TTS_model)
    return send_file(output_audio_path, mimetype='audio/wav')

if __name__ == '__main__':
    app.run(port=5000, debug=True)
