import streamlit as st
import google.generativeai as genai
import requests
import json

# --- Page Config ---
st.set_page_config(page_title="SPT Freelancer Automator", layout="wide")

# --- Glassmorphism UI & Custom CSS ---
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: white;
    }
    .glass-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        margin-bottom: 20px;
    }
    .login-box {
        max-width: 400px;
        margin: auto;
        margin-top: 100px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Login System ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<div class='login-box glass-container'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>🔒 පද්ධතියට ඇතුළු වන්න</h2>", unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("පරිශීලක නාමය (Username)")
        password = st.text_input("මුරපදය (Password)", type="password")
        submit_btn = st.form_submit_button("ඇතුළු වන්න (Login)")
        
        if submit_btn:
            try:
                secret_user = st.secrets["credentials"]["username"]
                secret_pwd = st.secrets["credentials"]["password"]
                if username == secret_user and password == secret_pwd:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("❌ Username හෝ Password වැරදියි!")
            except Exception as e:
                st.error("Secrets හඳුනාගැනීමේ දෝෂයකි. Streamlit Settings පරීක්ෂා කරන්න.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- Load API Keys Safely ---
gemini_key = st.secrets["api_keys"]["gemini_api_key"]
freelancer_token = st.secrets["api_keys"]["freelancer_token"]

# --- Helper Function: AI Processing ---
def ask_ai(prompt):
    genai.configure(api_key=gemini_key)
    available_model = None
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_model = m.name
                break
    except Exception as e:
        return f'{{"english": "API Error", "sinhala": "{e}"}}'
        
    if not available_model:
        return '{"english": "Error", "sinhala": "Model not found."}'

    model = genai.GenerativeModel(available_model)
    try:
        response = model.generate_content(prompt)
        return response.text.replace('```json', '').replace('```', '').strip()
    except Exception as e:
        return f'{{"english": "Generation Error", "sinhala": "{e}"}}'

# --- Main App Interface ---
st.markdown("<h1 style='text-align: center;'>⚡ SPT FREELANCER AUTOMATOR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>Next-Gen AI Bidding & Profile Intelligence System</p>", unsafe_allow_html=True)

# Tabs Navigation
tab1, tab2 = st.tabs(["🔍 ව්‍යාපෘති සෙවීම (Project Finder)", "👤 පැතිකඩ සැකසීම (Profile Builder)"])

# --- TAB 1: Project Finder ---
with tab1:
    st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        query = st.text_input("Target Skills (ඔබගේ කුසලතාවය):", "Video Editing")
    with col_s2:
        st.write("")
        st.write("")
        if st.button("🔄 අලුත් කරන්න (Refresh)"):
            st.session_state.pop("cached_projects", None)
            st.rerun()
    
    if st.button("🚀 SCAN FOR LIVE PROJECTS"):
        url = f"https://www.freelancer.com/api/projects/0.1/projects/active/?query={query}&full_description=true"
        headers = {"freelancer-oauth-v1": freelancer_token}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            st.session_state["cached_projects"] = res.json().get("result", {}).get("projects", [])
        else:
            st.error("❌ ව්‍යාපෘති ලබාගැනීමේ දෝෂයකි!")
    st.markdown("</div>", unsafe_allow_html=True)

    if "cached_projects" in st.session_state:
        for p in st.session_state["cached_projects"][:5]:
            title = p.get('title', 'No Title')
            desc = p.get('description', 'විස්තරයක් නොමැත.')
            pid = p.get('id', '')
            
            with st.expander(f"📌 {title} - [ID: {pid}]"):
                st.write(desc)
                prop_key = f"prop_{pid}"
                
                if st.button("⚡ Generate AI Proposal", key=f"btn_{pid}"):
                    with st.spinner("AI යෝජනාව සකසමින්..."):
                        prompt = f"""
                        You are an expert freelancer. Write a highly professional proposal (cover letter) for this project: {desc}.
                        Format EXACTLY in this JSON structure:
                        {{
                            "english": "Your English proposal...",
                            "sinhala": "සිංහල පරිවර්තනය..."
                        }}
                        """
                        res_text = ask_ai(prompt)
                        try:
                            st.session_state[prop_key] = json.loads(res_text)
                        except:
                            st.error("දත්ත සැකසීමේ දෝෂයකි.")
                
                if prop_key in st.session_state:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.info("🇺🇸 English Proposal")
                        st.write(st.session_state[prop_key].get("english", ""))
                    with c2:
                        st.success("🇱🇰 සිංහල තේරුම")
                        st.write(st.session_state[prop_key].get("sinhala", ""))
                    
                    st.markdown("---")
                    edit_req = st.text_input("🤖 AI සහායකයාට උපදෙස් දෙන්න (Chat to Edit):", key=f"chat_{pid}", placeholder="උදා: මගේ පළපුරුද්ද එකතු කරලා මේක කෙටි කරන්න...")
                    if st.button("යාවත්කාලීන කරන්න (Update)", key=f"upd_{pid}"):
                        with st.spinner("වෙනස්කම් සිදු කරමින්..."):
                            prompt = f"""
                            Current Proposal: {st.session_state[prop_key].get("english", "")}
                            User Request: {edit_req}
                            Update the proposal based on the request. Format EXACTLY in JSON:
                            {{
                                "english": "Updated English proposal...",
                                "sinhala": "Updated සිංහල පරිවර්තනය..."
                            }}
                            """
                            res_text = ask_ai(prompt)
                            try:
                                st.session_state[prop_key] = json.loads(res_text)
                                st.rerun()
                            except:
                                st.error("දෝෂයකි.")

# --- TAB 2: Profile Builder ---
with tab2:
    st.markdown("<div class='glass-container'>", unsafe_allow_html=True)
    st.subheader("👤 ජාත්‍යන්තර මට්ටමේ පැතිකඩක් සකසමු")
    default_skills = "12 years experience in miniature painting services, high-resolution video editing (Premiere Pro), and music production."
    profile_skills = st.text_area("ඔබගේ කුසලතා සහ පළපුරුද්ද මෙහි කෙටියෙන් දක්වන්න:", value=default_skills, height=100)
    
    if st.button("⚡ Generate Pro Profile"):
        with st.spinner("ජාත්‍යන්තර පැතිකඩ සකසමින්..."):
            prompt = f"""
            You are an expert profile copywriter for freelance platforms. Create a highly compelling, professional, and attractive profile description based on these skills: {profile_skills}.
            Format EXACTLY in this JSON structure:
            {{
                "english": "Professional Profile Description...",
                "sinhala": "සිංහල පරිවර්තනය..."
            }}
            """
            res_text = ask_ai(prompt)
            try:
                st.session_state["profile_data"] = json.loads(res_text)
            except:
                st.error("දෝෂයකි.")
                
    if "profile_data" in st.session_state:
        c1, c2 = st.columns(2)
        with c1:
            st.info("🇺🇸 English Profile")
            st.write(st.session_state["profile_data"].get("english", ""))
        with c2:
            st.success("🇱🇰 සිංහල තේරුම")
            st.write(st.session_state["profile_data"].get("sinhala", ""))
            
        st.markdown("---")
        prof_edit_req = st.text_input("🤖 AI සහායකයාට උපදෙස් දෙන්න (Chat to Edit):", key="chat_prof", placeholder="උදා: මේක තවත් ආකර්ෂණීය විදිහට ලියන්න...")
        if st.button("යාවත්කාලීන කරන්න (Update Profile)"):
            with st.spinner("වෙනස්කම් සිදු කරමින්..."):
                prompt = f"""
                Current Profile: {st.session_state["profile_data"].get("english", "")}
                User Request: {prof_edit_req}
                Update the profile. Format EXACTLY in JSON:
                {{
                    "english": "Updated Profile...",
                    "sinhala": "Updated සිංහල පරිවර්තනය..."
                }}
                """
                res_text = ask_ai(prompt)
                try:
                    st.session_state["profile_data"] = json.loads(res_text)
                    st.rerun()
                except:
                    st.error("දෝෂයකි.")
    st.markdown("</div>", unsafe_allow_html=True)
