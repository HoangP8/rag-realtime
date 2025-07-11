# Medical Chatbot Deployment Guide

This guide provides instructions for deploying the Medical Chatbot backend services to [fly.io](https://fly.io). For the initial trial phase, all microservices are deployed to a single instance for cost efficiency.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Architecture](#deployment-architecture)
3. [Environment Setup](#environment-setup)
4. [Deployment Steps](#deployment-steps)
5. [Monitoring and Logs](#monitoring-and-logs)
6. [Scaling Considerations](#scaling-considerations)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying, ensure you have:

- [flyctl](https://fly.io/docs/hands-on/install-flyctl/) installed and authenticated
- [Docker](https://docs.docker.com/get-docker/) installed (for local testing)
- A Supabase account with your database set up
- OpenAI API key for LLM functionality
- LiveKit account for real-time voice communication (if using voice features)

## Deployment Architecture

For cost efficiency during the trial phase, all microservices are deployed to a single fly.io instance:

- **API Gateway** (Port 8000): Entry point for all client requests
- **Auth Service** (Port 8001): Handles authentication and user management
- **Conversation Service** (Port 8002): Manages conversations and LLM interactions
- **Voice Service** (Port 8003): Handles real-time voice communication
   - Voice API: Manages voice sessions and client connections
   - LiveKit Agent Worker: Handles real-time speech-to-speech functionality

The services communicate with each other via localhost, eliminating the need for complex networking.

## Environment Setup

### 1. Create a .env file

Create a `.env` file in the `backend` directory with the following variables:

```
# Supabase credentials
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# OpenAI API key
OPENAI_API_KEY=your_openai_api_key

# LiveKit settings (for voice service)
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=your_livekit_url

# Service URLs (for local development)
AUTH_SERVICE_URL=http://localhost:8001
CONVERSATION_SERVICE_URL=http://localhost:8002
VOICE_SERVICE_URL=http://localhost:8003

# RabbitMQ configuration (if needed)
RABBITMQ_HOST=your_rabbitmq_host
RABBITMQ_PORT=5672
RABBITMQ_USER=your_rabbitmq_username
RABBITMQ_PASSWORD=your_rabbitmq_password
```

### 2. Set up fly.io secrets

Instead of including sensitive information in your deployment, set them as secrets in fly.io.

Secrets need to be set after first-time deployment. See next section for a quick start.

```bash
# Navigate to the backend-services directory
cd backend

# Set secrets from your .env file
flyctl secrets set NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
flyctl secrets set NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
flyctl secrets set OPENAI_API_KEY=your_openai_api_key
flyctl secrets set LIVEKIT_API_KEY=your_livekit_api_key
flyctl secrets set LIVEKIT_API_SECRET=your_livekit_api_secret
flyctl secrets set LIVEKIT_URL=your_livekit_url
flyctl secrets set RABBITMQ_HOST=your_rabbitmq_host
flyctl secrets set RABBITMQ_PORT=5672
flyctl secrets set RABBITMQ_USER=your_rabbitmq_username
flyctl secrets set RABBITMQ_PASSWORD=your_rabbitmq_password

# Set internal service URLs to use localhost
flyctl secrets set AUTH_SERVICE_URL=http://localhost:8001
flyctl secrets set CONVERSATION_SERVICE_URL=http://localhost:8002
flyctl secrets set VOICE_SERVICE_URL=http://localhost:8003
```

## Deployment Steps

### 1. Test locally with Docker (optional but recommended)

Before deploying to fly.io, test your setup locally:

```bash
# Navigate to the backend directory
cd backend

# Build the Docker image
docker build -t medical-chatbot .

# Run the container with environment variables
docker run -p 8000:8000 --env-file .env.local medical-chatbot

# Open another terminal and build the livekit agent
cd voice-service
docker build -t worker-agent -f Dockerfile.worker . 

# Run the container with environment variables
docker run --env-file .env.local worker-agent
```

Verify that all services start correctly and the API Gateway is accessible at http://localhost:8000.

### 2. Deploy to fly.io

Deploy the backend services first:

```bash
# Navigate to the backend directory
cd backend

# Launch the app (first-time deployment)
flyctl launch --config fly.toml

# Set the secrets
cat .env.local | tr '\n' ' ' | xargs flyctl secrets set

# For subsequent deployments
flyctl deploy --config fly.toml
```

Deploy the voice service worker:

```bash
# Navigate to the voice-service directory
cd backend/voice-service

# Launch the worker app
flyctl launch --config fly.worker.toml

# Set the secrets
cat .env.local | tr '\n' ' ' | xargs flyctl -a medbot-agent secrets set

# For subsequent deployments
flyctl deploy --config fly.worker.toml
```


During the first launch, fly.io will ask you several questions. You can accept most defaults, but make sure to:

- Select an appropriate region close to your users
- Skip PostgreSQL setup (since you're using Supabase)
- Skip Redis setup unless you need it

### 3. Verify the deployment

```bash
# Check the status of your app
flyctl -a medbot-backend status

# View logs to ensure all services started correctly
flyctl -a medbot-backend logs
```

The API should now be accessible at `https://medbot-backend.fly.dev` (or your custom domain if configured).

The agent should be accessible at `https://medbot-agent.fly.dev` (or your custom domain if configured).

## Monitoring and Logs

### View logs

```bash
# Stream logs in real-time
flyctl -a medbot-backend logs

# View recent logs
flyctl -a medbot-backend logs --recent 100
```

### Monitor app health

```bash
# Check app status
flyctl -a medbot-backend status

# View app metrics
flyctl -a medbot-backend metrics
```

## Scaling Considerations

The current deployment runs all services on a single instance, which is suitable for a trial phase. When you're ready to scale:

1. **Vertical Scaling**: Increase VM resources in `fly.toml`:
   ```toml
   [[vm]]
     cpu_kind = "shared"
     cpus = 2
     memory_mb = 2048
   ```

2. **Horizontal Scaling**: For production, consider deploying each service separately:
   - Create separate Dockerfiles and fly.toml files for each service
   - Update service URLs to use fly.io's internal networking
   - Deploy each service individually
   
   Note: When scaling the voice service, both the API and worker components need to be deployed together.

## Troubleshooting

### Common Issues

1. **Services not starting**: Check logs with `flyctl logs` to identify which service is failing.

2. **Database connection issues**: Verify Supabase credentials and ensure your IP is allowed in Supabase settings.

3. **Memory limitations**: If services crash due to memory constraints, increase the memory allocation in `fly.toml`. The voice service with its LiveKit agent may require more memory than other services.

4. **API Gateway can't connect to services**: Ensure internal service URLs are correctly set to use localhost with the right ports.

5. **Voice service issues**: If the voice service fails to start or crashes frequently, check that both the API and the worker component are running properly. Ensure all LiveKit credentials are correctly set.

### Restarting the Application

```bash
# Restart the application
flyctl restart
```

### Accessing the VM Shell

For debugging purposes, you can access the VM shell:

```bash
flyctl ssh console
```

## Next Steps

Once your trial phase is complete and you're ready to scale:

1. Evaluate performance metrics to determine resource needs
2. Consider separating services into individual deployments
3. Implement proper monitoring and alerting
4. Set up CI/CD pipelines for automated deployments
