# PR_Agent

An automated PR description generator powered by Claude AI. When a developer pushes code, this agent automatically creates or updates a Pull Request with an AI-generated description.

## How It Works

```
Developer: git push origin feature-branch
                    |
                    v
        GitHub sends push webhook
                    |
                    v
            app.py receives it
                    |
                    v
              run_agent(...)
                    |
        +-----------+-----------+
        |           |           |
     STEP 4      STEP 5      STEP 6
   Get Token   Check PR?    Get Diff
        |           |           |
        +-----------+-----------+
                    |
                    v
          STEP 7: Claude AI generates
          PR title + description
                    |
                    v
          STEP 8: Create or Update PR
```

## Flow (Step by Step)

### Step 1 - User Installs GitHub App
A user installs the GitHub App on their account. The app receives and stores the `installation_id`, which is used later to access the user's repos.

**File:** `app.py` (installation webhook handler)

### Step 2 - Developer Pushes Code
```bash
git push origin feature-login
```
Nothing happens in the app yet. GitHub detects the push internally.

### Step 3 - GitHub Sends Push Webhook
GitHub sends a POST request to `/webhook` with the push payload. The app extracts three things:
- `repo` - e.g. `"user/repo"`
- `branch` - e.g. `"feature-login"`
- `installation_id` - e.g. `123456`

Then calls `run_agent(repo, branch, installation_id)` in a background thread.

**File:** `app.py` (push event handler)

### Step 4 - Authenticate with GitHub
The agent authenticates using the GitHub App's private key:
1. Signs a JWT with the private key
2. Exchanges JWT + installation_id for an installation access token
3. Returns `token = "ghs_xxxxx"` (used for all API calls)

In test mode, it uses a personal `GITHUB_TOKEN` from the environment instead.

**File:** `github_auth.py`

### Step 5 - Check if PR Exists
Calls the GitHub API to check for open PRs on the branch:
- **No PR found** → will create a new PR (Step 8A)
- **PR exists** → will update it (Step 8B)

**File:** `github_client.py` → `get_open_prs()`

### Step 6 - Get Code Diff
Fetches the diff between the base branch (`main`) and the pushed branch via the GitHub API. This diff is what gets sent to the LLM.

**File:** `github_client.py` → `get_diff()`

### Step 7 - Generate PR Content (TODO)
Sends the diff to Claude AI, which generates:
- A concise PR title
- A markdown PR description with Summary, What Changed, Why, and Test Plan sections

### Step 8 - Create or Update PR (TODO)
- **Case A (no PR):** Creates a new PR with the AI-generated title and description
- **Case B (PR exists):** Updates the existing PR's title and description

## Project Structure

```
PR_Agent/
├── app.py              # Webhook server (Steps 1, 2, 3)
├── agent.py            # Agent orchestrator (Steps 4, 5, 6)
├── github_auth.py      # GitHub App JWT auth (Step 4)
├── github_client.py    # GitHub API calls (Steps 5, 6, 8)
├── config.py           # Environment-based configuration
├── test.sh             # Test script to simulate webhooks
├── requirements.txt    # Python dependencies
└── .gitignore
```


"
```
