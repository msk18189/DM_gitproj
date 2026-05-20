# Deployment Upgrade Report

**Project:** GitHub PR Intelligence Dashboard  
**Document:** `upgrade.md`  
**Purpose:** Scalability and security assessment for production deployment, with a prioritized upgrade roadmap.

---

## Executive Summary

This application is well suited as an **internal analytics tool**, **team dashboard**, or **portfolio demo**. In its current form it is **not production-ready** for a **public, multi-tenant** deployment without significant hardening.

| Dimension | Current state | Production-ready target |
|-----------|---------------|-------------------------|
| **Scalability** | Single process, SQLite, sync GitHub calls | PostgreSQL, job queue, horizontal API scaling |
| **Security** | No authentication; open API by `repo_id` | AuthN/AuthZ, HTTPS, per-user GitHub access |
| **Fit** | 1–10 trusted users, low concurrency | Depends on upgrade tier (see roadmap) |

---

## 1. Current Architecture

```
┌─────────────┐     HTTPS (required in prod)     ┌──────────────────┐
│  Next.js    │ ───────────────────────────────► │  FastAPI         │
│  Frontend   │     JSON + optional github_token │  (single process)│
└─────────────┘                                  └────────┬─────────┘
       │                                                  │
       │ sessionStorage (PAT)                             ├──► SQLite (pr_dashboard.db)
       │                                                  └──► GitHub GraphQL API
```

### Stack (as implemented)

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | Next.js 14, TypeScript, Tailwind | Static-friendly; scales on CDN |
| Backend | FastAPI, Uvicorn | Sync analyze endpoints |
| Database | SQLite (`./pr_dashboard.db`) | Single-file, single-writer |
| External API | GitHub GraphQL | Rate-limited per token |
| ML | scikit-learn (`.pkl` + heuristics) | Loaded in API process |

### Key operational limits

| Limit | Value | Impact |
|-------|-------|--------|
| PRs per analysis | ~50 | Not full repo history |
| Analyze duration | ~5–15 seconds | Blocks HTTP request |
| GitHub rate limit (no token) | ~60 requests/hour | Public repos only |
| GitHub rate limit (with token) | ~5,000 points/hour | Shared across all users if one server token |
| Database concurrency | SQLite single writer | Contention under parallel analyzes |

---

## 2. Scalability Assessment

### 2.1 Bottlenecks (in order)

1. **GitHub API quota** — Every analyze/verify hits GraphQL. Heavy or abusive use exhausts the PAT before server CPU.
2. **Synchronous `/api/analyze`** — Request thread blocked until fetch, parse, DB write, and stats complete.
3. **SQLite** — Cannot safely run multiple API instances writing to the same database without shared filesystem and locking issues.
4. **No background jobs** — No queue, retries, or scheduled re-sync.
5. **In-memory ML load** — Models loaded per worker process if scaled horizontally.

### 2.2 Capacity estimates (single small VM: 1–2 vCPU, 1 GB RAM)

| Scenario | Expected behavior |
|----------|-------------------|
| 1–5 users, occasional analyzes | ✅ Acceptable |
| 10+ simultaneous analyzes | ⚠️ Slow responses, SQLite lock waits |
| Multiple API replicas + SQLite | ❌ Data inconsistency / split databases |
| Large private monorepos | ⚠️ Timeouts or GitHub complexity limits |

### 2.3 What scales easily vs what does not

| Component | Scales well? | Notes |
|-----------|--------------|-------|
| Next.js frontend (Vercel/CDN) | ✅ Yes | Deploy as static or SSR; CDN handles traffic |
| FastAPI read endpoints (`/api/kpi`, charts) | ⚠️ Partially | Fast once data is in DB; limited by SQLite reads |
| `/api/analyze` | ❌ No | Sync + GitHub + DB write |
| SQLite | ❌ No | Replace for multi-instance |
| Shared `GITHUB_TOKEN` in `.env` | ❌ No | Becomes org-wide blast radius |

