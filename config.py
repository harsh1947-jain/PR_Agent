import os

BASE_BRANCH = os.environ.get("BASE_BRANCH", "main")

# Cap diff size sent to the LLM (characters)
DIFF_MAX_CHARS = int(os.environ.get("DIFF_MAX_CHARS", "120000"))
README_MAX_CHARS = int(os.environ.get("README_MAX_CHARS", "6000"))
