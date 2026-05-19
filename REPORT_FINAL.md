# GitHub PR Intelligence Dashboard — Full Project Report

## 1. Project Overview

**Name:** GitHub PR Intelligence Dashboard  
**Purpose:** Analyze GitHub repository pull request health, contributor behavior, and review workflows using analytics and machine learning.  
**Repository:** [https://github.com/msk18189/DM_gitproj](https://github.com/msk18189/DM_gitproj)

Users enter a GitHub repository URL; the system fetches PR data via the GitHub GraphQL API, stores it locally, computes metrics, runs ML predictions, and displays results on a web dashboard.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js 14)                        │
│  Repository Input │ KPI Cards │ Charts │ Tables │ Filters       │
│  PR Risk Panel │ Stale Alerts │ Compare │ Export CSV            │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST (Axios)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                            │
│  API Routes → Data Processor → Analytics / Extended Analytics   │
│              → GitHub GraphQL Client → ML Models                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        GitHub API      SQLite DB     ML Models (.pkl)
     (GraphQL)         (pr_dashboard.db)
```

**Data flow:**

1. User submits a repository URL on the frontend.
2. Backend parses the URL and calls the GitHub GraphQL API.
3. PRs are parsed, stored in SQLite, and ML predictions are generated.
4. Frontend loads KPIs, charts, tables, and advanced features via REST APIs.

---

## 3. Technology Stack

### 3.1 Backend

| Technology | Version | Role |
|------------|---------|------|
| **Python** | 3.12+ | Core language |
| **FastAPI** | 0.104.1 | REST API framework |
| **Uvicorn** | 0.24.0 | ASGI server |
| **SQLAlchemy** | 2.0.23 | ORM for SQLite |
| **SQLite** | Built-in | Local database (`pr_dashboard.db`) |
| **Pydantic** | 2.5.0 | Request/response validation |
| **python-dotenv** | 1.0.0 | Environment variables (`.env`) |
| **Requests** | 2.31.0 | HTTP client for GitHub API |
| **NumPy** | (via scikit-learn) | Numerical arrays for ML |
| **scikit-learn** | 1.3.2 | ML algorithms |
| **XGBoost** | 2.0.3 | Listed in requirements (available for extensions) |
| **LightGBM** | 4.1.0 | Listed in requirements (available for extensions) |

**Backend modules:**

| Module | File | Purpose |
|--------|------|---------|
| Entry point | `main.py` | FastAPI app, CORS, DB init |
| API | `api/routes.py` | REST endpoints |
| Config | `config.py` | Tokens, DB URL, CORS, ML settings |
| GitHub | `github/client.py` | GraphQL queries and PR parsing |
| Data pipeline | `services/data_processor.py` | Fetch, store, ML predictions |
| Analytics | `services/analytics.py` | Core metrics |
| Extended analytics | `services/extended_analytics.py` | Filters, compare, export, risk panel |
| Filters | `services/filters.py` | Date/author/state filtering, duration formatting |
| ML | `ml/models.py` | Model training and inference |
| Database | `database/db.py`, `models.py` | Schema and sessions |

### 3.2 Frontend

| Technology | Version | Role |
|------------|---------|------|
| **Next.js** | 14.x | React framework (App Router) |
| **React** | 18.2 | UI library |
| **TypeScript** | 5.3 | Type safety |
| **Tailwind CSS** | 3.3 | Styling (dark theme) |
| **Recharts** | 2.10.3 | Charts (bar, line) |
| **Framer Motion** | 10.16.4 | Animations |
| **Axios** | 1.6.2 | API calls |
| **Lucide React** | 0.292.0 | Icons |

**Frontend components:**

| Component | Purpose |
|-----------|---------|
| `RepositoryInput.tsx` | GitHub URL input and analyze button |
| `KPICard.tsx` | Metric cards |
| `Charts.tsx` | Monthly flow, throughput, contributors, review turnaround |
| `DataTable.tsx` | Sortable data tables |
| `DashboardFilters.tsx` | Date range, author, PR state filters |
| `PRRiskPanel.tsx` | ML risk and delay for open PRs |
| `StalePRAlerts.tsx` | Stale PR warnings and recommendations |
| `CompareRepos.tsx` | Side-by-side repo comparison |
| `ExportButton.tsx` | CSV export |
| `lib/api.ts` | API client |
| `lib/format.ts` | Duration formatting (hours vs days) |

### 3.3 External Services

| Service | Usage |
|---------|--------|
| **GitHub GraphQL API** | `https://api.github.com/graphql` — PRs, reviews, commits, files |
| **GitHub Personal Access Token** | Authentication (Bearer for fine-grained PATs, `token` for classic) |

---

