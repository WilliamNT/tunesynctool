from fastapi import HTTPException

def raise_missing_or_invalid_auth_credentials_exception(provider_name: str) -> None:
    """
    Raises an HTTPException with a 400 status code and a message indicating that the catalog operation failed due to user error.
    """
        
    raise HTTPException(
        status_code=401,
        detail=f"Missing or invalid credentials for provider \"{provider_name}\". If \"{provider_name}\" is an OAuth provider, authorization is required. Otherwise, please set the proper credentials.",
    )   