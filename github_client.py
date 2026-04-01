"""
GitHub API helpers for PR flow (list PRs, diff, context, create/update).
"""

import json
from urllib.parse import quote, urlencode
import urllib.request
import urllib.error

API = "https://api.github.com"


def _request(method, path, token, body=None):
    url = f"{API}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, method=method, data=data, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[github] {method} {url} → {e.code}: {e.read().decode()}")
        raise


def _compare_path(repo, base, head):
    spec = f"{quote(base, safe='')}...{quote(head, safe='')}"
    return f"/repos/{repo}/compare/{spec}"


def get_open_prs(repo, branch, token):
    """
    STEP 5 — Check if PR exists

    Input:  repo, branch, token
    Call:   get_open_prs(repo, branch, token)
    Output:
      Case 1 (no PR):     []
      Case 2 (PR exists): [{"number": 12, "title": "Old PR"}]
    """
    owner = repo.split("/")[0]
    head = f"{owner}:{branch}"
    q = urlencode({"state": "open", "head": head})
    return _request("GET", f"/repos/{repo}/pulls?{q}", token)


def get_diff(repo, base, head, token):
    """
    STEP 6 — Get code diff

    Input:  repo, base="main", head=branch, token
    Call:   get_diff(repo, base, head, token)
    Output: unified diff text
    """
    url = f"{API}{_compare_path(repo, base, head)}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        print(f"[STEP 6] Diff failed: {e.code}: {e.read().decode()}")
        raise


def get_compare_json(repo, base, head, token):
    """Compare metadata: commits, files, stats (JSON)."""
    return _request("GET", _compare_path(repo, base, head), token)


def get_repository(repo, token):
    """Repo metadata (description, default branch, etc.)."""
    return _request("GET", f"/repos/{repo}", token)


def get_readme_excerpt(repo, token, max_chars=6000):
    """
    Plain-text README (truncated). Returns empty string if missing or on error.
    """
    url = f"{API}/repos/{repo}/readme"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.raw",
    })
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode(errors="replace")
            if len(raw) > max_chars:
                return raw[:max_chars] + "\n\n[README truncated…]"
            return raw
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return ""
        print(f"[github] README fetch failed: {e.code}")
        return ""


def create_pull_request(repo, base, head, title, body, token):
    """Open a new PR: head branch into base."""
    return _request(
        "POST",
        f"/repos/{repo}/pulls",
        token,
        body={
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        },
    )


def update_pull_request(repo, pull_number, title, body, token):
    """Update title/body of an existing PR."""
    return _request(
        "PATCH",
        f"/repos/{repo}/pulls/{pull_number}",
        token,
        body={"title": title, "body": body},
    )
