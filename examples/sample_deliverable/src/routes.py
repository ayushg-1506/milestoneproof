"""
FastAPI route declarations for Authentication and Webhook modules.
"""

from fastapi import FastAPI, HTTPException, Request, Header
from typing import Optional
from .auth_service import JWTService
from .oauth_service import GoogleOAuthService
from .webhook_handler import StripeWebhookHandler

app = FastAPI(title="SaaS Onboarding & Billing API")
webhook_handler = StripeWebhookHandler()


@app.post("/api/v1/auth/login")
def login(payload: dict):
    """Authenticate with credentials and issue JWT."""
    username = payload.get("username")
    if username == "admin":
        access = JWTService.create_access_token("u1", "admin@example.com")
        refresh = JWTService.create_refresh_token("u1")
        return {"access_token": access, "refresh_token": refresh}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/api/v1/auth/google/callback")
def google_callback(code: str):
    """Google OAuth callback."""
    profile = GoogleOAuthService.handle_google_callback(code, "http://localhost/callback")
    if profile:
        return {"profile": profile}
    raise HTTPException(status_code=400, detail="OAuth failure")


@app.post("/api/v1/webhooks/stripe")
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    """Stripe webhook receiver."""
    body = await request.json()
    result = webhook_handler.process_webhook_event(body, stripe_signature or "")
    return result
