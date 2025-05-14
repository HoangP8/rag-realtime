#!/usr/bin/env python3
"""
Combined service runner for Medical Chatbot backend services.
This script starts all microservices on the same instance for cost-efficient deployment.
"""
import subprocess
import os
import signal
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("service-runner")

# Define service commands
services = [
    {
        "name": "api-gateway",
        "command": "cd api-gateway && uvicorn app.main:app --host 0.0.0.0 --port 8000"
    },
    {
        "name": "auth-service",
        "command": "cd auth-service && uvicorn app.main:app --host 0.0.0.0 --port 8001"
    },
    {
        "name": "conversation-service",
        "command": "cd conversation-service && uvicorn app.main:app --host 0.0.0.0 --port 8002"
    },
    {
        "name": "voice-service",
        "command": "cd voice-service && uvicorn app.main:app --host 0.0.0.0 --port 8003"
    },
]

# Process list
processes = []

def signal_handler(sig, frame):
    """Handle termination signals to gracefully shut down all services"""
    logger.info("Shutting down all services...")
    for process in processes:
        process.terminate()
    
    # Give processes time to terminate gracefully
    time.sleep(3)
    
    # Force kill any remaining processes
    for process in processes:
        if process.poll() is None:  # If process is still running
            process.kill()
    
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start all services
for service in services:
    logger.info(f"Starting {service['name']}...")
    process = subprocess.Popen(service['command'], shell=True)
    processes.append(process)
    time.sleep(2)  # Give each service time to start

logger.info("All services started. Press Ctrl+C to stop.")

# Monitor processes and restart if they fail
try:
    while True:
        for i, process in enumerate(processes):
            if process.poll() is not None:  # Process has terminated
                service = services[i]
                logger.error(f"{service['name']} terminated unexpectedly. Restarting...")
                process = subprocess.Popen(service['command'], shell=True)
                processes[i] = process
        time.sleep(5)
except KeyboardInterrupt:
    signal_handler(None, None)
