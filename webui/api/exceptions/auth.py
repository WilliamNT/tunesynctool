from typing import Optional


class OAuthTokenRefreshError(Exception):
    """Exception raised when OAuth token refresh fails."""
    
    def __init__(self, provider_name: str, user_id: int, cause: str = "unknown") -> None:
        super().__init__(f"Failed to refresh OAuth token for provider '{provider_name}' for user ID {user_id}.{f' Cause: {cause}' if cause else ''}")