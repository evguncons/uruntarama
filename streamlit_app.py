import streamlit as st
import streamlit.components.v1 as components
import os
import base64

# -----------------------------------------------------------------------------
# Sayfa Konfigürasyonu
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Hedef AVM | AI Ürün Piyasa ve Senet Radarı",
    page_icon="public/hedef-logo.png" if os.path.exists("public/hedef-logo.png") else "🎯",
    layout="wide"
)

# -----------------------------------------------------------------------------
# Tam Ekran ve Header/Footer Gizleme CSS (Kayıklığı Önleyen %100 Uyum)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
        /* Streamlit Header, Footer ve Menüyü gizle */
        header {visibility: hidden; display: none !important;}
        footer {visibility: hidden; display: none !important;}
        #MainMenu {visibility: hidden; display: none !important;}
        .stDeployButton {display: none !important;}

        /* Ana sayfanın (Streamlit container'ı) taşmasını sıfırla */
        html, body, [data-testid="stAppViewContainer"], .main, section.main, .block-container {
            overflow: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
            width: 100% !important;
            height: 100% !important;
            max-width: 100% !important;
            max-height: 100% !important;
        }

        /* iframe ekranın tamamını kaplar; kaydırma iframe içerisinde pürüzsüz çalışır */
        iframe {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            max-width: 100vw !important;
            max-height: 100vh !important;
            border: none !important;
            z-index: 999999 !important;
            display: block !important;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Aktif Gemini API Anahtarını Çözme
# -----------------------------------------------------------------------------
_KB64 = "QVEuQWI4Uk42TE5UTExKeHdadnFHbWZ0M0Fqa0JfQ1VPZ280UVl2a1pTUV9ybmppekZOdlE="

def get_active_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets and not st.secrets["GEMINI_API_KEY"].endswith("MgrTA"):
            return st.secrets["GEMINI_API_KEY"]
    except FileNotFoundError:
        pass
    if os.environ.get("GEMINI_API_KEY") and not os.environ.get("GEMINI_API_KEY").endswith("MgrTA"):
        return os.environ.get("GEMINI_API_KEY")
    return base64.b64decode(_KB64).decode("utf-8")

# -----------------------------------------------------------------------------
# HTML Dosyasını Okuma ve Gösterme
# -----------------------------------------------------------------------------
html_file_path = os.path.join(os.path.dirname(__file__), 'index.html')

if os.path.exists(html_file_path):
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_code = f.read()

        api_key = get_active_api_key()
        html_code = html_code.replace("__GEMINI_API_KEY__", api_key)

        from radar_component import render_radar
        render_radar(html_code)

    except Exception as e:
        st.error(f"Hata: {e}")
else:
    st.error("index.html bulunamadı! Lütfen dosyanın streamlit_app.py ile aynı klasörde olduğundan emin olun.")
