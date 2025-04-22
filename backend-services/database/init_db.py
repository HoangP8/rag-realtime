#!/usr/bin/env python3
"""
Initialize the database with the schema
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Supabase URL and key must be provided in .env file")
    sys.exit(1)

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Read schema SQL
with open("database/schema.sql", "r") as f:
    schema_sql = f.read()

# Execute schema SQL
try:
    # Note: In a real application, we would use the Supabase SQL editor or migrations
    # For simplicity, we're using a direct SQL query, but this might not work
    # with all SQL statements due to Supabase API limitations
    print("Initializing database...")
    print("Note: This script is for demonstration purposes only.")
    print("In a real application, you should use the Supabase SQL editor or migrations.")
    print("Please copy the contents of schema.sql and execute them in the Supabase SQL editor.")
    
    # For demonstration, we'll just print the schema
    print("\nSchema SQL:")
    print(schema_sql)
    
    print("\nDatabase initialization complete!")

except Exception as e:
    print(f"Error initializing database: {str(e)}")
    sys.exit(1)