## 4. Database Schema (SQLite)

| Table | Purpose | Main Fields |
|-------|---------|-------------|
| **repositories** | Analyzed repos | `owner`, `name`, `url`, `last_synced` |
| **pull_requests** | PR data | `pr_number`, `title`, `state`, dates, `commit_count`, `files_changed`, `lines_added/deleted`, `review_count`, `cycle_time_days`, `wait_for_review_hours`, `review_duration_hours`, `author` |
| **reviews** | Review records | `reviewer`, `state`, `submitted_at` |
| **contributors** | Aggregated stats | `username`, `total_prs`, `merged_prs`, `avg_cycle_time`, `stale_pr_count` |
| **ml_predictions** | ML outputs per PR | `predicted_delay_days`, `bottleneck_probability`, `risk_score`, `predicted_review_wait` |

---

## 5. Machine Learning Models

All models are implemented in `backend/ml/models.py` using **scikit-learn**. Trained models are saved as `.pkl` files under `backend/ml/trained_models/`.

### Model 1: PR Delay Prediction

| Property | Detail |
|----------|--------|
| **Algorithm** | `GradientBoostingRegressor` (100 trees, `random_state=42`) |
| **Purpose** | Predict how many days until a PR is merged |
| **Output** | Days (non-negative) |
| **Input features (6)** | `files_changed`, `commit_count`, `review_count`, `lines_added`, `lines_deleted`, `reviewer_count` |

**How it works:** Gradient boosting combines many decision trees; each tree corrects previous errors. It is well-suited for non-linear relationships between PR size/complexity and merge time.

---

### Model 2: Bottleneck Detection

| Property | Detail |
|----------|--------|
| **Algorithm** | `IsolationForest` (`contamination=0.1`) |
| **Purpose** | Flag PRs that look "stuck" or unusual |
| **Output** | Probability 0–1 (higher = more likely bottleneck) |
| **Input features (5)** | `wait_for_review_hours`, `review_duration_hours`, `comment_count`, `commit_count`, `age_days` |

**How it works:** Isolation Forest treats outliers as anomalies. PRs with long waits, many comments, or unusual patterns receive higher bottleneck scores. The score is converted to a probability via a sigmoid function.

---

### Model 3: Risk Scoring

| Property | Detail |
|----------|--------|
| **Algorithm** | `LogisticRegression` (`max_iter=1000`) |
| **Purpose** | Estimate PR risk (e.g., likely to stall or fail) |
| **Output** | Probability 0–1 (class 1 = higher risk) |
| **Input features (5)** | `change_request_count`, `review_count`, `files_changed`, `total_lines_changed`, `author_merge_rate` (placeholder 0.5) |

**How it works:** Logistic regression maps features to a probability. It is used to rank open PRs in the Risk Panel.

---

### Model 4: Review Wait Prediction

| Property | Detail |
|----------|--------|
| **Algorithm** | `RandomForestRegressor` (100 trees) |
| **Purpose** | Predict hours until first/meaningful review |
| **Output** | Hours (non-negative) |
| **Input features (5)** | `reviewer_count`, contributor activity (1.0), `files_changed`, labels (0.0), weekly activity (1.0) |

**How it works:** Random Forest averages predictions from many trees. It handles mixed feature types and reduces overfitting compared to a single tree.

---

### Model 5: Contributor Segmentation

| Property | Detail |
|----------|--------|
| **Algorithm** | `KMeans` (3 clusters) + `StandardScaler` |
| **Purpose** | Group contributors by behavior patterns |
| **Output** | Cluster ID (0, 1, or 2) |
| **Input features** | Merged PRs, avg cycle time, review activity, stale PR count |

**How it works:** Features are scaled, then K-Means partitions contributors into 3 groups (e.g., high/low activity, fast/slow merge patterns).

---

### ML Pipeline Notes

- Models are **lazy-loaded**; if `.pkl` files are missing, predictions return `0.0` and processing continues.
- Predictions run during `DataProcessor.process_repository()` for each new/updated PR.
- Results are stored in `ml_predictions` and displayed in the **PR Risk & Delay** panel.
- **XGBoost** and **LightGBM** are in `requirements.txt` but the current implementation uses scikit-learn only.

---

## 6. Data Extraction (GitHub)

**Client:** `github/client.py`  
**API:** GitHub GraphQL  
**Batch size:** Up to 50 recent PRs per analysis (newest first)

**Fetched per PR:**

- Number, title, state (OPEN / MERGED / CLOSED)
- `createdAt`, `mergedAt`, `closedAt`
- Commit count
- File changes (additions, deletions, file count)
- Reviews (state, reviewer, `submittedAt`)
- Comment count
- Author login

**Derived metrics:**