### 2.4 Target architecture (scaled)

```
┌─────────────┐
│  Next.js    │─── HTTPS ───► ┌─────────────────┐
│  (CDN)      │               │ Load balancer   │
└─────────────┘               └────────┬────────┘
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                       ┌────────────┐        ┌────────────┐
                       │ FastAPI    │        │ FastAPI    │
                       │ instance   │        │ instance   │
                       └─────┬──────┘        └─────┬──────┘
                             │                     │
                             └──────────┬──────────┘
                                        ▼
                              ┌─────────────────┐
                              │ PostgreSQL      │
                              └─────────────────┘
                                        ▲
                              ┌─────────┴─────────┐
                              │ Redis / job queue │
                              └─────────┬─────────┘
                                        ▼
                              ┌─────────────────┐
                              │ Worker processes│──► GitHub API
                              └─────────────────┘
```

---

## 3. Security Assessment

### 3.1 Threat model (deployed publicly)

| Threat | Risk today | Severity |
|--------|------------|----------|
| Unauthenticated API access | Anyone can call all endpoints | **Critical** |
| Enumeration of `repo_id` | Sequential IDs expose others’ analyzed data | **Critical** |
| PAT in request body over HTTP | Token interception | **Critical** (if not HTTPS) |
| Shared server `GITHUB_TOKEN` | One token accesses all repos it can read | **High** |
| No rate limiting | Abuse, cost, GitHub quota exhaustion | **High** |
| SQLite file on disk | Private PR metadata at rest | **Medium** |
| XSS on frontend | Steal PAT from `sessionStorage` | **Medium** |
| Verbose `print` logging | Accidental secret leakage if extended | **Low–Medium** |
| CORS misconfiguration | Browser-only restriction; not a substitute for auth | **Low** |

### 3.2 What is already acceptable

- User PAT is **not stored** in the database.
- Token is sent per request; optional override of `GITHUB_TOKEN` in `.env`.
- Password input type in UI; token kept in **sessionStorage** (tab session only).
- Private-repo errors avoid leaking repository contents.
- Support for `ghp_` and `github_pat_` authorization headers.

### 3.3 Data classification

| Data | Location | Sensitivity |
|------|----------|-------------|
| GitHub PAT (user-supplied) | Browser sessionStorage, request body | **Secret** |
| `GITHUB_TOKEN` (server) | `backend/.env` | **Secret** |
| PR titles, authors, metrics | SQLite | **Confidential** (if private repos analyzed) |
| Aggregated KPIs / exports | API responses, CSV/PDF | **Confidential** |

### 3.4 Security checklist before public deployment

| Priority | Requirement |
|----------|-------------|
| **Must** | Enforce **HTTPS** end-to-end |
| **Must** | Add **authentication** (OAuth, API keys, or SSO) |
| **Must** | Add **authorization** — users may only access their own `repo_id` / tenant data |
| **Must** | Rotate any token ever committed to git, README, or chat logs |
| **Should** | Rate limit `POST /api/analyze` and `POST /api/verify-repo` |
| **Should** | Restrict CORS to production frontend origin(s) only |
| **Should** | Prefer **GitHub OAuth** over pasted PATs for multi-user SaaS |
| **Should** | Store secrets in platform vault (not baked into images) |
| **Should** | Structured logging with **no tokens** in logs |
| **Nice** | Encrypt database at rest; CSP headers; security audit |

---

## 4. Deployment Models

| Model | Scalability | Security effort | Recommended for |
|-------|-------------|-----------------|-----------------|
| **Local only** | N/A | Low | Development, demos |
| **VPN / internal network** | Small team | Medium | Company internal tool |
| **Frontend public, API private** | Medium | Medium | API behind VPN or IP allowlist |
| **Public SaaS** | Requires Tier 2–3 upgrades | High | Product with paying users |

---

## 5. Upgrade Roadmap

