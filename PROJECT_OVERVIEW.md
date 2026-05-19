# GitHub PR Intelligence Dashboard - Project Overview

## What This Project Does

This is a full-stack analytics dashboard that analyzes GitHub repositories to provide insights into Pull Request activity, contributor behavior, and repository health. Users can enter any public GitHub repository URL and get instant analytics with ML-powered predictions.

## Key Features

### 1. Data Extraction
- Fetches PR data from GitHub GraphQL API
- Extracts: PR metadata, reviews, commits, file changes, contributors
- Processes timestamps into meaningful metrics (cycle time, wait time, review duration)

### 2. Analytics Engine
Calculates without ML:
- Open PR count
- Stale PR count (30+ days)
- Average cycle time (creation to merge)
- Merge rate (merged / closed)
- Average review duration
- Average wait for review
- PR throughput (weekly)
- Monthly PR flow (created vs merged vs closed)
- Contributor activity metrics

### 3. ML Models
Lightweight predictions:
- **Delay Prediction**: Will this PR take longer than usual?
- **Bottleneck Detection**: Is this PR stuck?
- **Risk Scoring**: How risky is this PR?
- **Review Wait Prediction**: How long until review?
- **Contributor Segmentation**: Group contributors by activity

### 4. Dashboard UI
- KPI cards with key metrics
- Interactive charts (bar, line, pie)
- Data tables with sorting
- Dark professional theme
- Responsive design
- Loading states and error handling

## Architecture

### Backend (FastAPI)
```
main.py                 - FastAPI app entry point
├── api/routes.py      - REST API endpoints
├── github/client.py   - GitHub GraphQL client
├── services/
│   ├── analytics.py   - Metric calculations
│   └── data_processor.py - Data pipeline
├── ml/models.py       - ML model training/prediction
└── database/
    ├── db.py          - SQLAlchemy setup
    └── models.py      - Database models
```

### Frontend (Next.js)
```
app/
├── page.tsx           - Main dashboard
├── layout.tsx         - Root layout
└── globals.css        - Global styles
components/
├── KPICard.tsx        - KPI display
├── RepositoryInput.tsx - URL input form
├── Charts.tsx         - Chart components
└── DataTable.tsx      - Table component
lib/
└── api.ts             - API client
```

### Database (SQLite)
- Repositories: Store analyzed repos
- PullRequests: PR data with calculated metrics
- Reviews: Review information
- Contributors: Contributor statistics
- MLPredictions: ML model outputs

## Data Flow

1. **User Input** → Repository URL
2. **GitHub API** → Fetch raw PR data
3. **Data Processing** → Calculate metrics, clean data
4. **Database** → Store processed data
5. **ML Pipeline** → Generate predictions
6. **API Response** → Return analytics
7. **Frontend** → Display visualizations

## How to Use

### Quick Start
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Using the Dashboard
1. Open http://localhost:3000
2. Enter GitHub repo URL (e.g., https://github.com/facebook/react)
3. Click "Analyze Repository"
4. View analytics and metrics

## Key Technologies

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database
- **scikit-learn**: ML algorithms
- **GitHub GraphQL API**: Data source

### Frontend
- **Next.js**: React framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Recharts**: Data visualization
- **Framer Motion**: Animations

## ML Models Explained

### 1. Delay Prediction (Gradient Boosting)
**Purpose**: Predict if PR will take longer than average
**Features**: Files changed, commits, reviews, lines added/deleted, reviewers
**Output**: Predicted days to merge

### 2. Bottleneck Detection (Isolation Forest)
**Purpose**: Find PRs stuck in workflow
**Features**: Wait time, review duration, comments, commits, age
**Output**: Probability (0-1) of being bottlenecked

### 3. Risk Scoring (Logistic Regression)
**Purpose**: Estimate PR risk level
**Features**: Change requests, review comments, files, lines changed, author history
**Output**: Risk score (0-1)

### 4. Review Wait Prediction (Random Forest)
**Purpose**: Predict review waiting time
**Features**: Reviewer count, contributor activity, files, labels, weekly activity
**Output**: Predicted hours until review

### 5. Contributor Segmentation (K-Means)
**Purpose**: Group contributors by patterns
**Features**: Merged PRs, cycle time, review activity, stale PR count
**Output**: Cluster assignment (0-2)

## Database Schema

### Repositories
- id, owner, name, url, last_synced

### PullRequests
- id, repo_id, pr_number, title, state
- created_at, merged_at, closed_at
- commit_count, files_changed, lines_added, lines_deleted
- review_count, comment_count, author
- cycle_time_days, wait_for_review_hours, review_duration_hours

### Reviews
- id, pr_id, reviewer, state, submitted_at, comment_count

### Contributors
- id, repo_id, username
- total_prs, merged_prs, avg_cycle_time, avg_review_time, stale_pr_count

### MLPredictions
- id, pr_id
- predicted_delay_days, bottleneck_probability, risk_score, predicted_review_wait
- created_at

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /api/analyze | Analyze repository |
| GET | /api/kpi/{repo_id} | Get KPI summary |
| GET | /api/oldest-prs/{repo_id} | Get oldest open PRs |
| GET | /api/slowest-prs/{repo_id} | Get slowest merged PRs |
| GET | /api/contributor-activity/{repo_id} | Get contributor stats |
| GET | /api/monthly-flow/{repo_id} | Get monthly PR flow |
| GET | /api/throughput/{repo_id} | Get PR throughput |

## Performance Considerations

- Fetches up to 100 recent PRs per repository
- Caches data in SQLite for fast queries
- ML models trained incrementally
- Async GitHub API calls
- Responsive UI with loading states

## Customization

### Change Stale PR Threshold
Edit `backend/config.py`:
```python
STALE_PR_DAYS = 30  # Change to desired days
```

### Add More ML Models
1. Create model in `backend/ml/models.py`
2. Add training data in `backend/services/data_processor.py`
3. Add prediction endpoint in `backend/api/routes.py`

### Modify Dashboard Layout
Edit `frontend/app/page.tsx` to rearrange components

## Limitations

- Fetches only 100 most recent PRs
- Requires public repository access
- GitHub API rate limits (60/hour without token, 5000 with)
- ML models need sufficient data to be accurate

## Future Enhancements

- Real-time PR notifications
- Custom metric definitions
- Export to CSV/PDF
- Team dashboards
- Advanced filtering
- Historical trend analysis
- Webhook integration
- Multiple repository comparison

## Troubleshooting

### "Failed to analyze repository"
- Check repository URL format
- Ensure repository is public
- Check GitHub token validity
- Check API rate limits

### "No data available"
- Repository may have no PRs
- Try a different repository
- Check backend logs

### Slow performance
- Clear database: `rm backend/pr_dashboard.db`
- Reduce PR_FETCH_LIMIT in config
- Check internet connection

## Support

For issues or questions:
1. Check SETUP.md for installation help
2. Review README.md for feature documentation
3. Check backend logs for API errors
4. Check browser console for frontend errors

## License

MIT - Feel free to use and modify
