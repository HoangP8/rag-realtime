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

First, install the Python dependencies:

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

Create the vector store from your medical PDF data:
```sh
python pdf_to_faiss.py
```

Run the backend agent:
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

## 🧩 Project Structure

- `/backend`: Python backend with RAG capabilities and LiveKit integration
  - `agent.py`: Main voice assistant agent
  - `pdf_to_faiss.py`: Script to generate vector database from medical PDFs
  - `/faiss`: Directory containing the vector stores

- `/frontend`: Next.js frontend application
  - `/app`: Next.js app directory
  - `/components`: React components