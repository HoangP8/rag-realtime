FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Create entrypoint script
RUN echo '#!/bin/bash\n\
# Start the worker in the background\n\
echo "Starting LiveKit Agents worker..."\n\
python -m agent.worker &\n\
WORKER_PID=$!\n\
\n\
# Start the FastAPI service\n\
echo "Starting FastAPI service..."\n\
uvicorn app.main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8003}\n\
\n\
# When the FastAPI service exits, kill the worker\n\
kill $WORKER_PID\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
