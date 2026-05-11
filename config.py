import os
from dotenv import load_dotenv
load_dotenv()

VOICE = "en-US-JennyNeural"

# ── Groq API Key (loaded from .env file) ───────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── Groq model names ───────────────────────────────────────────────────────────
GROQ_TEXT_MODEL   = "llama-3.3-70b-versatile"              # Fast + very capable text model
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
#GROQ_VISION_MODEL = "llama-3.2-90b-vision-preview"         # Best vision model for coding

# ── Audio / Speech ─────────────────────────────────────────────────────────────
SAMPLE_RATE = 16000
CHANNELS    = 1
MODEL_SIZE  = "base"   # Whisper model size for speech recognition

# "concise" → short sharp answers | "detailed" → thorough explanations
ANSWER_STYLE = "detailed"
