import streamlit as st
import google.generativeai as genai
import requests
import json
import base64

# --- තිරයේ මූලික සැකසුම (Page Configuration) ---
st.set_page_config(page_title="SPT Freelancer Automator", layout="wide", page_icon="⚡")

# --- Glassmorphism & High-tech CSS සැකසුම් (UI Styling) ---
# මෙමගින් සම්පූර්ණ අතුරුමුහුණතට වීදුරු සහ නවීන තාක්ෂණික පෙනුමක් ලබා දෙයි.
st.markdown("""
    <style>
    /* පසුබිම් වර්ණය සහ රටාව (Dark High-tech Background) */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #e2e8f0;
    }
    
    /* Glassmorphism Effect - Cards and Containers */
    .glass-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
    }
    
    /* Title Styling (Neon Glow Effect) */
    .title-text {
        font-family: 'Courier New', Courier, monospace;
        color: #38bdf8;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.5), 0 0 20px rgba(56, 189, 248, 0.3);
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
    }
    
    /* Subtitle */
    .subtitle-text {
        color: #94a3b8;
        text-align: center;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }

    /* Input Fields Customization */
    .stTextInput input, .stNumberInput input {
        background-color: rgba(0, 0, 0, 0.3) !important;
        color: #38bdf8 !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    
    /* Buttons Customization (Cyberpunk style) */
    .stButton>button {
        background: linear-gradient(90deg, #0284c7 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
        transition: all 0.3s ease;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.8);
        transform: translateY(-2px);
    }
    
    /* Expanders Customization */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        color: #38bdf8 !important;
    }
    </style>
""", unsafe_allow_html=True)


# --- සැසි මතකය (Session State) සකස් කිරීම ---
if "projects" not in st.session_state:
    st.session_state.projects = []
if "selected_project" not in st.session_state:
    st.session_state.selected_project = None
if "ai_proposal" not in st.session_state:
    st.session_state.ai_proposal = ""
if "sinhala_translation" not in st.session_state:
    st.session_state.sinhala_translation = ""


# --- පැති පාලක පුවරුව (Sidebar) ---
with st.sidebar:
    # Profile Picture Upload
    st.markdown("<h3 style='text-align: center; color: #38bdf8;'>👤 Profile</h3>", unsafe_allow_html=True)
    uploaded_image = st.file_uploader("ඔබගේ ඡායාරූපය යොදන්න (Upload Pic)", type=["png", "jpg", "jpeg"])
    
    if uploaded_image is not None:
        st.image(uploaded_image, width=150, use_column_width=False, caption="SPT Profile")
    else:
        st.info("ඡායාරූපයක් එක් කර නැත.")
        
    st.markdown("---")
    
    # API Settings in Glassmorphism look
    st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #cbd5e1;'>⚙️ API Settings</h4>", unsafe_allow_html=True)
    gemini_key = st.text_input("Gemini API Key", type="password")
    freelancer_token = st.text_input("Freelancer Token", type="password")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #cbd5e1;'>🎯 Target Skills</h4>", unsafe_allow_html=True)
    query_skill = st.text_input("සෙවිය යුතු අංශය (උදා: Video Editing)", "Video Editing")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("🔄 පද්ධතිය යාවත්කාලීන කරන්න"):
        if gemini_key and freelancer_token:
            st.success("API සැකසුම් සුරකින ලදී!")
        else:
            st.warning("API කේත දෙකම ඇතුළත් කරන්න.")


# --- ප්‍රධාන තිරය (Main Dashboard Header) ---
st.markdown("<h1 class='title-text'>⚡ SPT FREELANCER AUTOMATOR</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle-text'>Next-Gen AI Bidding & Intelligence System</p>", unsafe_allow_html=True)


