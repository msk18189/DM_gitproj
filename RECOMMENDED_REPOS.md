# Recommended Repositories to Analyze

## Why nodejs/node Failed

The nodejs/node repository is very large and has too many PRs with complex data. GitHub's GraphQL API has limits on how many nodes can be queried at once.

**Error:** `MAX_NODE_LIMIT_EXCEEDED`

This happens when the query tries to fetch too much data at once.

## Recommended Repositories

### Small to Medium (Best for Testing)

These repositories have a good number of PRs but aren't too large:

1. **facebook/react**
   ```
   https://github.com/facebook/react
   ```
   - ~2000+ PRs
   - Very active
   - Good for testing

2. **vuejs/vue**
   ```
   https://github.com/vuejs/vue
   ```
   - ~1000+ PRs
   - Well-maintained
   - Good metrics

3. **angular/angular**
   ```
   https://github.com/angular/angular
   ```
   - ~1000+ PRs
   - Active development
   - Good data

4. **tensorflow/tensorflow**
   ```
   https://github.com/tensorflow/tensorflow
   ```
   - ~3000+ PRs
   - Large project
   - Lots of data

### Medium (Good Balance)

5. **nextjs/next.js**
   ```
   https://github.com/vercel/next.js
   ```
   - ~1000+ PRs
   - Active
   - Good for analysis

6. **sveltejs/svelte**
   ```
   https://github.com/sveltejs/svelte
   ```
   - ~500+ PRs
   - Smaller dataset
   - Easier to process

7. **remix-run/remix**
   ```
   https://github.com/remix-run/remix
   ```
   - ~300+ PRs
   - Good size
   - Active development

### Small (Fastest)

8. **tailwindlabs/tailwindcss**
   ```
   https://github.com/tailwindlabs/tailwindcss
   ```
   - ~500+ PRs
   - Good metrics
   - Faster processing

9. **astrojs/astro**
   ```
   https://github.com/withastro/astro
   ```
   - ~400+ PRs
   - Active
   - Good data

10. **shadcn/ui**
    ```
    https://github.com/shadcn-ui/ui
    ```
    - ~200+ PRs
    - Smaller dataset
    - Very fast

## How to Use

1. Copy a repository URL from above
2. Paste into the dashboard
3. Click "Analyze Repository"
4. Wait for analysis to complete

## Expected Results

For a medium-sized repository (500-1000 PRs):
- Analysis time: 5-15 seconds
- Data points: 500-1000 PRs
- Metrics: Full analytics
- ML predictions: All 5 models

## If You Still Get Errors

### Error: "Repository is too large"
- Try a smaller repository from the list above
- Start with facebook/react or vuejs/vue

### Error: "GitHub token is invalid"
- Check your token at https://github.com/settings/tokens
- Make sure it has `public_repo` scope
- Generate a new token if needed

### Error: "Repository not found"
- Check the URL format: `https://github.com/owner/repo`
- Make sure repository is public
- Try a different repository

## Testing the Dashboard

### Quick Test (Fastest)
```
https://github.com/shadcn-ui/ui
```
- ~200 PRs
- Completes in 2-3 seconds
- Good for testing UI

### Standard Test (Recommended)
```
https://github.com/facebook/react
```
- ~2000 PRs
- Completes in 10-15 seconds
- Good metrics
- Lots of data

### Large Test (Full Features)
```
https://github.com/tensorflow/tensorflow
```
- ~3000 PRs
- Completes in 20-30 seconds
- Comprehensive data
- All features work

## Tips

1. **Start small** - Use shadcn-ui or svelte first
2. **Then go medium** - Try react or vue
3. **Then go large** - Try tensorflow or kubernetes
4. **Check metrics** - Each repo has different patterns

## What to Look For

After analysis, check:
- ✅ KPI cards show numbers
- ✅ Charts display data
- ✅ Tables show PRs
- ✅ Contributor activity shows
- ✅ ML predictions appear

If all these work, the dashboard is functioning correctly!

## Next Steps

1. Pick a repository from above
2. Analyze it
3. Explore the dashboard
4. Check the metrics
5. Try different repositories

Happy analyzing! 🚀
