# Quick Start - 5 Minutes

## Prerequisites
- Python 3.8+
- Node.js 16+

## Step 1: Backend (2 minutes)

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

✅ Backend running at http://localhost:8000

## Step 2: Frontend (2 minutes)

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

✅ Frontend running at http://localhost:3000

## Step 3: Use Dashboard (1 minute)

1. Open http://localhost:3000
2. Enter a GitHub repo URL:
   - `https://github.com/facebook/react`
   - `https://github.com/torvalds/linux`
   - `https://github.com/nodejs/node`
3. Click "Analyze Repository"
4. View analytics!

## Optional: Add GitHub Token

For higher API rate limits:

1. Go to https://github.com/settings/tokens
2. Create token with `public_repo` scope
3. Copy token
4. Paste in dashboard form

## What You Get

- 📊 KPI metrics (open PRs, cycle time, merge rate)
- 📈 Charts (monthly flow, throughput, contributors)
- 📋 Tables (oldest PRs, slowest PRs, contributors)
- 🤖 ML predictions (delays, bottlenecks, risk scores)

## Troubleshooting

### Backend won't start
```bash
# Make sure venv is activated
# Try: pip install --upgrade pip
# Delete pr_dashboard.db and try again
```

### Frontend won't start
```bash
# Delete node_modules
rm -rf node_modules
npm install
npm run dev
```

### API connection error
- Check backend is running on port 8000
- Check .env.local has NEXT_PUBLIC_API_URL=http://localhost:8000

## Next Steps

- Read README.md for full documentation
- Check SETUP.md for detailed setup
- See PROJECT_OVERVIEW.md for features
- Review ARCHITECTURE.md for technical details

## File Structure

```
.
├── backend/          # FastAPI server
├── frontend/         # Next.js dashboard
├── README.md         # Full documentation
├── SETUP.md          # Detailed setup
├── PROJECT_OVERVIEW.md
├── ARCHITECTURE.md
└── QUICK_START.md    # This file
```

## Key Files

**Backend**
- `backend/main.py` - Start here
- `backend/api/routes.py` - API endpoints
- `backend/services/analytics.py` - Metrics
- `backend/ml/models.py` - ML models

**Frontend**
- `frontend/app/page.tsx` - Main dashboard
- `frontend/components/` - UI components
- `frontend/lib/api.ts` - API client

## Common Commands

```bash
# Backend
cd backend
python main.py              # Start server
python -m venv venv        # Create venv
source venv/bin/activate   # Activate venv (macOS/Linux)
venv\Scripts\activate      # Activate venv (Windows)

# Frontend
cd frontend
npm run dev                # Start dev server
npm run build              # Build for production
npm run start              # Start production server
```

## API Endpoints

```
POST   /api/analyze                    - Analyze repo
GET    /api/kpi/{repo_id}             - Get metrics
GET    /api/oldest-prs/{repo_id}      - Get oldest PRs
GET    /api/slowest-prs/{repo_id}     - Get slowest PRs
GET    /api/contributor-activity/{repo_id}
GET    /api/monthly-flow/{repo_id}
GET    /api/throughput/{repo_id}
```

## Database

SQLite database automatically created at:
- `backend/pr_dashboard.db`

To reset:
```bash
rm backend/pr_dashboard.db
```

## Environment Variables

**Backend** (.env)
```
GITHUB_TOKEN=your_token_here
```

**Frontend** (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## That's It!

You now have a fully functional GitHub PR Intelligence Dashboard. Enjoy analyzing repositories! 🚀
