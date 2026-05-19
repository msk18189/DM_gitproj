# GitHub PR Intelligence Dashboard

A professional analytics dashboard for analyzing GitHub Pull Request activity, contributor behavior, and repository health using FastAPI backend and Next.js frontend with ML-powered insights.

## Features

- **Repository Analysis**: Enter any GitHub repository URL for instant analysis
- **KPI Metrics**: Open PRs, stale PRs, cycle time, merge rate, review duration
- **Visual Analytics**: Monthly PR flow, throughput trends, contributor activity
- **Data Tables**: Oldest open PRs, slowest merged PRs, contributor statistics
- **ML Predictions**: Delay predictions, bottleneck detection, risk scoring
- **Dark Theme UI**: Professional, responsive dashboard with Tailwind CSS

## Tech Stack

### Backend
- FastAPI (Python)
- SQLAlchemy ORM with SQLite
- GitHub GraphQL API
- scikit-learn, XGBoost, LightGBM for ML
- Pydantic for data validation

### Frontend
- Next.js 14 with TypeScript
- Tailwind CSS for styling
- Recharts for data visualization
- Framer Motion for animations
- Lucide React for icons

## Project Structure

```
.
├── backend/
│   ├── api/
│   │   └── routes.py          # API endpoints
│   ├── database/
│   │   ├── db.py              # Database setup
│   │   └── models.py          # SQLAlchemy models
│   ├── github/
│   │   └── client.py          # GitHub GraphQL client
│   ├── services/
│   │   ├── analytics.py       # Analytics calculations
│   │   └── data_processor.py  # Data processing pipeline
│   ├── ml/
│   │   └── models.py          # ML models
│   ├── main.py                # FastAPI app
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Main dashboard
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   ├── KPICard.tsx        # KPI card component
│   │   ├── RepositoryInput.tsx # Input form
│   │   ├── Charts.tsx         # Chart components
│   │   └── DataTable.tsx      # Table component
│   ├── lib/
│   │   └── api.ts             # API client
│   ├── package.json
│   └── tsconfig.json
│
└── README.md
```

## Setup & Installation

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
# Add your GitHub token to .env
```

5. Run backend:
```bash
python main.py
```

Backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local` file:
```bash
cp .env.example .env.local
```

4. Run development server:
```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Usage

1. Open the dashboard at `http://localhost:3000`
2. Enter a GitHub repository URL (e.g., `https://github.com/owner/repo`)
3. Optionally provide a GitHub token for higher rate limits
4. Click "Analyze Repository"
5. View comprehensive analytics and metrics

## API Endpoints

- `POST /api/analyze` - Analyze a repository
- `GET /api/kpi/{repo_id}` - Get KPI summary
- `GET /api/oldest-prs/{repo_id}` - Get oldest open PRs
- `GET /api/slowest-prs/{repo_id}` - Get slowest merged PRs
- `GET /api/contributor-activity/{repo_id}` - Get contributor stats
- `GET /api/monthly-flow/{repo_id}` - Get monthly PR flow
- `GET /api/throughput/{repo_id}` - Get PR throughput

## Analytics Metrics

### KPIs
- Open PR Count
- Stale PR Count (30+ days)
- Average Cycle Time
- Merge Rate
- Average Review Duration
- Average Wait for Review

### Charts
- Monthly PR Flow (created vs merged vs closed)
- PR Throughput (weekly)
- Contributor Activity
- Review Turnaround

### Tables
- Oldest Open PRs
- Slowest Merged PRs
- Contributor Activity

## ML Models

The system includes lightweight ML models for:
- **Delay Prediction**: Predicts PR merge delay using Gradient Boosting
- **Bottleneck Detection**: Identifies stuck PRs using Isolation Forest
- **Risk Scoring**: Estimates PR risk using Logistic Regression
- **Review Wait Prediction**: Predicts review time using Random Forest
- **Contributor Segmentation**: Groups contributors using K-Means

## Environment Variables

### Backend (.env)
```
GITHUB_TOKEN=your_github_token
DATABASE_URL=sqlite:///./pr_dashboard.db
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Performance Notes

- Fetches up to 100 recent PRs per repository
- Caches data in SQLite for fast subsequent queries
- ML models are trained incrementally as data is collected
- Responsive design works on desktop, tablet, and mobile

## Future Enhancements

- Real-time PR notifications
- Custom metric definitions
- Export analytics to CSV/PDF
- Team-based dashboards
- Advanced filtering and search
- Historical trend analysis
- Webhook integration for live updates

## License

MIT
