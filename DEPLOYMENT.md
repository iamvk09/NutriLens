# NutriLens V2 Production Deployment Guide

This guide details the step-by-step deployment of NutriLens V2 across **Cloudflare Pages** (Frontend) and **Render / Docker** (Backend API).

---

## 1. Prerequisites & Environment Secrets

Ensure you have credentials prepared from `.env.example`:
- `SUPABASE_URL` & `SUPABASE_KEY` (Anon public key)
- `SUPABASE_JWT_SECRET` (Found in Supabase Project Settings > API > JWT Settings)
- `USDA_API_KEY` (From [FoodData Central](https://fdc.nal.usda.gov/api-guide.html))
- `GEMINI_API_KEY` (From [Google AI Studio](https://aistudio.google.com/))
- `GEMINI_MODEL`: `gemini-3.5-flash` (or current supported model)
- `MODEL_DOWNLOAD_URL`: URL to download `food_model.onnx` if not baking into container.
- `MODEL_EXPECTED_SHA256`: `aa6157a28f37bd797fa6e9b09e24bdd1243aa93f9fcbbc0ea3d198c0f9e6f7cd`
- `MODEL_EXPECTED_SIZE_BYTES`: `14571154`

---

## 2. Model Provisioning Strategy

Because GitHub and version control systems are not designed for large binary binaries, `food_model.onnx` (14.5 MB) is handled via one of two production-ready mechanisms:

### Option A: Automated Download via `MODEL_DOWNLOAD_URL`
Set `MODEL_DOWNLOAD_URL` to an accessible artifact storage location (e.g., Supabase Storage bucket, Cloudflare R2, GitHub Release asset, or AWS S3 presigned URL).
On startup, NutriLens V2:
1. Downloads the binary to a temporary file.
2. Validates the SHA256 checksum against `MODEL_EXPECTED_SHA256`.
3. Verifies file size against `MODEL_EXPECTED_SIZE_BYTES`.
4. Atomically replaces `models/food_model.onnx`.

### Option B: Volume Mount or Docker Build Stage
Mount the verified ONNX model file into `/app/models/food_model.onnx` at container runtime.

---

## 3. Frontend Deployment (Cloudflare Pages)

1. Log into your [Cloudflare Dashboard](https://dash.cloudflare.com/) > **Workers & Pages** > **Create application** > **Pages** > **Connect to Git**.
2. Select repository `iamvk09/NutriLens` and target branch `v2`.
3. Build Settings:
   - **Framework preset**: `Vite`
   - **Root directory**: `frontend`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
4. Set Environment Variables:
   - `VITE_BACKEND_API_URL`: Your live backend API URL (e.g. `https://nutrilens-api.onrender.com/api/v1`)
   - `VITE_SUPABASE_URL`: Your Supabase URL
   - `VITE_SUPABASE_KEY`: Your Supabase anon key
5. Click **Save and Deploy**. Cloudflare provisions global CDN caching and free SSL.

---

## 4. Backend Deployment (Render Free Web Service)

1. In the [Render Dashboard](https://dashboard.render.com/), click **New** > **Web Service**.
2. Connect `iamvk09/NutriLens` on branch `v2`.
3. Configure:
   - **Runtime**: `Python` (or Docker via `Dockerfile.backend`)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free` (512 MB RAM)
4. Environment Variables:
   - `ENVIRONMENT`: `production`
   - `CORS_ORIGINS`: Your Cloudflare Pages URL
   - `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET`
   - `USDA_API_KEY`
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL`: `gemini-3.5-flash`
   - `MODEL_PATH`: `./models/food_model.onnx`
   - `MODEL_DOWNLOAD_URL`: (If using remote provisioning)
5. Deploy.

---

## 5. Free-Tier Operational Constraints
- **Cold Starts**: Render free instances sleep after 15 minutes of inactivity; the initial request will take 30–50 seconds to warm up.
- **Supabase Inactivity**: Free databases pause after 7 days without queries. Unpausing is performed via the Supabase dashboard.
- **Zero Billing Risk**: Neither Cloudflare Pages free tier nor Render free instances bill overages automatically without explicit plan changes.
