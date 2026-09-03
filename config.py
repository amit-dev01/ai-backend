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
SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_KEY)
JINA_API_KEY: str = os.getenv("JINA_API_KEY", "")

EXA_API_KEY: str = os.getenv("EXA_API_KEY", "")
SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")

MONITORING_SCHEDULE_NEWS: str = os.getenv("MONITORING_SCHEDULE_NEWS", "0 8 * * *")
MONITORING_SCHEDULE_PAGES: str = os.getenv("MONITORING_SCHEDULE_PAGES", "0 9 * * 1")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is not set. "
        "Copy .env.example to .env and add your Groq API key."
    )

