# PR Agent

An AI-powered tool that automatically generates Pull Request titles and descriptions when you push code. One command — push your code and get a well-written PR on GitHub.

**Zero API keys. Zero configuration. Zero pip dependencies.**

---

## Quick Start

### Prerequisites

| Tool | Install |
|------|---------|
| Python 3.10+ | [python.org](https://www.python.org/downloads/) |
| GitHub CLI (`gh`) | [cli.github.com](https://cli.github.com/) |
| Claude CLI | `npm install -g @anthropic-ai/claude-code` |

### One-Time Setup

```bash
# Authenticate with GitHub (opens browser, click Authorize, done)
gh auth login

# Clone this repo
git clone https://github.com/YOUR_USERNAME/PR_Agent.git
```

### Usage

From inside any git repository:

```bash
# Push and auto-create/update a PR
~/path/to/PR_Agent/push_and_pr.sh

# With git push flags — all work
~/path/to/PR_Agent/push_and_pr.sh origin feature-branch
~/path/to/PR_Agent/push_and_pr.sh -u origin HEAD
~/path/to/PR_Agent/push_and_pr.sh --force origin my-branch
```

Or run the agent directly (if you've already pushed):


---

## What It Does

When you push to a feature branch, the agent:

1. **Detects forks** — If your repo is a fork, the PR targets the original (upstream) repo automatically
2. **Checks for existing PRs** — Creates a new PR or updates the existing one
3. **Fetches the code diff** — Gets what changed between `main` and your branch
4. **Gathers context** — Repo description, README excerpt, commit messages, changed files
5. **Generates PR content** — Claude AI writes a detailed title and description
6. **Creates/updates the PR** — Posts it to GitHub with formatted sections

### Example Output

The agent generates PRs with these sections:

- **Summary** — Why this change exists
- **What changed** — Specific files, functions, and reasons
- **How it works** — Technical explanation of the approach
- **Test plan** — Steps to verify the change

---

## How It Works

```
push_and_pr.sh
  │
  ├── 1. git push (with all your flags)
  │
  ├── 2. Auto-detect repo + branch from git remote
  │
  └── 3. Run PR Agent
        │
        ├── Fork detection ──► gh api repos/owner/repo
        │                      (auto-targets upstream if fork)
        │
        ├── Check existing PR ──► gh pr list
        │
        ├── Get code diff ──► gh api compare/main...branch
        │
        ├── Build context ──► repo metadata + README + commits + files
        │
        ├── Generate content ──► claude CLI (AI writes title + body)
        │
        └── Create/update PR ──► gh api repos/.../pulls
```

---

## Project Structure

```
PR_Agent/
├── push_and_pr.sh         # Entry point — push + auto PR (run from any repo)
├── run_local.py           # Python entry point (if already pushed)
├── agent.py               # Orchestrator — runs the 6-step pipeline
├── github_client.py       # GitHub API calls via gh CLI
├── config.py              # BASE_BRANCH + size limits
├── context/
│   ├── __init__.py
│   └── builder.py         # Assembles repo context for the LLM
├── llm/
│   ├── __init__.py
│   └── claude_client.py   # PR generation via claude CLI
└── requirements.txt       # No dependencies (stdlib only)
```

### Module Responsibilities

| Module | File | What it does |
|--------|------|-------------|
| **Entry** | `push_and_pr.sh` | Wraps `git push`, detects repo/branch, calls `run_local.py` |
| **Runner** | `run_local.py` | Validates tools are installed, calls `agent.py` |
| **Orchestrator** | `agent.py` | Runs the 6-step pipeline end-to-end |
| **GitHub** | `github_client.py` | All GitHub interactions via `gh` CLI subprocess |
| **Context** | `context/builder.py` | Gathers repo metadata, README, commits, file list |
| **LLM** | `llm/claude_client.py` | Sends diff + context to Claude, parses JSON response |
| **Config** | `config.py` | `BASE_BRANCH` (default: main), diff/README size caps |

---

## Fork Support

The agent automatically detects forked repos:

- **Your repo** (`ShettyGaurav/project`) → PR created on **your repo**
- **Forked repo** (`ShettyGaurav/forked-project`) → PR created on the **original repo** (`originalowner/forked-project`)

No configuration needed. The agent reads GitHub's API to determine if a repo is a fork and routes the PR accordingly.

---

## Configuration

All configuration is optional via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_BRANCH` | `main` | Target branch for PRs |
| `DIFF_MAX_CHARS` | `120000` | Max diff size sent to LLM |
| `README_MAX_CHARS` | `6000` | Max README excerpt size |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `gh: not found` | Install: https://cli.github.com |
| `claude: not found` | Install: `npm install -g @anthropic-ai/claude-code` |
| `gh: Not Found (HTTP 404)` on diff | Branch not pushed to GitHub — run `git push` first |
| `gh: Validation Failed (HTTP 422)` | PR may already exist, or branch has no diff from base |
| `Empty diff — nothing to do` | Your branch is identical to `main` |
| Claude CLI timeout | Large diffs take longer — try reducing `DIFF_MAX_CHARS` |
