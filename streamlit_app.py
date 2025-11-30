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

# API Configuration
API_URL = "http://127.0.0.1:8000/api/v1"
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Page Config
st.set_page_config(page_title="NutriLens Ultimate", page_icon="🥗", layout="wide")

# --- GLOBAL CSS: MODERN DARK THEME ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit default menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Dark Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 25%, #24243e 50%, #1a1a2e 75%, #16213e 100%);
        background-size: 400% 400%;
        animation: gradientShift 20s ease infinite;
        min-height: 100vh;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Main Content Area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Login Card - Dark Premium Design */
    .login-card {
        background: rgba(18, 18, 30, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(102, 126, 234, 0.3);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 
                    0 0 0 1px rgba(102, 126, 234, 0.1) inset;
        border-radius: 24px;
        padding: 48px;
        margin: 20px 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .login-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 24px 72px rgba(102, 126, 234, 0.3), 
                    0 0 0 1px rgba(102, 126, 234, 0.2) inset;
    }
    
    /* Input Fields - Dark Design */
    .stTextInput > div > div > input,
    input[type="text"],
    input[type="password"],
    input[type="email"] {
        background-color: rgba(30, 30, 46, 0.8) !important;
        color: #e2e8f0 !important;
        border: 2px solid rgba(102, 126, 234, 0.3) !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
    }
    
    .stTextInput > div > div > input:focus,
    input[type="text"]:focus,
    input[type="password"]:focus,
    input[type="email"]:focus {
        border: 2px solid #667eea !important;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2), 
                    0 4px 12px rgba(102, 126, 234, 0.4) !important;
        outline: none !important;
        background-color: rgba(30, 30, 46, 1) !important;
    }
    
    .stTextInput label,
    label {
        color: #cbd5e0 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 8px !important;
    }
    
    /* Button Styling - Dark Theme */
    .stButton > button {
        width: 100% !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 14px 24px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: none !important;
        text-transform: none !important;
        letter-spacing: 0.3px !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) scale(0.98) !important;
    }
    
    /* Primary Button - Gradient */
    button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.5) !important;
    }
    
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.6) !important;
    }
    
    /* Secondary Button */
    button[kind="secondary"] {
        background-color: rgba(30, 30, 46, 0.8) !important;
        color: #cbd5e0 !important;
        border: 2px solid rgba(102, 126, 234, 0.4) !important;
    }
    
    button[kind="secondary"]:hover {
        background-color: rgba(30, 30, 46, 1) !important;
        border-color: #667eea !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Text Styling - Dark Theme */
    h1 {
        color: #f7fafc !important;
        font-weight: 800 !important;
        font-size: 32px !important;
        letter-spacing: -0.5px !important;
        margin-bottom: 8px !important;
    }
    
    h2 {
        color: #e2e8f0 !important;
        font-weight: 700 !important;
        font-size: 24px !important;
    }
    
    h3 {
        color: #cbd5e0 !important;
        font-weight: 600 !important;
        font-size: 20px !important;
    }
    
    p, .stMarkdown {
        color: #a0aec0 !important;
        line-height: 1.6 !important;
    }
    
    /* Tab Styling - Dark */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: rgba(30, 30, 46, 0.6);
        border-radius: 12px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 8px !important;
        color: #a0aec0 !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(102, 126, 234, 0.3) !important;
        color: #f7fafc !important;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* Alert/Message Styling - Dark */
    .stAlert {
        background-color: rgba(18, 18, 30, 0.95) !important;
        border-left: 4px solid #667eea !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        color: #e2e8f0 !important;
    }
    
    /* Link Button - Dark */
    .stLinkButton > a {
        background: rgba(30, 30, 46, 0.8) !important;
        color: #667eea !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        text-decoration: none !important;
        display: inline-block !important;
        transition: all 0.3s ease !important;
        font-weight: 600 !important;
        border: 2px solid rgba(102, 126, 234, 0.4) !important;
    }
    
    .stLinkButton > a:hover {
        background: rgba(30, 30, 46, 1) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
        border-color: #667eea !important;
    }
    
    /* Divider - Dark */
    hr {
        border-color: rgba(102, 126, 234, 0.3) !important;
        margin: 24px 0 !important;
    }
    
    /* Sidebar Styling - Dark */
    [data-testid="stSidebar"],
    .css-1d391kg {
        background-color: rgba(18, 18, 30, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(102, 126, 234, 0.2) !important;
    }
    
    /* Metric Cards - Dark */
    .metric-card {
        background: rgba(18, 18, 30, 0.8) !important;
        border: 1px solid rgba(102, 126, 234, 0.3) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        text-align: center !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
        transition: transform 0.2s ease !important;
    }
    
    .metric-card:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3) !important;
        border-color: rgba(102, 126, 234, 0.5) !important;
    }
    
    /* Scrollbar Styling - Dark */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(18, 18, 30, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(102, 126, 234, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(102, 126, 234, 0.7);
    }
    
    /* Dataframe Styling - Dark */
    .dataframe {
        background-color: rgba(18, 18, 30, 0.8) !important;
        color: #e2e8f0 !important;
    }
    
    /* Selectbox and other inputs */
    .stSelectbox > div > div {
        background-color: rgba(30, 30, 46, 0.8) !important;
        color: #e2e8f0 !important;
    }
    
    /* File Uploader */
    .stFileUploader {
        background-color: rgba(18, 18, 30, 0.6) !important;
        border: 2px dashed rgba(102, 126, 234, 0.3) !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Supabase
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Supabase keys missing from .env file!")
    st.stop()

# We use 'cache_resource' to ensure the client persists across re-runs
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Initialize Gemini
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    ai_model = genai.GenerativeModel('gemini-2.0-flash')

# Initialize Session State
if 'user' not in st.session_state:
    st.session_state.user = None

# --- HELPER FUNCTION: PDF REPORT GENERATION ---
def generate_pdf_report(user_email: str, dataframe: pd.DataFrame) -> bytes:
    """
    Generate a PDF health report with title, summary metrics, and meal table.
    Returns PDF as bytes.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "NutriLens Health Report", ln=True, align="C")
    pdf.ln(5)
    
    # User email
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"User: {user_email}", ln=True, align="C")
    pdf.cell(0, 10, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.ln(10)
    
    # Summary Metrics
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Summary Metrics", ln=True)
    pdf.set_font("Arial", "", 12)
    
    total_logs = len(dataframe)
    total_cals = dataframe['calories'].sum() if 'calories' in dataframe.columns else 0
    total_protein = dataframe['protein_g'].sum() if 'protein_g' in dataframe.columns else 0
    
    pdf.cell(0, 10, f"Total Logs: {total_logs}", ln=True)
    pdf.cell(0, 10, f"Total Calories: {int(total_cals)} kcal", ln=True)
    pdf.cell(0, 10, f"Total Protein: {round(total_protein, 1)} g", ln=True)
    pdf.ln(10)
    
    # Meal Table
    if not dataframe.empty and len(dataframe) > 0:
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Recent Meals", ln=True)
        pdf.ln(5)
        
        # Table headers
        pdf.set_font("Arial", "B", 10)
        col_widths = [30, 40, 30, 30, 30, 25, 25]
        headers = ["Date", "Food", "Calories", "Protein(g)", "Carbs(g)", "Fat(g)"]
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i] if i < len(col_widths) else 40, 8, header, border=1)
        pdf.ln()
        
        # Table rows (limit to last 20 meals)
        pdf.set_font("Arial", "", 9)
        display_df = dataframe.head(20)
        
        for idx, row in display_df.iterrows():
            date_str = str(row.get('Date', '')) if 'Date' in row else str(row.get('created_at', ''))[:10] if 'created_at' in row else ''
            food = str(row.get('Food', row.get('food_name', '')))[:35]
            cals = str(int(row.get('Calories', row.get('calories', 0))))
            prot = str(round(row.get('Protein (g)', row.get('protein_g', 0)), 1))
            carbs = str(round(row.get('Carbs (g)', row.get('carb_g', 0)), 1))
            fat = str(round(row.get('Fat (g)', row.get('fat_g', 0)), 1))
            
            pdf.cell(col_widths[0], 6, date_str, border=1)
            pdf.cell(col_widths[1], 6, food, border=1)
            pdf.cell(col_widths[2], 6, cals, border=1)
            pdf.cell(col_widths[3], 6, prot, border=1)
            pdf.cell(col_widths[4], 6, carbs, border=1)
            pdf.cell(col_widths[5], 6, fat, border=1)
            pdf.ln()
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')

# --- 2. LOGIN PAGE (FIXED FOR OAUTH ERROR) ---
def login_page():
    # Center the login card with better spacing
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        # Modern Premium Card Container
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # Logo and Title with better styling
        st.markdown("<div style='text-align: center; margin-bottom: 32px;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/2913/2913990.png", width=100)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<h1 style='text-align: center; margin-top: 16px; margin-bottom: 8px;'>Welcome to NutriLens</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #a0aec0; margin-bottom: 40px; font-size: 16px;'>Your AI-Powered Health & Nutrition Assistant</p>", unsafe_allow_html=True)

        # --- GOOGLE LOGIN (FIXED) ---
        if st.button("🌐 Continue with Google", type="primary", use_container_width=True):
            try:
                # We use skip_browser_redirect=True to prevent Streamlit from 
                # reloading prematurely, which causes the PKCE Verifier error.
                data = supabase.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {
                        "redirect_to": "http://localhost:8501",
                        "skip_browser_redirect": True 
                    }
                })
                # Show the URL as a clickable link
                st.link_button("👉 Click here to continue to Google", data.url)
            except Exception as e:
                st.error(f"Connection Error: {e}")
        
        st.markdown("<div style='text-align: center; margin: 32px 0;'><p style='color: #718096; font-size: 14px;'>━━━━ OR ━━━━</p></div>", unsafe_allow_html=True)
        
        # --- EMAIL LOGIN ---
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        with tab1:
            st.markdown("<div style='margin-bottom: 24px;'>", unsafe_allow_html=True)
            email = st.text_input("Email address", key="login_email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("Sign In", type="primary", use_container_width=True):
                try:
                    session = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = session.user
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")
        
        with tab2:
            st.markdown("<div style='margin-bottom: 24px;'>", unsafe_allow_html=True)
            new_email = st.text_input("Email address", key="signup_email", placeholder="you@example.com")
            new_password = st.text_input("Password", type="password", key="signup_pass", placeholder="Create a strong password")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("Create Account", type="primary", use_container_width=True):
                try:
                    session = supabase.auth.sign_up({"email": new_email, "password": new_password})
                    st.success("✅ Account created! Please check your email to confirm your account.")
                except Exception as e:
                    st.error(f"Signup failed: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- 3. MAIN APPLICATION (Protected) ---
def main_app():
    # Additional CSS for main app (global CSS already applied)
    st.markdown("""
    <style>
        /* Main content area styling - Dark */
        .main .block-container {
            background: rgba(18, 18, 30, 0.8);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 32px;
            margin: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(102, 126, 234, 0.2);
        }
        
        /* Sidebar enhancements - Dark */
        [data-testid="stSidebar"] {
            background: rgba(18, 18, 30, 0.95) !important;
            backdrop-filter: blur(20px) !important;
        }
        
        /* Metric cards - Dark */
        .metric-card {
            background: rgba(18, 18, 30, 0.8);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(102, 126, 234, 0.3);
            border-color: rgba(102, 126, 234, 0.5);
        }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/8804/8804665.png", width=50)
        st.write(f"Logged in: **{st.session_state.user.email}**")
        
        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()
            
        st.divider()
        
        selected = option_menu(
            menu_title="Menu",
            options=["Tracker", "Dashboard", "AI Chef", "Diet Planner", "Community", "Groceries", "Barcode Scanner"],
            icons=["camera", "activity", "egg-fried", "calendar-check", "people", "cart", "barcode"],
            default_index=0,
        )
        
        user_id = st.session_state.user.id
        
        st.divider()
        st.subheader("🎯 Goals")
        daily_cal_target = st.number_input("Calorie Target", value=2200, step=50)
        protein_target = st.number_input("Protein Target (g)", value=120, step=5)
        water_target = st.slider("Water Target (L)", 1.0, 4.0, 2.5)

        st.subheader("💧 Hydration")
        if 'water_count' not in st.session_state: st.session_state.water_count = 0.0
        c1, c2 = st.columns([1,2])
        with c1:
            if st.button("➕"): st.session_state.water_count += 0.25
        with c2:
            st.progress(min(st.session_state.water_count / water_target, 1.0))

    # --- TAB 1: TRACKER ---
    if selected == "Tracker":
        st.header("📸 AI Food Analysis")
        c1, c2 = st.columns([1, 1.2])
        with c1:
            uploaded_file = st.file_uploader("Upload Food Image", type=["jpg", "png", "jpeg"])
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, use_container_width=True)
        with c2:
            if uploaded_file:
                portion_mult = st.slider("Portion Size Estimate", 0.5, 2.0, 1.0, format="%gx")
                is_public = st.checkbox("Share to Community", value=False)
                if st.button("🔍 Scan & Analyze", type="primary"):
                    with st.spinner('Processing...'):
                        try:
                            # Send to Backend
                            uploaded_file.seek(0)
                            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                            response = requests.post(f"{API_URL}/analyze", files=files)
                            
                            if response.status_code == 200:
                                data = response.json()
                                food_name = data['food_name'].replace("_", " ").title()
                                
                                # Adjust for Portion
                                cals = int(data['calories'] * portion_mult)
                                prot = round(data['protein_g'] * portion_mult, 1)
                                fat = round(data['fat_g'] * portion_mult, 1)
                                carb = round(data['carb_g'] * portion_mult, 1)
                                
                                st.success(f"**Identified:** {food_name}")
                                m1, m2, m3, m4 = st.columns(4)
                                m1.metric("Cals", cals)
                                m2.metric("Prot", f"{prot}g")
                                m3.metric("Carbs", f"{carb}g")
                                m4.metric("Fat", f"{fat}g")
                                
                                # Log to DB
                                payload = {
                                    "user_id": user_id, "food_name": food_name,
                                    "calories": cals, "protein_g": prot,
                                    "fat_g": fat, "carb_g": carb,
                                    "is_public": is_public
                                }
                                requests.post(f"{API_URL}/log_meal", json=payload)
                                st.toast("Saved to Database!", icon="✅")
                                
                                st.session_state['last_food'] = food_name
                            else:
                                st.error("Backend Error. Is `main.py` running?")
                        except Exception as e:
                            st.error(f"Connection Failed: {e}")

# --- TAB 2: DASHBOARD ---
    if selected == "Dashboard":
        st.header("📊 Health Analytics")
        try:
            # 1. Fetch History from Backend
            res = requests.get(f"{API_URL}/history/{user_id}")
            
            if res.status_code == 200:
                data = res.json()
                if data:
                    # 2. Process Data
                    df = pd.DataFrame(data)
                    df['created_at'] = pd.to_datetime(df['created_at'])
                    df['Date'] = df['created_at'].dt.date
                    df['Time'] = df['created_at'].dt.strftime('%H:%M') # Format time
                    
                    # 3. Top Metrics
                    total_cals = df['calories'].sum()
                    k1, k2 = st.columns([1, 1])
                    k1.metric("Total Logs", len(df))
                    k2.metric("Total Calories", int(total_cals))
                    
                    # Download Report Button
                    try:
                        pdf_bytes = generate_pdf_report(st.session_state.user.email, df)
                        st.download_button(
                            label="📥 Download Report",
                            data=pdf_bytes,
                            file_name=f"nutrilens_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                    except Exception as e:
                        st.error(f"Failed to generate PDF: {e}")
                    
                    if df['protein_g'].mean() < protein_target:
                        st.warning(f"⚠️ Low Protein Average: {int(df['protein_g'].mean())}g")
                        
                    # 4. Charts
                    c1, c2 = st.columns(2)
                    with c1:
                        daily = df.groupby('Date')['calories'].sum().reset_index()
                        st.plotly_chart(px.bar(daily, x='Date', y='calories', title="Daily Calories"), use_container_width=True)
                    with c2:
                        macros = df[['protein_g', 'carb_g', 'fat_g']].sum().reset_index()
                        macros.columns = ['Macro', 'Grams']
                        st.plotly_chart(px.pie(macros, values='Grams', names='Macro', hole=0.4, title="Macro Split"), use_container_width=True)
                    
                    # --- NEW: DETAILED HISTORY TABLE ---
                    st.divider()
                    st.subheader("📜 Recent Meal Logs")
                    
                    # Select and rename columns for a cleaner look
                    display_df = df[['Date', 'Time', 'food_name', 'calories', 'protein_g', 'carb_g', 'fat_g']]
                    display_df.columns = ['Date', 'Time', 'Food', 'Calories', 'Protein (g)', 'Carbs (g)', 'Fat (g)']
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                else:
                    st.info("No data yet. Go to the Tracker tab and log a meal!")
        except Exception as e:
            st.error(f"Error fetching history: {e}")

    # --- TAB 3: AI CHEF (CHAT INTERFACE) ---
    if selected == "AI Chef":
        st.header("💬 AI Nutritionist & Chef")
        
        # 1. Initialize Chat History in Session State
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
            # Load past chat from Supabase on first load
            try:
                response = supabase.table("chat_history")\
                    .select("*")\
                    .eq("user_id", st.session_state.user.id)\
                    .order("created_at", desc=False)\
                    .execute()
                
                for msg in response.data:
                    st.session_state.messages.append({"role": msg["role"], "content": msg["content"]})
            except Exception as e:
                st.error(f"Failed to load chat history: {e}")

        # 2. Display Chat Messages
        last_assistant_index = -1
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant":
                    last_assistant_index = idx
        
        # Show "Add Ingredients" button if last message is assistant response
        if (last_assistant_index >= 0 and 
            len(st.session_state.messages) > 0 and 
            st.session_state.messages[-1]["role"] == "assistant" and
            last_assistant_index == len(st.session_state.messages) - 1):
            
            last_recipe = st.session_state.messages[last_assistant_index]["content"]
            # Store in session state for ingredient extraction
            if 'last_recipe' not in st.session_state or st.session_state.get('last_recipe_index') != last_assistant_index:
                st.session_state['last_recipe'] = last_recipe
                st.session_state['last_recipe_index'] = last_assistant_index
            
            # Button to add ingredients to shopping list
            if st.button("🛒 Add Ingredients to Shopping List", key="add_ingredients_btn"):
                if GEMINI_KEY:
                    with st.spinner("Extracting ingredients..."):
                        try:
                            # Use Gemini to extract ingredients from recipe
                            extraction_prompt = f"""From the following recipe or food content, extract ONLY the ingredient names as a comma-separated list. 
Return ONLY the ingredients separated by commas, nothing else. No explanations, no quantities, just ingredient names.
If no recipe or ingredients are present, return "none".

Content:
{last_recipe}

Ingredients (comma-separated):"""
                            
                            extraction_response = ai_model.generate_content(extraction_prompt)
                            ingredients_text = extraction_response.text.strip()
                            
                            if ingredients_text.lower() != "none" and ingredients_text:
                                # Parse ingredients (split by comma)
                                ingredients = [ing.strip() for ing in ingredients_text.split(",") if ing.strip()]
                                
                                if ingredients:
                                    # Add each ingredient to shopping list
                                    added_count = 0
                                    for ingredient in ingredients:
                                        try:
                                            # Check if item already exists
                                            existing = supabase.table("shopping_list")\
                                                .select("*")\
                                                .eq("user_id", user_id)\
                                                .ilike("item", ingredient.strip())\
                                                .execute()
                                            
                                            if not existing.data:
                                                supabase.table("shopping_list").insert({
                                                    "user_id": user_id,
                                                    "item": ingredient.strip(),
                                                    "created_at": datetime.datetime.now().isoformat()
                                                }).execute()
                                                added_count += 1
                                        except Exception as e:
                                            st.warning(f"Could not add '{ingredient}': {e}")
                                    
                                    if added_count > 0:
                                        st.success(f"✅ Added {added_count} ingredient(s) to shopping list! Check the Groceries tab. 🛒")
                                    else:
                                        st.info("All ingredients are already in your shopping list.")
                                else:
                                    st.warning("No ingredients found in the recipe.")
                            else:
                                st.info("No ingredients found in this content.")
                        except Exception as e:
                            st.error(f"Failed to extract ingredients: {e}")
                else:
                    st.error("Gemini API key is missing. Cannot extract ingredients.")

        # 3. Handle User Input
        if prompt := st.chat_input("Ask about recipes, diet plans, or fitness..."):
            
            # A. Display User Message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Save User Msg to DB
            supabase.table("chat_history").insert({
                "user_id": st.session_state.user.id,
                "role": "user",
                "content": prompt
            }).execute()

            # B. Generate AI Response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                # Context Awareness (Check last scanned food)
                context = ""
                if 'last_food' in st.session_state:
                    context = f"(Context: User recently scanned {st.session_state['last_food']}). "

                if GEMINI_KEY:
                    try:
                        # Call Gemini
                        response = ai_model.generate_content(context + prompt)
                        full_response = response.text
                        message_placeholder.markdown(full_response)
                        
                        # Save AI Msg to Session
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                        
                        # Save AI Msg to DB
                        supabase.table("chat_history").insert({
                            "user_id": st.session_state.user.id,
                            "role": "assistant",
                            "content": full_response
                        }).execute()
                        
                    except Exception as e:
                        message_placeholder.error(f"AI Error: {e}")
                else:
                    message_placeholder.error("Gemini Key missing.")


    # --- TAB 4: DIET PLANNER ---
    if selected == "Diet Planner":
        st.header("📅 Weekly Diet Planner")
        goal = st.selectbox("Goal", ["Weight Loss", "Muscle Gain"])
        if st.button("Create Plan"):
            if GEMINI_KEY:
                with st.spinner("Planning..."):
                    resp = ai_model.generate_content(f"7-day diet plan for {goal} targeting {daily_cal_target} cals/day.")
                    st.markdown(resp.text)

    # --- TAB 5: COMMUNITY ---
    if selected == "Community":
        st.header("🌎 Community Feed")
        
        # Split into Feed (70%) and Leaderboard (30%)
        feed_col, leaderboard_col = st.columns([0.7, 0.3])
        
        # --- LEFT COLUMN: FEED ---
        with feed_col:
            st.subheader("📱 Recent Meals")
            try:
                # Fetch community feed
                feed_response = requests.get(f"{API_URL}/community/feed")
                
                if feed_response.status_code == 200:
                    feed_data = feed_response.json()
                    
                    if feed_data:
                        for meal in feed_data:
                            # Create a card for each meal
                            with st.container():
                                st.markdown(f"""
                                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 15px; background-color: #0e1117;">
                                    <h4>{meal.get('food_name', 'Unknown Food')}</h4>
                                    <p><strong>Calories:</strong> {meal.get('calories', 0)} kcal</p>
                                    <p><strong>User:</strong> {str(meal.get('user_id', 'Unknown'))[:8]}...</p>
                                    <p><strong>❤️ Likes:</strong> {meal.get('likes_count', 0) or 0}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Action buttons
                                btn_col1, btn_col2 = st.columns(2)
                                with btn_col1:
                                    if st.button(f"❤️ Like", key=f"like_{meal.get('id')}"):
                                        try:
                                            like_response = requests.post(
                                                f"{API_URL}/community/like",
                                                json={"meal_id": meal.get('id')}
                                            )
                                            if like_response.status_code == 200:
                                                st.toast("Liked! ❤️", icon="❤️")
                                                st.rerun()
                                            else:
                                                st.error("Failed to like meal")
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                                
                                with btn_col2:
                                    if st.button(f"👨‍🍳 Cook This", key=f"cook_{meal.get('id')}"):
                                        food_name = meal.get('food_name', '')
                                        st.session_state['last_food'] = food_name
                                        st.toast(f"Ready in AI Chef tab! 👨‍🍳", icon="👨‍🍳")
                                
                                st.divider()
                    else:
                        st.info("No public meals yet. Be the first to share! 🎉")
                else:
                    st.error(f"Failed to load feed: {feed_response.status_code}")
            except Exception as e:
                st.error(f"Error fetching feed: {e}")
        
        # --- RIGHT COLUMN: LEADERBOARD ---
        with leaderboard_col:
            st.subheader("🏆 Leaderboard")
            st.caption("Top 3 users this week")
            
            try:
                # Fetch leaderboard
                leaderboard_response = requests.get(f"{API_URL}/community/leaderboard")
                
                if leaderboard_response.status_code == 200:
                    leaderboard_data = leaderboard_response.json()
                    
                    # Create a simple table
                    leaderboard_df = pd.DataFrame(leaderboard_data)
                    if not leaderboard_df.empty:
                        # Format for display
                        display_df = leaderboard_df[['rank', 'user_id', 'score']].copy()
                        display_df.columns = ['Rank', 'User', 'Score (Meals)']
                        
                        # Handle None user_ids
                        display_df['User'] = display_df['User'].apply(
                            lambda x: f"{str(x)[:8]}..." if x else "—"
                        )
                        
                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No leaderboard data yet.")
                else:
                    st.error(f"Failed to load leaderboard: {leaderboard_response.status_code}")
            except Exception as e:
                st.error(f"Error fetching leaderboard: {e}")

    # --- TAB 6: GROCERIES ---
    if selected == "Groceries":
        st.header("🛒 Shopping List")
        
        # A. Add items manually
        st.subheader("➕ Add Item")
        col1, col2 = st.columns([3, 1])
        with col1:
            new_item = st.text_input("Enter item name", key="new_grocery_item", placeholder="e.g., Milk, Bread, Eggs...")
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("Add", type="primary"):
                if new_item and new_item.strip():
                    try:
                        supabase.table("shopping_list").insert({
                            "user_id": user_id,
                            "item": new_item.strip(),
                            "created_at": datetime.datetime.now().isoformat()
                        }).execute()
                        st.success(f"✅ Added '{new_item.strip()}' to shopping list!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add item: {e}")
                else:
                    st.warning("Please enter an item name.")
        
        st.divider()
        
        # B. View and manage list
        st.subheader("📋 Your Shopping List")
        try:
            # Fetch shopping list from Supabase
            shopping_list_response = supabase.table("shopping_list")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=False)\
                .execute()
            
            if shopping_list_response.data:
                # Display items with delete buttons
                for idx, item in enumerate(shopping_list_response.data):
                    item_col, delete_col = st.columns([4, 1])
                    with item_col:
                        st.write(f"• {item.get('item', 'Unknown Item')}")
                    with delete_col:
                        if st.button("🗑️", key=f"delete_{item.get('id')}"):
                            try:
                                supabase.table("shopping_list")\
                                    .delete()\
                                    .eq("id", item.get('id'))\
                                    .execute()
                                st.success(f"Deleted '{item.get('item', 'Unknown')}'")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete item: {e}")
                
                # Bulk actions
                st.divider()
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Clear All", type="secondary"):
                        try:
                            for item in shopping_list_response.data:
                                supabase.table("shopping_list")\
                                    .delete()\
                                    .eq("id", item.get('id'))\
                                    .execute()
                            st.success("Shopping list cleared!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to clear list: {e}")
            else:
                st.info("Your shopping list is empty. Add items above! 🛒")
        except Exception as e:
            st.error(f"Error fetching shopping list: {e}")

    # --- TAB 7: BARCODE SCANNER ---
    if selected == "Barcode Scanner":
        st.header("📷 Barcode Scanner")
        st.write("Scan a barcode to get product information and health analysis.")
        
        # Initialize session state for product data
        if 'scanned_product' not in st.session_state:
            st.session_state.scanned_product = None
        
        # Input Section
        input_col1, input_col2 = st.columns([2, 1])
        
        with input_col1:
            uploaded_file = st.file_uploader("Upload Barcode Image", type=["jpg", "png", "jpeg"], key="barcode_image")
            if uploaded_file:
                st.image(uploaded_file, width=300, caption="Barcode Image")
        
        with input_col2:
            st.subheader("OR")
            manual_barcode = st.text_input("Enter Barcode Number", key="manual_barcode", placeholder="e.g., 3017620422003")
        
        # Scan/Search Button
        scan_button_col1, scan_button_col2, scan_button_col3 = st.columns([1, 2, 1])
        with scan_button_col2:
            if st.button("🔍 Scan / Search", type="primary", use_container_width=True):
                if uploaded_file or manual_barcode:
                    with st.spinner("Scanning barcode and fetching product data..."):
                        try:
                            # Prepare request
                            files = None
                            data = {}
                            
                            if uploaded_file:
                                uploaded_file.seek(0)
                                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                            
                            if manual_barcode and manual_barcode.strip():
                                data["barcode_number"] = manual_barcode.strip()
                            
                            # Send request to backend
                            if files:
                                response = requests.post(f"{API_URL}/scan_barcode", files=files, data=data)
                            else:
                                response = requests.post(f"{API_URL}/scan_barcode", data=data)
                            
                            if response.status_code == 200:
                                st.session_state.scanned_product = response.json()
                                st.success("✅ Product found!")
                                st.rerun()
                            elif response.status_code == 400:
                                st.error(f"❌ {response.json().get('detail', 'Invalid request')}")
                            elif response.status_code == 404:
                                st.warning(f"⚠️ {response.json().get('detail', 'Product not found')}")
                            else:
                                st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"Connection failed: {e}")
                else:
                    st.warning("Please upload a barcode image OR enter a barcode number.")
        
        st.divider()
        
        # Display Product Information
        if st.session_state.scanned_product:
            product = st.session_state.scanned_product
            
            # Product Header
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader(product.get('product_name', 'Unknown Product'))
                st.write(f"**Brand:** {product.get('brand', 'Unknown Brand')}")
                if product.get('barcode'):
                    st.caption(f"Barcode: {product.get('barcode')}")
            
            with col2:
                if product.get('image_url'):
                    st.image(product.get('image_url'), caption="Product Image", use_container_width=True)
            
            st.divider()
            
            # Health Cards
            st.subheader("🏥 Health Indicators")
            
            health_col1, health_col2 = st.columns(2)
            
            with health_col1:
                # NutriScore Display
                nutri_grade = product.get('nutriscore_grade')
                if nutri_grade:
                    # Color mapping for NutriScore
                    nutri_colors = {
                        'A': '🟢', 'B': '🟢', 'C': '🟡', 
                        'D': '🟠', 'E': '🔴'
                    }
                    nutri_color = nutri_colors.get(nutri_grade, '⚪')
                    st.metric(
                        label=f"NutriScore {nutri_color}",
                        value=nutri_grade,
                        help="A = Best, E = Worst"
                    )
                else:
                    st.metric(
                        label="NutriScore",
                        value="N/A",
                        help="Not available for this product"
                    )
            
            with health_col2:
                # NOVA Group Display
                nova_group = product.get('nova_group')
                if nova_group:
                    nova_labels = {
                        1: '🟢 Natural/Minimally Processed',
                        2: '🟡 Processed Culinary Ingredients',
                        3: '🟠 Processed Foods',
                        4: '🔴 Ultra-Processed Foods'
                    }
                    nova_label = nova_labels.get(nova_group, f'Group {nova_group}')
                    st.metric(
                        label="NOVA Group",
                        value=nova_label,
                        help="1 = Natural, 4 = Ultra Processed"
                    )
                else:
                    st.metric(
                        label="NOVA Group",
                        value="N/A",
                        help="Not available for this product"
                    )
            
            st.divider()
            
            # AI Safety Check
            st.subheader("🤖 AI Health Analysis")
            
            ingredients_text = product.get('ingredients_text', '')
            if ingredients_text:
                st.write("**Ingredients:**")
                st.info(ingredients_text[:500] + "..." if len(ingredients_text) > 500 else ingredients_text)
                
                # AI Analysis
                if GEMINI_KEY:
                    with st.spinner("🤖 Analyzing ingredients with AI..."):
                        try:
                            analysis_prompt = f"""Analyze these ingredients: {ingredients_text}
                            
Is this product healthy? Are there any harmful additives, preservatives, or artificial ingredients?
Provide a brief verdict: Safe or Unsafe, and give a short explanation (2-3 sentences).

Format your response as:
VERDICT: Safe/Unsafe
EXPLANATION: [brief explanation]"""
                            
                            ai_response = ai_model.generate_content(analysis_prompt)
                            analysis_text = ai_response.text
                            
                            # Parse verdict
                            verdict = "Unknown"
                            explanation = analysis_text
                            
                            if "VERDICT:" in analysis_text.upper():
                                lines = analysis_text.split('\n')
                                for line in lines:
                                    if 'VERDICT:' in line.upper():
                                        verdict = line.split(':', 1)[1].strip()
                                        break
                            
                            if "EXPLANATION:" in analysis_text.upper():
                                explanation = analysis_text.split("EXPLANATION:", 1)[-1].strip()
                            
                            # Display verdict with color coding
                            if "SAFE" in verdict.upper():
                                st.success(f"✅ **VERDICT: {verdict}**")
                            elif "UNSAFE" in verdict.upper():
                                st.error(f"❌ **VERDICT: {verdict}**")
                            else:
                                st.info(f"⚠️ **VERDICT: {verdict}**")
                            
                            st.write("**Analysis:**")
                            st.write(explanation)
                            
                        except Exception as e:
                            st.error(f"AI analysis failed: {e}")
                else:
                    st.warning("Gemini API key is missing. Cannot perform AI analysis.")
            else:
                st.info("No ingredients information available for this product.")
            
            # Allergens
            if product.get('allergens'):
                st.divider()
                st.subheader("⚠️ Allergens")
                st.warning(product.get('allergens'))

# --- 4. APP CONTROL FLOW ---

# Handle OAuth Redirect
query_params = st.query_params
if "code" in query_params:
    try:
        # Simple Exchange Logic
        auth_code = query_params["code"]
        session = supabase.auth.exchange_code_for_session({"auth_code": auth_code})
        st.session_state.user = session.user
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Login Error: {e}")
        if st.button("Try Again"):
            st.query_params.clear()
            st.rerun()

# Show Login or Main App
if st.session_state.user:
    main_app()
else:
    login_page()