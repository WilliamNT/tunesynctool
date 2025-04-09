import json

from api.core.security import get_fernet

def encrypt_str(data: str) -> str:
    """
    Encrypt a string using Fernet.
    """

    fernet = get_fernet()
    return fernet.encrypt(data.encode("utf-8")).decode("utf-8")

def decrypt_str(data: str) -> str:
    """
    Decrypt a string using Fernet.
    """

    fernet = get_fernet()
    return fernet.decrypt(data.encode("utf-8")).decode("utf-8")

def encrypt_dict(data: dict) -> str:
    """
    Encrypt a dictionary using Fernet.
    """

    json_data = json.dumps(data)
    return encrypt_str(json_data)

def decrypt_dict(data: str) -> dict:
    """
    Decrypt a string to a dictionary using Fernet.
    """

    json_data = decrypt_str(data)
    return json.loads(json_data)