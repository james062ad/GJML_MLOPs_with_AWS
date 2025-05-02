
""" AWS Refresh Service: Handles temporary STS credential refresh. """
import boto3
import time
from typing import Optional, Dict

class CredentialStore:
    _cache: Dict[str, str] = {}
    _expiration: float = 0

    @classmethod
    def refresh(cls, duration: int = 3600):
        sts = boto3.client("sts")
        response = sts.get_session_token(DurationSeconds=duration)
        creds = response["Credentials"]
        cls._cache = {
            "access_key": creds["AccessKeyId"],
            "secret_key": creds["SecretAccessKey"],
            "session_token": creds["SessionToken"]
        }
        cls._expiration = time.time() + duration - 60  # buffer before expiry
        print("🔄 Refreshed AWS credentials from STS")

    @classmethod
    def get_credentials(cls) -> Dict[str, str]:
        if not cls._cache or time.time() >= cls._expiration:
            cls.refresh()
        return cls._cache
