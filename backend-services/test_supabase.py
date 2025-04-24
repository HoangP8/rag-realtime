#!/usr/bin/env python3
"""
Test Supabase connection
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env and .env.local files
load_dotenv()
load_dotenv(".env.local")

def test_supabase_connection():
    """Test Supabase connection"""
    # Get Supabase credentials from environment variables
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Error: Supabase URL and key must be provided")
        print(f"NEXT_PUBLIC_SUPABASE_URL: {url}")
        print(f"NEXT_PUBLIC_SUPABASE_ANON_KEY: {'*****' if key else None}")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(url, key)
        
        # Test connection by fetching user count
        response = supabase.table("user_profiles").select("count", count="exact").execute()
        
        # Print response
        print("Supabase connection successful!")
        print(f"User count: {response.count}")
        return True
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        return False

if __name__ == "__main__":
    test_supabase_connection()
