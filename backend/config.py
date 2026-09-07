import os
from pathlib import Path

from dotenv import load_dotenv


# =========================================
# FLOWPILOT AI CONFIGURATION
# =========================================

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# =========================================
# DEVELOPMENT MODE
# =========================================

MOCK_MODE = False


# =========================================
# AI FALLBACK
# =========================================

AI_FALLBACK_ENABLED = True


# =========================================
# GEMINI
# =========================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.6-flash"


# =========================================
# GROQ
# =========================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "openai/gpt-oss-20b"


# =========================================
# POSTGRESQL
# =========================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")

DB_URL = DATABASE_URL


# =========================================
# APPLICATION
# =========================================

APP_NAME = "FlowPilot AI"
APP_VERSION = "1.0.0"