- **Cycle time** — seconds from create to merge → days (fractional; sub-day merges display as hours on the UI)
- **Wait for review** — hours from create to first review
- **Review duration** — hours from first to last review
- Approval / change-request counts

---

## 7. Analytics & Metrics

### KPIs (8 cards)

| Metric | Description |
|--------|-------------|
| Open PRs | Count of currently open PRs |
| Stale PRs (>30D) | Open PRs older than 30 days |
| Avg / Median cycle time | Create → merge (shows hours if &lt; 24h, else days) |
| Avg wait for review | Time until first review |
| Avg review duration | Length of review process |
| Merge rate | Merged ÷ (merged + closed) × 100 |
| Avg reviews per PR | Mean review count |

### Charts

| Chart | Type | Data |
|-------|------|------|
| Monthly PR Flow | Stacked bar | Created / merged / closed by month |
| PR Throughput | Line | Merged PRs per ISO week (8 weeks) |
| Contributor Activity | Horizontal bar | Total vs merged PRs per author |
| Review Turnaround | Bar list | Avg wait for first review per contributor |

### Tables

- Oldest open PRs
- Slowest merged PRs
- Contributor activity

---

## 8. Features Implemented

| Feature | Description |
|---------|-------------|
| **Repository analysis** | Analyze any public repo via URL |
| **PR risk panel** | ML risk, bottleneck %, delay, review wait for open PRs |
| **Compare repositories** | Compare two repos side-by-side (KPIs + deltas) |
| **Export CSV** | Download full analytics report |
| **Filters** | Last 30/90/180 days, author, PR state |
| **Stale PR alerts** | Reasons + recommended actions |
| **Duration display** | Shows hours (e.g. `6 hrs`) when under 1 day instead of `0 d` |

---

## 9. API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/analyze` | Analyze a repository |
| GET | `/api/kpi/{repo_id}` | KPI summary (supports filters) |
| GET | `/api/oldest-prs/{repo_id}` | Oldest open PRs |
| GET | `/api/slowest-prs/{repo_id}` | Slowest merged PRs |
| GET | `/api/contributor-activity/{repo_id}` | Contributor stats |
| GET | `/api/monthly-flow/{repo_id}` | Monthly PR flow |
| GET | `/api/throughput/{repo_id}` | Weekly throughput |
| GET | `/api/authors/{repo_id}` | Author list for filters |
| GET | `/api/pr-risk/{repo_id}` | ML risk panel data |
| GET | `/api/stale-alerts/{repo_id}` | Stale PR recommendations |
| POST | `/api/compare` | Compare two repositories |
| GET | `/api/export/{repo_id}` | Export CSV report |
| GET | `/api/features` | Feature documentation |
| GET | `/api/system-status` | Health and diagnostics |
| GET | `/health` | Simple health check |

**Filter query parameters (where supported):** `days`, `author`, `state`

---

## 10. Configuration

### Backend (`.env`)

```env
GITHUB_TOKEN=your_github_token
DATABASE_URL=sqlite:///./pr_dashboard.db
```

### Frontend (`.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Config (`config.py`)

- `STALE_PR_DAYS = 30`
- `PR_FETCH_LIMIT = 100`
- `ML_CONTAMINATION = 0.1` (Isolation Forest)
- `ML_KMEANS_CLUSTERS = 3`
- CORS: `localhost` / `127.0.0.1` ports 3000–3019

---

## 11. Project Structure

```
git-data-analysis/
├── backend/
│   ├── api/routes.py
│   ├── database/db.py, models.py
│   ├── github/client.py
│   ├── ml/models.py
│   ├── services/
│   │   ├── analytics.py
│   │   ├── extended_analytics.py
│   │   ├── data_processor.py
│   │   └── filters.py
│   ├── config.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── app/page.tsx, layout.tsx, globals.css
│   ├── components/ (9 components)
│   └── lib/api.ts, format.ts
├── README.md
└── REPORT_FINAL.md
```

---

## 12. Limitations

- Fetches up to **50 PRs** per run (performance vs completeness trade-off).
- ML models require **pre-trained `.pkl` files**; without them, predictions default to 0.
- **SQLite** is local only (not multi-user/cloud by default).
- **No real-time webhooks** — refresh requires re-analyzing the repository.
- Contributor segmentation (K-Means) is implemented in the backend but not yet exposed in the UI.

---

## 13. How to Run

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt
# Add GITHUB_TOKEN to .env
python main.py           # http://localhost:8000

# Frontend
cd frontend
npm install
# Add NEXT_PUBLIC_API_URL to .env.local
npm run dev              # http://localhost:3000
```

---

## 14. License

MIT

---

*Report generated for the GitHub PR Intelligence Dashboard project.*
