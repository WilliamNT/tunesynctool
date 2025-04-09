from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import jwt
import bcrypt

from api.core.config import config
from api.models.token import Token

JWT_ALGORITHM = "HS256"

def create_access_token(subject: str, expiration: datetime) -> Token:
    payload = {
        "sub": subject,
        "exp": expiration,
    }

    encoded_jwt = jwt.encode(
        payload=payload,
        key=config.APP_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return Token(
        value=encoded_jwt,
        expires_at=expiration,
    )

def verify_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            jwt=token,
            key=config.APP_SECRET,
            algorithms=[JWT_ALGORITHM],
            verify=True,
        )

        if "sub" not in payload:
            return None
        
        return str(payload["sub"])
    except jwt.ExpiredSignatureError:
        return None

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """

    return bcrypt.hashpw(
        password=password.encode("utf-8"),
        salt=bcrypt.gensalt(),
    )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.
    """

    return bcrypt.checkpw(
        password=plain_password.encode("utf-8"),
        hashed_password=hashed_password.encode("utf-8"),
    )