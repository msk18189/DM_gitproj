import io
import re
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.db import get_db, check_db_health
from services.data_processor import DataProcessor
from services.analytics import AnalyticsService
from services.extended_analytics import ExtendedAnalytics
from github.utils import parse_github_url
from utils import cache as redis_cache
from utils.logging_config import get_logger
from utils.exceptions import (
    GitHubPRDashboardException, ValidationError, 
    InvalidTokenError, GitHubAPIError
)

router = APIRouter()
logger = get_logger("api_routes")

class RepositoryRequest(BaseModel):
    url: str
    github_token: Optional[str] = None
    refresh: Optional[bool] = False

class CompareRequest(BaseModel):
    url_a: str
    url_b: str
    github_token: Optional[str] = None
    refresh: Optional[bool] = False

# --- RATE LIMITER ---
RATE_LIMIT_STORE = {}
RATE_LIMIT_WINDOW = 3600  # 1 hour
RATE_LIMIT_MAX_REQUESTS = 60  # 60 requests per hour

def check_rate_limit(request: Request):
    """
    Lightweight, in-memory IP-based rate limiter.
    Limits clients to 60 requests per hour on protected endpoints.
    """
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Clean up old timestamps
    if ip not in RATE_LIMIT_STORE:
        RATE_LIMIT_STORE[ip] = []
        
    timestamps = [t for t in RATE_LIMIT_STORE[ip] if now - t < RATE_LIMIT_WINDOW]
    RATE_LIMIT_STORE[ip] = timestamps
    
    if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 60 requests per hour on this endpoint."
        )
        
    RATE_LIMIT_STORE[ip].append(now)

# --- UTILITIES ---
def validate_token_format(token: Optional[str]) -> Optional[str]:
    """Validates that a token (if provided) contains only safe characters."""
    if not token:
        return None
    token_clean = token.strip()
    if not token_clean:
        return None
    # GitHub PATs are alphanumeric + hyphens/underscores (e.g. ghp_..., github_pat_...)
    if not re.match(r"^[a-zA-Z0-9_\-]+$", token_clean):
        raise ValidationError("Invalid GitHub token format")
    return token_clean


def secure_error_handler(e: Exception) -> HTTPException:
    """
    Translates exceptions to clean, stack-trace-free HTTPExceptions.
    Shields tokens, DB credentials, and internal traceback details.
    """
    # Handle FastAPI's internal HTTPExceptions
    if isinstance(e, HTTPException):
        return e

    # Handle our custom exceptions
    if isinstance(e, GitHubPRDashboardException):
        logger.info(f"API expected error: {e.user_message} (Internal: {e.internal_details})")
        return HTTPException(
            status_code=e.status_code,
            detail=e.user_message
        )
    
    # Handle generic exceptions safely
    error_msg = str(e).lower()
    
    # 1. Database-related exceptions
    if any(db_err in error_msg for db_err in ("sqlalchemy", "psycopg", "asyncpg", "sqlite", "database", "connection")):
        logger.warning(f"Database error details: {str(e)}")
        return HTTPException(
            status_code=500,
            detail="A service-side data connection error occurred. Please try again later."
        )
        
    # 2. Validation errors
    if isinstance(e, ValueError):
        logger.info(f"Validation error: {str(e)}")
        return HTTPException(
            status_code=400,
            detail=str(e)
        )
        
    # 3. Catch-all fallback
    logger.error(f"Unhandled system error: {str(e)}", exc_info=True)
    return HTTPException(
        status_code=500,
        detail="An internal server error occurred. Our engineers have been notified."
    )


# --- API ROUTES ---