### Tier 0 — Minimum viable deployment (internal / demo)

**Goal:** Deploy safely for a trusted small team.

| # | Task | Area |
|---|------|------|
| 0.1 | Deploy behind HTTPS (reverse proxy or PaaS TLS) | Security |
| 0.2 | Set `CORS_ORIGINS` to production frontend URL only | Security |
| 0.3 | Set `API_RELOAD=false`; use production Uvicorn/gunicorn | Ops |
| 0.4 | Remove or restrict public access to `/docs` if not needed | Security |
| 0.5 | Document that `GITHUB_TOKEN` must not be shared publicly | Ops |
| 0.6 | Automated backups of `pr_dashboard.db` | Ops |

**Estimated effort:** 0.5–1 day  
**Outcome:** Safe for **VPN or password-protected** internal use only.

---

### Tier 1 — Hardened single-instance (small team, internet-facing)

**Goal:** Reduce abuse and basic data exposure without full SaaS rebuild.

| # | Task | Area |
|---|------|------|
| 1.1 | Add API key or simple JWT auth on all `/api/*` routes | Security |
| 1.2 | Associate `Repository` records with `user_id`; filter all queries by owner | Security |
| 1.3 | Add rate limiting (e.g. `slowapi`: 10 analyzes/hour per key) | Security |
| 1.4 | Add request ID logging; never log `github_token` | Security |
| 1.5 | Environment-based config: `CORS_ORIGINS`, `DATABASE_URL`, secrets from vault | Ops |
| 1.6 | Health check + monitoring (`/health`, uptime alerts) | Ops |

**Estimated effort:** 3–5 days  
**Outcome:** Suitable for **5–20 trusted users** on one server.

---

### Tier 2 — Production team tool (moderate scale)

**Goal:** Reliable analyzes and multi-user access without SQLite limits.

| # | Task | Area |
|---|------|------|
| 2.1 | Migrate SQLite → **PostgreSQL** (SQLAlchemy URL only; schema migration) | Scalability |
| 2.2 | Background jobs for `/api/analyze` (Celery + Redis or RQ) | Scalability |
| 2.3 | Job status endpoint: `GET /api/jobs/{id}` | UX |
| 2.4 | GitHub **OAuth App** instead of pasted PAT (scoped per user) | Security |
| 2.5 | Cache GitHub responses (Redis, TTL 15–60 min) | Scalability |
| 2.6 | Increase PR pagination with cursor-based GraphQL fetch | Feature |
| 2.7 | 2+ Uvicorn workers behind load balancer | Scalability |

**Estimated effort:** 2–3 weeks  
**Outcome:** **Team dashboard** with tens of users and moderate concurrency.

---

### Tier 3 — Multi-tenant SaaS (high scale)

**Goal:** Many organizations, strong isolation, operable at scale.

| # | Task | Area |
|---|------|------|
| 3.1 | Tenant model (`organization_id` on all tables) | Security |
| 3.2 | Row-level security or strict tenant middleware | Security |
| 3.3 | Per-tenant GitHub App installation (not user PAT) | Security |
| 3.4 | Horizontal pod autoscaling (K8s or managed containers) | Scalability |
| 3.5 | Object storage for exports; async PDF generation | Scalability |
| 3.6 | Audit log (who analyzed which repo, when) | Compliance |
| 3.7 | Encrypt DB at rest; secret rotation policy | Compliance |
| 3.8 | WAF / DDoS protection in front of API | Security |

**Estimated effort:** 1–3 months  
**Outcome:** **Public or enterprise SaaS** with proper isolation.

---

## 6. Configuration Changes for Production

### 6.1 Backend (`config.py` / environment)

| Variable | Development | Production |
|----------|-------------|------------|
| `API_RELOAD` | `true` | **`false`** |
| `API_HOST` | `0.0.0.0` | Behind reverse proxy |
| `CORS_ORIGINS` | `localhost:3000–3019` | **`https://your-app.example.com`** |
| `DATABASE_URL` | `sqlite:///./pr_dashboard.db` | **`postgresql://...`** (Tier 2+) |
| `GITHUB_TOKEN` | `.env` (optional) | Secrets manager; prefer per-user OAuth |

