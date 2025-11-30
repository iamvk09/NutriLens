import streamlit as st
import requests
from PIL import Image
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
import google.generativeai as genai
import os
from dotenv import load_dotenv
import datetime
from supabase import create_client
from fpdf import FPDF

# --- 1. SETUP & CONFIGURATION ---
load_dotenv()

# --- CONFIGURATION: DEPLOYMENT URLS ---
# 1. Backend URL (Hugging Face)
# We check st.secrets first (best practice), fallback to your hardcoded HF URL
if "API_URL" in st.secrets:
    API_URL = st.secrets["API_URL"]
else:
    # ⚠️ THIS IS YOUR REAL BACKEND URL
    API_URL = "https://iamvk09-nutrilens-api.hf.space/api/v1"

# 2. Frontend URL (Streamlit Cloud) used for Login Redirect
# ⚠️ THIS IS YOUR REAL FRONTEND URL
APP_URL = "https://nutrilens-cvx2xuevg8hlqycnfghuiv.streamlit.app"

# Page Config
st.set_page_config(page_title="NutriLens", page_icon="🥗", layout="wide")

# --- INSTAGRAM DARK MODE CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* BASE THEME - Instagram Dark */
    .stApp {
        background-color: #000000; /* Pitch Black */
        color: #F5F5F5;
        font-family: 'Inter', sans-serif;
    }

    /* HIDE STREAMLIT CHROME */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* CONTAINERS & CARDS */
    .css-1r6slb0, .css-12oz5g7 {
        background-color: #121212; /* Dark Gray Card */
        border: 1px solid #262626;
        border-radius: 12px;
        padding: 20px;
    }
    
    /* Login Card Specifics */
    .login-card {
        background-color: #1c1c1c;
        border: 1px solid #363636;
        border-radius: 16px;
        padding: 40px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    }

    /* TYPOGRAPHY */
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    p, label {
        color: #A8A8A8 !important; /* Muted Text */
    }

    /* INPUT FIELDS */
    .stTextInput > div > div > input {
        background-color: #262626 !important;
        color: white !important;
        border: 1px solid #363636 !important;
        border-radius: 8px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #0095F6 !important; /* Instagram Blue */
    }

    /* BUTTONS */
    .stButton > button {
        background-color: #0095F6 !important; /* Instagram Blue */
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #1877F2 !important;
    }
    
    /* SECONDARY BUTTONS (Gray) */
    button[kind="secondary"] {
        background-color: #262626 !important;
        color: white !important;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #000000 !important;
        border-right: 1px solid #262626;
    }

    /* METRIC CARDS */
    div[data-testid="metric-container"] {
        background-color: #121212;
        border: 1px solid #262626;
        padding: 15px;
        border-radius: 10px;
    }
    label[data-testid="stMetricLabel"] {
        color: #A8A8A8 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid #262626;
    }
    .stTabs [data-baseweb="tab"] {
        color: #A8A8A8;
    }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        border-bottom-color: #FFFFFF !important;
    }
    
    /* FEED CARDS */
    .feed-card {
        background-color: #121212;
        border: 1px solid #262626;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- SUPABASE & GEMINI SETUP ---
# Try secrets first, then environment variables
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
except:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Configuration Error: Supabase Keys Missing.")
    st.stop()

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    ai_model = genai.GenerativeModel('gemini-2.0-flash')

if 'user' not in st.session_state:
    st.session_state.user = None

# --- HELPER: PDF REPORT ---
def generate_pdf_report(user_email: str, dataframe: pd.DataFrame) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "NutriLens Health Report", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"User: {user_email}", ln=True, align="C")
    pdf.cell(0, 10, f"Date: {datetime.date.today()}", ln=True, align="C")
    pdf.ln(10)
    
    total_cals = dataframe['calories'].sum() if not dataframe.empty else 0
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Total Calories: {int(total_cals)} kcal", ln=True)
    pdf.ln(5)
    
    if not dataframe.empty:
        pdf.set_font("Arial", "B", 10)
        pdf.cell(40, 10, "Date", 1)
        pdf.cell(80, 10, "Food", 1)
        pdf.cell(30, 10, "Cals", 1)
        pdf.ln()
        pdf.set_font("Arial", "", 10)
        for _, row in dataframe.head(20).iterrows():
            d = str(row.get('Date', ''))
            f = str(row.get('food_name', ''))[:30]
            c = str(int(row.get('calories', 0)))
            pdf.cell(40, 10, d, 1)
            pdf.cell(80, 10, f, 1)
            pdf.cell(30, 10, c, 1)
            pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIN PAGE ---
