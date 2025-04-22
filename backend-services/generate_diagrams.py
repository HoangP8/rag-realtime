#!/usr/bin/env python3
"""
Generate system architecture diagrams for the Medical Chatbot backend
using the diagrams library (https://diagrams.mingrammer.com/)
"""
import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS
from diagrams.aws.network import APIGateway
from diagrams.aws.security import IAM
from diagrams.aws.storage import S3
from diagrams.onprem.client import User, Users
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.network import Nginx
from diagrams.programming.framework import FastAPI
from diagrams.saas.chat import Slack
from diagrams.custom import Custom

# Create output directory if it doesn't exist
os.makedirs("diagrams", exist_ok=True)

# High-level architecture diagram
with Diagram("Medical Chatbot Architecture", filename="diagrams/architecture", show=False):
    # External users
    users = Users("Patients & Healthcare Providers")
    
    # Frontend
    with Cluster("Frontend Applications"):
        web = User("Web App")
        mobile = User("Mobile App")
    
    # API Gateway
    with Cluster("API Gateway"):
        api_gateway = APIGateway("FastAPI Gateway")
    
    # Backend Services
    with Cluster("Backend Services"):
        auth_service = FastAPI("Auth Service")
        conversation_service = FastAPI("Conversation Service")
        voice_service = FastAPI("Voice Service")
        llm_service = FastAPI("LLM Service")
    
    # External Services
    with Cluster("External Services"):
        openai = Custom("OpenAI", "./diagrams/icons/openai.png")
        livekit = Custom("LiveKit", "./diagrams/icons/livekit.png")
        supabase = Custom("Supabase", "./diagrams/icons/supabase.png")
    
    # Database
    with Cluster("Database"):
        db = PostgreSQL("PostgreSQL")
    
    # Storage
    with Cluster("Storage"):
        storage = S3("Object Storage")
    
    # Connections
    users >> [web, mobile]
    [web, mobile] >> api_gateway
    
    api_gateway >> auth_service
    api_gateway >> conversation_service
    api_gateway >> voice_service
    api_gateway >> llm_service
    
    auth_service >> supabase
    conversation_service >> supabase
    voice_service >> supabase
    
    conversation_service >> llm_service
    voice_service >> llm_service
    
    llm_service >> openai
    voice_service >> livekit
    
    supabase >> db
    supabase >> storage

# Detailed service diagram
with Diagram("Medical Chatbot Service Details", filename="diagrams/services", show=False):
    # External users
    users = Users("Users")
    
    # API Gateway
    with Cluster("API Gateway"):
        api_router = FastAPI("API Router")
        
        with Cluster("Endpoints"):
            auth_endpoints = Lambda("Auth Endpoints")
            conversation_endpoints = Lambda("Conversation Endpoints")
            voice_endpoints = Lambda("Voice Endpoints")
            profile_endpoints = Lambda("Profile Endpoints")
    
    # Auth Service
    with Cluster("Auth Service"):
        auth_router = FastAPI("Auth Router")
        auth_service = Server("Auth Service")
        auth_models = Server("Auth Models")
    
    # Conversation Service
    with Cluster("Conversation Service"):
        conversation_router = FastAPI("Conversation Router")
        conversation_service = Server("Conversation Service")
        conversation_models = Server("Conversation Models")
    
    # Voice Service
    with Cluster("Voice Service"):
        voice_router = FastAPI("Voice Router")
        voice_service = Server("Voice Service")
        livekit_integration = Server("LiveKit Integration")
    
    # LLM Service
    with Cluster("LLM Service"):
        llm_router = FastAPI("LLM Router")
        llm_service = Server("LLM Service")
        openai_integration = Server("OpenAI Integration")
        prompts = Server("Prompts")
        validation = Server("Response Validation")
    
    # External Services
    openai = Custom("OpenAI", "./diagrams/icons/openai.png")
    livekit = Custom("LiveKit", "./diagrams/icons/livekit.png")
    supabase = Custom("Supabase", "./diagrams/icons/supabase.png")
    
    # Connections
    users >> api_router
    
    api_router >> auth_endpoints
    api_router >> conversation_endpoints
    api_router >> voice_endpoints
    api_router >> profile_endpoints
    
    auth_endpoints >> auth_router
    conversation_endpoints >> conversation_router
    voice_endpoints >> voice_router
    profile_endpoints >> auth_router
    
    auth_router >> auth_service >> auth_models
    conversation_router >> conversation_service >> conversation_models
    voice_router >> voice_service >> livekit_integration
    
    conversation_service >> llm_router
    voice_service >> llm_router
    
    llm_router >> llm_service
    llm_service >> openai_integration
    llm_service >> prompts
    llm_service >> validation
    
    openai_integration >> openai
    livekit_integration >> livekit
    
    [auth_service, conversation_service, voice_service] >> supabase

