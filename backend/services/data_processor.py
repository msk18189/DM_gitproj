from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database.models import PullRequest, Repository, Contributor, MLPrediction
from github.client import GitHubClient
import numpy as np
from utils.logging_config import get_logger
from utils.exceptions import (
    GitHubPRDashboardException, EmptyRepositoryError, GitHubAPIError
)

from github.utils import parse_github_url

logger = get_logger("data_processor")

class DataProcessor:
    def __init__(self, db: Session):
        self.db = db

    def process_repository(self, repo_url: str, github_token: Optional[str] = None, refresh: bool = False) -> Dict[str, Any]:
        """Process GitHub repository and extract PR data.

        github_token: optional PAT from the user (for private repos or higher limits).
        Falls back to GITHUB_TOKEN in environment when omitted.
        """
        try:
            parsed = parse_github_url(repo_url)
            owner, repo_name = parsed.owner, parsed.repo
            normalized_url = parsed.repo_url

            logger.info(
                "Processing %s/%s mode=%s",
                owner,
                repo_name,
                parsed.mode,
            )
            
            # Check if repo exists in DB
            repo = self.db.query(Repository).filter(
                Repository.owner == owner,
                Repository.name == repo_name
            ).first()
            
            if not repo:
                repo = Repository(owner=owner, name=repo_name, url=normalized_url)
                self.db.add(repo)
                self.db.commit()
                logger.debug(f"Created new repository record: {repo.id}")
            else:
                # Update URL if it was not normalized previously
                if repo.url != normalized_url:
                    repo.url = normalized_url
                    self.db.commit()
                logger.debug(f"Using existing repository record: {repo.id}")
            
            # Fetch PR data from GitHub (user token overrides env for this run)
            client = GitHubClient(token=github_token.strip() if github_token else None)
            
            # Validate repository access before fetching
            logger.debug(f"Validating repository access...")
            repo_info = client.validate_repository(owner, repo_name)
            
            # Log whether it's public or private to help with debugging auth flow
            if repo_info.get("is_private"):
                logger.info(f"Private repository detected. Token is required and active.")
            else:
                logger.info(f"Public repository detected. Tokens are optional.")

            logger.info("Fetching PRs from GitHub...")
            from config import PR_FETCH_LIMIT
            raw_prs = client.fetch_pull_requests(owner, repo_name, limit=PR_FETCH_LIMIT)
            if parsed.mode == "file" and parsed.file_path:
                raw_prs = client.filter_prs_by_file_path(
                    raw_prs, parsed.file_path, branch=parsed.branch
                )
                logger.info(
                    "File-mode filter '%s': %s matching PRs",
                    parsed.file_path,
                    len(raw_prs),
                )
            logger.info("Fetched %s PRs from GitHub", len(raw_prs))
            
            existing_count = self.db.query(PullRequest).filter(
                PullRequest.repo_id == repo.id
            ).count()

            if len(raw_prs) == 0:
                # Empty repository - return graceful response
                if existing_count > 0:
                    logger.info(f"No new PRs from API; using {existing_count} cached PRs")
                    self._update_contributor_stats(repo.id)
                    self.db.commit()
                    return {
                        "success": True,
                        "owner": owner,
                        "repo": repo_name,
                        "prs_processed": 0,
                        "repo_id": repo.id,
                        "total_prs": existing_count,
                        "message": "No new pull requests, showing cached data"
                    }
                else:
                    # Truly empty repository
                    logger.info(f"Repository {owner}/{repo_name} has no pull requests")
                    self.db.commit()
                    return {
                        "success": True,
                        "owner": owner,
                        "repo": repo_name,
                        "prs_processed": 0,
                        "repo_id": repo.id,
                        "total_prs": 0,
                        "message": "This repository has no pull requests"
                    }
            
            # Process and store PRs
            pr_count = 0
            for idx, raw_pr in enumerate(raw_prs):
                try:
                    parsed_pr = client.parse_pr_data(raw_pr)
                    
                    # Check if PR exists
                    existing_pr = self.db.query(PullRequest).filter(
                        PullRequest.repo_id == repo.id,
                        PullRequest.pr_number == parsed_pr["number"]
                    ).first()
                    
                    if existing_pr:
                        existing_pr.title = parsed_pr["title"][:200]
                        existing_pr.state = parsed_pr["state"]
                        existing_pr.merged_at = parsed_pr["merged_at"]
                        existing_pr.closed_at = parsed_pr["closed_at"]
                        existing_pr.commit_count = parsed_pr["commit_count"]
                        existing_pr.files_changed = parsed_pr["files_changed"]
                        existing_pr.lines_added = parsed_pr["lines_added"]
                        existing_pr.lines_deleted = parsed_pr["lines_deleted"]
                        existing_pr.review_count = parsed_pr["review_count"]
                        existing_pr.comment_count = parsed_pr["comment_count"]
                        existing_pr.cycle_time_days = parsed_pr["cycle_time_days"]
                        existing_pr.wait_for_review_hours = parsed_pr["wait_for_review_hours"]
                        existing_pr.review_duration_hours = parsed_pr["review_duration_hours"]
                    else:
                        pr = PullRequest(
                            repo_id=repo.id,
                            pr_number=parsed_pr["number"],
                            title=parsed_pr["title"][:200],
                            state=parsed_pr["state"],
                            created_at=parsed_pr["created_at"],
                            merged_at=parsed_pr["merged_at"],
                            closed_at=parsed_pr["closed_at"],
                            commit_count=parsed_pr["commit_count"],
                            files_changed=parsed_pr["files_changed"],
                            lines_added=parsed_pr["lines_added"],
                            lines_deleted=parsed_pr["lines_deleted"],
                            review_count=parsed_pr["review_count"],
                            comment_count=parsed_pr["comment_count"],
                            author=parsed_pr["author"][:100],
                            cycle_time_days=parsed_pr["cycle_time_days"],
                            wait_for_review_hours=parsed_pr["wait_for_review_hours"],
                            review_duration_hours=parsed_pr["review_duration_hours"],
                        )
                        self.db.add(pr)
                        self.db.flush()
                        existing_pr = pr
                        pr_count += 1

                    self._generate_predictions_safe(existing_pr, parsed_pr)

                    if (idx + 1) % 10 == 0:
                        logger.debug(f"Processed {idx + 1}/{len(raw_prs)} PRs")
                except Exception as e:
                    logger.warning(f"Error processing PR {raw_pr.get('number')}: {str(e)}")
                    continue
            
            logger.info(f"Stored {pr_count} new PRs in database")
            
            # Update contributor stats
            logger.debug(f"Updating contributor statistics")
            self._update_contributor_stats(repo.id)
            
            self.db.commit()
            
            logger.info(f"Successfully processed {pr_count} PRs for {owner}/{repo_name}")
            
            total_prs = self.db.query(PullRequest).filter(
                PullRequest.repo_id == repo.id
            ).count()

            return {
                "success": True,
                "owner": owner,
                "repo": repo_name,
                "prs_processed": pr_count,
                "repo_id": repo.id,
                "total_prs": total_prs,
                "analytics_mode": parsed.mode,
                "file_path": parsed.file_path if parsed.mode == "file" else None,
            }
        except GitHubPRDashboardException:
            # Re-raise our safe exceptions
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing repository: {str(e)}", exc_info=True)
            self.db.rollback()
            raise GitHubAPIError("Failed to process repository", internal_details=str(e))
    
    def _generate_predictions_safe(self, pr: PullRequest, parsed_pr: Dict):
        """Store PR-specific scores from statistical / heuristic analytics (no serialized models)."""
        try:
            from services.pr_analytics_v2 import compute_heuristic_scores_v2
            from services.risk_heuristics import compute_heuristic_scores

            scores = None
            try:
                scores = compute_heuristic_scores_v2(pr, self.db)
            except Exception as e:
                logger.debug("V2 heuristics failed for PR %s: %s", pr.pr_number, e)
                scores = compute_heuristic_scores(pr)

            predicted_delay = float(scores["predicted_delay_days"])
            bottleneck_prob = float(scores["bottleneck_probability"]) / 100.0
            risk_score = float(scores["risk_score"]) / 100.0
            predicted_review_wait = float(scores["predicted_review_wait_hours"])

            self.db.query(MLPrediction).filter(MLPrediction.pr_id == pr.id).delete()
            self.db.add(
                MLPrediction(
                    pr_id=pr.id,
                    predicted_delay_days=predicted_delay,
                    bottleneck_probability=bottleneck_prob,
                    risk_score=risk_score,
                    predicted_review_wait=predicted_review_wait,
                )
            )
        except Exception as e:
            logger.warning("Error generating predictions for PR %s: %s", pr.pr_number, e)
    
    def _update_contributor_stats(self, repo_id: int):
        """Update contributor statistics"""
        try:
            now = datetime.now(timezone.utc)
            
            prs = self.db.query(PullRequest).filter(
                PullRequest.repo_id == repo_id
            ).all()
            
            logger.debug(f"Processing {len(prs)} PRs for contributor stats")
            
            contributor_stats = {}
            for pr in prs:
                if not pr.author:
                    continue
                    
                if pr.author not in contributor_stats:
                    contributor_stats[pr.author] = {
                        "total_prs": 0,
                        "merged_prs": 0,
                        "cycle_times": [],
                        "review_times": [],
                        "stale_count": 0,
                    }
                
                contributor_stats[pr.author]["total_prs"] += 1
                
                if pr.state == "MERGED":
                    contributor_stats[pr.author]["merged_prs"] += 1
                    if pr.cycle_time_days and pr.cycle_time_days > 0:
                        contributor_stats[pr.author]["cycle_times"].append(pr.cycle_time_days)
                
                # Check if PR is stale (open for 30+ days)
                if pr.state == "OPEN" and pr.created_at:
                    created = pr.created_at
                    if created.tzinfo is None:
                        created = created.replace(tzinfo=timezone.utc)
                    else:
                        created = created.astimezone(timezone.utc)
                    age_days = (now - created).days
                    if age_days > 30:
                        contributor_stats[pr.author]["stale_count"] += 1
                
                if pr.review_duration_hours and pr.review_duration_hours > 0:
                    contributor_stats[pr.author]["review_times"].append(pr.review_duration_hours)
            
            # Store or update contributors
            for username, stats in contributor_stats.items():
                try:
                    contributor = self.db.query(Contributor).filter(
                        Contributor.repo_id == repo_id,
                        Contributor.username == username
                    ).first()
                    
                    avg_cycle = np.mean(stats["cycle_times"]) if stats["cycle_times"] else 0.0
                    avg_review = np.mean(stats["review_times"]) if stats["review_times"] else 0.0
                    
                    if contributor:
                        contributor.total_prs = stats["total_prs"]
                        contributor.merged_prs = stats["merged_prs"]
                        contributor.avg_cycle_time = float(avg_cycle)
                        contributor.avg_review_time = float(avg_review)
                        contributor.stale_pr_count = stats["stale_count"]
                    else:
                        contributor = Contributor(
                            repo_id=repo_id,
                            username=username[:100],
                            total_prs=stats["total_prs"],
                            merged_prs=stats["merged_prs"],
                            avg_cycle_time=float(avg_cycle),
                            avg_review_time=float(avg_review),
                            stale_pr_count=stats["stale_count"],
                        )
                        self.db.add(contributor)
                except Exception as e:
                    logger.warning(f"Error updating contributor {username}: {str(e)}")
                    continue
            
            logger.debug(f"Updated {len(contributor_stats)} contributors")
        except Exception as e:
            logger.warning(f"Error updating contributor stats: {str(e)}")
