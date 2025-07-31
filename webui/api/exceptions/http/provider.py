from fastapi import HTTPException

from api.core.logging import logger

def raise_unsupported_provider_exception(provider_name: str) -> None:
    logger.warning(f"Provider \"{provider_name}\" is not supported.")

    raise HTTPException(
        status_code=400,
        detail=f"Provider \"{provider_name}\" is not supported.",
    )