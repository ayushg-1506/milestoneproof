"""
Google OAuth2 Authentication Provider.
"""

import requests
from typing import Dict, Any, Optional

GOOGLE_CLIENT_ID = "mock-client-id"
GOOGLE_CLIENT_SECRET = "mock-client-secret"


class GoogleOAuthService:
    """Manages Google OAuth2 authentication flow."""

    @staticmethod
    def get_authorization_url(redirect_uri: str) -> str:
        """Generate Google consent screen URL."""
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={GOOGLE_CLIENT_ID}&response_type=code&"
            f"scope=openid%20email%20profile&redirect_uri={redirect_uri}"
        )

    @staticmethod
    def handle_google_callback(code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for user profile."""
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        # In mock environment, returns mock profile
        return {
            "email": "user@gmail.com",
            "name": "Jane Developer",
            "google_id": "google-123456"
        }

    @staticmethod
    def get_google_user(access_token: str) -> Optional[Dict[str, Any]]:
        """Fetch profile from Google UserInfo endpoint."""
        return {
            "email": "user@gmail.com",
            "sub": "google-123456"
        }
