# NutriLens Security Model & Hardening Specifications

## 1. Authentication & Authorization Controls

- **Cryptographic JWT Verification**: Tokens issued by Supabase GoTrue Auth are verified using `pyjwt` with HMAC-SHA256 and public keys.
- **IDOR Safeguards**: Endpoints enforcing user identity (e.g. `/api/v1/history/{user_id}` and `/api/v1/log_meal`) bind database operations to `current_user.user_id` extracted from the cryptographically validated token, rejecting spoofed identities.
- **Row Level Security (RLS)**: Enforced directly at the PostgreSQL layer. `auth.uid()::text = user_id` ensures that even direct database queries cannot read or mutate other users' private meals or groceries.
- **Atomic Operations**: Like counter increments are guarded inside a single transactional stored procedure (`increment_meal_likes`) with unique constraints `(meal_id, user_id)` to eliminate race condition vulnerabilities.

---

## 2. Input Validation & Defense-in-Depth

- **Pydantic Validation**: Strict numeric boundaries on all food payloads (`calories` <= 10,000, `macros` <= 1,000g, non-empty stripped strings).
- **File Upload Limits**: Enforces a strict 10 MB maximum request payload limit and PIL header verification (`image.verify()`) to thwart image decompression bombs or arbitrary binary execution.
- **CORS Protection**: Restricted to whitelist domains configured in `CORS_ORIGINS`.

---

## 3. Secret Management
- **Zero Secrets in Repository**: `.env` is ignored by `.gitignore`. Template credentials and placeholder configurations are placed in `.env.example`.
- **Runtime Environment Isolation**: In cloud deployment, API keys and database secrets are injected via platform environment secrets (Cloudflare Pages Secrets & Render Environment Variables).
