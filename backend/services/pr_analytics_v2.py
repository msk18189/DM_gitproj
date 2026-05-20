"""
Statistical PR analytics engine — continuous, PR-specific scores from real GitHub metrics.

Repo-level distributions are used only for normalization (percentile ranks), never copied
onto individual PRs as their score.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from database.models import PullRequest
from services.filters import ensure_utc, format_duration
from services.statistical_scoring import (
    clamp,
    hours_between,
    log_ratio,
    percentile_rank,
    robust_percentile,
    sigmoid,
    weighted_score,
)
from utils.logging_config import get_logger

logger = get_logger("pr_analytics_v2")

SCORE_SOURCE = "statistical_v2"


class RepositoryDistributions:
    """Empirical distributions for normalization — not applied as PR scores."""

    def __init__(self, db: Session, repo_id: int):
        self.db = db
        self.repo_id = repo_id
        self._bundle: Optional[Dict[str, Any]] = None

    def get(self) -> Dict[str, Any]:
        if self._bundle is not None:
            return self._bundle

        prs = (
            self.db.query(PullRequest)
            .filter(PullRequest.repo_id == self.repo_id)
            .all()
        )
        now = ensure_utc(datetime.now(timezone.utc))

        if not prs:
            self._bundle = self._empty()
            return self._bundle

        open_prs = [p for p in prs if p.state == "OPEN"]
        closed = [p for p in prs if p.state in ("MERGED", "CLOSED")]

        age_hours_open = []
        code_changes = []
        files_changed = []
        wait_hours = []
        review_durations = []
        commit_counts = []
        comment_counts = []
        cycle_days = []

        for pr in prs:
            code = float((pr.lines_added or 0) + (pr.lines_deleted or 0))
            files = float(pr.files_changed or 0)
            commits = float(pr.commit_count or 0)
            comments = float(pr.comment_count or 0)
            code_changes.append(code)
            files_changed.append(files)
            commit_counts.append(commits)
            comment_counts.append(comments)

            w = float(pr.wait_for_review_hours or 0)
            if w > 0:
                wait_hours.append(w)

            rd = float(pr.review_duration_hours or 0)
            if rd > 0:
                review_durations.append(rd)

            if pr.cycle_time_days and pr.cycle_time_days > 0:
                cycle_days.append(float(pr.cycle_time_days))

        for pr in open_prs:
            if pr.created_at:
                age_hours_open.append(
                    hours_between(ensure_utc(pr.created_at), now)
                )

        open_by_author: Dict[str, int] = {}
        for pr in open_prs:
            if pr.author:
                open_by_author[pr.author] = open_by_author.get(pr.author, 0) + 1

        author_open_counts = list(open_by_author.values()) or [0]

        self._bundle = {
            "total_prs": len(prs),
            "open_prs_count": len(open_prs),
            "age_hours_open": age_hours_open,
            "code_changes": code_changes,
            "files_changed": files_changed,
            "wait_hours": wait_hours,
            "review_durations": review_durations,
            "commit_counts": commit_counts,
            "comment_counts": comment_counts,
            "cycle_days": cycle_days,
            "median_cycle_days": robust_percentile(cycle_days, 50) or 3.0,
            "p75_cycle_days": robust_percentile(cycle_days, 75) or 5.0,
            "p90_wait_hours": robust_percentile(wait_hours, 90) or 48.0,
            "median_wait_hours": robust_percentile(wait_hours, 50) or 12.0,
            "median_files": robust_percentile(files_changed, 50) or 1.0,
            "p90_code": robust_percentile(code_changes, 90) or 500.0,
            "median_code": robust_percentile(code_changes, 50) or 100.0,
            "median_age_hours": robust_percentile(age_hours_open, 50) or 24.0,
            "p75_age_hours": robust_percentile(age_hours_open, 75) or 168.0,
            "median_open_per_author": robust_percentile(author_open_counts, 50) or 1.0,
            "prs_with_no_reviews": sum(
                1 for p in open_prs if (p.review_count or 0) == 0
            ),
        }
        return self._bundle

    @staticmethod
    def _empty() -> Dict[str, Any]:
        return {
            "total_prs": 0,
            "open_prs_count": 0,
            "age_hours_open": [],
            "code_changes": [],
            "files_changed": [],
            "wait_hours": [],
            "review_durations": [],
            "commit_counts": [],
            "comment_counts": [],
            "cycle_days": [],
            "median_cycle_days": 3.0,
            "p75_cycle_days": 5.0,
            "p90_wait_hours": 48.0,
            "median_wait_hours": 12.0,
            "median_files": 1.0,
            "p90_code": 500.0,
            "median_code": 100.0,
            "median_age_hours": 24.0,
            "p75_age_hours": 168.0,
            "median_open_per_author": 1.0,
            "prs_with_no_reviews": 0,
        }


class PRStatisticalEngine:
    """Compute continuous PR-level analytics from measured features."""

    def __init__(self, db: Session, repo_id: int):
        self.db = db
        self.repo_id = repo_id
        self.distributions = RepositoryDistributions(db, repo_id)

    def compute_scores(
        self, pr: PullRequest, now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        now = now or ensure_utc(datetime.now(timezone.utc))
        dist = self.distributions.get()
        features = self._build_features(pr, dist, now)

        risk = self._risk_score(features, dist)
        bottleneck = self._bottleneck_score(features, dist)
        delay_days = self._delay_days(features, dist)
        review_wait_h = self._review_wait_hours(features, dist)
        merge_complexity = self._merge_complexity(features, dist)
        stale_prob = self._stale_probability(features, dist)

        logger.info(
            "PR #%s analytics: risk=%.1f%% bottleneck=%.1f%% delay=%.2fd "
            "review_wait=%.1fh stale_prob=%.1f%% age_h=%.1f files=%.0f reviews=%.0f",
            pr.pr_number,
            risk,
            bottleneck,
            delay_days,
            review_wait_h,
            stale_prob,
            features["age_hours"],
            features["files_changed"],
            features["review_count"],
        )

        return {
            "risk_score": risk,
            "bottleneck_probability": bottleneck,
            "predicted_delay_days": delay_days,
            "predicted_review_wait_hours": review_wait_h,
            "predicted_review_wait_display": (
                None
                if review_wait_h is None
                else format_duration(review_wait_h)
            ),
            "merge_complexity": merge_complexity,
            "stale_probability": stale_prob,
            "contributor_merge_rate": features["contributor_merge_rate"],
            "predicted_delay_display": format_duration(delay_days * 24),
            "source": SCORE_SOURCE,
            "features_used": list(features.keys()),
        }

    def _build_features(
        self, pr: PullRequest, dist: Dict[str, Any], now: datetime
    ) -> Dict[str, float]:
        created = ensure_utc(pr.created_at) if pr.created_at else now
        age_hours = hours_between(created, now)
        age_days = age_hours / 24.0

        files_changed = float(pr.files_changed or 0)
        lines_added = float(pr.lines_added or 0)
        lines_deleted = float(pr.lines_deleted or 0)
        code_changes = lines_added + lines_deleted
        review_count = float(pr.review_count or 0)
        comment_count = float(pr.comment_count or 0)
        commit_count = float(pr.commit_count or 0)

        stored_wait = float(pr.wait_for_review_hours or 0)
        if stored_wait > 0:
            effective_wait_hours = stored_wait
        elif review_count == 0 and pr.state == "OPEN":
            effective_wait_hours = age_hours
        else:
            effective_wait_hours = stored_wait

        review_duration = float(pr.review_duration_hours or 0)

        author_prs = self._author_pr_counts(pr.author)
        merged = author_prs.get("merged", 0)
        total_author = author_prs.get("total", 1)
        open_author = author_prs.get("open", 0)
        merge_rate = (merged / total_author * 100.0) if total_author else 50.0

        reviews_per_day = review_count / max(age_days, 0.04)
        commits_per_day = commit_count / max(age_days, 0.04)
        comments_per_day = comment_count / max(age_days, 0.04)

        churn = commit_count / max(files_changed, 1.0)

        return {
            "age_hours": age_hours,
            "age_days": age_days,
            "files_changed": files_changed,
            "code_changes": code_changes,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "review_count": review_count,
            "comment_count": comment_count,
            "commit_count": commit_count,
            "wait_hours": effective_wait_hours,
            "stored_wait_hours": stored_wait,
            "review_duration_hours": review_duration,
            "reviews_per_day": reviews_per_day,
            "commits_per_day": commits_per_day,
            "comments_per_day": comments_per_day,
            "churn": churn,
            "contributor_merge_rate": merge_rate,
            "contributor_open_prs": float(open_author),
            "is_open": 1.0 if pr.state == "OPEN" else 0.0,
        }

    def _author_pr_counts(self, author: Optional[str]) -> Dict[str, int]:
        if not author:
            return {"total": 1, "merged": 0, "open": 0}
        prs = (
            self.db.query(PullRequest)
            .filter(
                PullRequest.repo_id == self.repo_id,
                PullRequest.author == author,
            )
            .all()
        )
        return {
            "total": len(prs) or 1,
            "merged": sum(1 for p in prs if p.state == "MERGED"),
            "open": sum(1 for p in prs if p.state == "OPEN"),
        }

    def _risk_score(self, f: Dict[str, float], dist: Dict[str, Any]) -> float:
        age_factor = percentile_rank(f["age_hours"], dist["age_hours_open"])
        if not dist["age_hours_open"]:
            age_factor = sigmoid(f["age_days"], steepness=0.35, midpoint=14.0)

        size_factor = percentile_rank(f["code_changes"], dist["code_changes"])
        files_factor = percentile_rank(f["files_changed"], dist["files_changed"])

        wait_factor = percentile_rank(f["wait_hours"], dist["wait_hours"])
        if f["review_count"] == 0 and f["is_open"]:
            wait_factor = max(
                wait_factor,
                sigmoid(f["age_days"], steepness=0.4, midpoint=5.0),
            )

        stale_factor = sigmoid(
            f["age_days"],
            steepness=0.25,
            midpoint=dist["median_age_hours"] / 24.0 + 7.0,
        )

        complexity_factor = clamp(
            (
                log_ratio(f["code_changes"], dist["p90_code"])
                + log_ratio(f["files_changed"], dist["median_files"] * 3)
                + log_ratio(f["churn"], 8.0)
            )
            / 3.0,
            0.0,
            1.0,
        )

        engagement_gap = clamp(
            sigmoid(f["comments_per_day"] * 3.0, steepness=1.2, midpoint=1.0)
            * (1.0 - min(1.0, f["reviews_per_day"] * 2.0)),
            0.0,
            1.0,
        )

        author_risk = sigmoid(
            100.0 - f["contributor_merge_rate"],
            steepness=0.08,
            midpoint=50.0,
        )

        return weighted_score(
            {
                "age": age_factor,
                "size": size_factor * 0.6 + files_factor * 0.4,
                "review_delay": wait_factor,
                "stale": stale_factor,
                "complexity": complexity_factor,
                "engagement_gap": engagement_gap,
                "author": author_risk * 0.5,
            },
            {
                "age": 0.22,
                "size": 0.18,
                "review_delay": 0.22,
                "stale": 0.18,
                "complexity": 0.10,
                "engagement_gap": 0.05,
                "author": 0.05,
            },
        )

    def _bottleneck_score(self, f: Dict[str, float], dist: Dict[str, Any]) -> float:
        review_delay = percentile_rank(f["wait_hours"], dist["wait_hours"])
        if f["review_count"] == 0 and f["is_open"]:
            review_delay = max(
                review_delay,
                percentile_rank(f["age_hours"], dist["age_hours_open"]),
            )

        stale_days = sigmoid(
            f["age_days"],
            steepness=0.3,
            midpoint=dist["p75_age_hours"] / 24.0,
        )

        median_open = dist["median_open_per_author"] or 1.0
        reviewer_load = sigmoid(
            f["contributor_open_prs"],
            steepness=1.5,
            midpoint=median_open,
        )

        review_stuck = 0.0
        if f["review_duration_hours"] > 0 and dist["review_durations"]:
            review_stuck = percentile_rank(
                f["review_duration_hours"], dist["review_durations"]
            )

        size_drag = clamp(
            log_ratio(f["files_changed"], dist["median_files"] * 2), 0.0, 1.0
        )

        return weighted_score(
            {
                "review_delay": review_delay,
                "stale": stale_days,
                "reviewer_load": reviewer_load,
                "review_stuck": review_stuck,
                "size_drag": size_drag * 0.6,
            },
            {
                "review_delay": 0.38,
                "stale": 0.28,
                "reviewer_load": 0.22,
                "review_stuck": 0.07,
                "size_drag": 0.05,
            },
        )

    def _delay_days(self, f: Dict[str, float], dist: Dict[str, Any]) -> float:
        """Estimated days until merge — unique per PR from velocity + load + size."""
        if not f["is_open"]:
            return round(max(f["age_days"], 0.1), 2)

        base_velocity = max(dist["median_cycle_days"], 0.5)
        size_p = percentile_rank(f["code_changes"], dist["code_changes"])
        files_p = percentile_rank(f["files_changed"], dist["files_changed"])
        wait_p = percentile_rank(f["wait_hours"], dist["wait_hours"] or [f["wait_hours"]])

        size_blend = 0.25 + 0.75 * (size_p * 0.65 + files_p * 0.35)
        wait_blend = 0.20 + 0.80 * wait_p
        author_blend = 0.70 + 0.30 * (f["contributor_merge_rate"] / 100.0)
        queue_blend = 1.0 + 0.18 * max(
            0.0, f["contributor_open_prs"] - dist["median_open_per_author"]
        )
        review_blend = 1.12 if f["review_count"] == 0 else 0.92 + 0.08 * min(
            f["reviews_per_day"], 1.0
        )
        churn_blend = 1.0 + 0.06 * min(f["churn"], 15.0)

        remaining = (
            base_velocity
            * size_blend
            * wait_blend
            * author_blend
            * queue_blend
            * review_blend
            * churn_blend
        )

        estimated = f["age_days"] + remaining
        per_pr_cap = f["age_days"] + dist["p75_cycle_days"] * (1.2 + size_blend * 0.8)
        return round(clamp(estimated, 0.15, min(per_pr_cap, 120.0)), 2)

    def _review_wait_hours(
        self, f: Dict[str, float], dist: Dict[str, Any]
    ) -> Optional[float]:
        """Actual measured wait, or elapsed time since open if no reviews yet."""
        if f["stored_wait_hours"] > 0:
            return round(min(f["stored_wait_hours"], 720.0), 1)

        if f["review_count"] == 0 and f["is_open"]:
            return round(f["age_hours"], 1)

        if f["review_count"] > 0 and f["stored_wait_hours"] <= 0:
            return 0.0

        return None

    def _merge_complexity(self, f: Dict[str, float], dist: Dict[str, Any]) -> float:
        size_c = percentile_rank(f["code_changes"], dist["code_changes"])
        files_c = percentile_rank(f["files_changed"], dist["files_changed"])
        review_c = clamp(1.0 - min(1.0, f["reviews_per_day"] * 1.5), 0.0, 1.0)
        churn_c = clamp(log_ratio(f["churn"], 10.0), 0.0, 1.0)

        return weighted_score(
            {
                "size": size_c,
                "files": files_c,
                "review_gap": review_c,
                "churn": churn_c,
            },
            {"size": 0.35, "files": 0.30, "review_gap": 0.20, "churn": 0.15},
        )

    def _stale_probability(self, f: Dict[str, float], dist: Dict[str, Any]) -> float:
        age_p = percentile_rank(f["age_hours"], dist["age_hours_open"])
        inactivity = clamp(
            sigmoid(f["age_days"], 0.35, 21.0)
            * (1.0 - min(1.0, f["commits_per_day"] * 5.0))
            * (1.0 - min(1.0, f["reviews_per_day"] * 4.0)),
            0.0,
            1.0,
        )
        no_review = 0.85 if f["review_count"] == 0 and f["age_days"] > 3 else 0.0

        return weighted_score(
            {"age": age_p, "inactivity": inactivity, "no_review": no_review},
            {"age": 0.45, "inactivity": 0.40, "no_review": 0.15},
        )


def build_dynamic_stale_reasons(
    pr: PullRequest,
    now: Optional[datetime] = None,
    stale_days: int = 30,
) -> tuple[List[str], List[str], str]:
    """
    PR-specific stale reasons from timestamps and activity rates.
    Returns (reasons, actions, severity).
    """
    now = now or ensure_utc(datetime.now(timezone.utc))
    if not pr.created_at:
        return [], [], "low"

    created = ensure_utc(pr.created_at)
    age_hours = hours_between(created, now)
    age_days = age_hours / 24.0
    reasons: List[str] = []
    actions: List[str] = []
    severity = "low"

    review_count = pr.review_count or 0
    commit_count = pr.commit_count or 0
    comment_count = pr.comment_count or 0
    wait_h = float(pr.wait_for_review_hours or 0)

    if age_days >= stale_days:
        reasons.append(
            f"Open for {age_days:.1f} days (threshold {stale_days}d)"
        )
        actions.append("Prioritize review or close if obsolete")
        severity = "high"
    elif age_days >= 14:
        reasons.append(f"Open for {age_days:.1f} days without merge")
        actions.append("Schedule review this week")
        severity = "medium"

    if review_count == 0:
        reasons.append(f"No reviews for {age_days:.1f} days")
        actions.append("Assign a reviewer")
        severity = "high"
    elif wait_h > 0:
        reasons.append(f"First review after {wait_h / 24:.1f} days")
        if wait_h > 72:
            severity = "high" if severity != "high" else severity
            actions.append("Escalate reviewer assignment")

    if commit_count == 0 and age_days >= 1:
        reasons.append(f"No commits recorded in {age_days:.1f} days")
        actions.append("Confirm branch activity or close draft PR")
        if severity == "low":
            severity = "medium"
    else:
        commits_per_day = commit_count / max(age_days, 0.1)
        if commits_per_day < 0.08 and age_days >= 7:
            reasons.append(
                f"Low commit activity ({commits_per_day:.2f} commits/day)"
            )
            actions.append("Check if PR is still in active development")

    if comment_count > 0 and review_count < 2:
        comments_per_day = comment_count / max(age_days, 0.1)
        if comments_per_day > 0.5:
            reasons.append(
                f"Active discussion ({comment_count} comments) but only "
                f"{review_count} formal review(s)"
            )
            actions.append("Convert discussion into explicit review approval")

    files = pr.files_changed or 0
    if files > 20:
        reasons.append(f"Large diff ({files} files changed)")
        actions.append("Consider splitting into smaller PRs")
        if severity == "low":
            severity = "medium"

    return reasons, actions, severity


def compute_heuristic_scores_v2(
    pr: PullRequest, db: Session, now: Optional[datetime] = None
) -> Dict[str, Any]:
    """Public entry: continuous statistical scores for one PR."""
    try:
        engine = PRStatisticalEngine(db, pr.repo_id)
        return engine.compute_scores(pr, now)
    except Exception as e:
        logger.error("Statistical analytics failed for PR %s: %s", pr.pr_number, e)
        raise
