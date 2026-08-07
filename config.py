"""
Configuration module for Competitor Analysis AI.

Loads environment variables from .env file and exports application settings
including the Groq API key, base URL, and model selections.
"""

import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
EXTRACTION_MODEL: str = os.getenv("EXTRACTION_MODEL", "llama-3.1-8b-instant")

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is not set. "
        "Copy .env.example to .env and add your Groq API key."
    )

