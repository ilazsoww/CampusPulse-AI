import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DB_PATH = os.getenv("DB_PATH", "campuspulse.db")

# Fail fast if critical configuration is missing
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_api_key_here":
    raise ValueError("CRITICAL: GEMINI_API_KEY is not set or is invalid in the .env file.")