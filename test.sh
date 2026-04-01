#!/usr/bin/env bash
#
# Test script — sends fake webhook payloads to your server using curl.
# Make sure app.py is running first: python3 app.py
#
# Usage:
#   bash test.sh                          # Tests Steps 1-3 only
#   GITHUB_TOKEN=ghp_xxx bash test.sh     # Tests Steps 1-6 (needs real token + repo)

SERVER="http://localhost:5000"

echo "=== TEST 1: Simulate App Installation (STEP 1) ==="
echo ""
curl -s -X POST "$SERVER/webhook" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: installation" \
  -d '{
    "action": "created",
    "installation": {
      "id": 123456,
      "account": { "login": "user123" }
    }
  }' | python3 -m json.tool
echo ""

echo "=== TEST 2: Simulate Push Event (STEPS 2-3) ==="
echo ""
echo "Change 'user/repo' below to a REAL repo you own (e.g. harsh1947-jain/Git_Agent)"
echo "Change 'test-branch' to a REAL branch that exists on that repo"
echo ""
curl -s -X POST "$SERVER/webhook" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -d '{
    "ref": "refs/heads/test-branch",
    "repository": {
      "full_name": "user/repo"
    },
    "installation": {
      "id": 123456
    },
    "commits": [
      { "message": "Added login API" }
    ]
  }' | python3 -m json.tool
echo ""

echo "=== TEST 3: Push to main (should be ignored) ==="
echo ""
curl -s -X POST "$SERVER/webhook" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -d '{
    "ref": "refs/heads/main",
    "repository": { "full_name": "user/repo" },
    "installation": { "id": 123456 },
    "commits": [{ "message": "merge" }]
  }' | python3 -m json.tool
echo ""

echo "=== DONE ==="
echo "Check the app.py terminal for the full output (Steps 4-8 logs)"
echo ""
echo "Full stack (Groq + create/update PR) without webhook:"
echo "  export GITHUB_TOKEN=ghp_xxx GROQ_API_KEY=gsk_xxx"
echo "  python3 run_local.py owner/repo your-branch"
