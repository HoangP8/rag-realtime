# Medical Assistant System

We build a medical assistant using GPT-4o, LiveKit, Deepgram, and Google Cloud for voice and text interactions.

## Components

- **`voice-assistant/frontend`**: Frontend interface for the voice assistant (Node.js-based).
- **`voice-assistant/voice-pipeline-agent-python`**: Python backend for voice processing.
- **`website`**: Main website with frontend and backend components.

## Prerequisites

- Python 3.x
- Node.js and pnpm
- API keys for LiveKit, OpenAI, Deepgram, and Google Cloud

## Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-repo/Capstone-Medical-Assistant.git
   cd Capstone-Medical-Assistant

2. **Set Environment Variables**

    Each component requires specific environment variables. Please refer to the `README` in each subfolder for instructions on setting them up:

    - `voice-assistant/frontend/README.md`
    - `voice-assistant/voice-pipeline-agent-python/README.md`
    - `website/README.md`

3. **Install Dependencies**
    - For Python components: Install the required Python packages for the voice pipeline and website backend:
    ```
    pip install -r requirements.txt
    pip install -r voice-assistant/voice-pipeline-agent-python/requirements.txt
    ```

    - For the frontend: Navigate to the frontend directory and install `Node.js` dependencies using `pnpm`:
    ```
    cd voice-assistant/frontend
    pnpm install
    cd ../..
    ```

## Running the Project
To interact with the Medical Assistant, you need to run both the Voice Agent and the Frontend simultaneously. Use two separate terminals or tabs as follows:

1. Voice Agent
    Start the voice processing agent:
    ```
    cd voice-assistant/voice-pipeline-agent-python
    python agent.py dev
    ```

2. Frontend
    Run the frontend development server:
    ```
    cd voice-assistant/frontend
    pnpm dev
    ```

    Once running, open your browser and go to http://localhost:3000.