# Voice Assistant Project


## 📋 Prerequisites
Before starting, ensure you have the following installed:

- **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 18+**: [Download Node.js](https://nodejs.org/)
- **pnpm**: Install with `npm install -g pnpm`
- **API Keys** for:
  - OpenAI
  - LiveKit
  - Deepgram

## 🚀 Quick Start

### 1️⃣ Clone the Repository

```sh
git clone https://github.com/your-repo-name.git
cd your-repo-name
```

### 2️⃣ Install Dependencies

First, install the required libraries:

```sh
pip install -r requirements.txt
```

### 3️⃣ Setup Environment

Create and configure your environment variables:

1. Copy `.env.example` to `.env.local` in the project root:
   ```sh
   cp .env.example .env.local
   ```

2. Open `.env.local` and add the required API keys:
   - `LIVEKIT_URL`
   - `LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET`
   - `OPENAI_API_KEY`
   - `DEEPGRAM_API_KEY` (if using Deepgram)

### 4️⃣ Setup Backend

Navigate to the backend folder:

```sh
cd backend
```

To have the vectorstore to RAG, you can choose one of two following ways:
- Option 1: Generate the vector store locally:
  ```sh
  bash vectorstore.sh
  ```
- Option 2: Download pre-built vector store:
  ```sh
  pip install gdown
  gdown --folder https://drive.google.com/drive/folders/1TlG4wPt0vxXO938jI3UMDO270ttn-VNk?usp=sharing
  ```

After having vectorstore, run the backend agent with RAG:
```sh
python agent.py dev
```

### 5️⃣ Setup Frontend

Open a new terminal, navigate to the frontend folder, and install dependencies:

```sh
cd frontend
pnpm install
```

Start the development server:
```sh
pnpm dev
```