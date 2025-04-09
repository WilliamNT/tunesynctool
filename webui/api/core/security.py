from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from fastapi.security import OAuth2PasswordBearer
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64

from api.core.config import config
from api.models.token import AccessToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{config.API_BASE_URL}/auth/token")

JWT_ALGORITHM = "HS256"

def create_access_token(subject: str, expires_in_days: int) -> AccessToken:
    expiration = datetime.now(timezone.utc) + timedelta(days=expires_in_days)


    payload = {
        "sub": subject,
        "exp": expiration,
    }

    encoded_jwt = jwt.encode(
        payload=payload,
        key=config.APP_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return AccessToken(
        access_token=encoded_jwt,
        token_type="bearer",
        expires_in=timedelta(days=expires_in_days).total_seconds()
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

def get_fernet() -> Fernet:
    """
    Generate a Fernet key for encryption/decryption.
    This key is derived from the ENCRYPTION_KEY and ENCRYPTION_SALT.
    """

    kdf = Scrypt(
        salt=config.ENCRYPTION_SALT.encode("utf-8"),
        length=32,
        n=2**14,
        r=8,
        p=1,
        backend=default_backend(),
    )

    key = kdf.derive(config.ENCRYPTION_KEY.encode("utf-8"))

    return Fernet(
        key=base64.urlsafe_b64encode(key)
    )