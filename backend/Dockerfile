FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files first for better caching
COPY api-gateway/requirements.txt /app/api-gateway/
COPY auth-service/requirements.txt /app/auth-service/
COPY conversation-service/requirements.txt /app/conversation-service/
COPY voice-service/requirements.txt /app/voice-service/

# Install dependencies for all services
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r api-gateway/requirements.txt \
    && pip install --no-cache-dir -r auth-service/requirements.txt \
    && pip install --no-cache-dir -r conversation-service/requirements.txt \
    && pip install --no-cache-dir -r voice-service/requirements.txt 

# Copy service code
COPY api-gateway/ /app/api-gateway/
COPY auth-service/ /app/auth-service/
COPY conversation-service/ /app/conversation-service/
COPY voice-service/ /app/voice-service/
COPY combined_service.py /app/

# Make scripts executable
RUN chmod +x /app/combined_service.py
RUN find /app -name "*.sh" -exec chmod +x {} \;

# Create a directory for logs
RUN mkdir -p /app/logs

# Expose the API gateway port
EXPOSE 8000

# Run the combined service
CMD ["python", "combined_service.py"]

