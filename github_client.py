"""
GitHub helpers using the gh CLI (no tokens, no urllib).

Requires: gh CLI installed and authenticated (gh auth login).
"""

import json
import subprocess
from urllib.parse import quote


def _gh(args, check=True, stdin_data=None):
    """Run a gh CLI command and return stdout as a string."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        timeout=30,
        input=stdin_data,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip()
        if result.stdout.strip():
            detail += f"\nResponse: {result.stdout.strip()[:500]}"
        raise RuntimeError(
            f"gh {' '.join(args[:3])}... failed ({result.returncode}): {detail}"
        )
    return result.stdout


def _gh_json_input(args, payload):
    """Run a gh api command with a JSON payload via stdin."""
    raw = _gh(args + ["--input", "-"], stdin_data=json.dumps(payload))
    return json.loads(raw)


def _gh_json(args):
    """Run a gh CLI command and parse stdout as JSON."""
    raw = _gh(args)
    return json.loads(raw)


def _compare_spec(base, head):
    return f"{quote(base, safe='')}...{quote(head, safe=':')}"


# ── Repo metadata ────────────────────────────────────────────────────

def get_repository(repo):
    """Repo metadata (description, default branch, etc.)."""
    return _gh_json(["api", f"repos/{repo}"])


def resolve_upstream(repo):
    """
    If *repo* is a fork, return (parent_full_name, fork_owner).
    Otherwise return (repo, None).
    """
    meta = get_repository(repo)
    if meta.get("fork") and meta.get("parent"):
        parent = meta["parent"]["full_name"]
        fork_owner = repo.split("/")[0]
        return parent, fork_owner
    return repo, None


# ── PRs ───────────────────────────────────────────────────────────────

def get_open_prs(repo, head_ref):
    """
    Check for open PRs matching *head_ref*.

    *head_ref* can be "branch" (same-repo) or "forkowner:branch" (cross-repo).
    gh pr list expects bare branch name (no owner prefix).
    """
    branch_only = head_ref.split(":")[-1] if ":" in head_ref else head_ref

    return _gh_json([
        "pr", "list",
        "--repo", repo,
        "--head", branch_only,
        "--state", "open",
        "--json", "number,title,body",
    ])


# ── Diff & compare ───────────────────────────────────────────────────

def get_diff(repo, base, head):
    """Return unified diff text for base...head."""
    spec = _compare_spec(base, head)
    return _gh([
        "api", f"repos/{repo}/compare/{spec}",
        "-H", "Accept: application/vnd.github.v3.diff",
    ])


def get_compare_json(repo, base, head):
    """Compare metadata: commits, files, stats (JSON)."""
    spec = _compare_spec(base, head)
    return _gh_json(["api", f"repos/{repo}/compare/{spec}"])


# ── README ────────────────────────────────────────────────────────────

def get_readme_excerpt(repo, max_chars=6000):
    """Plain-text README (truncated). Returns empty string if missing."""
    try:
        raw = _gh([
            "api", f"repos/{repo}/readme",
            "-H", "Accept: application/vnd.github.v3.raw",
        ], check=False)
        if not raw:
            return ""
        if len(raw) > max_chars:
            return raw[:max_chars] + "\n\n[README truncated…]"
        return raw
    except Exception:
        return ""


# ── Create / update PR ───────────────────────────────────────────────

def create_pull_request(repo, base, head, title, body):
    """Open a new PR: head branch into base."""
    return _gh_json_input(
        ["api", f"repos/{repo}/pulls", "-X", "POST"],
        {"title": title, "body": body, "head": head, "base": base},
    )


def update_pull_request(repo, pull_number, title, body):
    """Update title/body of an existing PR."""
    return _gh_json_input(
        ["api", f"repos/{repo}/pulls/{pull_number}", "-X", "PATCH"],
        {"title": title, "body": body},
    )