### 6.2 Frontend

| Variable | Production value |
|----------|------------------|
| `NEXT_PUBLIC_API_URL` | `https://api.your-app.example.com` |

### 6.3 Infrastructure recommendations

| Component | Suggested platforms |
|-----------|---------------------|
| Frontend | Vercel, Netlify, Cloudflare Pages |
| API | Railway, Render, Fly.io, AWS ECS, Azure App Service |
| Database (Tier 2+) | Neon, Supabase, RDS, Cloud SQL |
| Queue (Tier 2+) | Redis (Upstash, ElastiCache) |
| Secrets | Platform env vars, AWS Secrets Manager, Doppler |

---

## 7. API Surface — Security Notes

| Endpoint | Risk if public | Mitigation |
|----------|----------------|------------|
| `POST /api/analyze` | Uses GitHub quota; ingests data | Auth + rate limit |
| `POST /api/verify-repo` | Probes repos with token | Auth + rate limit |
| `GET /api/kpi/{repo_id}` | Leaks analyzed metrics | AuthZ on `repo_id` |
| `GET /api/export/*` | Downloads full reports | AuthZ on `repo_id` |
| `GET /api/system-status` | Information disclosure | Disable or restrict in prod |
| `GET /docs` | API discovery | Disable or protect |

---

## 8. Cost and Rate Limit Considerations

| Resource | Constraint |
|----------|------------|
| GitHub GraphQL | 5,000 points/hour per authenticated token (typical) |
| Server CPU | ML inference + PDF export on same process |
| SQLite disk | Grows with repos analyzed; backup size increases |
| Egress | CSV/PDF downloads |

**Recommendation:** One GitHub token per organization or OAuth per user — never one global token for all public users.

---

## 9. Compliance and Privacy (if handling private repos)

- Inform users that PR metadata is **stored on your server** after analyze.
- Provide a **data deletion** path (delete repository record and related PRs).
- Document retention policy (e.g. 90-day purge).
- If EU users: consider GDPR (lawful basis, export, erasure).
- Do not commit PATs; rotate tokens if ever exposed.

---

## 10. Summary Recommendations

### Deploy as-is only if:

- Users are **trusted** (internal team or personal use).
- API is **not** exposed to the open internet, **or** Tier 0 controls are applied.
- You accept **SQLite** and **~50 PR** analysis limits.

### Before any public multi-user launch:

1. Implement **Tier 1** (auth + authorization + rate limits + HTTPS).
2. Plan **Tier 2** if more than ~20 users or concurrent analyzes.
3. Never rely on CORS alone for security.

### Quick reference

| Goal | Minimum tier |
|------|----------------|
| Demo on laptop | None |
| Internal team (VPN) | Tier 0 |
| Internet-facing, small team | Tier 1 |
| Growing engineering org | Tier 2 |
| Public SaaS product | Tier 3 |

---

## Appendix A — Files relevant to upgrades

| File | Relevance |
|------|-----------|
| `backend/main.py` | CORS, app entry |
| `backend/config.py` | CORS, DB URL, API settings |
| `backend/database/db.py` | SQLite engine → PostgreSQL |
| `backend/api/routes.py` | All endpoints; add auth middleware |
| `backend/github/client.py` | Token handling, GitHub calls |
| `backend/services/data_processor.py` | Analyze pipeline → background job |
| `frontend/lib/api.ts` | API client; add auth headers |
| `frontend/lib/tokenStorage.ts` | PAT storage; replace with OAuth session |

---

## Appendix B — Document history

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-05-19 | Initial scalability and security upgrade report |

---

*This document describes the project as of the private-repo token feature and PDF export implementation. Revisit after major architectural changes.*
