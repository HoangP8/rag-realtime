# Voice Assistant Project

A full-stack voice assistant application powered by [LiveKit](https://livekit.io/), combining a Python backend and a Next.js frontend.

## 🚀 Quick Start

### 1️⃣ Clone the Repository

```sh
git clone https://github.com/your-repo-name.git
cd your-repo-name
```

### 2️⃣ Setup Backend
Navigate to the backend folder and create a virtual environment:

```
cd backend
pip install -r ../requirements.txt
```

Copy and rename `.env.example` to `.env.local` and filling in the required values:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `OPENAI_API_KEY`
- `DEEPGRAM_API_KEY`

Run the backend agent:
```
python agent.py dev
```

### 3️⃣ Setup Frontend
Navigate to the frontend folder and install dependencies:
```
cd frontend
pnpm install
pnpm dev
```
