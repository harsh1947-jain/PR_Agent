#!/usr/bin/env bash
#
# Push to GitHub and auto-create/update a PR using the PR Agent.
#
# Usage:
#   ./push_and_pr.sh                           # push current branch
#   ./push_and_pr.sh origin feature-branch     # explicit remote + branch
#   ./push_and_pr.sh -u origin HEAD            # with flags
#   ./push_and_pr.sh --force origin my-branch  # any git push flags work
#

set -euo pipefail

AGENT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── 1. Run git push with all user-supplied arguments ─────────────────

if [ $# -eq 0 ]; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    echo "[push_and_pr] Pushing '$BRANCH' to origin..."
    git push -u origin "$BRANCH"
else
    echo "[push_and_pr] Running: git push $*"
    git push "$@"
fi

# ── 2. Detect repo and branch from git ───────────────────────────────

BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    echo "[push_and_pr] On base branch ($BRANCH) — skipping PR agent."
    exit 0
fi

REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE_URL" ]; then
    echo "[push_and_pr] Error: no 'origin' remote found."
    exit 1
fi

# Extract owner/repo from SSH or HTTPS remote URLs
REPO=$(echo "$REMOTE_URL" | sed -E 's#.*github\.com[:/]##' | sed 's/\.git$//')

if [ -z "$REPO" ]; then
    echo "[push_and_pr] Error: could not detect repo from remote URL: $REMOTE_URL"
    exit 1
fi

echo ""
echo "[push_and_pr] Detected: repo=$REPO  branch=$BRANCH"
echo "[push_and_pr] Running PR Agent..."
echo ""

# ── 3. Run the PR agent ──────────────────────────────────────────────

python3 "$AGENT_DIR/run_local.py" "$REPO" "$BRANCH"
