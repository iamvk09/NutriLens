import os
import io
import datetime
from typing import Optional, Dict, Any

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from dotenv import load_dotenv
from supabase import create_client
from fpdf import FPDF
from PIL import Image

# Load environment variables
load_dotenv()

# --- CONFIGURATION: CENTRALIZED URLS & SECRETS ---
# Backend API URL
if "API_URL" in st.secrets:
    API_URL = st.secrets["API_URL"].rstrip("/")
else:
    API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/v1").rstrip("/")

# Frontend URL used for OAuth Redirect
if "APP_URL" in st.secrets:
    APP_URL = st.secrets["APP_URL"].rstrip("/")
else:
    APP_URL = os.getenv("FRONTEND_APP_URL", "http://localhost:8501").rstrip("/")

# Supabase and Gemini settings
try:
    SUPABASE_URL = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
except Exception:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Page Config
st.set_page_config(page_title="NutriLens", page_icon="🥗", layout="wide")

# Dark Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        background-color: #000000;
        color: #F5F5F5;
        font-family: 'Inter', sans-serif;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .login-card {
        background-color: #1c1c1c;
        border: 1px solid #363636;
        border-radius: 16px;
        padding: 40px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    p, label {
        color: #A8A8A8 !important;
    }
    .feed-card {
        background-color: #121212;
        border: 1px solid #262626;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

# Optional Gemini setup
ai_model = None
if GEMINI_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        ai_model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        pass

# Session state initialization
if "user" not in st.session_state:
    st.session_state.user = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None


def get_auth_headers() -> Dict[str, str]:
    """Helper to generate Authorization header from current session."""
    headers = {}
    if st.session_state.access_token:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    return headers


def generate_pdf_report(user_email: str, dataframe: pd.DataFrame) -> bytes:
    """Generates user health and meal history PDF report."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, "NutriLens Health Report", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, f"User: {user_email}", ln=True, align="C")
    pdf.cell(0, 10, f"Date: {datetime.date.today()}", ln=True, align="C")
    pdf.ln(10)

    total_cals = dataframe["calories"].sum() if not dataframe.empty else 0
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Total Calories: {int(total_cals)} kcal", ln=True)
    pdf.ln(5)

    if not dataframe.empty:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(40, 10, "Date", 1)
        pdf.cell(80, 10, "Food", 1)
        pdf.cell(30, 10, "Cals", 1)
        pdf.ln()
        pdf.set_font("Helvetica", "", 10)
        for _, row in dataframe.head(20).iterrows():
            d = str(row.get("Date", ""))
            f = str(row.get("food_name", ""))[:30]
            c = str(int(row.get("calories", 0)))
            pdf.cell(40, 10, d, 1)
            pdf.cell(80, 10, f, 1)
            pdf.cell(30, 10, c, 1)
            pdf.ln()
    return bytes(pdf.output())


def login_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/2913/2913990.png", width=80)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<h2 style='text-align: center; margin-bottom: 5px;'>NutriLens</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 14px; margin-bottom: 30px;'>Your Personal AI Nutritionist</p>", unsafe_allow_html=True)

        if supabase:
            if st.button("🌐 Continue with Google", type="primary", use_container_width=True):
                try:
                    data = supabase.auth.sign_in_with_oauth({
                        "provider": "google",
                        "options": {
                            "redirect_to": APP_URL,
                            "skip_browser_redirect": True
                        }
                    })
                    st.link_button("👉 Click to Authenticate", data.url, use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")

            st.markdown("<div style='text-align: center; margin: 20px 0; color: #555;'>OR</div>", unsafe_allow_html=True)

            tab1, tab2 = st.tabs(["Log In", "Sign Up"])
            with tab1:
                email = st.text_input("Username or Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                if st.button("Log In", use_container_width=True):
                    try:
                        session = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state.user = session.user
                        st.session_state.access_token = session.session.access_token
                        st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {e}")
            with tab2:
                ne = st.text_input("Email", key="su_email")
                np = st.text_input("Password", type="password", key="su_pass")
                if st.button("Sign Up", use_container_width=True):
                    try:
                        supabase.auth.sign_up({"email": ne, "password": np})
                        st.success("Confirmation sent! Check your inbox.")
                    except Exception as e:
                        st.error(f"Signup failed: {e}")
        else:
            st.warning("Running in local demo mode without active Supabase credentials.")
            if st.button("Enter as Guest Demo User", type="primary", use_container_width=True):
                class DemoUser:
                    id = "demo_guest_user"
                    email = "demo@nutrilens.local"
                st.session_state.user = DemoUser()
                st.session_state.access_token = "demo_guest_token"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def main_app():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/8804/8804665.png", width=40)
        st.markdown(f"<small>Logged in as</small><br><b>{st.session_state.user.email}</b>", unsafe_allow_html=True)
        st.write("")

        selected = option_menu(
            menu_title=None,
            options=["Tracker", "Dashboard", "Groceries", "AI Chef", "Community", "Scanner"],
            icons=["camera", "graph-up", "cart", "robot", "people", "upc-scan"],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#000000"},
                "icon": {"color": "#fafafa", "font-size": "14px"},
                "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px", "color": "#fafafa"},
                "nav-link-selected": {"background-color": "#262626"},
            }
        )

        st.divider()
        if st.button("Logout", use_container_width=True):
            if supabase:
                try:
                    supabase.auth.sign_out()
                except Exception:
                    pass
            st.session_state.user = None
            st.session_state.access_token = None
            st.rerun()

    user_id = st.session_state.user.id
    headers = get_auth_headers()

    # --- TRACKER ---
    if selected == "Tracker":
        st.title("Log Meal")
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.markdown('<div class="feed-card" style="text-align: center; height: 300px; display: flex; align-items: center; justify-content: center;">', unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Upload Food Photo", type=["jpg", "png", "jpeg"])
            if uploaded_file:
                st.image(uploaded_file, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            if uploaded_file:
                st.markdown("### Details")
                portion = st.slider("Portion Size Multiplier", 0.5, 3.0, 1.0, 0.1)
                is_public = st.toggle("Share to Community Feed", value=False)

                if st.button("Analyze & Log", type="primary"):
                    with st.spinner("Analyzing with AI..."):
                        uploaded_file.seek(0)
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        try:
                            res = requests.post(f"{API_URL}/analyze", files=files, timeout=15)
                            if res.status_code == 200:
                                data = res.json()
                                food = data["food_name"].replace("_", " ").title()
                                cals = round(data["calories"] * portion, 1)

                                # Log to backend with Auth Headers
                                payload = {
                                    "food_name": food,
                                    "calories": cals,
                                    "protein_g": round(data["protein_g"] * portion, 1),
                                    "fat_g": round(data["fat_g"] * portion, 1),
                                    "carb_g": round(data["carb_g"] * portion, 1),
                                    "is_public": is_public
                                }
                                log_res = requests.post(f"{API_URL}/log_meal", json=payload, headers=headers, timeout=10)
                                if log_res.status_code == 200:
                                    st.balloons()
                                    st.success(f"Logged: {food} ({cals} kcal)")
                                    st.session_state["last_food"] = food
                                else:
                                    st.warning(f"Analyzed {food}, but logging failed: {log_res.text}")
                            else:
                                st.error(f"Analysis failed ({res.status_code}): {res.text}")
                        except Exception as e:
                            st.error(f"Network error: {e}")

    # --- DASHBOARD ---
    elif selected == "Dashboard":
        st.title("Insights & Analytics")
        try:
            res = requests.get(f"{API_URL}/history/{user_id}", headers=headers, timeout=10)
            if res.status_code == 200 and res.json():
                data = res.json()
                df = pd.DataFrame(data)
                df["Date"] = pd.to_datetime(df["created_at"]).dt.date

                m1, m2, m3 = st.columns(3)
                m1.metric("Total Meals", len(df))
                m2.metric("Avg Daily Calories", f"{int(df['calories'].mean())} kcal")
                m3.metric("Avg Protein", f"{int(df['protein_g'].mean())}g")

                pdf = generate_pdf_report(st.session_state.user.email, df)
                st.download_button("Download PDF Health Report", data=pdf, file_name="nutrilens_report.pdf", mime="application/pdf", use_container_width=True)

                fig = px.bar(df.groupby("Date")["calories"].sum().reset_index(), x="Date", y="calories", title="Caloric Intake Over Time")
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No meal history recorded yet. Use the Tracker tab to log your meals!")
        except Exception as exc:
            st.error(f"Unable to load dashboard insights: {exc}")

    # --- COMMUNITY ---
    elif selected == "Community":
        st.title("Community Feed & Leaderboard")
        tab_feed, tab_leaderboard = st.tabs(["Explore Meals", "Weekly Leaderboard"])

        with tab_feed:
            try:
                res = requests.get(f"{API_URL}/community/feed", timeout=10)
                if res.status_code == 200:
                    feed = res.json()
                    if not feed:
                        st.info("No public meals shared yet. Be the first to share one in Tracker!")
                    cols = st.columns(3)
                    for idx, meal in enumerate(feed):
                        with cols[idx % 3]:
                            st.markdown(f"""
                            <div class="feed-card">
                                <h4 style="margin:0">{meal.get('food_name')}</h4>
                                <p style="font-size:12px">{meal.get('calories')} kcal • ❤️ {meal.get('likes_count', 0)} likes</p>
                            </div>
                            """, unsafe_allow_html=True)
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("❤️ Like", key=f"like_{meal.get('id')}_{idx}"):
                                    like_res = requests.post(f"{API_URL}/community/like", json={"meal_id": meal.get("id")}, headers=headers, timeout=10)
                                    if like_res.status_code == 200:
                                        st.toast("Liked!")
                                        st.rerun()
                                    elif like_res.status_code == 409:
                                        st.toast("You already liked this meal!")
                                    else:
                                        st.warning("Could not register like.")
                            with b2:
                                if st.button("👨‍🍳 Recipe", key=f"rec_{meal.get('id')}_{idx}"):
                                    st.session_state["last_food"] = meal.get("food_name")
                                    st.toast("Food loaded to AI Chef!")
                else:
                    st.error("Failed to load feed.")
            except Exception as e:
                st.error(f"Feed error: {e}")

        with tab_leaderboard:
            try:
                l_res = requests.get(f"{API_URL}/community/leaderboard", timeout=10)
                if l_res.status_code == 200:
                    leaderboard = l_res.json()
                    st.markdown("### Top Community Members (Last 7 Days)")
                    for row in leaderboard:
                        u = row.get("user_id") or "Vacant"
                        st.write(f"**Rank {row.get('rank')}**: {u} — {row.get('score')} meals logged")
            except Exception as e:
                st.error(f"Failed to fetch leaderboard: {e}")

    # --- AI CHEF ---
    elif selected == "AI Chef":
        st.title("AI Chef Assistant")
        food_query = st.text_input("What would you like to cook?", value=st.session_state.get("last_food", ""))
        if food_query:
            if st.button("Generate Healthy Recipe", type="primary"):
                if ai_model:
                    with st.spinner("Chef is generating recipe..."):
                        resp = ai_model.generate_content(f"Create a nutritious recipe using {food_query} with macronutrient breakdown and clear preparation steps.")
                        st.markdown(resp.text)
                        st.session_state["last_recipe"] = resp.text
                else:
                    st.info(f"Gemini API key not configured. Here is a quick healthy suggestion for {food_query}: Sauté with olive oil, add seasonal greens, and season with herbs and lemon juice.")

    # --- GROCERIES ---
    elif selected == "Groceries":
        st.title("Shopping List")
        c1, c2 = st.columns([3, 1])
        with c1:
            new_item = st.text_input("Add Groceries Item")
        with c2:
            st.write("")
            st.write("")
            if st.button("Add Item") and new_item.strip():
                if supabase:
                    supabase.table("shopping_list").insert({"user_id": user_id, "item": new_item.strip()}).execute()
                    st.rerun()

        if supabase:
            items = supabase.table("shopping_list").select("*").eq("user_id", user_id).execute().data or []
            for item in items:
                col_del, col_txt = st.columns([0.1, 0.9])
                with col_del:
                    if st.button("✕", key=f"del_{item['id']}"):
                        supabase.table("shopping_list").delete().eq("id", item["id"]).execute()
                        st.rerun()
                with col_txt:
                    st.write(item["item"])
        else:
            st.info("Shopping list requires configured Supabase connection.")

    # --- SCANNER (RESOLVED BARCODE / LABEL SPLIT) ---
    elif selected == "Scanner":
        st.title("Barcode Scanner & Nutrition Label Inspector")
        scan_mode = st.radio("Choose Scanner Mode", ["Barcode Scanning (OpenFoodFacts)", "Nutrition Label Inspection (AI Vision)"], horizontal=True)

        if scan_mode == "Barcode Scanning (OpenFoodFacts)":
            st.markdown("Scan standard product barcodes using a camera photo or direct barcode number.")
            barcode_file = st.file_uploader("Upload Barcode Image", type=["jpg", "png", "jpeg"], key="bc_file")
            barcode_input = st.text_input("Or Enter Barcode Digits Directly (e.g. 3017620422003)", key="bc_input")

            if st.button("Lookup Product", type="primary"):
                with st.spinner("Decoding and fetching product data..."):
                    files = None
                    data = {}
                    if barcode_file:
                        barcode_file.seek(0)
                        files = {"file": (barcode_file.name, barcode_file.getvalue(), barcode_file.type)}
                    if barcode_input.strip():
                        data["barcode_number"] = barcode_input.strip()

                    try:
                        res = requests.post(f"{API_URL}/scan_barcode", files=files, data=data, timeout=15)
                        if res.status_code == 200:
                            prod = res.json()
                            st.success(f"Product: **{prod.get('product_name')}** ({prod.get('brand')})")
                            c1, c2 = st.columns(2)
                            with c1:
                                st.write(f"**NutriScore**: {prod.get('nutriscore_grade') or 'N/A'}")
                                st.write(f"**NOVA Group**: {prod.get('nova_group') or 'N/A'}")
                                st.write(f"**Allergens**: {prod.get('allergens') or 'None detected'}")
                            with c2:
                                if prod.get("image_url"):
                                    st.image(prod.get("image_url"), width=150)
                            st.markdown(f"**Ingredients**: {prod.get('ingredients_text') or 'Not listed'}")
                        else:
                            st.error(f"Barcode search failed: {res.text}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")

        else:
            st.markdown("Upload a photo of any ingredients or nutrition facts label for AI health analysis.")
            label_file = st.file_uploader("Upload Nutrition / Ingredients Label", type=["jpg", "png", "jpeg"], key="label_file")

            if label_file and st.button("Inspect Label with AI", type="primary"):
                with st.spinner("Analyzing ingredient list with Gemini Vision..."):
                    label_file.seek(0)
                    files = {"file": (label_file.name, label_file.getvalue(), label_file.type)}
                    try:
                        res = requests.post(f"{API_URL}/scan_label", files=files, timeout=20)
                        if res.status_code == 200:
                            result = res.json()
                            st.success(f"Analyzed: {result.get('product_name')}")
                            st.metric("Estimated Health Rating", result.get("health_rating") or "N/A")
                            st.write(f"**Ingredients**: {result.get('ingredients_text')}")
                            if result.get("warnings"):
                                st.warning("⚠️ **Warnings**: " + ", ".join(result.get("warnings")))
                            if result.get("positive_points"):
                                st.info("✅ **Positive Points**: " + ", ".join(result.get("positive_points")))
                        else:
                            st.error(f"Label analysis failed: {res.text}")
                    except Exception as e:
                        st.error(f"Error inspecting label: {e}")


# --- AUTH ENTRY POINT ---
qp = st.query_params
if "code" in qp and supabase:
    try:
        s = supabase.auth.exchange_code_for_session({"auth_code": qp["code"]})
        st.session_state.user = s.user
        st.session_state.access_token = s.session.access_token
        st.query_params.clear()
        st.rerun()
    except Exception as exc:
        st.error(f"Authentication exchange error: {exc}")

if st.session_state.user:
    main_app()
else:
    login_page()