def login_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/2913/2913990.png", width=80)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align: center; margin-bottom: 5px;'>NutriLens</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 14px; margin-bottom: 30px;'>Your Personal AI Nutritionist</p>", unsafe_allow_html=True)

        if st.button("🌐 Continue with Google", type="primary", use_container_width=True):
            try:
                data = supabase.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {
                        "redirect_to": APP_URL, # Uses the Real App URL
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
                    st.rerun()
                except:
                    st.error("Invalid credentials")
        with tab2:
            ne = st.text_input("Email", key="su_email")
            np = st.text_input("Password", type="password", key="su_pass")
            if st.button("Sign Up", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": ne, "password": np})
                    st.success("Check email to confirm!")
                except:
                    st.error("Signup failed")
        st.markdown('</div>', unsafe_allow_html=True)

# --- MAIN APP ---
def main_app():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/8804/8804665.png", width=40)
        st.markdown(f"<small>Logged in as</small><br><b>{st.session_state.user.email}</b>", unsafe_allow_html=True)
        st.write("")
        
        selected = option_menu(
            menu_title=None,
            options=["Tracker", "Dashboard", "Groceries", "AI Chef", "Community", "Barcode"],
            icons=["camera", "graph-up", "cart", "robot", "people", "upc-scan"],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#000000"},
                "icon": {"color": "#fafafa", "font-size": "14px"}, 
                "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "color": "#fafafa"},
                "nav-link-selected": {"background-color": "#262626"},
            }
        )
        
        st.divider()
        if st.button("Logout", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

    user_id = st.session_state.user.id

    # --- TRACKER ---
    if selected == "Tracker":
        st.title("New Post")
        col1, col2 = st.columns([1, 1.2])
        with col1:
            st.markdown('<div class="feed-card" style="text-align: center; height: 300px; display: flex; align-items: center; justify-content: center;">', unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Choose Photo", type=["jpg", "png", "jpeg"])
            if uploaded_file:
                st.image(uploaded_file, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            if uploaded_file:
                st.markdown("### Details")
                portion = st.slider("Portion Size", 0.5, 2.0, 1.0)
                is_public = st.toggle("Share to Feed")
                
                if st.button("Share & Log", type="primary"):
                    with st.spinner("Analyzing..."):
                        uploaded_file.seek(0)
                        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                        try:
                            # CALL BACKEND
                            res = requests.post(f"{API_URL}/analyze", files=files)
                            if res.status_code == 200:
                                data = res.json()
                                food = data['food_name'].replace("_", " ").title()
                                cals = int(data['calories'] * portion)
                                
                                # LOG TO DB
                                payload = {
                                    "user_id": user_id, "food_name": food, 
                                    "calories": cals, "protein_g": data['protein_g']*portion, 
                                    "fat_g": data['fat_g']*portion, "carb_g": data['carb_g']*portion,
                                    "is_public": is_public
                                }
                                requests.post(f"{API_URL}/log_meal", json=payload)
                                st.balloons()
                                st.success(f"Logged: {food} ({cals} kcal)")
                                st.session_state['last_food'] = food
                            else:
                                st.error("Analysis failed.")
                        except Exception as e:
                            st.error(f"Error: {e}")

    # --- DASHBOARD ---
    if selected == "Dashboard":
        st.title("Insights")
        try:
            res = requests.get(f"{API_URL}/history/{user_id}")
            if res.status_code == 200 and res.json():
                data = res.json()
                df = pd.DataFrame(data)
                df['Date'] = pd.to_datetime(df['created_at']).dt.date
                
                # Metrics Row
                m1, m2, m3 = st.columns(3)
                m1.metric("Meals", len(df))
                m2.metric("Avg Cals", int(df['calories'].mean()))
                m3.metric("Protein", f"{int(df['protein_g'].mean())}g")
                
                # Report
                pdf = generate_pdf_report(st.session_state.user.email, df)
                st.download_button("Download Report", data=pdf, file_name="report.pdf", mime="application/pdf", use_container_width=True)
                
                # Charts (Dark Theme)
                fig = px.bar(df.groupby('Date')['calories'].sum().reset_index(), x='Date', y='calories')
                fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data yet.")
        except:
            st.error("Network error.")

    # --- COMMUNITY ---
    if selected == "Community":
        st.title("Explore")
        try:
            res = requests.get(f"{API_URL}/community/feed")
            if res.status_code == 200:
                feed = res.json()
                # Instagram Grid Layout
                cols = st.columns(3)
                for idx, meal in enumerate(feed):
                    with cols[idx % 3]:
                        st.markdown(f"""
                        <div class="feed-card">
                            <h4 style="margin:0">{meal.get('food_name')}</h4>
                            <p style="font-size:12px">{meal.get('calories')} kcal • ❤️ {meal.get('likes_count',0)}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("❤️", key=f"l_{idx}"):
                                requests.post(f"{API_URL}/community/like", json={"meal_id": meal.get('id')})
                                st.rerun()
                        with b2:
                            if st.button("👨‍🍳", key=f"c_{idx}"):
                                st.session_state['last_food'] = meal.get('food_name')
                                st.toast("Recipe loaded!")
            else:
                st.info("Feed empty.")
        except:
            st.error("Feed error.")

    # --- AI CHEF ---
    if selected == "AI Chef":
        st.title("AI Chef")
        if 'last_food' in st.session_state:
            st.info(f"Ingredient: {st.session_state['last_food']}")
            if st.button("Generate Recipe", type="primary"):
                with st.spinner("Cooking..."):
                    resp = ai_model.generate_content(f"Recipe for {st.session_state['last_food']}")
                    st.markdown(resp.text)
                    st.session_state['last_recipe'] = resp.text
            
            if 'last_recipe' in st.session_state:
                if st.button("Add to Shopping List"):
                    # Quick add logic
                    supabase.table("shopping_list").insert({"user_id": user_id, "item": f"Ingredients for {st.session_state['last_food']}"}).execute()
                    st.success("Added!")
        else:
            st.warning("Select food from Tracker or Community first.")

    # --- GROCERIES ---
    if selected == "Groceries":
        st.title("Shopping List")
        c1, c2 = st.columns([3, 1])
        with c1:
            ni = st.text_input("Add Item")
        with c2:
            st.write("")
            st.write("")
            if st.button("Add"):
                supabase.table("shopping_list").insert({"user_id": user_id, "item": ni}).execute()
                st.rerun()
        
        items = supabase.table("shopping_list").select("*").eq("user_id", user_id).execute().data
        for i in items:
            c1, c2 = st.columns([0.1, 0.9])
            with c1:
                if st.button("✕", key=f"d_{i['id']}"):
                    supabase.table("shopping_list").delete().eq("id", i['id']).execute()
                    st.rerun()
            with c2:
                st.write(i['item'])

    # --- BARCODE ---
    if selected == "Barcode":
        st.title("Scanner")
        f = st.file_uploader("Upload Barcode/Label")
        if f and st.button("Scan"):
            with st.spinner("Scanning..."):
                f.seek(0)
                files = {"file": (f.name, f, f.type)}
                # Try Label scan first (AI Vision)
                res = requests.post(f"{API_URL}/scan_label", files=files)
                if res.status_code == 200:
                    st.json(res.json())
                else:
                    st.error("Scan failed")

# --- AUTH FLOW ---
qp = st.query_params
if "code" in qp:
    try:
        s = supabase.auth.exchange_code_for_session({"auth_code": qp["code"]})
        st.session_state.user = s.user
        st.query_params.clear()
        st.rerun()
    except:
        st.error("Login failed")

if st.session_state.user:
    main_app()
else:
    login_page()
