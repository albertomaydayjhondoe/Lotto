"""
Meta Ads API Client Exceptions

Custom exception classes for Meta API error handling.
"""


class MetaAPIError(Exception):
    """Base exception for Meta API errors."""
    
    def __init__(self, message: str, error_code: str | None = None, status_code: int | None = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)
    
    def __str__(self) -> str:
        base = f"MetaAPIError: {self.message}"
        if self.error_code:
            base += f" (error_code: {self.error_code})"
        if self.status_code:
            base += f" (status: {self.status_code})"
        return base


class MetaAuthError(MetaAPIError):
    """Exception raised when authentication fails with Meta API."""
    
    def __init__(self, message: str = "Authentication failed with Meta API"):
        super().__init__(message, error_code="AUTH_ERROR", status_code=401)


class MetaRateLimitError(MetaAPIError):
    """Exception raised when Meta API rate limit is exceeded."""
    
    def __init__(self, message: str = "Meta API rate limit exceeded", retry_after: int | None = None):
        super().__init__(message, error_code="RATE_LIMIT", status_code=429)
        self.retry_after = retry_after
    
    def __str__(self) -> str:
        base = super().__str__()
        if self.retry_after:
            base += f" (retry after: {self.retry_after}s)"
        return base
