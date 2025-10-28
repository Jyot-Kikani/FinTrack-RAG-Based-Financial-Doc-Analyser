# app/config.py
import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the project's root directory
load_dotenv()

# --- Model and Embedding Configuration ---
EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
REPO_ID: str = "meta-llama/Llama-3.1-8B-Instruct"

# --- Supabase Configuration ---
SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")

# --- Supabase Naming Conventions ---
PDF_BUCKET_NAME: str = "financial_reports"  # The name of your Supabase Storage bucket
VECTOR_TABLE_NAME: str = "documents"        # The name of the table for pgvector
MATCH_FUNCTION_NAME: str = "match_documents"  # The name of the RPC function for similarity search