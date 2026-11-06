# Bolt's Journal - NutriLens Critical Learnings

## 2026-11-05 - Streamlit secrets access and PDF generation row iteration
**Learning:** `if "API_URL" in st.secrets:` raises `StreamlitSecretNotFoundError` when no secrets file is configured in local or testing environments. Also, `pandas.DataFrame.iterrows()` creates a Series object per row which introduces significant overhead during report generation, whereas caching with `@st.cache_data` and iterating via `itertuples(index=False)` avoids per-row Series overhead and eliminates redundant rendering on dashboard re-renders.
**Action:** When building Streamlit utilities, wrap or cache expensive computations like PDF rendering using `@st.cache_data` and prefer `itertuples(index=False)` over `iterrows()`.