@router.post("/api/analyze", dependencies=[Depends(check_rate_limit)])
def analyze_repository(request: RepositoryRequest, db: Session = Depends(get_db)):
    """Analyze a GitHub repository"""
    try:
        # Validate URL and Token formats
        parsed = parse_github_url(request.url)
        normalized_url = parsed.repo_url
        token = validate_token_format(request.github_token)
        
        logger.info(
            "Analyzing %s mode=%s branch=%s file=%s",
            normalized_url,
            parsed.mode,
            parsed.branch,
            parsed.file_path,
        )
        processor = DataProcessor(db)
        result = processor.process_repository(
            request.url,
            github_token=token,
            refresh=bool(request.refresh),
        )
        result["analytics_mode"] = parsed.mode
        if parsed.mode == "file" and parsed.file_path:
            result["file_path"] = parsed.file_path
            result["branch"] = parsed.branch
        return result
        
    except HTTPException:
        raise
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.post("/api/compare", dependencies=[Depends(check_rate_limit)])
def compare_repositories(request: CompareRequest, db: Session = Depends(get_db)):
    """Compare two repositories side by side"""
    try:
        # Validate URLs and Token format
        normalized_a = parse_github_url(request.url_a).repo_url
        normalized_b = parse_github_url(request.url_b).repo_url
        token = validate_token_format(request.github_token)
        
        processor = DataProcessor(db)
        result_a = processor.process_repository(normalized_a, github_token=token, refresh=bool(request.refresh))
        result_b = processor.process_repository(normalized_b, github_token=token, refresh=bool(request.refresh))
        
        ext = ExtendedAnalytics(db)
        return ext.compare_repos(result_a["repo_id"], result_b["repo_id"])
        
    except HTTPException:
        raise
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.get("/api/kpi/{repo_id}")
def get_kpi(
    repo_id: int,
    days: Optional[int] = None,
    author: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get KPI summary for a repository"""
    try:
        ext = ExtendedAnalytics(db)
        return ext.get_kpi_with_duration(repo_id, days, author, state)
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.get("/api/oldest-prs/{repo_id}")
def get_oldest_prs(
    repo_id: int,
    limit: int = 10,
    days: Optional[int] = None,
    author: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get oldest open PRs"""
    try:
        ext = ExtendedAnalytics(db)
        return ext.get_oldest_open_filtered(repo_id, limit, days=days, author=author)
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.get("/api/slowest-prs/{repo_id}")
def get_slowest_prs(
    repo_id: int,
    limit: int = 10,
    days: Optional[int] = None,
    author: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get slowest merged PRs"""
    try:
        ext = ExtendedAnalytics(db)
        return ext.get_slowest_merged_filtered(repo_id, limit, days=days, author=author)
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.get("/api/contributor-activity/{repo_id}")
def get_contributor_activity(
    repo_id: int,
    days: Optional[int] = None,
    author: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get contributor activity"""
    try:
        ext = ExtendedAnalytics(db)
        return ext.get_contributors_filtered(repo_id, days=days, author=author, state=state)
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.get("/api/monthly-flow/{repo_id}")
def get_monthly_flow(
    repo_id: int,
    months: int = 6,
    days: Optional[int] = None,
    author: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get monthly PR flow"""
    try:
        ext = ExtendedAnalytics(db)
        return ext.get_monthly_flow_filtered(repo_id, months, days=days, author=author, state=state)
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.get("/api/throughput/{repo_id}")
def get_throughput(
    repo_id: int,
    weeks: int = 8,
    days: Optional[int] = None,
    author: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get PR throughput"""
    try:
        ext = ExtendedAnalytics(db)
        return ext.get_throughput_filtered(repo_id, weeks, days=days, author=author, state=state)
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.get("/api/authors/{repo_id}")
def get_authors(repo_id: int, db: Session = Depends(get_db)):
    """List PR authors for filter dropdown"""
    try:
        ext = ExtendedAnalytics(db)
        return {"authors": ext.get_authors(repo_id)}
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.get("/api/pr-risk/{repo_id}")
def get_pr_risk(repo_id: int, limit: int = 15, db: Session = Depends(get_db)):
    """ML risk & delay predictions for open PRs"""
    try:
        ext = ExtendedAnalytics(db)
        return ext.get_pr_risk_panel(repo_id, limit)
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.get("/api/stale-alerts/{repo_id}")
def get_stale_alerts(repo_id: int, db: Session = Depends(get_db)):
    """Stale PR alerts with recommendations"""
    try:
        ext = ExtendedAnalytics(db)
        return ext.get_stale_recommendations(repo_id)
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.get("/api/export/{repo_id}", dependencies=[Depends(check_rate_limit)])
def export_report(
    repo_id: int,
    days: Optional[int] = None,
    author: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Export dashboard data as CSV"""
    try:
        ext = ExtendedAnalytics(db)
        csv_content = ext.build_export_csv(repo_id, days, author, state)
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=pr_report_{repo_id}.csv"},
        )
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.get("/api/export-pdf/{repo_id}", dependencies=[Depends(check_rate_limit)])
def export_report_pdf(
    repo_id: int,
    days: Optional[int] = None,
    author: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Export dashboard data as PDF"""
    try:
        ext = ExtendedAnalytics(db)
        pdf_bytes = ext.build_export_pdf(repo_id, days, author, state)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=pr_report_{repo_id}.pdf"},
        )
    except GitHubPRDashboardException as e:
        raise secure_error_handler(e)
    except Exception as e:
        raise secure_error_handler(e)

@router.get("/api/features")
def get_all_features():
    """Get all available features and metrics"""
    return {
        "dashboard_name": "GitHub PR Intelligence Dashboard",
        "version": "1.0.0",
        "features": {
            "data_extraction": {
                "description": "Extracts comprehensive GitHub PR data",
                "items": [
                    "Pull Requests (title, state, dates, metrics)",
                    "Reviews (reviewer, state, timestamps)",
                    "Commits (count per PR)",
                    "Contributors (activity, merge rates)",
                    "File changes (additions, deletions)",
                    "Comments and labels"
                ]
            },
            "analytics_metrics": {
                "description": "20+ calculated metrics without ML",
                "kpi_cards": [
                    {
                        "name": "Open PRs",
                        "description": "Count of currently open pull requests",
                        "unit": "count"
                    },
                    {
                        "name": "Stale PRs",
                        "description": "PRs open for 30+ days",
                        "unit": "count"
                    },
                    {
                        "name": "Avg Cycle Time",
                        "description": "Average days from creation to merge",
                        "unit": "days"
                    },
                    {
                        "name": "Merge Rate",
                        "description": "Percentage of merged vs closed PRs",
                        "unit": "%"
                    },
                    {
                        "name": "Avg Review Duration",
                        "description": "Average review process time",
                        "unit": "days"
                    },
                    {
                        "name": "Avg Wait for Review",
                        "description": "Average time until first review",
                        "unit": "days"
                    }
                ],
                "additional_metrics": [
                    "PR Throughput (weekly)",
                    "Monthly PR Flow (created vs merged vs closed)",
                    "Contributor Activity",
                    "Oldest Open PRs",
                    "Slowest Merged PRs",
                    "Median Cycle Time"
                ]
            },
            "charts": {
                "description": "Interactive data visualizations",
                "types": [
                    {
                        "name": "Monthly PR Flow",
                        "type": "Stacked Bar Chart",
                        "shows": "Created vs Merged vs Closed PRs by month"
                    },
                    {
                        "name": "PR Throughput",
                        "type": "Line Chart",
                        "shows": "Weekly PR merge trends"
                    },
                    {
                        "name": "Contributor Activity",
                        "type": "Bar Chart",
                        "shows": "Total and merged PRs per contributor"
                    }
                ]
            },
            "tables": {
                "description": "Detailed data tables",
                "types": [
                    {
                        "name": "Oldest Open PRs",
                        "columns": ["#", "Title", "Age (days)", "Author", "Reviews"]
                    },
                    {
                        "name": "Slowest Merged PRs",
                        "columns": ["#", "Title", "Cycle Time (days)", "Author", "Files Changed"]
                    },
                    {
                        "name": "Contributor Activity",
                        "columns": ["Username", "Total PRs", "Merged", "Avg Cycle Time", "Merge Rate %"]
                    }
                ]
            },
            "statistical_engineering_analytics": {
                "description": "Deterministic heuristic and repo-relative statistical scoring (no trained ML deserialization)",
                "signals": [
                    {
                        "name": "Merge delay outlook",
                        "method": "Weighted blend of age, churn, review depth, contributor baselines",
                        "inputs": ["files_changed", "commit_count", "review_count", "lines_added", "lines_deleted"],
                    },
                    {
                        "name": "Bottleneck pressure",
                        "method": "Review wait / activity imbalance heuristics",
                        "inputs": ["wait_for_review_hours", "review_duration_hours", "comment_count", "commit_count"],
                    },
                    {
                        "name": "Risk index",
                        "method": "Rule + distribution-based signals scaled 0–100",
                        "inputs": ["change_requests", "reviews", "churn", "age", "contributor_merge_rate"],
                    },
                    {
                        "name": "Review wait outlook",
                        "method": "Hours-to-first-review style signals from timeline data",
                        "inputs": ["reviewer_count", "files_changed", "comment_count", "author_activity"],
                    },
                    {
                        "name": "Contributor patterns",
                        "method": "Aggregated merge/cycle/review stats per author (no clustering artifacts loaded from disk)",
                        "inputs": ["merged_prs", "avg_cycle_time", "review_activity", "stale_pr_count"],
                    },
                ],
            }
        },
        "api_endpoints": {
            "analysis": {
                "POST /api/analyze": "Analyze a GitHub repository",
                "parameters": {
                    "url": "GitHub repository URL (e.g., https://github.com/owner/repo)",
                    "github_token": "Optional - for private repos or higher rate limits"
                }
            },
            "metrics": {
                "GET /api/kpi/{repo_id}": "Get KPI summary",
                "GET /api/oldest-prs/{repo_id}": "Get oldest open PRs",
                "GET /api/slowest-prs/{repo_id}": "Get slowest merged PRs",
                "GET /api/contributor-activity/{repo_id}": "Get contributor stats",
                "GET /api/monthly-flow/{repo_id}": "Get monthly PR flow",
                "GET /api/throughput/{repo_id}": "Get PR throughput"
            },
            "info": {
                "GET /api/features": "Get all features and metrics",
                "GET /api/health": "Health check",
                "GET /api/system-status": "System status and diagnostics"
            }
        },
        "health_checks": {
            "database": "PostgreSQL/SQLite connection and schema",
            "github_api": "GitHub GraphQL API connectivity",
            "pr_analytics_engine": "Statistical analytics module availability (no unsafe model load)",
            "data_integrity": "PR data consistency"
        },
        "supported_repositories": {
            "public": "All public repositories",
            "private": "Private repositories (requires token with 'repo' scope)",
            "requirements": [
                "Repository must be accessible with provided token",
                "Token must have 'public_repo' scope for public repos",
                "Token must have 'repo' scope for private repos"
            ]
        },
        "limitations": {
            "pr_limit": "Configurable fetch limit (default 100 PRs)",
            "rate_limit": "60 requests/hour without token, 5000 with token",
            "response_time": "3-15 seconds per repository",
            "data_retention": "Stored in configured database"
        },
        "tech_stack": {
            "backend": "FastAPI, SQLAlchemy, Python",
            "frontend": "Next.js, TypeScript, Tailwind CSS, Recharts",
            "database": "PostgreSQL (Production) / SQLite (Local fallback)",
            "analytics_engine": "Statistical and heuristic PR intelligence (no serialized model deserialization)"
        }
    }

@router.get("/health")
async def health():
    """Service health status endpoint with detailed DB and Cache checks"""
    db_health = await check_db_health()
    redis_health = redis_cache.check_health()
    status = "ok" if db_health["status"] == "healthy" else "degraded"
    return {
        "status": status,
        "database": db_health,
        "cache": redis_health
    }

@router.get("/api/system-status")
async def get_system_status(db: Session = Depends(get_db)):
    """Get system status and diagnostics"""
    from database.models import Repository, PullRequest, Contributor
    
    try:
        # Count data
        repo_count = db.query(Repository).count()
        pr_count = db.query(PullRequest).count()
        contributor_count = db.query(Contributor).count()
        
        # Check database health
        db_health = await check_db_health()
        db_status = "Connected" if db_health["status"] == "healthy" else "Degraded"
        
        # Check Redis cache health
        redis_health = redis_cache.check_health()
        redis_status = "Available" if redis_health["status"] == "healthy" else "Unavailable"
        
        # Check GitHub API
        try:
            from github.client import GitHubClient
            client = GitHubClient()
            github_status = "Available"
        except Exception as e:
            github_status = f"Error: {str(e)}"
        
        # Analytics engine facade (no pickle/joblib model loading at runtime)
        try:
            from ml.models import MLModels

            _ = MLModels()
            analytics_status = "Active (statistical)"
        except Exception as e:
            analytics_status = f"Warning: {str(e)}"
        
        return {
            "status": "healthy" if db_health["status"] == "healthy" and redis_health["status"] == "healthy" else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": {
                "status": db_status,
                "repositories": repo_count,
                "pull_requests": pr_count,
                "contributors": contributor_count,
                "details": db_health["details"]
            },
            "services": {
                "github_api": github_status,
                "pr_analytics_engine": analytics_status,
                "database": db_status,
                "redis_cache": redis_status
            },
            "health_checks": {
                "database_connection": "Pass" if db_health["status"] == "healthy" else "Fail",
                "redis_cache_access": "Pass" if redis_health["status"] == "healthy" else "Fail",
                "github_api_access": "Pass" if "Available" in github_status else "Fail",
                "analytics_engine_ready": "Pass" if "Active" in analytics_status else "Warning",
                "data_integrity": "Pass" if pr_count > 0 else "No data"
            },
            "recommendations": [
                "Analyze more repositories for richer statistical baselines"
                if pr_count < 100
                else "Good data volume for repo-relative scoring",
                "Check GitHub token if API access fails" if "Error" in github_status else "GitHub API working",
                "Review analytics_engine service if diagnostics show warnings"
                if "Warning" in analytics_status
                else "Statistical analytics engine operational",
                "Start Redis server if cache access fails" if redis_health["status"] != "healthy" else "Redis cache active"
            ]
        }
    except Exception as e:
        logger.error("System status failed: %s", e, exc_info=True)
        return {
            "status": "error",
            "error": "Unable to retrieve system status.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
