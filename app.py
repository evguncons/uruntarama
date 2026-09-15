import streamlit as st
import streamlit.components.v1 as components
import os
import shutil
import tempfile
from services.analysis_service import analyze_product

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
def get_active_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except FileNotFoundError:
        pass
    return os.environ.get("GEMINI_API_KEY", "")

# -----------------------------------------------------------------------------
# HTML Dosyasını Okuma ve Gösterme
# -----------------------------------------------------------------------------
html_file_path = os.path.join(os.path.dirname(__file__), 'index.html')

if os.path.exists(html_file_path):
    @st.cache_resource
    def component_path():
        folder = tempfile.mkdtemp(prefix='uruntarama-ui-')
        shutil.copy2(html_file_path, os.path.join(folder, 'index.html'))
        return folder

    radar = components.declare_component('verified_product_radar', path=component_path())
    action = radar(analysis=st.session_state.get('analysis'), error=st.session_state.get('analysis_error'), key='radar', default=None)
    if action and action.get('requestId') != st.session_state.get('request_id'):
        st.session_state.request_id = action['requestId']
        st.session_state.analysis_error = None
        try:
            st.session_state.analysis = analyze_product(
                action.get('productName', ''), get_active_api_key(),
                action.get('userCost', 0), action.get('notes', ''), action.get('image'))
            st.rerun()
        except Exception as exc:
            st.session_state.analysis_error = f"Analiz tamamlanamadı: {exc}"
            st.rerun()
else:
    st.error("index.html bulunamadı! Lütfen dosyanın streamlit_app.py ile aynı klasörde olduğundan emin olun.")
