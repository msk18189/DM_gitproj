import os
import requests
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv
from utils.logging_config import get_logger
from utils.exceptions import (
    GitHubPRDashboardException, GitHubAPIError, RateLimitError, InvalidTokenError,
    RepositoryNotFoundError, PrivateRepositoryError
)

load_dotenv()

logger = get_logger("github_client")


class GitHubClient:
    _semaphore = asyncio.Semaphore(5)

    def __init__(self, token: str = None):
        env_token = os.getenv("GITHUB_TOKEN")
        self.token = (token or "").strip()
        if not self.token and env_token:
            self.token = env_token.strip()
        if not self.token:
            self.token = None

        self.base_url = "https://api.github.com/graphql"
        
        # Build headers - use token if available
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.token:
            clean_token = self.token.strip()
            if clean_token.startswith("github_pat_") or clean_token.startswith("ghp_") or clean_token.startswith("gho_"):
                self.headers["Authorization"] = f"Bearer {clean_token}"
            else:
                self.headers["Authorization"] = f"token {clean_token}"
                
    def query(self, query: str, variables: Dict = None, timeout: int = 60, max_retries: int = 3, initial_delay: float = 1.0) -> Dict:
        """
        Execute GraphQL query with timeout and exponential backoff retry logic.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Executing GraphQL query (attempt {attempt + 1}/{max_retries})")
                response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=timeout)
                logger.debug(f"GitHub API response status: {response.status_code}")
                
                if response.status_code == 401:
                    raise InvalidTokenError(internal_details="GraphQL API returned 401 Unauthorized")
                if response.status_code == 403:
                    body = response.json() if response.content else {}
                    message = body.get("message", "GitHub API rate limit or missing token")
                    if not self.token:
                        raise RateLimitError(internal_details="Rate limit hit without token")
                    raise RateLimitError(internal_details=f"Rate limit: {message}")
                if response.status_code == 429:
                    raise RateLimitError(internal_details="GraphQL rate limit exceeded")
                if response.status_code >= 500:
                    raise GitHubAPIError(f"GitHub server error", status_code=503, internal_details=f"GitHub returned {response.status_code}")
                
                data = response.json()
                
                if "message" in data and "errors" not in data:
                    raise GitHubAPIError(data['message'], status_code=400)
                
                if "errors" in data:
                    error_msg = str(data['errors'])
                    logger.debug(f"GraphQL error: {error_msg}")
                    raise GitHubAPIError("GraphQL query failed", status_code=400, internal_details=error_msg)
                
                return data.get("data", {})
                
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exception = e
                if attempt == max_retries - 1:
                    break
                logger.debug(f"Request failed: {type(e).__name__}. Retrying in {delay}s")
                time.sleep(delay)
                delay *= 2
            except GitHubPRDashboardException:
                raise
            except Exception as e:
                # Immediately raise credential or protocol errors without retry
                if "Bad credentials" in str(e) or "forbidden" in str(e).lower() or "rate limit" in str(e).lower():
                    raise
                last_exception = e
                if attempt == max_retries - 1:
                    break
                logger.debug(f"Error occurred: {str(e)}. Retrying in {delay}s")
                time.sleep(delay)
                delay *= 2
                
        # If all retries failed, raise the final exception
        if last_exception:
            if isinstance(last_exception, requests.exceptions.Timeout):
                raise GitHubAPIError("GitHub API request timed out", status_code=504)
            elif isinstance(last_exception, requests.exceptions.ConnectionError):
                raise GitHubAPIError("Connection error to GitHub API", status_code=503)
            else:
                raise last_exception
        raise GitHubAPIError("Failed to execute GitHub API query after retries", status_code=500)

    async def query_async(self, query: str, variables: Dict = None, timeout: int = 60) -> Dict:
        """
        Asynchronous query wrapper that respects the asyncio.Semaphore limit of 5.
        """
        async with self._semaphore:
            return await asyncio.to_thread(self.query, query, variables, timeout)

    def validate_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Validates the repository using REST API GET /repos/{owner}/{repo}.
        Handles 200, 403, 404, 429, and 503 HTTP status codes correctly.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        current_token = self.token
        headers_with_auth = headers.copy()
        
        if current_token:
            clean_token = current_token.strip()
            if clean_token.startswith("github_pat_") or clean_token.startswith("ghp_"):
                headers_with_auth["Authorization"] = f"Bearer {clean_token}"
            else:
                headers_with_auth["Authorization"] = f"token {clean_token}"
                
        try:
            # Set a safety timeout for validation
            response = requests.get(url, headers=headers_with_auth, timeout=15)
            status = response.status_code
            
            # If 401 Unauthorized or 403 (but NO rate limit message), it might be an invalid token
            # hindering access to a public repo. We retry without token once.
            if (status == 401 or status == 403) and current_token:
                body = response.json() if response.content else {}
                msg = body.get("message", "").lower()
                if "rate limit" not in msg:
                    logger.warning(f"Validation failed (status {status}) with token. Retrying {owner}/{repo} without token...")
                    response = requests.get(url, headers=headers, timeout=15)
                    status = response.status_code

            if status == 200:
                data = response.json()
                is_private = data.get("private", False)
                if is_private and not self.token:
                    raise PrivateRepositoryError(internal_details=f"Repository {owner}/{repo} is private but no token provided.")
                return {
                    "exists": True,
                    "is_private": is_private,
                    "owner": data.get("owner", {}).get("login"),
                    "name": data.get("name"),
                    "permissions": data.get("permissions", {})
                }
            elif status == 403:
                # If we still got 403 after optional retry (or if we had no token), it's either
                # a rate limit or a real access issue.
                body = response.json() if response.content else {}
                message = body.get("message", "").lower()
                if "rate limit" in message:
                    raise RateLimitError(internal_details=f"Rate limit hit during validation: {message}")
                if not self.token:
                    # Might be private, but we don't know for sure if it's 403.
                    raise PrivateRepositoryError(internal_details="403 Forbidden without token - likely private or IP rate limited.")
                raise GitHubAPIError(f"Access forbidden: {message}", status_code=403)
            elif status == 401:
                # 401 after retry means something is very wrong with the second attempt? 
                # Should not happen as second attempt has no headers.
                raise GitHubAPIError("Unauthorized access attempt. Please check your credentials.", status_code=401)
            elif status == 404:
                if not self.token:
                    raise RepositoryNotFoundError(f"{owner}/{repo}", internal_details="Repo not found. If it's private, a token is required.")
                raise RepositoryNotFoundError(f"{owner}/{repo}")
            elif status == 429:
                raise RateLimitError()
            elif status == 503:
                raise GitHubAPIError("GitHub service is temporarily unavailable", status_code=503)
            else:
                raise GitHubAPIError(f"Failed to access repository", status_code=status)
        except requests.exceptions.Timeout:
            raise GitHubAPIError("GitHub API request timed out during repository validation", status_code=504)
        except requests.exceptions.ConnectionError:
            raise GitHubAPIError("Connection error to GitHub API during repository validation", status_code=503)

    def validate_token(self) -> Dict[str, Any]:
        """
        Validates GitHub token validity and gets rate limit status.
        """
        if not self.token:
            return {"valid": False, "reason": "No token provided"}
            
        url = "https://api.github.com/rate_limit"
        headers = {
            "Accept": "application/vnd.github+json"
        }
        if self.token.startswith("github_pat_"):
            headers["Authorization"] = f"Bearer {self.token}"
        else:
            headers["Authorization"] = f"token {self.token}"
            
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                resources = data.get("resources", {})
                graphql_limit = resources.get("graphql", {})
                core_limit = resources.get("core", {})
                
                return {
                    "valid": True,
                    "graphql": {
                        "limit": graphql_limit.get("limit"),
                        "remaining": graphql_limit.get("remaining"),
                        "reset_time": datetime.fromtimestamp(graphql_limit.get("reset", 0), timezone.utc).isoformat()
                    },
                    "core": {
                        "limit": core_limit.get("limit"),
                        "remaining": core_limit.get("remaining"),
                        "reset_time": datetime.fromtimestamp(core_limit.get("reset", 0), timezone.utc).isoformat()
                    }
                }
            elif response.status_code == 401:
                return {"valid": False, "reason": "Bad credentials: Token is invalid or expired."}
            else:
                return {"valid": False, "reason": f"GitHub API error (status {response.status_code})"}
        except Exception as e:
            return {"valid": False, "reason": f"GitHub API connection issue: {str(e)}"}

    def _fetch_prs_rest(self, owner: str, repo: str, limit: int = 100) -> List[Dict]:
        """
        Fetch PRs using GitHub REST API for unauthenticated access.
        """
        all_prs = []
        page = 1
        per_page = min(100, limit)
        
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.token:
            if self.token.startswith("github_pat_"):
                headers["Authorization"] = f"Bearer {self.token}"
            else:
                headers["Authorization"] = f"token {self.token}"
                
        # 1. Fetch pull requests list
        while len(all_prs) < limit:
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page={per_page}&page={page}"
            try:
                response = requests.get(url, headers=headers, timeout=15)
                status = response.status_code
                
                # Retry once without token if we get 401/403 (could be invalid credentials for public repo)
                if (status == 401 or status == 403) and "Authorization" in headers:
                    body = response.json() if response.content else {}
                    if "rate limit" not in body.get("message", "").lower():
                        logger.warning(f"REST fetch failed (status {status}) with token. Retrying without token...")
                        headers.pop("Authorization", None) # Permanently remove for this session
                        response = requests.get(url, headers=headers, timeout=15)
                        status = response.status_code

                if status == 200:
                    data = response.json()
                    if not data:
                        break
                    all_prs.extend(data)
                    if len(data) < per_page:
                        break
                    page += 1
                elif status == 401:
                    raise InvalidTokenError()
                elif status in (403, 429):
                    raise RateLimitError()
                elif status == 404:
                    raise RepositoryNotFoundError(f"{owner}/{repo}")
                else:
                    raise GitHubAPIError(f"Failed to fetch pull requests", status_code=status)
            except requests.exceptions.Timeout:
                raise GitHubAPIError("GitHub API request timed out during pull request fetch", status_code=504)
            except requests.exceptions.ConnectionError:
                raise GitHubAPIError("Connection error to GitHub API during pull request fetch", status_code=503)
                
        # Truncate to limit
        all_prs = all_prs[:limit]
        
        # 2. Fetch details for each PR if rate limit permits
        mapped_prs = []
        remaining_limit = 60
        
        # Get rate limit from last response headers if available
        if 'response' in locals() and response is not None:
            limit_hdr = response.headers.get("X-RateLimit-Remaining")
            if limit_hdr is not None:
                remaining_limit = int(limit_hdr)
                
        logger.debug(f"Fetched {len(all_prs)} PRs. Remaining rate limit: {remaining_limit}")
        
        for pr in all_prs:
            number = pr.get("number")
            
            commits_count = 0
            additions = 0
            deletions = 0
            changed_files = 0
            comments_count = 0
            reviews_nodes = []
            
            # Fetch detailed PR info
            if remaining_limit > 5:
                try:
                    detail_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
                    detail_resp = requests.get(detail_url, headers=headers, timeout=15)
                    
                    limit_hdr = detail_resp.headers.get("X-RateLimit-Remaining")
                    if limit_hdr is not None:
                        remaining_limit = int(limit_hdr)
                        
                    if detail_resp.status_code == 200:
                        detail_data = detail_resp.json()
                        commits_count = detail_data.get("commits", 0)
                        additions = detail_data.get("additions", 0)
                        deletions = detail_data.get("deletions", 0)
                        changed_files = detail_data.get("changed_files", 0)
                        comments_count = detail_data.get("comments", 0) + detail_data.get("review_comments", 0)
                    elif detail_resp.status_code in (403, 429):
                        remaining_limit = 0
                except Exception:
                    pass
            
            # Fetch reviews
            if remaining_limit > 5:
                try:
                    reviews_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/reviews"
                    reviews_resp = requests.get(reviews_url, headers=headers, timeout=15)
                    
                    limit_hdr = reviews_resp.headers.get("X-RateLimit-Remaining")
                    if limit_hdr is not None:
                        remaining_limit = int(limit_hdr)
                        
                    if reviews_resp.status_code == 200:
                        for r in reviews_resp.json():
                            reviews_nodes.append({
                                "state": r.get("state"),
                                "submittedAt": r.get("submitted_at"),
                                "author": {
                                    "login": r.get("user", {}).get("login") if r.get("user") else "unknown"
                                }
                            })
                    elif reviews_resp.status_code in (403, 429):
                        remaining_limit = 0
                except Exception:
                    pass
                    
            # Map to GraphQL format
            mapped_prs.append({
                "number": pr.get("number"),
                "title": pr.get("title"),
                "state": "MERGED" if pr.get("merged_at") else pr.get("state", "").upper(),
                "createdAt": pr.get("created_at"),
                "mergedAt": pr.get("merged_at"),
                "closedAt": pr.get("closed_at"),
                "author": {
                    "login": pr.get("user", {}).get("login") if pr.get("user") else "unknown"
                },
                "commits": {
                    "totalCount": commits_count
                },
                "files": {
                    "totalCount": changed_files,
                    "nodes": [
                        {
                            "additions": additions,
                            "deletions": deletions
                        }
                    ]
                },
                "reviews": {
                    "totalCount": len(reviews_nodes),
                    "nodes": reviews_nodes
                },
                "comments": {
                    "totalCount": comments_count
                }
            })
            
        return mapped_prs

    def fetch_pull_requests(self, owner: str, repo: str, first: int = 50, limit: int = 100) -> List[Dict]:
        """
        Fetch PRs with reviews and commits, utilizing pagination loops and per_page=50.
        Fetches up to `limit` PRs in total.
        """
        if not self.token:
            return self._fetch_prs_rest(owner, repo, limit)
        try:
            return self._fetch_prs_graphql(owner, repo, first, limit)
        except (GitHubAPIError, InvalidTokenError) as e:
            # If GraphQL fails due to bad token (401) or some permissions (403 non-rate-limit),
            # attempt REST fallback as it might be a public repo.
            if e.status_code in (401, 403) and "rate limit" not in str(e).lower():
                logger.warning(f"GraphQL access failed (status {e.status_code}) for {owner}/{repo}. Falling back to REST...")
                return self._fetch_prs_rest(owner, repo, limit)
            raise

    def _fetch_prs_graphql(self, owner: str, repo: str, first: int, limit: int) -> List[Dict]:
        """Internal GraphQL fetcher logic"""
        query = """
        query($owner: String!, $repo: String!, $first: Int!, $cursor: String) {
            repository(owner: $owner, name: $repo) {
                pullRequests(first: $first, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                    nodes {
                        number
                        title
                        state
                        createdAt
                        mergedAt
                        closedAt
                        commits(first: 5) {
                            totalCount
                        }
                        files(first: 100) {
                            totalCount
                            nodes {
                                path
                                additions
                                deletions
                            }
                        }
                        reviews(first: 5) {
                            totalCount
                            nodes {
                                state
                                submittedAt
                                author {
                                    login
                                }
                            }
                        }
                        comments(first: 3) {
                            totalCount
                        }
                        author {
                            login
                        }
                    }
                }
            }
        }
        """
        
        all_prs = []
        cursor = None
        has_next_page = True
        
        per_page = min(50, limit)
        
        while has_next_page and len(all_prs) < limit:
            variables = {
                "owner": owner, 
                "repo": repo, 
                "first": min(per_page, limit - len(all_prs)),
                "cursor": cursor
            }
            
            try:
                data = self.query(query, variables)
                repo_data = data.get("repository")
                if not repo_data:
                    raise RepositoryNotFoundError(f"{owner}/{repo}")
                
                pr_connection = repo_data.get("pullRequests", {})
                nodes = pr_connection.get("nodes", []) or []
                all_prs.extend(nodes)
                
                page_info = pr_connection.get("pageInfo", {})
                has_next_page = page_info.get("hasNextPage", False)
                cursor = page_info.get("endCursor")
                
                logger.debug(f"Fetched page. Total PRs collected: {len(all_prs)}")
                
                if not nodes:
                    break
                    
            except GitHubPRDashboardException:
                raise
            except Exception as e:
                logger.warning(f"Error during PR pagination: {str(e)}")
                raise GitHubAPIError("Failed to fetch PRs", status_code=400, internal_details=str(e))
                
        return all_prs

    @staticmethod
    def filter_prs_by_file_path(
        prs: List[Dict],
        file_path: str,
        branch: Optional[str] = None,
    ) -> List[Dict]:
        """Keep PRs that modified the target file path (suffix match supported)."""
        if not file_path:
            return prs
        target = file_path.strip().lstrip("/")
        matched = []
        for pr in prs:
            files_data = pr.get("files") or {}
            nodes = files_data.get("nodes") if isinstance(files_data, dict) else []
            paths = [
                (n.get("path") or "").lstrip("/")
                for n in (nodes or [])
                if isinstance(n, dict)
            ]
            if not paths:
                continue
            if any(p == target or p.endswith("/" + target) or target.endswith(p) for p in paths):
                matched.append(pr)
        return matched

    def parse_pr_data(self, pr: Dict) -> Dict:
        """Parse raw PR data into structured format"""
        try:
            if not pr:
                raise ValueError("PR data is None")
            
            # Parse dates with timezone info
            created_at_str = pr.get("createdAt")
            if not created_at_str:
                raise ValueError("PR missing createdAt")
            
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            
            merged_at = pr.get("mergedAt")
            if merged_at:
                merged_at = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
            
            closed_at = pr.get("closedAt")
            if closed_at:
                closed_at = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
            
            # Calculate cycle time (fractional days)
            cycle_time_days = None
            if merged_at:
                cycle_time_days = (merged_at - created_at).total_seconds() / 86400
            
            # Calculate review metrics
            reviews_data = pr.get("reviews")
            reviews = []
            if reviews_data and isinstance(reviews_data, dict):
                reviews = reviews_data.get("nodes", []) or []
            
            first_review_time = None
            last_review_time = None
            approval_count = 0
            change_request_count = 0
            
            for review in reviews:
                if review and review.get("submittedAt"):
                    review_time = datetime.fromisoformat(review["submittedAt"].replace("Z", "+00:00"))
                    if not first_review_time or review_time < first_review_time:
                        first_review_time = review_time
                    if not last_review_time or review_time > last_review_time:
                        last_review_time = review_time
                    
                    if review.get("state") == "APPROVED":
                        approval_count += 1
                    elif review.get("state") == "CHANGES_REQUESTED":
                        change_request_count += 1
            
            wait_for_review_hours = None
            if first_review_time:
                wait_for_review_hours = (first_review_time - created_at).total_seconds() / 3600
            
            review_duration_hours = None
            if first_review_time and last_review_time:
                review_duration_hours = (last_review_time - first_review_time).total_seconds() / 3600
            
            # Calculate file changes
            files_data = pr.get("files")
            files = []
            if files_data and isinstance(files_data, dict):
                files = files_data.get("nodes", []) or []
            
            file_paths = [
                (f.get("path") or "").lstrip("/")
                for f in files
                if f and f.get("path")
            ]
            lines_added = sum(f.get("additions", 0) for f in files if f)
            lines_deleted = sum(f.get("deletions", 0) for f in files if f)
            
            # Get author safely
            author_data = pr.get("author")
            author = "unknown"
            if author_data and isinstance(author_data, dict):
                author = author_data.get("login", "unknown")
            
            # Get counts safely
            commits_data = pr.get("commits")
            commit_count = 0
            if commits_data and isinstance(commits_data, dict):
                commit_count = commits_data.get("totalCount", 0) or 0
            
            files_count = 0
            if files_data and isinstance(files_data, dict):
                files_count = files_data.get("totalCount", 0) or 0
            
            reviews_count = 0
            if reviews_data and isinstance(reviews_data, dict):
                reviews_count = reviews_data.get("totalCount", 0) or 0
            
            comments_data = pr.get("comments")
            comment_count = 0
            if comments_data and isinstance(comments_data, dict):
                comment_count = comments_data.get("totalCount", 0) or 0
            
            return {
                "number": pr.get("number", 0),
                "title": pr.get("title", ""),
                "state": pr.get("state", "UNKNOWN"),
                "created_at": created_at,
                "merged_at": merged_at,
                "closed_at": closed_at,
                "commit_count": commit_count,
                "files_changed": files_count,
                "lines_added": lines_added,
                "lines_deleted": lines_deleted,
                "review_count": reviews_count,
                "comment_count": comment_count,
                "author": author,
                "cycle_time_days": cycle_time_days,
                "wait_for_review_hours": wait_for_review_hours,
                "review_duration_hours": review_duration_hours,
                "approval_count": approval_count,
                "change_request_count": change_request_count,
                "reviewer_count": len(set(r.get("author", {}).get("login") for r in reviews if r and r.get("author"))),
                "file_paths": file_paths,
            }
        except Exception as e:
            logger.warning(f"Error parsing PR data: {str(e)}")
            raise ValueError(f"Failed to parse PR data: {str(e)}")
