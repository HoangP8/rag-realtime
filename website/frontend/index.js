
let mediaRecorder;
let audioChunks = [];
let audioBlob;
let e2eMediaRecorder;
let e2eAudioChunks = [];
let e2eAudioBlob;

const e2eRecordButton = document.getElementById('e2eRecordButton');
const e2eStopButton = document.getElementById('e2eStopButton');
const e2eAudioPreview = document.getElementById('e2eAudioPreview');
const e2eAudioOutput = document.getElementById('e2eAudioOutput');
const e2eTimeTaken = document.getElementById('e2eTimeTaken');

const recordButton = document.getElementById('recordButton');
const stopButton = document.getElementById('stopButton');
const audioPreview = document.getElementById('audioPreview');

const transcriptSTT = document.getElementById('transcriptSTT');
const timeTakenSTT = document.getElementById('timeTakenSTT');
const getTranscriptButton = document.getElementById('getTranscriptButton');

const responseLLM = document.getElementById('responseLLM');
const timeTakenLLM = document.getElementById('timeTakenLLM');
const getLLMResponse = document.getElementById('getLLMResponse');

const audioResponseTTS = document.getElementById('audioResponseTTS');
const timeTakenTTS = document.getElementById('timeTakenTTS');
const getTTSResponse = document.getElementById('getTTSResponse');

const audioOutput = document.getElementById('audioOutput');
const fileInput = document.getElementById('fileInput');
const uploadButton = document.getElementById('uploadButton');
const timeTakenElement = document.getElementById('timeTaken');

recordButton.addEventListener('click', async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = event => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = () => {
        audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        audioChunks = [];

        // Set the audio playback source to the recorded audio
        const audioURL = URL.createObjectURL(audioBlob);
        audioPreview.src = audioURL;
    };

    mediaRecorder.start();
    recordButton.disabled = true;
    stopButton.disabled = false;
});

stopButton.addEventListener('click', () => {
    mediaRecorder.stop();
    recordButton.disabled = false;
    stopButton.disabled = true;
});

e2eRecordButton.addEventListener('click', async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    e2eMediaRecorder = new MediaRecorder(stream);

    e2eMediaRecorder.ondataavailable = event => {
        e2eAudioChunks.push(event.data);
    };

    e2eMediaRecorder.onstop = async () => {
        e2eAudioBlob = new Blob(e2eAudioChunks, { type: 'audio/webm' });
        e2eAudioChunks = [];

        // Set the audio playback source to the recorded audio
        const audioURL = URL.createObjectURL(e2eAudioBlob);
        e2eAudioPreview.src = audioURL;

        const startTime = performance.now();
        // Send the audioBlob to the backend
        const formData = new FormData();
        formData.append('audio', e2eAudioBlob, 'recording.webm');
        formData.append('STT_type', STT_type);
        formData.append('LLM_type', LLM_type);
        formData.append('TTS_type', TTS_type);
    
        const response = await fetch('https://machinelearning.vinunilegacy.com/api/upload', {
            method: 'POST',
            body: formData
        });
    
        const responseBlob = await response.blob();
    
        // Play the returned audio
        e2eAudioOutput.src = URL.createObjectURL(responseBlob);
        e2eAudioOutput.play();
    
        // Calc time takn
        const endTime = performance.now();
        const timeTaken = Math.round(endTime - startTime);
        e2eTimeTaken.textContent = timeTaken / 1000;
    };

    e2eMediaRecorder.start();
    e2eRecordButton.disabled = true;
    e2eStopButton.disabled = false;
});

e2eStopButton.addEventListener('click', async () => {
    e2eMediaRecorder.stop();
    e2eRecordButton.disabled = false;
    e2eStopButton.disabled = true;
});

getTranscriptButton.addEventListener('click', async () => {
    const startTime = performance.now();
    // Send the audioBlob to the backend
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('STT_type', STT_type);

    // Make the Deepgram API request
    const response = await fetch('https://machinelearning.vinunilegacy.com/api/transcribe', {
        method: 'POST',
        body: formData
    });

    const data = await response.json();

    const transcript = data["transcript"]
    transcriptSTT.textContent = transcript

    // Calc time takn
    const endTime = performance.now();
    const timeTaken = Math.round(endTime - startTime);
    timeTakenSTT.textContent = timeTaken / 1000;
});

getLLMResponse.addEventListener('click', async () => {
    const startTime = performance.now();

    // Make the Deepgram API request
    const response = await fetch('https://machinelearning.vinunilegacy.com/api/llmresponse', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json' // Indicate JSON content type
        },
        body: JSON.stringify({"transcript": transcriptSTT.textContent, "LLM_type": LLM_type})
    });

    const data = await response.json();

    const llmresponse = data["response"]
    responseLLM.textContent = llmresponse

    // Calc time takn
    const endTime = performance.now();
    const timeTaken = Math.round(endTime - startTime);
    timeTakenLLM.textContent = timeTaken / 1000;
});

getTTSResponse.addEventListener('click', async () => {
    const startTime = performance.now();

    // Make the Deepgram API request
    const response = await fetch('https://machinelearning.vinunilegacy.com/api/voiceresponse', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json' // Indicate JSON content type
        },
        body: JSON.stringify({"response": responseLLM.textContent, "TTS_type": TTS_type})
    });

    const responseBlob = await response.blob();

    const audioURL = URL.createObjectURL(responseBlob);
    audioResponseTTS.src = audioURL;
    audioResponseTTS.play();

    // Calc time takn
    const endTime = performance.now();
    const timeTaken = Math.round(endTime - startTime);
    timeTakenTTS.textContent = timeTaken / 1000;
});