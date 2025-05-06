# 🎙️ RAG Voice Assistant project

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: Version 3.10 or higher ([Download Python](https://www.python.org/downloads/))
- **Node.js**: Version 18 or higher ([Download Node.js](https://nodejs.org/))
- **pnpm**: Install globally using npm: `npm install -g pnpm`
- **API Keys**: Obtain necessary API keys for:
  - OpenAI
  - LiveKit
  - Deepgram

Follow these steps to set up and run the project:

### 1. 📥 Clone the Repository

```sh
git clone https://github.com/your-repo-name.git 
cd your-repo-name
```

### 2. 📦 Install Dependencies

Install the required Python libraries:

```sh
pip install -r requirements.txt
```

### 3. 🔑 Configure Environment Variables

Set up your environment variables by copying the example file and adding your API keys:

1.  Copy `.env.example` to `.env.local` in the project root:
    ```sh
    cp .env.example .env.local
    ```
2.  Edit `.env.local` and provide the values for:
    - `LIVEKIT_URL`
    - `LIVEKIT_API_KEY`
    - `LIVEKIT_API_SECRET`
    - `OPENAI_API_KEY`
    - `DEEPGRAM_API_KEY` (required if using Deepgram)

### 4. ⚙️ Set Up the Backend

Navigate to the backend directory:

```sh
cd backend
```

**Vector Store Setup (for RAG):**

You need a vector store for Retrieval-Augmented Generation (RAG). Choose one of the following options:

-   Option 1: Generate Locally (you can modify `vectorstore.py` to use your own dataset)
    ```sh
    bash scripts/vectorstore.sh
    ```
-   Option 2: Download Pre-built Store for our dataset
    ```sh
    pip install gdown
    gdown --folder https://drive.google.com/drive/folders/1TlG4wPt0vxXO938jI3UMDO270ttn-VNk?usp=sharing
    ```

**Run the Backend Agent:**

Once the vector store is ready, start the backend agent:

```sh
python agent.py dev
```

**Evaluate the Backend Agent:**
To evaluate the backend agent's performance with RAG, follow these steps:

1. Connect to Hugging Face by running the following command in your terminal:

    ```sh
    huggingface-cli login
    ```
2. RAGAS Evaluation: We test the GPT-4o language model performance with RAG using the [RAGAS](https://github.com/explodinggradients/ragas) library. Run the evaluation script:

    ```sh
    bash scripts/text_benchmark.sh
    ```
    You can vary parameters such as chunk size, embedding models, and the number of relevant documents retrieved.
3. Latency Benchmarking: We also measure the latency of the Real-time model ([Multimodal](https://github.com/livekit-examples/multimodal-agent-python)) compared with a traditional STT-LLM-TTS pipeline ([VoicePipelineAgent](https://github.com/livekit-examples/voice-pipeline-agent-python)). Please set up the frontend (instructions in part 5) and run:
    ```sh
    python voice_benchmark.py dev
    ```


### 5. 🖥️ Set Up the Frontend (Web)

Open a new terminal window, navigate to the frontend directory, and install dependencies:

```sh
cd frontend
pnpm install
```

**Start the Development Server:**

```sh
pnpm dev
```

Your frontend application should now be running and accessible in your browser (typically at `http://localhost:3000`).