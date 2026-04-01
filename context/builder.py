"""
Assemble a compact text block for the LLM: repo metadata, README snippet, commits, files.
"""

from config import README_MAX_CHARS
from github_client import get_compare_json, get_readme_excerpt, get_repository


def build_pr_context(repo, base, branch, token):
    """
    Best-effort context; failures for optional pieces are swallowed so the agent still runs.
    """
    blocks = []

    try:
        meta = get_repository(repo, token)
        desc = meta.get("description") or "(none)"
        default = meta.get("default_branch") or ""
        blocks.append(
            f"Repository: {meta.get('full_name', repo)}\n"
            f"Description: {desc}\n"
            f"Default branch: {default}"
        )
    except Exception:
        blocks.append(f"Repository: {repo}")

    try:
        readme = get_readme_excerpt(repo, token, max_chars=README_MAX_CHARS)
        if readme.strip():
            blocks.append("README (excerpt):\n" + readme.strip())
    except Exception:
        pass

    try:
        compare = get_compare_json(repo, base, branch, token)
        commits = compare.get("commits") or []
        commit_lines = []
        for c in commits[-15:]:
            msg = (c.get("commit") or {}).get("message") or ""
            first = msg.strip().split("\n")[0][:200]
            sha = (c.get("sha") or "")[:7]
            if first:
                commit_lines.append(f"- {sha} {first}")
        if commit_lines:
            blocks.append("Recent commits on this branch:\n" + "\n".join(commit_lines))

        files = compare.get("files") or []
        if files:
            names = [f.get("filename", "") for f in files[:80]]
            names = [n for n in names if n]
            if names:
                blocks.append("Files changed:\n" + "\n".join(f"- {n}" for n in names))
            if len(files) > 80:
                blocks.append(f"(+ {len(files) - 80} more files)")
    except Exception:
        blocks.append("(Compare metadata unavailable.)")

    blocks.append(f"Merge target: {base} ← head branch: {branch}")

    return "\n\n".join(blocks)
