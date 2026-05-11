import sys
from groq import Groq
from config import GROQ_API_KEY, GROQ_TEXT_MODEL
from ears import run_ears


def check_groq_connection():
    """Quick test to confirm the Groq API key is valid and reachable."""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        client.chat.completions.create(
            model=GROQ_TEXT_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        print("[Jerry] Groq API connection verified [OK]")
    except Exception as e:
        print("\n=======================================================")
        print("[ERROR] Cannot connect to Groq API")
        print("=======================================================")
        print(f"Reason: {e}")
        print("\nCheck your internet connection or verify the API key in config.py.\n")
        sys.exit(1)


if __name__ == "__main__":
    print("[Jerry] Initializing...")
    check_groq_connection()
    print("[Jerry] ONLINE — Hold ALT+K to talk")
    run_ears()