# Milestone 2 SOW: User Authentication, Google OAuth & Stripe Webhook Service

- **Project**: SaaS Billing & Onboarding Platform
- **Contractor**: Alex Rivera (Senior Backend Subcontractor)
- **Milestone Amount**: $2,500 USD
- **Due Date**: 2026-10-18

## Scope of Work

The contractor is engaged to implement the core authentication and payment webhook infrastructure for the onboarding platform. All code must be modular, secure, and covered by automated tests.

## Acceptance Criteria

| ID | Title / Requirement | Priority | Verification Method |
| :--- | :--- | :---: | :--- |
| **AC-1** | JWT Authentication Service with Access & Refresh Token Generation (`jwt_service`) | MUST | AST_FUNCTION: `create_access_token`, `verify_token`, `refresh_token` |
| **AC-2** | Google OAuth2 Authentication Flow & User Profile Ingestion (`oauth_service`) | MUST | AST_FUNCTION: `handle_google_callback`, `get_google_user` |
| **AC-3** | Stripe Webhook Processing with HMAC Signature Verification (`webhook_handler`) | MUST | SECURITY_CHECK: `verify_stripe_signature`, constant-time HMAC check |
| **AC-4** | Token-Bucket API Rate Limiting Middleware (`rate_limiter`) | MUST | AST_FUNCTION: `rate_limit_middleware`, 100 req/min bucket |
| **AC-5** | Automated Pytest Unit Test Suite covering auth and error edge cases | SHOULD | TEST_SUITE: `test_auth.py`, test assertions, error cases |
