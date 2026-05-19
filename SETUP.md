# Quick Setup Guide

## Prerequisites

- Python 3.8+
- Node.js 16+
- Git
- GitHub account (for token)

## Step 1: Get GitHub Token (Optional but Recommended)

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Select scopes: `public_repo`, `read:user`
4. Copy the token

## Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your GitHub token
# GITHUB_TOKEN=your_token_here

# Run backend
python main.py
```

Backend will start at `http://localhost:8000`

## Step 3: Frontend Setup (in new terminal)

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
cp .env.example .env.local

# Run development server
npm run dev
```

Frontend will start at `http://localhost:3000`

## Step 4: Use the Dashboard

1. Open http://localhost:3000 in your browser
2. Enter a GitHub repository URL:
   - Example: `https://github.com/facebook/react`
   - Example: `https://github.com/torvalds/linux`
3. Optionally add your GitHub token for higher rate limits
4. Click "Analyze Repository"
5. Wait for analysis to complete
6. View comprehensive analytics and metrics

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.8+)
- Ensure virtual environment is activated
- Try: `pip install --upgrade pip`
- Delete `pr_dashboard.db` and try again

### Frontend won't start
- Check Node version: `node --version` (should be 16+)
- Delete `node_modules` folder and run `npm install` again
- Try: `npm cache clean --force`

### API connection error
- Ensure backend is running on port 8000
- Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
- Check browser console for CORS errors

### GitHub API rate limit
- Add a GitHub token to backend `.env`
- Rate limit: 60 requests/hour without token, 5000 with token

## Production Deployment

### Backend (FastAPI)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### Frontend (Next.js)
```bash
npm run build
npm run start
```

## Database

- SQLite database stored at `backend/pr_dashboard.db`
- Automatically created on first run
- Delete to reset all data

## Next Steps

- Explore different repositories
- Check the ML predictions for insights
- Monitor contributor activity
- Track PR metrics over time