# Database schema diagram
with Diagram("Medical Chatbot Database Schema", filename="diagrams/database", show=False):
    # Auth tables
    with Cluster("Authentication"):
        users_table = IAM("auth.users")
        user_profiles = IAM("user_profiles")
        user_roles = IAM("user_roles")
    
    # Conversation tables
    with Cluster("Conversations"):
        conversations = RDS("conversations")
        messages = RDS("messages")
        conversation_context = RDS("conversation_context")
    
    # Voice tables
    with Cluster("Voice"):
        voice_sessions = RDS("voice_sessions")
    
    # Relationships
    users_table >> Edge(label="1:1") >> user_profiles
    users_table >> Edge(label="1:N") >> user_roles
    users_table >> Edge(label="1:N") >> conversations
    conversations >> Edge(label="1:N") >> messages
    conversations >> Edge(label="1:1") >> conversation_context
    conversations >> Edge(label="1:N") >> voice_sessions
    users_table >> Edge(label="1:N") >> voice_sessions

# Data flow diagram
with Diagram("Medical Chatbot Data Flow", filename="diagrams/data_flow", show=False):
    # User
    user = User("User")
    
    # Frontend
    with Cluster("Frontend"):
        frontend = Nginx("Frontend App")
    
    # Backend
    with Cluster("Backend"):
        api = APIGateway("API Gateway")
        
        with Cluster("Services"):
            auth = FastAPI("Auth Service")
            conversation = FastAPI("Conversation Service")
            voice = FastAPI("Voice Service")
            llm = FastAPI("LLM Service")
    
    # External Services
    with Cluster("External Services"):
        openai = Custom("OpenAI", "./diagrams/icons/openai.png")
        livekit = Custom("LiveKit", "./diagrams/icons/livekit.png")
        supabase = Custom("Supabase", "./diagrams/icons/supabase.png")
    
    # Data flow
    user >> Edge(label="1. User Input") >> frontend
    frontend >> Edge(label="2. API Request") >> api
    
    api >> Edge(label="3a. Authenticate") >> auth
    auth >> Edge(label="4a. Verify User") >> supabase
    
    api >> Edge(label="3b. Process Message") >> conversation
    conversation >> Edge(label="4b. Store Message") >> supabase
    conversation >> Edge(label="5b. Generate Response") >> llm
    llm >> Edge(label="6b. AI Completion") >> openai
    
    api >> Edge(label="3c. Voice Session") >> voice
    voice >> Edge(label="4c. Create Session") >> livekit
    voice >> Edge(label="5c. Transcribe Audio") >> llm
    llm >> Edge(label="6c. Text to Speech") >> openai
    
    # Return flow
    openai >> Edge(label="7. AI Response") >> llm
    llm >> Edge(label="8. Processed Response") >> [conversation, voice]
    [conversation, voice, auth] >> Edge(label="9. API Response") >> api
    api >> Edge(label="10. Frontend Update") >> frontend
    frontend >> Edge(label="11. User Display") >> user

print("Diagrams generated successfully in the 'diagrams' directory.")
