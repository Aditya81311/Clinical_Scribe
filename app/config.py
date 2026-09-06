import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-70b-instruct")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODEL_PATH = os.getenv("MODEL_PATH", "/mnt/AssistModel/whisper_finetuned/final_model")

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "dev-secret-change-me-in-production")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'scribe.db')}"

os.makedirs(UPLOAD_DIR, exist_ok=True)
