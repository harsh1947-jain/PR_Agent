"""
Agent flow — called from run_local.py.

Uses gh CLI for GitHub and claude CLI for LLM (no API keys needed).
"""

import traceback

from config import BASE_BRANCH, DIFF_MAX_CHARS
from context import build_pr_context
from github_client import (
    create_pull_request,
    get_diff,
    get_open_prs,
    resolve_upstream,
    update_pull_request,
)
from llm import generate_pr_content


def run_agent(repo, branch):
    """
    Main agent entry point.

    Input: repo="user/repo", branch="feature-login"
    """

    print(f"\n{'='*50}")
    print(f"[AGENT] Starting for {repo} @ {branch}")
    print(f"{'='*50}")

    # ── STEP 1: Detect fork → target the upstream (original) repo ────
    print(f"\n[STEP 1] Checking if repo is a fork...")
    target_repo, fork_owner = resolve_upstream(repo)
    if fork_owner:
        head_ref = f"{fork_owner}:{branch}"
        print(f"[STEP 1] ✓ Fork detected → PRs will target upstream: {target_repo}")
        print(f"[STEP 1]   head ref: {head_ref}")
    else:
        head_ref = branch
        target_repo = repo
        print(f"[STEP 1] ✓ Not a fork → PRs target: {target_repo}")

    # ── STEP 2: Check if PR exists ───────────────────────────────────
    print(f"\n[STEP 2] Checking for open PRs on '{head_ref}' in {target_repo}...")
    open_prs = get_open_prs(target_repo, head_ref)

    existing_title = None
    existing_body = None
    if len(open_prs) == 0:
        print(f"[STEP 2] ✓ No PR exists → will CREATE new PR")
        pr_exists = False
        pr_number = None
    else:
        pr_number = open_prs[0]["number"]
        pr_title = open_prs[0]["title"]
        existing_title = open_prs[0].get("title")
        existing_body = open_prs[0].get("body") or ""
        print(f"[STEP 2] ✓ PR exists → #{pr_number} \"{pr_title}\" → will UPDATE")
        pr_exists = True

    # ── STEP 3: Get code diff ────────────────────────────────────────
    base = BASE_BRANCH
    print(f"\n[STEP 3] Getting diff: {target_repo} {base}...{head_ref}...")
    diff = get_diff(target_repo, base, head_ref)
    print(f"[STEP 3] ✓ Got diff ({len(diff)} chars)")

    if not diff.strip():
        print("[STEP 3] Empty diff — nothing to do")
        return

    diff_for_llm = diff
    if len(diff_for_llm) > DIFF_MAX_CHARS:
        diff_for_llm = diff_for_llm[:DIFF_MAX_CHARS] + "\n\n[DIFF TRUNCATED]\n"

    # ── STEP 4: Build context ─────────────────────────────────────────
    print(f"\n[STEP 4] Building context (repo metadata, README, commits)...")
    ctx = build_pr_context(target_repo, base, head_ref)
    print(f"[STEP 4] ✓ Done")

    # ── STEP 5: LLM title + body ─────────────────────────────────────
    print(f"\n[STEP 5] Calling Claude to generate PR title and body...")
    try:
        content = generate_pr_content(
            diff_text=diff_for_llm,
            context_text=ctx,
            repo=target_repo,
            branch=branch,
            base=base,
            is_update=pr_exists,
            existing_title=existing_title,
            existing_body=existing_body,
        )
    except Exception as e:
        print(f"[STEP 5] Failed: {e}")
        traceback.print_exc()
        return

    title = content["title"]
    body = content["body"]
    print(f"[STEP 5] ✓ Title: {title[:100]!r}")

    # ── STEP 6: Create or update PR ───────────────────────────────────
    print(f"\n[STEP 6] {'Updating' if pr_exists else 'Creating'} PR on {target_repo}...")
    try:
        if pr_exists:
            update_pull_request(target_repo, pr_number, title, body)
            print(f"[STEP 6] ✓ Updated PR #{pr_number}")
        else:
            pr = create_pull_request(target_repo, base, head_ref, title, body)
            num = pr.get("number")
            url = pr.get("html_url", "")
            print(f"[STEP 6] ✓ Created PR #{num}: {url}")
    except Exception as e:
        print(f"[STEP 6] Failed: {e}")
        traceback.print_exc()

    print(f"\n{'='*50}")
    print(f"[AGENT] Done!")
    print(f"{'='*50}")
