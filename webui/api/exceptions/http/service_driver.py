from typing import Optional
from fastapi import HTTPException

from api.core.logging import logger

def raise_unsupported_driver_feature_exception(provider_name: str, e: Optional[Exception] = None) -> None:
        logger.warning(f"Provider \"{provider_name}\" does not support a feature but it was called anyway{": " + str(e) if e else "."}")

        msg = f"Provider \"{provider_name}\" does not support this feature."
        code = 400

        if e:
            raise HTTPException(
                status_code=code,
                detail=msg,
            ) from e
            
        raise HTTPException(
            status_code=code,
            detail=msg,
        )

def raise_service_driver_generic_exception(provider_name: str, e: Optional[Exception] = None) -> None:
    logger.error(f"Service driver error: {e}")

    msg = f"Provider \"{provider_name}\" returned an error."
    code = 400

    if e:
        raise HTTPException(
            status_code=code,
            detail=msg,
        ) from e
    
    raise HTTPException(
        status_code=code,
        detail=msg,
    )