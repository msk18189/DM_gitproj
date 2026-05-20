from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from database.db import Base
from datetime import datetime

class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True)
    owner = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    url = Column(String, unique=True)
    last_synced = Column(DateTime, default=datetime.utcnow)

class PullRequest(Base):
    __tablename__ = "pull_requests"
    
    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, nullable=False, index=True)
    pr_number = Column(Integer, index=True)
    title = Column(String)
    state = Column(String, index=True)
    created_at = Column(DateTime, index=True)
    merged_at = Column(DateTime, nullable=True, index=True)
    closed_at = Column(DateTime, nullable=True)
    commit_count = Column(Integer, default=0)
    files_changed = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    author = Column(String, index=True)
    cycle_time_days = Column(Float, nullable=True)
    wait_for_review_hours = Column(Float, nullable=True)
    review_duration_hours = Column(Float, nullable=True)

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True)
    pr_id = Column(Integer, nullable=False, index=True)
    reviewer = Column(String, index=True)
    state = Column(String)
    submitted_at = Column(DateTime)
    comment_count = Column(Integer, default=0)

class Contributor(Base):
    __tablename__ = "contributors"
    
    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, nullable=False, index=True)
    username = Column(String, index=True)
    total_prs = Column(Integer, default=0)
    merged_prs = Column(Integer, default=0)
    avg_cycle_time = Column(Float, default=0)
    avg_review_time = Column(Float, default=0)
    stale_pr_count = Column(Integer, default=0)

class MLPrediction(Base):
    """Cached PR scores from statistical/heuristic analytics (table name is historical)."""

    __tablename__ = "ml_predictions"
    
    id = Column(Integer, primary_key=True)
    pr_id = Column(Integer, nullable=False, index=True)
    predicted_delay_days = Column(Float, nullable=True)
    bottleneck_probability = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    predicted_review_wait = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

