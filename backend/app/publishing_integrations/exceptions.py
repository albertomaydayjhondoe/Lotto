"""
Exceptions for Publishing Integrations module.

These exceptions are raised by real API clients when authentication,
upload, or posting operations fail.
"""


class PublishingAuthError(Exception):
    """
    Raised when authentication with a social platform fails.
    
    Examples:
    - Invalid access token
    - Expired token that couldn't be refreshed
    - Missing required scopes
    - OAuth flow failure
    """
    pass


class PublishingUploadError(Exception):
    """
    Raised when video/media upload to a social platform fails.
    
    Examples:
    - File too large
    - Unsupported format
    - Upload timeout
    - Network error during upload
    - Platform API rate limit exceeded
    """
    pass


class PublishingPostError(Exception):
    """
    Raised when creating/publishing a post fails.
    
    Examples:
    - Invalid post parameters (caption too long, etc.)
    - Video not found after upload
    - Platform content policy violation
    - Account not authorized to post
    - API rate limit exceeded
    """
    pass
