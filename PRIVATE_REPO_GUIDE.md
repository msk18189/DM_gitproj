# Private Repository Access Guide

## The Error You Got

```
Could not resolve to a Repository with the name 'nrgglobal/store-admin'
```

This means the repository is **private** and your token doesn't have permission to access it.

## Why It Happens

GitHub has different permission levels:

### Public Repositories
- ✅ Anyone can access
- ✅ No token needed
- ✅ Works with any token

### Private Repositories
- ❌ Only owner/collaborators can access
- ✅ Needs token with `repo` scope
- ✅ Token must have read access

## Solution: Update Your Token Scopes

Your current token only has `public_repo` scope. For private repos, you need `repo` scope.

### Step 1: Generate New Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: `PR Dashboard`
4. **Select these scopes:**
   - ✓ `repo` (Full control of private repositories)
   - ✓ `read:user` (Read user profile)
5. Click "Generate token"
6. **Copy the token immediately**

### Step 2: Update .env File

1. Open `backend/.env`
2. Replace the old token with the new one:
   ```
   GITHUB_TOKEN=ghp_your_new_token_here
   ```

### Step 3: Restart Backend

```bash
cd backend
python run.py
```

### Step 4: Try Again

Analyze your private repository:
```
https://github.com/nrgglobal/store-admin
```

## Token Scopes Explained

### `public_repo` (Current)
- ✅ Access public repositories
- ❌ Cannot access private repositories
- ❌ Cannot access private user data

### `repo` (Recommended)
- ✅ Access public repositories
- ✅ Access private repositories
- ✅ Access private user data
- ⚠️ Full control (be careful with this token)

## Security Note

**Important:** The `repo` scope gives full control of your repositories. 

- ✅ Safe for read-only operations (like this dashboard)
- ⚠️ Don't share this token
- ⚠️ Delete it if compromised
- ✅ You can always generate a new one

## Verification

### Check if Token Has Right Scopes

1. Go to: https://github.com/settings/tokens
2. Find your token
3. Check the scopes listed
4. Should include `repo`

### Test Token Access

```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/user/repos
```

Should show your private repositories.

## Troubleshooting

### Still Getting "NOT_FOUND" Error

**Possible causes:**
1. Token doesn't have `repo` scope
2. Repository name is wrong
3. Repository was deleted
4. You don't have access to the repository

**Solutions:**
1. Generate new token with `repo` scope
2. Check repository URL is correct
3. Verify repository exists
4. Check you're a collaborator on the repo

### Token Expired

If your token is old, it might have expired:
1. Go to https://github.com/settings/tokens
2. Check expiration date
3. Generate new token if expired

### Still Can't Access

If you still can't access after updating token:
1. Make sure you're a collaborator on the repo
2. Ask repo owner to add you as collaborator
3. Try with a public repository first to verify token works

## Testing with Public Repos First

Before trying private repos, test with public ones:

```
https://github.com/facebook/react
https://github.com/shadcn-ui/ui
https://github.com/vuejs/vue
```

If these work, your token is valid. Then try private repos.

## Summary

**To access private repositories:**

1. ✅ Generate new token with `repo` scope
2. ✅ Update `backend/.env` with new token
3. ✅ Restart backend
4. ✅ Try analyzing private repository

**The dashboard will then work with:**
- ✅ Public repositories
- ✅ Private repositories (if you have access)
- ✅ Your own private repositories

## Next Steps

1. Generate new token with `repo` scope
2. Update `.env` file
3. Restart backend
4. Try your private repository again

Good luck! 🚀
