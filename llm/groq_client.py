"""
Groq chat completions (OpenAI-compatible API).
"""

import json
import re
import urllib.error
import urllib.request
from typing import Optional

from config import GROQ_API_BASE, GROQ_MODEL

SYSTEM_PROMPT = """You write concise GitHub pull request titles and bodies for reviewers.
You MUST respond with a single JSON object only (no markdown fences, no prose before or after).
Keys: "title" (string, under 80 characters) and "body" (string, GitHub-flavored markdown).

The body MUST use these sections with ## headings:
## Summary
## What changed
## Test plan

Keep the summary short. In "Test plan", use bullets or write "N/A" if not inferable.
If updating an existing PR, merge new information with the prior description; do not drop important prior context unless it is clearly wrong."""


def _parse_json_object(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


def generate_pr_content(
    *,
    diff_text: str,
    context_text: str,
    repo: str,
    branch: str,
    base: str,
    is_update: bool,
    existing_title: Optional[str],
    existing_body: Optional[str],
    api_key: str,
    model: str | None = None,
) -> dict:
    """
    Returns {"title": str, "body": str}. Raises on API or parse errors.
    """
    model = model or GROQ_MODEL
    url = f"{GROQ_API_BASE.rstrip('/')}/chat/completions"

    prior = ""
    if is_update and (existing_title or existing_body):
        prior = (
            "\n\nExisting PR title:\n"
            + (existing_title or "")
            + "\n\nExisting PR body:\n"
            + (existing_body or "")
        )

    user_msg = (
        f"{context_text}\n\n"
        f"Target merge: {base} <- {branch} (repo `{repo}`).\n"
        f"{prior}\n\n"
        "Unified diff (may be truncated):\n```diff\n"
        + diff_text
        + "\n```\n\n"
        "Produce the JSON object with title and body as specified."
    )

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.2,
        "max_tokens": 8192,
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="replace")
        raise RuntimeError(f"Groq HTTP {e.code}: {err}") from e

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"Unexpected Groq response: {data!r}") from e

    parsed = _parse_json_object(content)
    title = (parsed.get("title") or "").strip()
    body = (parsed.get("body") or "").strip()
    if not title:
        title = f"Update {branch}"
    if not body:
        body = "_No description generated._"
    return {"title": title, "body": body}
