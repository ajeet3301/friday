"""
FRIDAY LIVE - Streamlit Cloud
"""
import os
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY", "")

st.set_page_config(page_title="Friday", page_icon="✦", layout="wide")

st.markdown("""
<style>
* { margin:0 !important; padding:0 !important; }
html,body,[class*="css"],section,[data-testid] {
    background:#000 !important;
    overflow:hidden !important;
}
#MainMenu,footer,header,.stDeployButton { display:none !important; }
.block-container { padding:0 !important; max-width:100vw !important; width:100vw !important; }
iframe { width:100vw !important; height:100vh !important; border:none !important; }
</style>
""", unsafe_allow_html=True)

if not GROQ_KEY:
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                min-height:100vh;background:#000;color:#fff;gap:16px;font-family:sans-serif;
                text-align:center;padding:20px;">
      <div style="font-size:3rem;color:#8ab4f8;">✦</div>
      <div style="font-size:1.4rem;font-weight:300;letter-spacing:.1em;">FRIDAY</div>
      <div style="font-size:.9rem;color:#666;max-width:420px;line-height:1.8;">
        Add your Groq API key to Streamlit Secrets:<br><br>
        <code style="background:#111;padding:10px 20px;border-radius:8px;color:#4ade80;display:block;">
          GROQ_API_KEY = "gsk_your_key_here"
        </code><br>
        Settings → Secrets → paste above → Save → Reboot app
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Fix: use path relative to THIS file, not working directory
HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "static", "friday.html"), "r") as f:
    html = f.read()

html = html.replace("__GROQ_KEY__", GROQ_KEY)

st.components.v1.html(html, height=900, scrolling=False)
