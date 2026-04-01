"""
Agent flow — Steps 4–8 (called from app.py after a push webhook).
"""

import os
import traceback

from config import BASE_BRANCH, DIFF_MAX_CHARS, GROQ_API_KEY, GROQ_MODEL
from context import build_pr_context
from github_auth import get_installation_token
from github_client import (
    create_pull_request,
    get_diff,
    get_open_prs,
    update_pull_request,
)
from llm import generate_pr_content


def run_agent(repo, branch, installation_id):
    """
    Called from app.py after a push webhook is received.

    Input: repo="user/repo", branch="feature-login", installation_id=123456
    """

    print(f"\n{'='*50}")
    print(f"[AGENT] Starting for {repo} @ {branch}")
    print(f"{'='*50}")

    # ── STEP 4: Authenticate with GitHub ─────────────────────────────
    test_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if test_token:
        print(f"\n[STEP 4] TEST MODE — using GITHUB_TOKEN from env")
        token = test_token
    else:
        print(f"\n[STEP 4] Authenticating with installation_id={installation_id}...")
        token = get_installation_token(installation_id)
    print(f"[STEP 4] ✓ Got token: {token[:10]}...")

    # ── STEP 5: Check if PR exists ───────────────────────────────────
    print(f"\n[STEP 5] Checking for open PRs on branch '{branch}'...")
    open_prs = get_open_prs(repo, branch, token)

    existing_title = None
    existing_body = None
    if len(open_prs) == 0:
        print(f"[STEP 5] ✓ No PR exists → will CREATE new PR")
        pr_exists = False
        pr_number = None
    else:
        pr_number = open_prs[0]["number"]
        pr_title = open_prs[0]["title"]
        existing_title = open_prs[0].get("title")
        existing_body = open_prs[0].get("body") or ""
        print(f"[STEP 5] ✓ PR exists → #{pr_number} \"{pr_title}\" → will UPDATE")
        pr_exists = True

    # ── STEP 6: Get code diff ────────────────────────────────────────
    base = BASE_BRANCH
    print(f"\n[STEP 6] Getting diff: {base}...{branch}...")
    diff = get_diff(repo, base, branch, token)
    print(f"[STEP 6] ✓ Got diff ({len(diff)} chars)")
    print(f"[STEP 6] Preview:\n{diff[:500]}")

    if not diff.strip():
        print("[STEP 6] Empty diff — nothing to do")
        return

    if not GROQ_API_KEY:
        print("\n[STEP 7] Skipping — GROQ_API_KEY is not set")
        return

    diff_for_llm = diff
    if len(diff_for_llm) > DIFF_MAX_CHARS:
        diff_for_llm = diff_for_llm[:DIFF_MAX_CHARS] + "\n\n[DIFF TRUNCATED]\n"

    # ── STEP 7: LLM title + body ─────────────────────────────────────
    print(f"\n[STEP 7] Building context + calling Groq ({GROQ_MODEL})...")
    try:
        ctx = build_pr_context(repo, base, branch, token)
        content = generate_pr_content(
            diff_text=diff_for_llm,
            context_text=ctx,
            repo=repo,
            branch=branch,
            base=base,
            is_update=pr_exists,
            existing_title=existing_title,
            existing_body=existing_body,
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL,
        )
    except Exception as e:
        print(f"[STEP 7] Failed: {e}")
        traceback.print_exc()
        return

    title = content["title"]
    body = content["body"]
    print(f"[STEP 7] ✓ Title: {title[:100]!r}")

    # ── STEP 8: Create or update PR ───────────────────────────────────
    print(f"\n[STEP 8] {'Updating' if pr_exists else 'Creating'} PR...")
    try:
        if pr_exists:
            update_pull_request(repo, pr_number, title, body, token)
            print(f"[STEP 8] ✓ Updated PR #{pr_number}")
        else:
            pr = create_pull_request(repo, base, branch, title, body, token)
            num = pr.get("number")
            url = pr.get("html_url", "")
            print(f"[STEP 8] ✓ Created PR #{num}: {url}")
    except Exception as e:
        print(f"[STEP 8] Failed: {e}")
        traceback.print_exc()
