import os

GITHUB_APP_ID = os.environ.get("GITHUB_APP_ID")
GITHUB_PRIVATE_KEY_PATH = os.environ.get("GITHUB_PRIVATE_KEY_PATH", "private-key.pem")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

PORT = int(os.environ.get("PORT", 5000))
HOST = os.environ.get("HOST", "0.0.0.0")
BASE_BRANCH = os.environ.get("BASE_BRANCH", "main")

# Groq (OpenAI-compatible) — https://console.groq.com/keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_BASE = os.environ.get("GROQ_API_BASE", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# Cap diff size sent to the LLM (characters)
DIFF_MAX_CHARS = int(os.environ.get("DIFF_MAX_CHARS", "120000"))
README_MAX_CHARS = int(os.environ.get("README_MAX_CHARS", "6000"))
