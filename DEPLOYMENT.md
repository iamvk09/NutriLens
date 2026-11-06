# NutriLens V2 Production Deployment Guide

This guide details deployment of NutriLens V2 using **Cloudflare Pages** for the React frontend and **Render / Fly.io** for the FastAPI backend, connected to **Supabase** for PostgreSQL and Authentication.

---

## 1. Prerequisites & Environment Setup

Verify the following secrets from `.env.example`:
1. `SUPABASE_URL` & `SUPABASE_KEY` (Anon public key)
2. `SUPABASE_JWT_SECRET` (For server-side offline token authentication)
3. `USDA_API_KEY` (From [FoodData Central](https://fdc.nal.usda.gov/api-guide.html))
4. `GEMINI_API_KEY` (From [Google AI Studio](https://aistudio.google.com/))

---

## 2. Frontend Deployment (Cloudflare Pages)

1. Log into your [Cloudflare Dashboard](https://dash.cloudflare.com/) and navigate to **Workers & Pages** > **Create application** > **Pages** > **Connect to Git**.
2. Select repository `iamvk09/NutriLens` and target branch `v2`.
3. Set the build configuration:
   - **Framework preset**: `Vite`
   - **Root directory**: `frontend`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
4. Set Environment Variables:
   - `VITE_BACKEND_API_URL`: Your deployed backend URL (e.g., `https://nutrilens-api.onrender.com/api/v1`)
   - `VITE_SUPABASE_URL`: Your Supabase URL
   - `VITE_SUPABASE_KEY`: Your Supabase anon key
5. Click **Save and Deploy**. Cloudflare provisions automatic global CDN hosting and free HTTPS.

---

## 3. Backend Deployment (Render Free Web Service)

1. Log into your [Render Dashboard](https://dashboard.render.com/) and click **New** > **Web Service**.
2. Connect your GitHub repository `iamvk09/NutriLens`, selecting branch `v2`.
3. Specify configuration:
   - **Runtime**: `Python 3` (or Docker via `Dockerfile.backend`)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free` (0.1 CPU, 512 MB RAM)
4. Add Environment Variables:
   - `ENVIRONMENT`: `production`
   - `CORS_ORIGINS`: Your Cloudflare Pages URL (e.g. `https://nutrilens.pages.dev,http://localhost:3000`)
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_KEY`: Your Supabase anon key
   - `SUPABASE_JWT_SECRET`: Your Supabase JWT secret
   - `USDA_API_KEY`: Your USDA key
   - `GEMINI_API_KEY`: Your Gemini key
   - `MODEL_PATH`: `./models/food_model.onnx`
5. Click **Create Web Service**.

---

## 4. Local Development Run

### Run Backend
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Frontend
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 5. Rollback Procedure
If a regression occurs, redeploy the previous commit on branch `v2`:
```bash
git checkout v2
git revert HEAD
git push origin v2
```
Cloudflare Pages and Render will automatically build the reverted release.
