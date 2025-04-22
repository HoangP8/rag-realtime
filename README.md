# 🎙️ Voice Assistant Project

## 📋 Prerequisites

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

-   Option 1: Generate Locally
    ```sh
    bash vectorstore.sh
    ```
-   Option 2: Download Pre-built Store
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

To evaluate the backend agent's performance with RAG, you can vary parameters such as chunk size, embedding models, and the number of relevant documents retrieved:

```sh
bash text_benchmark.sh
```

### 5. 🖥️ Set Up the Frontend

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