# --- ශ්‍රිත (Functions) ---
def fetch_active_projects(token, query):
    url = f"https://www.freelancer.com/api/projects/0.1/projects/active/?query={query}&full_description=true"
    headers = {"freelancer-oauth-v1": token}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('result', {}).get('projects', [])
        else:
            st.error("ව්‍යාපෘති ලබා ගැනීමේදී දෝෂයක් මතු විය.")
            return []
    except Exception as e:
        st.error(f"ජාල දෝෂයකි: {e}")
        return []

def generate_ai_content(project_desc, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    You are an expert freelancer in Video Editing, AI Automation, and Music Production. 
    Write a highly professional proposal (cover letter) for the following project description.
    Also, provide the exact Sinhala translation of the project description and your proposal.
    Format EXACTLY in this JSON structure:
    {{
        "english_proposal": "Your proposal...",
        "sinhala_meaning": "සිංහල පරිවර්තනය..."
    }}
    Project Description: {project_desc}
    """
    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(cleaned_response)
        return result["english_proposal"], result["sinhala_meaning"]
    except Exception as e:
        st.error(f"AI දෝෂයකි: {e}")
        return "", ""


# --- ව්‍යාපෘති සෙවීම (Search Section) ---
st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
col_search1, col_search2, col_search3 = st.columns([1, 2, 1])
with col_search2:
    if st.button("📡 SCAN FOR LIVE PROJECTS"):
        if not freelancer_token:
            st.warning("කරුණාකර Sidebar එකේ Freelancer Token එක ලබා දෙන්න.")
        else:
            with st.spinner('Scanning Freelancer Database...'):
                projects = fetch_active_projects(freelancer_token, query_skill)
                if projects:
                    st.session_state.projects = projects[:5]
                    st.success(f"ව්‍යාපෘති {len(st.session_state.projects)} ක් සොයාගන්නා ලදී!")
st.markdown("</div>", unsafe_allow_html=True)


# --- ව්‍යාපෘති ලැයිස්තුව (Project List) ---
if st.session_state.projects:
    st.markdown("### 📋 සොයාගත් ව්‍යාපෘති")
    for proj in st.session_state.projects:
        with st.expander(f"📌 {proj.get('title', 'Unknown')} - [ID: {proj.get('id', 'N/A')}]"):
            st.write(proj.get('description', 'විස්තරයක් නොමැත.'))
            if st.button(f"⚡ Generate AI Proposal", key=f"btn_{proj.get('id')}"):
                if not gemini_key:
                    st.warning("කරුණාකර Gemini API Key එක ලබා දෙන්න.")
                else:
                    st.session_state.selected_project = proj
                    with st.spinner('Processing AI Intelligence...'):
                        eng_prop, sin_mean = generate_ai_content(proj.get('description', ''), gemini_key)
                        st.session_state.ai_proposal = eng_prop
                        st.session_state.sinhala_translation = sin_mean


# --- ද්විභාෂා පුවරුව (Bilingual Workspace) ---
if st.session_state.selected_project and st.session_state.ai_proposal:
    st.markdown("---")
    st.markdown("<h3 style='color: #38bdf8;'>🎯 AI Intelligence Workspace</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
        st.info("🇬🇧 ඉංග්‍රීසි අංශය (Final Output)")
        edited_proposal = st.text_area("අවශ්‍ය වෙනස්කම් මෙහි සිදු කරන්න:", value=st.session_state.ai_proposal, height=350)
        
        bid_amount = st.number_input("බිඩ් කරන මුදල ($):", min_value=1)
        delivery_days = st.number_input("වැඩේ නිම කරන දින ගණන:", min_value=1)
        
        if st.button("🚀 SUBMIT BID NOW"):
            st.success("බිඩ් එක සාර්ථකව පද්ධතියට යොමු කිරීමට සූදානම්!")
        st.markdown("</div>", unsafe_allow_html=True)
            
    with col2:
        st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
        st.success("🇱🇰 සිංහල අංශය (Translation)")
        st.markdown("**සිංහල අදහස:**")
        st.write(st.session_state.sinhala_translation)
        st.markdown("</div>", unsafe_allow_html=True)
