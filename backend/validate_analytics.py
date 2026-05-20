"""
Validation script for PR analytics V2.

Demonstrates that the new system produces:
- Dynamic PR-specific scores (not identical)
- Realistic variation based on PR characteristics
- Proper handling of edge cases

Run this after processing a repository to validate.
"""

import sys
from datetime import datetime, timezone, timedelta
from database.db import SessionLocal
from database.models import PullRequest, Repository
from services.pr_analytics_v2 import compute_heuristic_scores_v2
from services.risk_heuristics import compute_heuristic_scores
from utils.logging_config import get_logger

logger = get_logger("validation")


def validate_analytics_diversity():
    """Validate that scores are diverse and realistic."""
    db = SessionLocal()
    
    try:
        # Get repositories
        repos = db.query(Repository).all()
        
        if not repos:
            logger.info("No repositories in database. Skipping validation.")
            return
        
        logger.info(f"Validating analytics for {len(repos)} repositories")
        
        for repo in repos:
            logger.info(f"\n{'='*80}")
            logger.info(f"Repository: {repo.owner}/{repo.name}")
            logger.info(f"{'='*80}")
            
            # Get open PRs
            open_prs = db.query(PullRequest).filter(
                PullRequest.repo_id == repo.id,
                PullRequest.state == "OPEN"
            ).all()
            
            if not open_prs:
                logger.info("No open PRs. Skipping.")
                continue
            
            logger.info(f"Found {len(open_prs)} open PRs")
            
            # Collect scores
            scores_v2 = []
            scores_legacy = []
            
            now = datetime.now(timezone.utc)
            
            for pr in open_prs[:10]:  # Limit to first 10 for display
                try:
                    # Get V2 scores
                    v2 = compute_heuristic_scores_v2(pr, db, now)
                    scores_v2.append({
                        "number": pr.pr_number,
                        "title": pr.title[:40],
                        "risk": v2["risk_score"],
                        "bottleneck": v2["bottleneck_probability"],
                        "delay": v2["predicted_delay_days"],
                        "review_wait": v2["predicted_review_wait_hours"],
                    })
                    
                    # Get legacy scores for comparison
                    legacy = compute_heuristic_scores(pr, now)
                    scores_legacy.append({
                        "number": pr.pr_number,
                        "risk": legacy["risk_score"],
                        "bottleneck": legacy["bottleneck_probability"],
                        "delay": legacy["predicted_delay_days"],
                        "review_wait": legacy["predicted_review_wait_hours"],
                    })
                except Exception as e:
                    logger.error(f"Error processing PR {pr.pr_number}: {str(e)}")
            
            # Analyze diversity
            if scores_v2:
                _analyze_scores(scores_v2, "V2 (Dynamic)")
                _analyze_scores(scores_legacy, "Legacy (Static)")
                _compare_scores(scores_v2, scores_legacy)
    
    finally:
        db.close()


def _analyze_scores(scores: list, label: str) -> None:
    """Analyze score diversity."""
    if not scores:
        return
    
    logger.info(f"\n{label} Scores Analysis:")
    logger.info("-" * 60)
    
    # Extract individual metrics
    risks = [s["risk"] for s in scores]
    bottlenecks = [s["bottleneck"] for s in scores]
    delays = [s["delay"] for s in scores]
    
    # Calculate statistics
    logger.info(f"Risk Score Distribution:")
    logger.info(f"  Min: {min(risks):.1f}, Max: {max(risks):.1f}, Range: {max(risks) - min(risks):.1f}")
    logger.info(f"  Avg: {sum(risks)/len(risks):.1f}, StdDev: {_stddev(risks):.1f}")
    logger.info(f"  Unique values: {len(set(round(r, 1) for r in risks))}/{len(risks)}")
    
    logger.info(f"Bottleneck Distribution:")
    logger.info(f"  Min: {min(bottlenecks):.1f}, Max: {max(bottlenecks):.1f}, Range: {max(bottlenecks) - min(bottlenecks):.1f}")
    logger.info(f"  Avg: {sum(bottlenecks)/len(bottlenecks):.1f}, StdDev: {_stddev(bottlenecks):.1f}")
    logger.info(f"  Unique values: {len(set(round(b, 1) for b in bottlenecks))}/{len(bottlenecks)}")
    
    logger.info(f"Delay Days Distribution:")
    logger.info(f"  Min: {min(delays):.1f}, Max: {max(delays):.1f}, Range: {max(delays) - min(delays):.1f}")
    logger.info(f"  Avg: {sum(delays)/len(delays):.1f}, StdDev: {_stddev(delays):.1f}")
    
    # Show all scores for review
    logger.info(f"\nAll {label} Scores:")
    logger.info("PR#     Risk    Bottleneck  Delay   Title")
    logger.info("-" * 60)
    for score in scores:
        logger.info(
            f"{score['number']:5d}  {score['risk']:6.1f}  {score['bottleneck']:6.1f}    "
            f"{score['delay']:5.1f}d  {score['title']}"
        )


def _compare_scores(v2_scores: list, legacy_scores: list) -> None:
    """Compare V2 vs Legacy scores."""
    logger.info(f"\n{'='*60}")
    logger.info("V2 vs Legacy Comparison:")
    logger.info("-" * 60)
    
    # Check if V2 has more diversity
    v2_risks = [s["risk"] for s in v2_scores]
    legacy_risks = [s["risk"] for s in legacy_scores]
    
    v2_unique = len(set(round(r, 1) for r in v2_risks))
    legacy_unique = len(set(round(r, 1) for r in legacy_risks))
    
    logger.info(f"Risk Score Uniqueness:")
    logger.info(f"  V2:     {v2_unique} unique values out of {len(v2_scores)}")
    logger.info(f"  Legacy: {legacy_unique} unique values out of {len(legacy_scores)}")
    
    if v2_unique > legacy_unique:
        logger.info(f"  ✓ V2 produces MORE varied scores (+{v2_unique - legacy_unique})")
    elif v2_unique < legacy_unique:
        logger.info(f"  ✗ V2 produces FEWER varied scores (-{legacy_unique - v2_unique})")
    else:
        logger.info(f"  = V2 and Legacy have same diversity")
    
    # Check variance
    v2_range = max(v2_risks) - min(v2_risks)
    legacy_range = max(legacy_risks) - min(legacy_risks)
    
    logger.info(f"\nRisk Score Range:")
    logger.info(f"  V2:     {min(v2_risks):.1f} - {max(v2_risks):.1f} (range: {v2_range:.1f})")
    logger.info(f"  Legacy: {min(legacy_risks):.1f} - {max(legacy_risks):.1f} (range: {legacy_range:.1f})")
    
    if v2_range > legacy_range:
        logger.info(f"  ✓ V2 has wider score distribution (+{v2_range - legacy_range:.1f})")
    else:
        logger.info(f"  ✗ V2 has narrower score distribution (-{legacy_range - v2_range:.1f})")
    
    logger.info(f"\n{'='*60}")


def _stddev(values: list) -> float:
    """Calculate standard deviation."""
    if not values or len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5


if __name__ == "__main__":
    try:
        validate_analytics_diversity()
        logger.info("\n✓ Validation complete!")
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}", exc_info=True)
        sys.exit(1)
