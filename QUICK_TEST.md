# Quick Test - Get Dashboard Working in 2 Minutes

## The Issue

nodejs/node is too large. Let's use a smaller repository.

## Step 1: Restart Backend

```bash
cd backend
python run.py
```

## Step 2: Try This Repository

Use this smaller repository instead:

```
https://github.com/facebook/react
```

Or even smaller:

```
https://github.com/shadcn-ui/ui
```

## Step 3: Analyze

1. Open http://localhost:3000
2. Paste the URL
3. Click "Analyze Repository"
4. Wait 5-15 seconds

## Expected Result

You should see:
- ✅ 6 KPI cards with numbers
- ✅ 3 charts with data
- ✅ 3 tables with PR information
- ✅ Contributor activity
- ✅ Monthly flow data

## If It Works

Congratulations! The dashboard is working! 🎉

You can now:
- Try different repositories
- Explore the metrics
- Check the ML predictions
- Analyze your own projects

## If It Still Fails

Check the backend logs for error messages and share them.

## Recommended First Repositories

1. **facebook/react** - Most reliable
2. **vuejs/vue** - Good data
3. **shadcn-ui/ui** - Fastest
4. **tailwindlabs/tailwindcss** - Good metrics

Pick one and try it!
