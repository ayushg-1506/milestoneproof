"""
Authentication Service implementing JWT access and refresh tokens.
"""

import jwt
import datetime
from typing import Dict, Any, Optional

SECRET_KEY = "insecure-dev-secret-replace-in-prod"
ALGORITHM = "HS256"


class JWTService:
    """Handles issuance and validation of signed JWT tokens."""

    @staticmethod
    def create_access_token(user_id: str, email: str, expires_in_minutes: int = 15) -> str:
        """Issue short-lived access token."""
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_in_minutes)
        payload = {
            "sub": user_id,
            "email": email,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: str, expires_in_days: int = 7) -> str:
        """Issue long-lived refresh token."""
        expire = datetime.datetime.utcnow() + datetime.timedelta(days=expires_in_days)
        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify token signature and return decoded payload."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

    @staticmethod
    def refresh_token(old_refresh_token: str) -> Optional[Dict[str, str]]:
        """Validate refresh token and issue new token pair."""
        payload = JWTService.verify_token(old_refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload["sub"]
        new_access = JWTService.create_access_token(user_id, "user@example.com")
        new_refresh = JWTService.create_refresh_token(user_id)
        return {
            "access_token": new_access,
            "refresh_token": new_refresh
        }
