# NutriLens V2 Cost & Cloud Resource Analysis

## 1. Hosting Architecture & Free-Tier Limits

The core design principle of NutriLens V2 is to maintain recurring operational costs at **₹0.00 / month ($0.00)** using legitimate always-free allowances without reliance on temporary promotional credits.

| Component | Provider & Tier | Free Allowance | Expected Usage | Risk of Charges | Mitigation Safeguards |
|---|---|---|---|---|---|
| **Frontend Application** | **Cloudflare Pages** (Always Free) | Unlimited bandwidth, 500 builds/month, global anycast CDN | ~100–500 MB / mo | **Zero Risk** (Card not required, free tier does not auto-upgrade) | Built-in DDoS protection, automatic SSL, no bandwidth metering |
| **Backend API Service** | **Render Free Web Service** / **Fly.io** | 750 free instance hours / month, 512 MB RAM | ~100–200 hours / mo (spins down when inactive) | **Zero Risk** (Instance spins down, does not charge overage) | ONNX Runtime reduces RAM to ~48 MB, comfortably below 512 MB limit |
| **Inference Engine** | **Client-Side (User Device WASM/WebGL) + Server ONNX** | 100% Client-side compute | Infinite zero-cost client inferences | **Zero Risk** | Offloads image tensors from cloud egress and CPU compute |
| **PostgreSQL Database** | **Supabase Free Tier** | 500 MB database, 1 GB file storage, 50,000 monthly active users | <15 MB for thousands of meal records | **Zero Risk** (Pauses if inactive after weeks, project stays free) | Row Level Security, efficient foreign key indexes, JSON logging |
| **User Authentication** | **Supabase GoTrue Auth** | 50,000 MAU free forever, OAuth & Email | ~100–500 active users | **Zero Risk** | JWT verification, client-side session storage |
| **Nutrition Data API** | **USDA FoodData Central** | Free government public API key | 1,000 req/hour | **Zero Risk** (Free public service) | Client caching + portion calculations in memory |
| **Barcode Scanning** | **OpenFoodFacts** | Free community open-data JSON API | Unlimited reasonable rate-limit | **Zero Risk** (Free open-source database) | Direct client/server async requests |
| **AI Recipe & OCR** | **Google Gemini 1.5 Flash (Free Tier)** | 15 RPM (Requests Per Minute), 1M TPM, 1,500 RPD | ~10–50 requests / day | **Zero Risk** (Hard capped at free-tier quota, rejects overages without billing) | Fallback template recipes & local validation when quota reached |

---

## 2. Monthly Estimated Cost Summary

- **Promotional Credits Used**: ₹0 ($0.00)
- **Temporary Trials Used**: None
- **Total Estimated Monthly Recurring Cost**: **₹0.00 / month**
- **Billing Prevention**: No paid cloud subscriptions or payment profiles required to deploy.
