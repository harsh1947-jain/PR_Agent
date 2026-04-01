"""
PR content generation using the claude CLI (no API key needed).

Requires: claude CLI installed and authenticated.
"""

import json
import re
import subprocess
from typing import Optional


SYSTEM_PROMPT = """\
You are an expert software engineer writing GitHub pull request descriptions for code reviewers.
You MUST respond with a single JSON object only (no markdown fences, no prose before or after).
Keys: "title" (string, under 80 characters) and "body" (string, GitHub-flavored markdown).

The body MUST use these sections with ## headings:

## Summary
Write 2-3 sentences explaining the PURPOSE and MOTIVATION of this change.
What problem does it solve? Why is it needed? Give context a reviewer needs.

## What changed
List every meaningful change as a bullet point. For each change:
- Name the file(s) affected
- Describe WHAT was added, modified, or removed and WHY
- Mention any new functions, classes, endpoints, or dependencies introduced
- Note any architectural decisions or patterns used
Group related changes together. Be specific — don't just say "updated file.py".

## How it works
Briefly explain the technical approach. How does the new code work?
Describe the flow, key logic, or algorithm in 2-4 sentences so a reviewer
understands the implementation before reading the diff.

## Test plan
- List specific steps to verify this change works correctly
- Include edge cases or scenarios to test
- If not inferable from the diff, write "Manual testing required" with suggestions

Use clear, professional language. Write for a reviewer who has NOT seen the code before.
If updating an existing PR, merge new information with the prior description; \
do not drop important prior context unless it is clearly wrong."""


def _parse_json_object(text: str) -> dict:
    """Extract a JSON object from text that may contain fences or extra prose."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1).strip()
    brace = re.search(r"\{[\s\S]*\}", text)
    if brace:
        text = brace.group(0)
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
) -> dict:
    """
    Returns {"title": str, "body": str}. Raises on CLI or parse errors.
    """
    prior = ""
    if is_update and (existing_title or existing_body):
        prior = (
            "\n\nExisting PR title:\n"
            + (existing_title or "")
            + "\n\nExisting PR body:\n"
            + (existing_body or "")
        )

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"{context_text}\n\n"
        f"Target merge: {base} <- {branch} (repo `{repo}`).\n"
        f"{prior}\n\n"
        "Unified diff (may be truncated):\n```diff\n"
        + diff_text
        + "\n```\n\n"
        "Produce the JSON object with title and body as specified."
    )

    print("[LLM] Calling Claude CLI (this may take a moment)...")

    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "claude CLI not found. Install it: npm install -g @anthropic-ai/claude-code"
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Claude CLI timed out after 120 seconds")

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI failed ({result.returncode}): {result.stderr.strip()}"
        )

    raw = result.stdout.strip()
    if not raw:
        raise RuntimeError("Claude CLI returned empty output")

    # --output-format json wraps the response in a JSON envelope with a "result" key
    try:
        envelope = json.loads(raw)
        if isinstance(envelope, dict) and "result" in envelope:
            raw = envelope["result"]
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        parsed = _parse_json_object(raw if isinstance(raw, str) else json.dumps(raw))
    except (json.JSONDecodeError, ValueError) as e:
        raise RuntimeError(f"Failed to parse Claude response as JSON: {e}\n{raw[:500]}")

    title = (parsed.get("title") or "").strip()
    body = (parsed.get("body") or "").strip()
    if not title:
        title = f"Update {branch}"
    if not body:
        body = "_No description generated._"
    return {"title": title, "body": body}
