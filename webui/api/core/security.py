from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from passlib.context import CryptContext
import jwt

from api.core.config import config

hasher = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

JWT_ALGORITHM = "HS256"

def create_access_token(subject: str, expiration: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expiration

    payload = {
        "sub": subject,
        "exp": expire,
    }

    encoded_jwt = jwt.encode(
        payload=payload,
        key=config.APP_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return encoded_jwt

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

    return hasher.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.
    """

    return hasher.verify(plain_password, hashed_password)