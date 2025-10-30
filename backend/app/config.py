import os
from dotenv import load_dotenv

load_dotenv()

# Model and Embedding Configuration
EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
REPO_ID: str = "meta-llama/Llama-3.1-8B-Instruct"

# Supabase Configuration
SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")

# Supabase Naming Conventions
PDF_BUCKET_NAME: str = "financial_reports"
VECTOR_TABLE_NAME: str = "documents"
MATCH_FUNCTION_NAME: str = "match_documents"