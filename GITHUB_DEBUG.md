# GitHub API Debugging

## Issue: Fetched 0 PRs

The backend is successfully connecting to GitHub but getting 0 PRs back. This could be:

1. **Token is not being sent** - Headers show no Authorization
2. **Token is invalid** - GitHub rejects it silently
3. **Query is malformed** - GitHub returns empty results
4. **Repository has no PRs** - Unlikely for nodejs/node

## How to Debug

### Step 1: Restart Backend with New Debugging

```bash
cd backend
python run.py
```

### Step 2: Analyze Repository Again

Try: `https://github.com/nodejs/node`

### Step 3: Check Backend Logs

Look for these lines:

```
GitHub Client: Sending query with token: True
GitHub Client: Headers: {'Content-Type': 'application/json', 'Authorization': 'token ghp_xxxxx...'}
GitHub Client: Response status: 200
GitHub Client: Query response data keys: dict_keys(['repository'])
GitHub Client: Found 100 PRs
```

### What Each Log Means

**"Sending query with token: True"**
- ✅ Good: Token is loaded from environment
- ❌ Bad: Token is False - check `.env` file

**"Authorization: 'token ghp_xxxxx..."**
- ✅ Good: Token is in headers
- ❌ Bad: No Authorization header - token not loaded

**"Response status: 200"**
- ✅ Good: GitHub API accepted request
- ❌ Bad: Status 401 = invalid token, 404 = repo not found

**"Query response data keys: dict_keys(['repository'])"**
- ✅ Good: Repository data returned
- ❌ Bad: Empty dict or errors - check for error messages

**"Found 100 PRs"**
- ✅ Good: PRs were fetched
- ❌ Bad: Found 0 PRs - query returned empty

## Common Issues & Fixes

### Issue: "Sending query with token: False"

**Problem:** Token not loaded from environment

**Fix:**
1. Check `.env` file exists: `cat backend/.env`
2. Should have: `GITHUB_TOKEN=ghp_xxxxx...`
3. Restart backend: `python run.py`

### Issue: "Response status: 401"

**Problem:** Token is invalid

**Fix:**
1. Generate new token: https://github.com/settings/tokens
2. Make sure scopes: `public_repo`, `read:user`
3. Update `.env` with new token
4. Restart backend

### Issue: "Response status: 404"

**Problem:** Repository not found

**Fix:**
1. Check URL format: `https://github.com/owner/repo`
2. Make sure repository is public
3. Try: `https://github.com/facebook/react`

### Issue: "Found 0 PRs"

**Problem:** Query returned empty results

**Possible causes:**
1. Token doesn't have right scopes
2. Repository is archived/deleted
3. GitHub API issue

**Fix:**
1. Try different repository
2. Check token scopes at https://github.com/settings/tokens
3. Check GitHub status: https://www.githubstatus.com

## Testing Token Directly

```bash
# Test if token works
curl -H "Authorization: token YOUR_TOKEN" \
  -X POST -H "Content-Type: application/json" \
  -d '{"query":"query { viewer { login } }"}' \
  https://api.github.com/graphql
```

Should return your GitHub username.

## Next Steps

1. **Restart backend** with new debugging
2. **Try analyzing** nodejs/node again
3. **Check logs** for the issue
4. **Share logs** if still stuck

## Expected Logs (Working)

```
Analyzing repository: https://github.com/nodejs/node
Processing repository: nodejs/node
GitHub Client: Sending query with token: True
GitHub Client: Headers: {'Content-Type': 'application/json', 'Authorization': 'token ghp_xxxxx...'}
GitHub Client: Making request to https://api.github.com/graphql
GitHub Client: Response status: 200
GitHub Client: Response keys: dict_keys(['data'])
GitHub Client: Query response data keys: dict_keys(['repository'])
GitHub Client: Found 100 PRs
Fetching PRs from GitHub...
Successfully processed 100 PRs for nodejs/node
```

## Expected Logs (Not Working)

```
Analyzing repository: https://github.com/nodejs/node
Processing repository: nodejs/node
GitHub Client: Sending query with token: False  ← TOKEN NOT LOADED
GitHub Client: Headers: {'Content-Type': 'application/json'}  ← NO AUTHORIZATION
GitHub Client: Making request to https://api.github.com/graphql
GitHub Client: Response status: 401  ← UNAUTHORIZED
GitHub API Error: [{'message': 'Bad credentials', ...}]
```

## Verify Token Setup

```bash
# Check if .env exists
ls -la backend/.env

# Check token is set
cat backend/.env

# Check Python can read it
cd backend
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Token:', os.getenv('GITHUB_TOKEN'))"
```

Should print your token (not empty).
