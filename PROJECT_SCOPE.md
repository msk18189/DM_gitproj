# GitHub PR Intelligence Dashboard — Project Scope & Milestones

**Project Name:** GitHub PR Intelligence Dashboard  
**Project Type:** Git Analytics & Engineering Intelligence Platform  
**Repository:** [https://github.com/msk18189/DM_gitproj](https://github.com/msk18189/DM_gitproj)

**Objective:** Build a production-grade GitHub pull-request analytics platform with real-time repository health metrics, ML-driven risk insights, private-repository support, collaborative team workflows, and exportable engineering reports—serving as a scalable alternative to ad-hoc PR spreadsheets and basic GitHub Insights.

---

## Core Objectives

- Create a scalable **GitHub PR analytics platform** for engineering teams.
- Support **public and private repository** analysis via secure token handling.
- Ingest PR, review, commit, and contributor data through the **GitHub GraphQL API**.
- Compute **20+ engineering metrics** (cycle time, merge rate, throughput, stale PRs).
- Implement **ML-powered predictions** (delay, bottleneck, risk, review wait).
- Deliver **grounded, actionable insights** (stale alerts, risk panel, recommendations).
- Enable **repository comparison** and filtered dashboard views.
- Support **CSV and PDF export** for stakeholder reporting.
- Provide an **intelligent dashboard UI** with charts, tables, and real-time filter application.
- Evolve toward **authenticated multi-tenant deployment** with async ingestion and webhooks.

---

## Technology Stack

| Layer | Current (MVP) | Target (Production) |
|-------|---------------|---------------------|
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts, Framer Motion, Lucide | Next.js 15, shadcn/ui (optional UI refresh) |
| **Backend** | FastAPI, Uvicorn, Pydantic | FastAPI, Gunicorn/Uvicorn workers |
| **Database** | SQLite (SQLAlchemy ORM) | PostgreSQL |
| **Cache / Queue** | — | Redis + Celery |
| **External API** | GitHub GraphQL API | GitHub GraphQL + Webhooks |
| **ML** | scikit-learn (Gradient Boosting, Isolation Forest, Logistic Regression, Random Forest, K-Means) | Trained `.pkl` pipeline + scheduled retraining |
| **Export** | CSV, PDF (fpdf2) | CSV, PDF, scheduled reports |
| **Auth** | Optional PAT (client + server `.env`) | JWT / GitHub OAuth |
| **Deployment** | Local dev (manual) | Docker Compose → cloud (Vercel + Railway/AWS) |

**AI / ML note:** This project uses **classical ML** (scikit-learn) for PR predictions—not LLM/RAG. LLM integration is listed as a future optional enhancement.

---

## Major Features

### Delivered (MVP)

| Feature | Description |
|---------|-------------|
| **Repository analysis** | Analyze any GitHub repo via URL (public or private with PAT) |
| **Private repo access** | User-supplied token, server `.env` fallback, test-access endpoint |
| **KPI dashboard** | Open PRs, stale PRs, cycle time, merge rate, review metrics |
| **Visual analytics** | Monthly PR flow, throughput, contributor activity, review turnaround |
| **Data tables** | Oldest open PRs, slowest merged PRs, contributor statistics |
| **Dashboard filters** | Last 30/90/180 days, author, PR state |
| **PR risk panel** | ML + heuristic risk, bottleneck %, predicted delay |
| **Stale PR alerts** | Severity, reasons, recommended actions |
| **Compare repositories** | Side-by-side KPI comparison with deltas |
| **Export reports** | CSV and PDF download with filters applied |
| **Duration formatting** | Hours display when cycle time &lt; 1 day |
| **System diagnostics** | `/api/system-status`, health checks |

### Planned (Production Roadmap)

| Feature | Description |
|---------|-------------|
| **JWT / GitHub OAuth** | Secure multi-user access |
| **Workspace & team management** | Org-level dashboards |
| **Async analyze pipeline** | Background jobs via Celery |
| **Full PR pagination** | Beyond 50 PRs per repository |
| **GitHub webhooks** | Live PR updates without re-analyze |
| **ML training pipeline** | Automated model training from stored PRs |
| **Contributor segmentation UI** | K-Means clusters exposed in dashboard |
| **Real-time notifications** | Stale PR and risk alerts |
| **Historical trend storage** | Time-series metrics per repo |
| **Rate limiting & audit logs** | Enterprise security controls |

---

## System Architecture

### Current Architecture (MVP)

```
User
  │
  ▼
Browser
  │
  ▼
Frontend ─────────────────────────────────────────────┐
Next.js 14 UI                                         │
  │  RepositoryInput │ KPIs │ Charts │ Export        │
  │  Filters │ Risk Panel │ Compare │ Stale Alerts    │
  ▼                                                   │
Backend API                                           │
FastAPI (REST)                                        │
  │                                                   │
  ├──► GitHub Client ──────► GitHub GraphQL API       │
  │         (Bearer / token auth)                     │
  │                                                   │
  ├──► Data Processor                                 │
  │         parse │ store │ ML predict                │
  │                                                   │
  ├──► Analytics / Extended Analytics                 │
  │         KPIs │ filters │ export │ risk heuristics │
  │                                                   │
  ├──► ML Models (scikit-learn .pkl)                 │
  │                                                   │
  └──► SQLite (pr_dashboard.db)                       │
        repositories │ pull_requests │ ml_predictions│
──────────────────────────────────────────────────────┘
```

### Target Architecture (Production)

```
User
  │
  ▼
Browser
  │
  ▼
Frontend
Next.js UI (CDN)
  │
  │  HTTPS + JWT
  ▼
Backend API
FastAPI (load balanced)
  │
  ├──► Auth (JWT / GitHub OAuth)
  │
  ├──► PostgreSQL
  │      metadata │ PRs │ users │ workspaces
  │
  ├──► Redis + Celery
  │      async analyze │ webhooks │ ML training
  │
  ├──► GitHub GraphQL + Webhooks
  │
  ├──► Ingestion Pipeline
  │      fetch │ parse │ derive metrics │ embed features
  │
  ├──► ML Service
  │      train │ predict │ risk heuristics fallback
  │
  └──► Object Storage (optional)
         PDF exports │ report archives
  │
  ▼
Dashboard
KPIs + charts + citations-style PR links + exports
```

---

## GitHub PR Intelligence Dashboard — System Architecture (Component View)

```
┌──────────┐     REST/JSON      ┌──────────────┐     GraphQL      ┌─────────────┐
│   User   │ ────────────────► │   FastAPI    │ ───────────────► │   GitHub    │
│ Browser  │ ◄──────────────── │   Backend    │ ◄─────────────── │   API       │
└──────────┘   KPIs, exports   └──────┬───────┘   PRs, reviews   └─────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              ┌──────────┐     ┌──────────┐     ┌──────────────┐
              │ SQLite / │     │    ML    │     │   Analytics  │
              │ Postgres │     │  Models  │     │   Engine     │
              └──────────┘     └──────────┘     └──────────────┘
```

---

## Project Milestones

| Phase | Milestone | Deliverables | Schedule | Status |
|-------|-----------|--------------|----------|--------|
| **Phase 1** | **Foundation Setup** | FastAPI project, SQLite schema, GitHub GraphQL client, Next.js shell, CORS, `.env` config | 01-05-2026 → 05-05-2026 | ✅ Complete |
| **Phase 2** | **Core Dashboard UI** | KPI cards, Recharts (monthly flow, throughput, contributors), data tables, dark theme | 06-05-2026 → 10-05-2026 | ✅ Complete |
| **Phase 3** | **Data Pipeline & Analytics** | `DataProcessor`, PR parsing, cycle time / review metrics, contributor stats | 08-05-2026 → 12-05-2026 | ✅ Complete |
| **Phase 4** | **ML Intelligence Layer** | 5 scikit-learn models, `ml_predictions` table, PR risk panel, heuristic fallback | 10-05-2026 → 14-05-2026 | ✅ Complete |
| **Phase 5** | **Advanced Features** | Filters (days/author/state), stale alerts, compare repos, CSV export, duration UX | 12-05-2026 → 16-05-2026 | ✅ Complete |
| **Phase 6** | **Private Repos & Token UX** | PAT input, `POST /api/verify-repo`, session token storage, PDF export, access errors | 17-05-2026 → 19-05-2026 | ✅ Complete |
| **Phase 7** | **Documentation & Hardening Plan** | `REPORT_FINAL.md`, `upgrade.md`, deployment/security assessment | 19-05-2026 | ✅ Complete |
| **Phase 8** | **Production Infrastructure** | Docker Compose, PostgreSQL migration, Redis, environment-based config | 20-05-2026 → 24-05-2026 | 🔲 Planned |
| **Phase 9** | **Authentication & Workspaces** | JWT auth, GitHub OAuth, user-owned `repo_id`, workspace model | 25-05-2026 → 28-05-2026 | 🔲 Planned |
| **Phase 10** | **Async Ingestion Pipeline** | Celery workers, job status API, PR pagination, retry logic | 29-05-2026 → 02-06-2026 | 🔲 Planned |
| **Phase 11** | **ML Training & Segmentation UI** | Train `.pkl` from DB, contributor clusters in UI, model metrics | 03-06-2026 → 05-06-2026 | 🔲 Planned |
| **Phase 12** | **Webhooks & Live Updates** | GitHub webhook receiver, incremental PR sync | 06-06-2026 → 08-06-2026 | 🔲 Planned |
| **Phase 13** | **Team Collaboration** | Shared workspaces, role-based access, team export | 09-06-2026 → 12-06-2026 | 🔲 Planned |
| **Phase 14** | **Testing & Production Deploy** | Integration tests, rate limits, HTTPS, CI/CD, monitoring | 13-06-2026 → 18-06-2026 | 🔲 Planned |

---

## Phase Details

### Phase 1 — Foundation Setup ✅

- FastAPI application with health endpoint  
- SQLAlchemy models: `repositories`, `pull_requests`, `reviews`, `contributors`, `ml_predictions`  
- GitHub GraphQL client with token auth (`ghp_` / `github_pat_`)  
- Next.js 14 frontend with Axios API client  

### Phase 2 — Core Dashboard UI ✅

- Responsive dark-theme layout  
- KPI card grid  
- Recharts: monthly flow, throughput, contributor bars  
- Sortable data tables  

### Phase 3 — Data Pipeline & Analytics ✅

- URL parsing (`owner/repo`)  
- Metric derivation: cycle time, wait for review, review duration  
- `AnalyticsService` and extended filtered queries  

### Phase 4 — ML Intelligence Layer ✅

- Delay prediction (Gradient Boosting)  
- Bottleneck detection (Isolation Forest)  
- Risk scoring (Logistic Regression)  
- Review wait prediction (Random Forest)  
- Contributor segmentation (K-Means, backend only)  

### Phase 5 — Advanced Features ✅

- `DashboardFilters`: 30/90/180 days, author, state  
- Stale PR alerts with recommendations  
- Compare two repositories  
- CSV export  

### Phase 6 — Private Repos & Token UX ✅

- Optional `github_token` on analyze/compare  
- `POST /api/verify-repo`  
- `verify_repository_access()` pre-check  
- PDF export (`fpdf2`)  
- Browser `sessionStorage` for PAT  

### Phase 7 — Documentation & Hardening Plan ✅

- Full technical report (`REPORT_FINAL.md`)  
- Scalability & security upgrade roadmap (`upgrade.md`)  
- This scope document (`PROJECT_SCOPE.md`)  

### Phase 8 — Production Infrastructure 🔲

- `docker-compose.yml`: API, frontend, PostgreSQL, Redis  
- Migrate `DATABASE_URL` to PostgreSQL  
- Production Uvicorn settings (`API_RELOAD=false`)  
- CORS from environment variables  

### Phase 9 — Authentication & Workspaces 🔲

- User registration / login (JWT)  
- GitHub OAuth as preferred token flow  
- Bind repositories to `user_id` / `workspace_id`  
- Authorization middleware on all `/api/*` routes  

### Phase 10 — Async Ingestion Pipeline 🔲

- `POST /api/analyze` → enqueue Celery task  
- `GET /api/jobs/{job_id}` for progress  
- Cursor-based GraphQL pagination (100+ PRs)  
- GitHub rate-limit aware throttling  

### Phase 11 — ML Training & Segmentation UI 🔲

- Training script from historical `pull_requests`  
- Model evaluation metrics (MAE, precision/recall)  
- Contributor cluster visualization  
- Scheduled retrain (weekly cron / Celery beat)  

### Phase 12 — Webhooks & Live Updates 🔲

- `POST /api/webhooks/github`  
- Signature verification  
- Incremental PR upsert on `pull_request` events  

### Phase 13 — Team Collaboration 🔲

- Organization workspaces  
- Invite members, read-only vs admin roles  
- Shared compare and export permissions  

### Phase 14 — Testing & Production Deploy 🔲

- pytest + API integration tests  
- Frontend E2E (Playwright)  
- Rate limiting (`slowapi`)  
- Deploy: Vercel (frontend) + Railway/Render (API + Postgres)  
- Uptime monitoring and structured logging (no secrets in logs)  

---

## API Surface (Current)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/analyze` | Analyze repository (optional `github_token`) |
| POST | `/api/verify-repo` | Verify token can access repo |
| POST | `/api/compare` | Compare two repositories |
| GET | `/api/kpi/{repo_id}` | KPI summary (filters) |
| GET | `/api/monthly-flow/{repo_id}` | Monthly PR flow chart |
| GET | `/api/throughput/{repo_id}` | Weekly throughput chart |
| GET | `/api/contributor-activity/{repo_id}` | Contributor stats |
| GET | `/api/oldest-prs/{repo_id}` | Oldest open PRs |
| GET | `/api/slowest-prs/{repo_id}` | Slowest merged PRs |
| GET | `/api/pr-risk/{repo_id}` | ML risk panel |
| GET | `/api/stale-alerts/{repo_id}` | Stale PR recommendations |
| GET | `/api/authors/{repo_id}` | Filter dropdown authors |
| GET | `/api/export/{repo_id}` | CSV export |
| GET | `/api/export-pdf/{repo_id}` | PDF export |
| GET | `/api/system-status` | Diagnostics |
| GET | `/health` | Health check |

---

## Non-Functional Requirements

| Requirement | MVP | Production Target |
|-------------|-----|-------------------|
| **Availability** | Best effort (local) | 99.5% uptime |
| **Analyze latency** | 5–15 s (sync) | &lt; 30 s (async job) |
| **PR coverage** | ~50 PRs per run | Configurable pagination |
| **Security** | PAT in session; open API | JWT, AuthZ, HTTPS, rate limits |
| **Scalability** | Single user / demo | 50+ users, horizontal API |
| **Data retention** | Indefinite (local SQLite) | Policy-based purge (e.g. 90 days) |

---

## Success Criteria

| Criteria | MVP | Production |
|----------|-----|------------|
| Analyze public repo end-to-end | ✅ | ✅ |
| Analyze private repo with PAT | ✅ | ✅ (OAuth) |
| Display 8+ KPIs and 4 charts | ✅ | ✅ |
| ML risk panel with actionable output | ✅ (heuristics fallback) | ✅ (trained models) |
| Export CSV/PDF | ✅ | ✅ |
| Multi-user secure deployment | ❌ | ✅ |
| Async analyze under load | ❌ | ✅ |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| GitHub API rate limits | Analysis fails for heavy use | Per-user OAuth, caching, Celery throttling |
| Untrained ML models | Zero predictions in UI | Heuristic fallback (implemented) |
| SQLite concurrency | Data corruption at scale | PostgreSQL (Phase 8) |
| Open API (`repo_id` enumeration) | Data leak | AuthZ (Phase 9) |
| Token exposure in logs | Credential leak | Never log PAT; structured logging policy |
| Large repos (&gt;50 PRs) | Incomplete analytics | Pagination (Phase 10) |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `README.md` | Setup and usage |
| `REPORT_FINAL.md` | Full technical report (architecture, ML, API) |
| `upgrade.md` | Scalability, security, tiered upgrade roadmap |
| `PROJECT_SCOPE.md` | This document — scope, milestones, production vision |

---

## Conclusion

**GitHub PR Intelligence Dashboard** is designed as a modular, analytics-first engineering intelligence platform. The **MVP (Phases 1–7)** delivers a complete local and demo-ready experience: GitHub ingestion, rich metrics, ML insights, private-repo support, and exportable reports.

**Phases 8–14** evolve the system into an **enterprise-grade, multi-tenant platform** with PostgreSQL, async workers, authentication, webhooks, and production deployment—aligned with the scalability and security requirements documented in `upgrade.md`.

---

*Document version: 1.0 | Last updated: 19-05-2026*
