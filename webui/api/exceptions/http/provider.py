from fastapi import HTTPException

from api.core.logging import logger

def raise_unsupported_provider_exception(provider_name: str) -> None:
    logger.warning(f"Provider \"{provider_name}\" is either not supported or is not a valid option per the current configuration.")

    raise HTTPException(
        status_code=400,
        detail=f"Provider unavailable.",
    )