# NutriLens Security Policy & Hardening Guide

## 1. Security Architecture & Threat Model

NutriLens implements defense-in-depth principles across all application layers to safeguard sensitive dietary data, user sessions, and external API integrations.

### Key Protections
- **Supabase JWT Authentication**: Every mutation (`/log_meal`, `/community/like`) and private resource access (`/history/{user_id}`) requires a signed JSON Web Token issued by Supabase Auth.
- **Strict IDOR Mitigation**: Users can only query and write records belonging to their authenticated identity (`current_user.user_id == user_id`). Unauthenticated or mismatched requests receive `401 Unauthorized` or `403 Forbidden`.
- **CORS Origin Whitelisting**: `main.py` restricts cross-origin resource sharing to explicitly allowed origins specified in `CORS_ORIGINS` (e.g. `http://localhost:8501`). Wildcard `*` origins with credentials have been eradicated.
- **Duplicate Like & Race Condition Prevention**: `meal_likes` table maintains a database-level `UNIQUE (meal_id, user_id)` constraint, preventing concurrent race conditions and multiple likes from the same account.
- **Upload Validation & DoS Protection**: Image uploads are constrained to `MAX_IMAGE_SIZE_BYTES` (default 10 MB) with header verification and PIL image decoding integrity checks.
- **Error Masking & Information Leakage Prevention**: Production logs capture full stack traces internally while sanitizing public error responses to generic user-safe error messages.
- **Zero Secrets in Code**: All API keys, secrets, and database credentials are fully decoupled from git and managed through `.env` and environment variables.

## 2. Row Level Security (RLS)

All Supabase PostgreSQL tables must have Row Level Security enabled:

```sql
ALTER TABLE logged_meals ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE shopping_list ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
```

Policies defined in `db/schema.sql` restrict writes and reads to matching `auth.uid()`, guaranteeing that users cannot tamper with or inspect meals belonging to other individuals.

## 3. Reporting Vulnerabilities

If you identify a security vulnerability in NutriLens, please do not open a public issue. Email security reports directly to `security@nutrilens.dev` with replication details and affected endpoints.
