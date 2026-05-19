# Setup GitHub Token - REQUIRED

## The Problem

Your backend is showing:
```
GitHub Client: Sending query with token: False
GitHub Client: Response status: 403
```

This means **the `.env` file was missing**. I've created it, but you need to add your token.

## Step 1: Create GitHub Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: `PR Dashboard`
4. Select scopes:
   - ✓ `public_repo` - Access public repositories
   - ✓ `read:user` - Read user profile
5. Click "Generate token"
6. **COPY THE TOKEN IMMEDIATELY** (you won't see it again!)

## Step 2: Create local `.env` (not committed to git)

Create `backend/.env` on your machine only (this file is gitignored and must never be pushed):

```
GITHUB_TOKEN=your_github_token_here
DATABASE_URL=sqlite:///./pr_dashboard.db
```

Replace `your_github_token_here` with your actual token:

```
GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz
```

**Important:** 
- Don't add quotes around the token
- Don't add spaces
- Keep it exactly as copied from GitHub

## Step 3: Restart Backend

```bash
cd backend
python run.py
```

You should now see:
```
GitHub Client: Sending query with token: True
GitHub Client: Response status: 200
GitHub Client: Found 100 PRs
```

## Step 4: Try Analyzing Again

1. Open http://localhost:3000
2. Enter: `https://github.com/nodejs/node`
3. Click "Analyze Repository"
4. Should now show PRs!

## Verify Token Works

Check backend logs for:
```
GitHub Client: Sending query with token: True
```

If you see `False`, the token wasn't loaded. Check:
1. `.env` file exists in `backend/` folder
2. Token is set correctly (no quotes, no spaces)
3. Backend was restarted after adding token

## If Still Not Working

1. **Check `.env` file:**
   ```bash
   cat backend/.env
   ```
   Should show your token

2. **Verify token is valid:**
   - Go to https://github.com/settings/tokens
   - Check token hasn't expired
   - Check token has right scopes

3. **Restart backend:**
   ```bash
   python run.py
   ```

4. **Try analyzing again**

## Token Scopes Needed

Your token MUST have these scopes:
- ✓ `public_repo` - Read public repositories
- ✓ `read:user` - Read user profile

If your token doesn't have these, generate a new one.

## Security Note

- Never commit `.env` to git
- Never share your token
- If token is leaked, delete it at https://github.com/settings/tokens
- Generate a new one

## Next Steps

1. Create token at https://github.com/settings/tokens
2. Add to `backend/.env`
3. Restart backend
4. Try analyzing nodejs/node
5. Should now see PRs!
