#!/usr/bin/env python3
"""
Run the PR agent locally.

Prerequisites:
  - gh CLI installed and authenticated:  gh auth login
  - claude CLI installed:  npm install -g @anthropic-ai/claude-code

Usage:
  python3 run_local.py owner/repo feature-branch
"""

import argparse
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from agent import run_agent  # noqa: E402


def _check_tool(name, check_args, install_hint):
    """Verify a CLI `tool is available."""
    try:
        subprocess.run(
            check_args,
            capture_output=True,
            timeout=10,
        )
    except FileNotFoundError:
        print(f"Error: '{name}' not found. {install_hint}", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        pass  # tool exists but slow to respond — fine


def main():
    parser = argparse.ArgumentParser(description="Run PR agent locally.")
    parser.add_argument("repo", help="Repository full name, e.g. octocat/Hello-World")
    parser.add_argument("branch", help="Head branch name (must exist on GitHub)")
    args = parser.parse_args()

    _check_tool("gh", ["gh", "auth", "status"], "Install: https://cli.github.com")
    _check_tool("claude", ["claude", "--version"], "Install: npm install -g @anthropic-ai/claude-code")

    run_agent(args.repo, args.branch)


if __name__ == "__main__":
    main()
