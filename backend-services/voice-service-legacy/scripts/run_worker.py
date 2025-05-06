#!/usr/bin/env python
"""
Script to run the LiveKit Agents worker
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()
load_dotenv(".env.local")

# Import the worker module
from app.worker import cli, WorkerOptions, entrypoint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Run the worker with our entrypoint
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
