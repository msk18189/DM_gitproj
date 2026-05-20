"""
Custom exceptions for safe error handling.
These exceptions have user-friendly messages suitable for client exposure.
"""


class GitHubPRDashboardException(Exception):
    """Base exception for the dashboard."""
    
    def __init__(self, user_message: str, status_code: int = 400, internal_details: str = None):
        """
        Initialize exception with safe client message.
        
        Args:
            user_message: Safe message to send to client
            status_code: HTTP status code
            internal_details: Internal logging details (not sent to client)
        """
        self.user_message = user_message
        self.status_code = status_code
        self.internal_details = internal_details or user_message
        super().__init__(self.user_message)


class RepositoryNotFoundError(GitHubPRDashboardException):
    """Repository not found or inaccessible."""
    
    def __init__(self, repo_url: str, internal_details: str = None):
        super().__init__(
            user_message="Repository not found or inaccessible. Check the repository URL and your token permissions.",
            status_code=404,
            internal_details=internal_details or f"Repository {repo_url} could not be accessed"
        )


class PrivateRepositoryError(GitHubPRDashboardException):
    """Private repository requires authentication."""
    
    def __init__(self, internal_details: str = None):
        super().__init__(
            user_message="This is a private repository. Please provide a valid GitHub token with repository access.",
            status_code=401,
            internal_details=internal_details or "Private repository requires token"
        )


class InvalidTokenError(GitHubPRDashboardException):
    """GitHub token is invalid or expired."""
    
    def __init__(self, internal_details: str = None):
        super().__init__(
            user_message="GitHub token is invalid, expired, or insufficient. Please check your token and permissions.",
            status_code=401,
            internal_details=internal_details or "Token validation failed"
        )


class RateLimitError(GitHubPRDashboardException):
    """GitHub API rate limit exceeded."""
    
    def __init__(self, internal_details: str = None):
        super().__init__(
            user_message=(
                "GitHub API rate limit exceeded. Wait a few minutes, or add a personal "
                "access token for higher limits (recommended for large repositories)."
            ),
            status_code=429,
            internal_details=internal_details or "Rate limit exceeded"
        )


class EmptyRepositoryError(GitHubPRDashboardException):
    """Repository has no pull requests."""
    
    def __init__(self, internal_details: str = None):
        super().__init__(
            user_message="No pull requests found in this repository.",
            status_code=200,  # Not an error - valid response
            internal_details=internal_details or "Repository has no PRs"
        )


class InvalidURLError(GitHubPRDashboardException):
    """Invalid GitHub URL format."""
    
    def __init__(self, url: str = None, internal_details: str = None):
        super().__init__(
            user_message="Invalid GitHub URL format. Please use: https://github.com/owner/repo or owner/repo",
            status_code=400,
            internal_details=internal_details or f"Invalid URL: {url}"
        )


class GitHubAPIError(GitHubPRDashboardException):
    """GitHub API error."""
    
    def __init__(self, message: str = None, status_code: int = 500, internal_details: str = None):
        super().__init__(
            user_message=message or "GitHub API returned an error. Please try again later.",
            status_code=status_code,
            internal_details=internal_details or message or "GitHub API error"
        )


class DatabaseError(GitHubPRDashboardException):
    """Database error."""
    
    def __init__(self, internal_details: str = None):
        super().__init__(
            user_message="A database error occurred. Please try again later.",
            status_code=500,
            internal_details=internal_details or "Database operation failed"
        )


class ValidationError(GitHubPRDashboardException):
    """Validation error."""
    
    def __init__(self, message: str, internal_details: str = None):
        super().__init__(
            user_message=message,
            status_code=400,
            internal_details=internal_details or message
        )
