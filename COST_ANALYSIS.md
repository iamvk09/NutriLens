# NutriLens V2 Cost & Cloud Resource Analysis

## 1. Hosting Architecture & Free-Tier Realities

NutriLens V2 is designed for zero recurring software license costs and low-overhead hosting. However, production uptime and cloud provider constraints must be clearly distinguished from promotional marketing claims.

| Component | Provider & Tier | Quota & Free Allowance | Realistic Operational Behavior | Downtime & Billing Risks | Mitigation Strategy |
|---|---|---|---|---|---|
| **Frontend Application** | **Cloudflare Pages** (Free Tier) | Unlimited bandwidth, 500 monthly builds, global anycast CDN | Zero cold starts, fast global edge delivery | **Zero financial risk**. High traffic is absorbed without automated billing. | Automatic SSL, static asset caching. |
| **Backend API Service** | **Render Web Service** (Free Instance) | 750 free instance hours / month, 512 MB RAM | **Spins down after 15 minutes of inactivity**. First incoming request encounters ~30-50s cold-start spinup latency. | Free tier has strict limits; will sleep when idle. Cannot offer 99.9% commercial SLA for free. | ONNX runtime cuts RAM to ~48 MB (preventing OOM crashes). For 24/7 uptime, upgrade to paid tier ($7/mo) requires explicit user approval. |
| **Backend API (Alternative)** | **Fly.io** | Limited credit allowance depending on account eligibility and location | Requires valid credit card for signup; subject to region availability and change in free allowances. | Moderate billing risk if exceeded or if trial expires. | Default to Render free or containerized self-hosted. |
| **Inference Engine** | **Server-Side ONNX Runtime** | Included in container runtime | 1.6 ms CPU execution time. 14.5 MB model binary. | No external per-inference API cost. | Standardized opset 15 on CPU. Zero GPU cost. |
| **Database & Identity** | **Supabase** (Free Tier) | 500 MB database, 1 GB storage, 50,000 monthly active users | **Inactivity Pause**: Free projects automatically pause after 7 days of complete inactivity and must be manually restored via dashboard. | No unexpected credit card billing (free tier pauses instead of charging). | PostgreSQL Row Level Security (RLS) protects data isolation. Regular active usage keeps DB active. |
| **Nutrition Data API** | **USDA FoodData Central** | Free US government public API | 1,000 requests per hour with API key | Service outage or rate-limiting if key is exhausted. | In-memory portion calculations and fallback nutritional profiles. |
| **Barcode Scanning** | **OpenFoodFacts** | Free public community database | Generous rate-limiting | Dependent on community crowd-sourced barcode availability. | User can enter barcode manually or enter food title directly. |
| **AI Recipe & OCR** | **Google Gemini Interactions API** | Free tier quota (15 RPM / 1,500 RPD) | Fast response on supported models (`gemini-3.5-flash`). Subject to temporary 503 high-demand spikes. | Free tier rejects overages with HTTP 429 rather than charging card. | Configurable `GEMINI_MODEL`, graceful JSON parsing fallback, offline culinary recipes. |

---

## 2. Hobby vs. Production-Grade SLA Comparison

| Metric | Free / Hobby Deployment | Production-Grade Upgrade (Paid) |
|---|---|---|
| **Monthly Cost** | **₹0.00 / month ($0.00)** | **~$12.00–$25.00 / month** |
| **Backend Availability** | Sleeps after 15m idle (30s cold start) | 24/7 zero-cold-start dedicated container |
| **Database State** | Auto-pauses if idle for 7 days | Pro tier ($25/mo) never pauses |
| **SLA Guarantee** | Best-effort, no financial guarantee | 99.9% uptime SLA with daily automated backups |
| **Credit Card Requirement** | None (Render + Cloudflare Pages) | Required for paid tier upgrades |

*Never assume a cloud provider provides permanent commercial-grade hosting for free. NutriLens V2 achieves ₹0/month operation by adhering strictly to genuine free limits.*
