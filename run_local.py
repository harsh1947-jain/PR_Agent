#!/usr/bin/env python3
"""
Run the PR agent without GitHub webhooks (local / CI smoke test).

Requires:
  - GITHUB_TOKEN or GH_TOKEN with repo scope (and permission to open/edit PRs)
  - GROQ_API_KEY from https://console.groq.com/keys

Usage (from the PR_Agent directory):
  export GITHUB_TOKEN=ghp_...
  export GROQ_API_KEY=gsk_...
  python3 run_local.py owner/repo feature-branch
"""

import argparse
import os
import sys

# Run as: python run_local.py ... from PR_Agent/
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from agent import run_agent  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Run PR agent locally (no webhook).")
    parser.add_argument("repo", help="Repository full name, e.g. octocat/Hello-World")
    parser.add_argument("branch", help="Head branch name (must exist on GitHub)")
    parser.add_argument(
        "--installation-id",
        type=int,
        default=0,
        help="Ignored when GITHUB_TOKEN is set; placeholder for App installs",
    )
    args = parser.parse_args()

    if not (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")):
        print("Error: set GITHUB_TOKEN or GH_TOKEN for local runs.", file=sys.stderr)
        sys.exit(1)
    if not os.environ.get("GROQ_API_KEY"):
        print("Error: set GROQ_API_KEY.", file=sys.stderr)
        sys.exit(1)

    iid = args.installation_id or int(os.environ.get("INSTALLATION_ID", "123456"))
    run_agent(args.repo, args.branch, iid)


if __name__ == "__main__":
    main()
