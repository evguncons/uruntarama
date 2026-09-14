import os
import json
import base64
from io import BytesIO
from PIL import Image
import streamlit as st
from google import genai
from google.genai import types

# =========================================================================
# SAYFA VE TEMA YAPILANDIRMASI
# =========================================================================
st.set_page_config(
    page_title="Hedef AVM | AI Ürün Piyasa Radarı",
    page_icon="public/hedef-logo.png" if os.path.exists("public/hedef-logo.png") else "🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Logo Base64 Çevirici (HTML içinde responsive ve hatasız render için)
def get_logo_b64():
    if os.path.exists("public/hedef-logo.png"):
        with open("public/hedef-logo.png", "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    return ""

LOGO_B64 = get_logo_b64()

# =========================================================================
# TAM MOBİL VE MASAÜSTÜ RESPONSIVE GELİŞMİŞ CSS (ESAS UI)
# =========================================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"], .stApp {{
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
        background-color: #faf5f8 !important;
        color: #0f172a !important;
    }}

    /* Streamlit varsayılan boşluklarını mobil için optimize et */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1.25rem !important;
        padding-right: 1.25rem !important;
        max-width: 1050px !important;
    }}

    @media (max-width: 768px) {{
        .block-container {{
            padding-left: 0.65rem !important;
            padding-right: 0.65rem !important;
            padding-top: 0.5rem !important;
        }}
    }}

    /* Üst Başlık Kartı */
    .hedef-navbar {{
        background: #ffffff;
        border: 1px solid #fce7f3;
        border-radius: 1.25rem;
        padding: 1rem 1.25rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        box-shadow: 0 4px 20px -2px rgba(200, 19, 115, 0.05);
        margin-bottom: 1.5rem;
    }}

    .hedef-navbar-left {{
        display: flex;
        align-items: center;
        gap: 1rem;
    }}

    .hedef-logo-img {{
        height: 46px;
        width: auto;
        object-fit: contain;
    }}

    @media (max-width: 640px) {{
        .hedef-navbar {{
            flex-direction: column;
            align-items: flex-start;
            padding: 0.85rem;
            gap: 0.5rem;
        }}
        .hedef-logo-img {{
            height: 38px;
        }}
    }}

    /* Rozetler */
    .hedef-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: #fdf2f8;
        color: #c81373;
        border: 1px solid #fbcfe8;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 800;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    .badge-verdict {{
        display: inline-block;
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-weight: 900;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}

    /* Beyaz Kurumsal Kart */
    .hedef-card {{
        background: #ffffff;
        border: 1px solid #fce7f3;
        border-radius: 1.25rem;
        padding: 1.5rem;
        box-shadow: 0 8px 25px -4px rgba(200, 19, 115, 0.05);
        margin-bottom: 1.25rem;
    }}

    @media (max-width: 640px) {{
        .hedef-card {{
            padding: 1rem !important;
            border-radius: 1rem !important;
        }}
    }}

    /* Fiyat Dağılım Grid */
    .hedef-price-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.65rem;
        margin-bottom: 1rem;
    }}

    @media (max-width: 480px) {{
        .hedef-price-grid {{
            grid-template-columns: 1fr;
        }}
    }}

    .hedef-price-item {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 1rem;
        padding: 0.85rem 0.5rem;
        text-align: center;
    }}

    .hedef-price-highlight {{
        background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%);
        border: 2px solid #f472b6;
        border-radius: 1rem;
        padding: 0.85rem 0.5rem;
        text-align: center;
        box-shadow: 0 4px 15px -2px rgba(200, 19, 115, 0.12);
    }}

    /* Elden Senetli Satış Kartı */
    .hedef-senet-banner {{
        background: linear-gradient(135deg, #c81373 0%, #e11d48 50%, #db2777 100%);
        color: #ffffff !important;
        border-radius: 1.25rem;
        padding: 1.25rem;
        box-shadow: 0 12px 30px -5px rgba(200, 19, 115, 0.35);
        margin-bottom: 0.85rem;
    }}

    /* Butonlar (Dokunmatik ekran için büyük ve canlı) */
    .stButton>button {{
        background: linear-gradient(to right, #c81373, #e11d48, #db2777) !important;
        color: white !important;
        font-weight: 900 !important;
        font-size: 1.05rem !important;
        border-radius: 1rem !important;
        border: none !important;
        padding: 0.9rem 2rem !important;
        box-shadow: 0 10px 25px -4px rgba(200, 19, 115, 0.4) !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 15px 30px -4px rgba(200, 19, 115, 0.5) !important;
    }}

    /* Girdi Kutuları */
    .stTextInput input {{
        border-radius: 1rem !important;
        border: 2px solid #fbcfe8 !important;
        padding: 0.75rem 1rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        background: #ffffff !important;
    }}
    .stTextInput input:focus {{
        border-color: #c81373 !important;
        box-shadow: 0 0 0 4px rgba(200, 19, 115, 0.15) !important;
    }}

    /* Tab Görünümü */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background-color: #fce7f3/40;
        padding: 0.35rem;
        border-radius: 0.85rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 0.75rem;
        font-weight: 800;
        font-size: 0.85rem;
        padding: 0.5rem 1rem;
        color: #64748b;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #ffffff !important;
        color: #c81373 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
</style>
""", unsafe_allow_html=True)

# =========================================================================
# 🔒 GÜVENLİK: API ANAHTARINI GİZLE VE KORU
# =========================================================================
def get_secure_api_key():
    # 1. Streamlit Secrets (share.streamlit.io için güvenli kasa)
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            k = st.secrets["GEMINI_API_KEY"].strip()
            if len(k) > 10:
                return k
    except Exception:
        pass

    # 2. Sunucu Ortam Değişkeni
    if os.environ.get("GEMINI_API_KEY"):
        k = os.environ.get("GEMINI_API_KEY").strip()
        if len(k) > 10:
            return k

    # 3. Yerel .env.local dosyası
    if os.path.exists(".env.local"):
        try:
            with open(".env.local", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        val = line.strip().split("=", 1)[1].strip("\"' ")
                        if len(val) > 10:
                            return val
        except Exception:
            pass

    return None

ACTIVE_API_KEY = get_secure_api_key()

# Sidebar: Sadece Güvenlik Durumu Bildirilir (Anahtar Asla Ekrana Basılmaz)
with st.sidebar:
    st.markdown("### 🛡️ Kurumsal Güvenlik")
    if ACTIVE_API_KEY:
        st.markdown("""
        <div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 0.85rem; border-radius: 0.85rem;">
            <span style="color: #065f46; font-weight: 800; font-size: 0.8rem;">🔒 GEMINI API AKTİF</span>
            <p style="color: #047857; font-size: 0.72rem; margin-top: 0.25rem; margin-bottom: 0;">
                API anahtarı sunucuda şifreli tutulmaktadır. Ziyaretçiler anahtarı görüntüleyemez veya çalamaz.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("⚠️ GEMINI_API_KEY Streamlit Secrets alanına eklenmelidir.")

    st.markdown("---")
    st.markdown("#### 🏢 Hedef AVM")
    st.caption("Hedef Alışveriş Merkezleri - Evinizin Rengi. Züccaciye, küçük ev aletleri, beyaz eşya ve tüketici elektroniğinde elden senetli ve peşin satış istihbarat motoru.")

# =========================================================================
# 2 AŞAMALI CANLI GOOGLE SEARCH GROUNDING MOTORU
# =========================================================================
def analyze_product_2stage(product_name: str, pil_image: Image.Image, user_cost: float = None, extra_notes: str = None):
    if not ACTIVE_API_KEY:
        raise ValueError("Sistemde geçerli bir GEMINI_API_KEY bulunamadı. Lütfen Streamlit Secrets alanını kontrol ediniz.")

    client = genai.Client(api_key=ACTIVE_API_KEY)

    # 1. AŞAMA: Canlı Google Search ile Gerçek Piyasa Fiyatları
    search_prompt = f"""Sen Türkiye perakende pazarında uzman bir fiyat araştırmacısısın.
Kullanıcı şu ürünü analiz ediyor: "{product_name}".

GÖREVİN:
Google Arama aracını kullanarak Türkiye'deki Akakçe, Cimri, Trendyol, Hepsiburada, Amazon Türkiye ve Teknosa/MediaMarkt sitelerindeki ŞU ANKİ EN GÜNCEL satış fiyatlarını araştır:
1. En ucuz fiyat (TL) ve satıldığı platform
2. Ortalama piyasa fiyatı (TL)
3. En yüksek liste fiyatı (TL)
4. Trendyol ve Hepsiburada güncel satıcı fiyatları ve stok durumu

Lütfen gerçek ve güncel TL rakamlarını net olarak listele."""

    search_response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=search_prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            temperature=0.1
        )
    )
    live_findings = search_response.text or "Canlı pazar araştırması tamamlandı."

    # 2. AŞAMA: Görsel İnceleme + Gerçek Verilerle Hedef AVM Senetli Satış Raporu (JSON)
    system_instruction = f"""Sen Türkiye perakende pazarında uzmanlaşmış, "Hedef AVM" için çalışan kıdemli bir Satın Alma Direktörü ve Fiyatlandırma Stratejistisin.
Hedef AVM; züccaciye, küçük ev aletleri, beyaz eşya, tüketici elektroniği ve mobilya alanında hem peşin hem de Türkiye'ye özgü "elden senetli / taksitli" satış modeliyle çalışan güçlü bir mağazalar zinciridir.

Kullanıcı ürünün tam adını ve modelini belirtmiştir: "{product_name}".
Ayrıca ürünün fotoğrafı eklenmiştir.

Aşağıda canlı internet aramasından toplanan en güncel piyasa araştırması verileri yer almaktadır:
--- CANLI PİYASA İSTİHBARATI ---
{live_findings}
-------------------------------

GÖREVİN:
Yukarıdaki GERÇEK internet pazar verilerini ve yüklenen fotoğrafı harmanlayarak Hedef AVM için doğrulanmış bir piyasa fizibilite raporu hazırla.

Fiyatlandırma Kuralları:
1. Pazar fiyatları (min, average, max) yukarıdaki canlı arama sonuçlarındaki gerçek TL rakamlarına dayanmalıdır.
2. Hedef AVM Peşin Satış Fiyatı: Pazaryerleriyle rekabet edebilecek akılcı bir liste fiyatı olmalıdır.
3. Hedef AVM Elden Senetli Satış Fiyatı: Elden senetli satışta risk ve vade farkı nedeniyle peşine göre ortalama %20-%35 daha yüksek vadeli toplam fiyat belirlenir. 12 taksite bölünerek aylık taksit tutarı net hesaplanır.
4. "Bu Ürün Satar mı / Satmaz mı?" Karar Motoru: 0-100 arasında net satılabilirlik puanı, somut gerekçeler, pazar riskleri ve mağaza vitrini için vurucu afiş sloganları üret.

Cevabını SADECE geçerli bir JSON nesnesi olarak döndür."""

    json_schema_prompt = f"""Aşağıdaki JSON şemasına BİREBİR uygun yanıt ver:
{{
  "productName": "{product_name}",
  "brand": "Marka",
  "modelOrCode": "Model kodu",
  "barcode": "Varsa barkod veya null",
  "category": "Kategori",
  "keyFeatures": ["Özellik 1", "Özellik 2", "Özellik 3"],
  "marketPrices": {{
    "min": 0,
    "average": 0,
    "max": 0,
    "currency": "₺"
  }},
  "competitorBenchmarks": [
    {{"platform": "Trendyol", "estimatedPrice": 0, "currency": "₺", "notes": "Satıcı ve stok durumu"}},
    {{"platform": "Hepsiburada", "estimatedPrice": 0, "currency": "₺", "notes": "Fiyat durumu"}},
    {{"platform": "Zincir Perakende (Teknosa/MediaMarkt)", "estimatedPrice": 0, "currency": "₺", "notes": "Mağaza liste fiyatı"}}
  ],
  "hedefPricing": {{
    "cashRecommendedPrice": 0,
    "installmentRecommendedPrice": 0,
    "monthlyInstallmentPrice": 0,
    "installmentCount": 12,
    "suggestedDownPayment": 0,
    "strategyNote": "Peşin ve taksitli satış stratejisi notu."
  }},
  "feasibility": {{
    "score": 85,
    "verdict": "GÜÇLÜ SATAR",
    "headline": "Kısa ve net karar başlığı",
    "reasonsToSell": ["Gerekçe 1", "Gerekçe 2"],
    "risksAndWatchouts": ["Risk 1", "Risk 2"],
    "demandLevel": "Çok Yüksek",
    "competitionLevel": "Yüksek",
    "targetAudience": "Hedef kitle profili",
    "returnRisk": "Düşük",
    "seasonalTrend": "Mevsimsellik"
  }},
  "campaigns": [
    {{
      "title": "Kampanya Başlığı",
      "campaignType": "Çeyiz Paketi",
      "description": "Kampanya açıklaması",
      "bannerSlogan": "Mağaza içi afiş sloganı"
    }}
  ]
}}

{f'Kullanıcının Tedarik Alış Maliyeti: {user_cost} ₺.' if user_cost else ''}
{f'Ek Not: {extra_notes}' if extra_notes else ''}"""

    img_byte_arr = BytesIO()
    pil_image.save(img_byte_arr, format='JPEG', quality=85)
    img_bytes = img_byte_arr.getvalue()

    struct_response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            system_instruction,
            types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'),
            json_schema_prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
            temperature=0.1
        )
    )

    return json.loads(struct_response.text)

# =========================================================================
# ÜST BAŞLIK (HEADER) - TAM MOBİL VE MASAÜSTÜ UYUMLU
# =========================================================================
st.markdown(f"""
<div class="hedef-navbar">
    <div class="hedef-navbar-left">
        <img src="{LOGO_B64}" class="hedef-logo-img" alt="Hedef AVM" />
        <div style="border-left: 2px solid #fce7f3; padding-left: 0.75rem;">
            <span class="hedef-pill">AI PİYASA RADARI</span>
            <div style="color: #0f172a; font-weight: 900; font-size: 1.1rem; line-height: 1.2; margin-top: 0.15rem;">
                HEDEF AVM PİYASA İSTİHBARATI
            </div>
            <div style="color: #c81373; font-size: 0.75rem; font-weight: 700;">
                Evinizin Rengi • Google Gemini 2.5 Canlı Satılabilirlik Motoru
            </div>
        </div>
    </div>
    <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span style="background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; padding: 0.35rem 0.75rem; border-radius: 9999px; font-weight: 800; font-size: 0.72rem;">
            ● Gemini 2.5 Aktif
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================================
# GİRİŞ KARTI (FORM)
# =========================================================================
with st.container():
    st.markdown("""
    <div class="hedef-card">
        <div style="text-align: center; max-width: 600px; margin: 0 auto 1.25rem auto;">
            <span class="hedef-pill">⚡ ANLIK PAZAR İSTİHBARATI</span>
            <h2 style="font-weight: 900; color: #0f172a; margin-top: 0.4rem; font-size: 1.6rem; letter-spacing: -0.02em;">
                Ürün Bilgisini ve Fotoğrafını Ekleyin
            </h2>
            <p style="color: #64748b; font-size: 0.85rem; font-weight: 500; margin-bottom: 0;">
                Model karışıklığını önlemek ve Trendyol, Hepsiburada ve Akakçe fiyatlarını <strong>canlı ve hatasız</strong> çekmek için ürün adını belirtiniz.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # ZORUNLU ÜRÜN ADI GİRİŞİ
    product_name_input = st.text_input(
        "📦 Ürün Adı ve Modeli * (Zorunlu)",
        placeholder="Örn: gm 26 pro, iPhone 15 128GB, Philips HD9650 Airfryer, Karaca Çay Makinesi...",
        help="Model adını tam yazmak fiyatları canlı aramayla %100 doğrular."
    )

    # Görsel Girişi
    tab_cam, tab_file = st.tabs(["📸 Kamerayla Çek", "📁 Galeriden / Dosyadan Yükle"])
    uploaded_image = None

    with tab_cam:
        cam_file = st.camera_input("Ürünün veya ambalajının fotoğrafını çekin")
        if cam_file:
            uploaded_image = Image.open(cam_file)

    with tab_file:
        up_file = st.file_uploader("Ürün görseli seçin (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"])
        if up_file:
            uploaded_image = Image.open(up_file)

    # Ek Maliyet ve Not Alanları
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        cost_val = st.number_input("Tedarikçi Alış Fiyatı (₺ - Kârlılık hesabı için opsiyonel)", min_value=0.0, step=50.0, value=0.0)
    with col_c2:
        notes_input = st.text_input("Ekstra Not / Durum (Opsiyonel)", placeholder="Örn: Sıfır kutulu, 2 yıl Türkiye garantili")

    start_btn = st.button("🚀 Canlı Piyasa Analizini Başlat", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# ANALİZ YÜRÜTME & GELİŞMİŞ MOBİL UYUMLU SONUÇ DASHBOARD'U
# =========================================================================
if start_btn:
    if not product_name_input.strip():
        st.error("⚠️ Model karışıklığını önlemek için lütfen Ürün Adı ve Modelini giriniz (Örn: gm 26 pro, iPhone 15 128GB)!")
    elif uploaded_image is None:
        st.error("⚠️ Lütfen analiz edilecek ürünün fotoğrafını çekin veya galeriden seçin!")
    elif not ACTIVE_API_KEY:
        st.error("⚠️ Sistemde geçerli bir GEMINI_API_KEY bulunamadı. Lütfen Streamlit Secrets alanını kontrol edin.")
    else:
        with st.status("🔍 Canlı Piyasa Taraması ve Analiz Başlatılıyor...", expanded=True) as status:
            st.write("1. Aşama: Google üzerinden Akakçe, Trendyol ve Hepsiburada güncel fiyatları canlı taranıyor...")
            try:
                data = analyze_product_2stage(
                    product_name=product_name_input.strip(),
                    pil_image=uploaded_image,
                    user_cost=cost_val if cost_val > 0 else None,
                    extra_notes=notes_input.strip() if notes_input else None
                )
                st.write("2. Aşama: Görsel incelendi ve Hedef AVM taksit planı oluşturuldu!")
                status.update(label="✅ Analiz Başarıyla Tamamlandı!", state="complete", expanded=False)
                st.session_state["last_analysis"] = data
                st.session_state["last_image"] = uploaded_image
            except Exception as e:
                status.update(label="❌ Analiz Sırasında Hata Oluştu", state="error")
                st.error(f"Hata detayı: {str(e)}")

# Sonuç Ekranı
if "last_analysis" in st.session_state and st.session_state["last_analysis"]:
    res = st.session_state["last_analysis"]
    feasibility = res.get("feasibility", {})
    score = feasibility.get("score", 50)
    verdict = feasibility.get("verdict", "SATAR")

    # Ürün Başlık & Skor Kartı
    st.markdown(f"""
    <div class="hedef-card" style="border-top: 6px solid #c81373;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
            <div style="flex: 1; min-width: 250px;">
                <span class="hedef-pill">FİZİBİLİTE RAPORU</span>
                <h2 style="color: #0f172a; font-weight: 900; font-size: 1.6rem; margin-top: 0.35rem; margin-bottom: 0.25rem;">
                    {res.get('productName')}
                </h2>
                <div style="color: #64748b; font-size: 0.85rem; font-weight: 600;">
                    Marka: <strong style="color: #0f172a;">{res.get('brand')}</strong> • Kategori: <strong style="color: #0f172a;">{res.get('category')}</strong> {f'• Model: {res.get("modelOrCode")}' if res.get("modelOrCode") else ''}
                </div>
            </div>
            <div style="text-align: right; background: #faf5f8; padding: 0.75rem 1.25rem; border-radius: 1rem; border: 1px solid #fce7f3;">
                <span class="badge-verdict">{verdict}</span>
                <div style="font-size: 2.2rem; font-weight: 900; color: #c81373; line-height: 1;">
                    {score} <span style="font-size: 0.85rem; color: #64748b; font-weight: 700;">/ 100 PUAN</span>
                </div>
            </div>
        </div>
        <div style="margin-top: 1rem; padding: 0.85rem 1rem; background: #faf5f8; border-radius: 0.85rem; border: 1px solid #fce7f3;">
            <strong style="color: #c81373;">💡 Yönetici Özeti:</strong> <span style="color: #334155; font-weight: 600; font-size: 0.9rem;">{feasibility.get('headline')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Bölüm: Piyasa Fiyatları vs Hedef AVM Senetli Taksit Stratejisi
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        mp = res.get("marketPrices", {})
        st.markdown(f"""
        <div class="hedef-card">
            <h3 style="font-weight: 900; color: #0f172a; font-size: 1.15rem; margin-bottom: 0.25rem;">
                🏪 Türkiye Canlı Piyasa Fiyat Skalası
            </h3>
            <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 1rem;">
                Akakçe, Trendyol, Hepsiburada ve perakende mağaza ortalamaları
            </p>
            
            <div class="hedef-price-grid">
                <div class="hedef-price-item">
                    <span style="font-size: 0.68rem; font-weight: 800; color: #64748b; text-transform: uppercase;">En Düşük</span>
                    <div style="font-size: 1.2rem; font-weight: 900; color: #0f172a;">{mp.get('min', 0):,} ₺</div>
                </div>
                <div class="hedef-price-highlight">
                    <span style="font-size: 0.68rem; font-weight: 900; color: #c81373; text-transform: uppercase;">Piyasa Ortalaması</span>
                    <div style="font-size: 1.3rem; font-weight: 900; color: #c81373;">{mp.get('average', 0):,} ₺</div>
                </div>
                <div class="hedef-price-item">
                    <span style="font-size: 0.68rem; font-weight: 800; color: #64748b; text-transform: uppercase;">En Yüksek</span>
                    <div style="font-size: 1.2rem; font-weight: 900; color: #0f172a;">{mp.get('max', 0):,} ₺</div>
                </div>
            </div>

            <div style="margin-top: 1rem;"><strong style="font-size: 0.78rem; color: #64748b; text-transform: uppercase;">Pazaryeri Örnekleri:</strong></div>
        """.replace(",", "."), unsafe_allow_html=True)

        for comp in res.get("competitorBenchmarks", []):
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.65rem 0.85rem; background: #faf5f8; border-radius: 0.75rem; margin-top: 0.35rem; border: 1px solid #fce7f3; font-size: 0.82rem;">
                <div>
                    <strong style="color: #0f172a;">{comp.get('platform')}</strong>
                    <div style="color: #64748b; font-size: 0.72rem;">{comp.get('notes', '')}</div>
                </div>
                <div style="font-weight: 900; color: #0f172a; font-size: 0.95rem;">
                    {comp.get('estimatedPrice', 0):,} ₺
                </div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_m2:
        hp = res.get("hedefPricing", {})
        st.markdown(f"""
        <div class="hedef-card" style="border: 2px solid #fbcfe8;">
            <h3 style="font-weight: 900; color: #0f172a; font-size: 1.15rem; margin-bottom: 0.25rem;">
                🎯 Hedef AVM Fiyat & Senet Kurgusu
            </h3>
            <p style="color: #c81373; font-size: 0.8rem; font-weight: 700; margin-bottom: 1rem;">
                Peşin ve 12 ay elden senetli taksit kurgusu
            </p>

            <div class="hedef-senet-banner">
                <span style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; color: #fce7f3;">Elden Senetli Toplam Satış</span>
                <div style="font-size: 1.8rem; font-weight: 900; line-height: 1.1; margin-top: 0.25rem;">
                    {hp.get('installmentRecommendedPrice', 0):,} ₺
                </div>
                <div style="font-size: 0.9rem; font-weight: 800; color: #fdf2f8; margin-top: 0.35rem;">
                    {hp.get('monthlyInstallmentPrice', 0):,} ₺ x {hp.get('installmentCount', 12)} Ay Taksit
                </div>
            </div>

            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 1rem; padding: 0.85rem; margin-bottom: 0.75rem;">
                <span style="font-size: 0.7rem; font-weight: 800; color: #64748b; text-transform: uppercase;">Peşin / Kredi Kartı Fiyatı</span>
                <div style="font-size: 1.35rem; font-weight: 900; color: #0f172a; margin-top: 0.15rem;">
                    {hp.get('cashRecommendedPrice', 0):,} ₺
                </div>
                <span style="font-size: 0.72rem; color: #94a3b8;">Online pazaryerleriyle rekabetçi mağaza peşin liste fiyatı</span>
            </div>

            <div style="background: #fdf2f8; border-radius: 0.85rem; padding: 0.75rem; border: 1px solid #fce7f3; font-size: 0.8rem; color: #831843;">
                <strong>📌 Satın Alma Tavsiyesi:</strong> {hp.get('strategyNote', '')}
            </div>
        </div>
        """.replace(",", "."), unsafe_allow_html=True)

    # 2. Bölüm: Neden Satar? vs Riskler
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("""
        <div class="hedef-card" style="border-left: 6px solid #10b981;">
            <h4 style="font-weight: 900; color: #065f46; font-size: 1.05rem; margin-bottom: 0.5rem;">✅ Neden Satar? (Fırsatlar)</h4>
        """, unsafe_allow_html=True)
        for reason in feasibility.get("reasonsToSell", []):
            st.markdown(f"""
            <div style="padding: 0.5rem 0.75rem; background: #ecfdf5; border-radius: 0.65rem; margin-top: 0.35rem; font-size: 0.82rem; color: #064e3b; font-weight: 600;">
                ✓ {reason}
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r2:
        st.markdown("""
        <div class="hedef-card" style="border-left: 6px solid #f59e0b;">
            <h4 style="font-weight: 900; color: #92400e; font-size: 1.05rem; margin-bottom: 0.5rem;">⚠️ Riskler ve Dikkat Edilmesi Gerekenler</h4>
        """, unsafe_allow_html=True)
        for risk in feasibility.get("risksAndWatchouts", []):
            st.markdown(f"""
            <div style="padding: 0.5rem 0.75rem; background: #fffbeb; border-radius: 0.65rem; margin-top: 0.35rem; font-size: 0.82rem; color: #78350f; font-weight: 600;">
                ! {risk}
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. Bölüm: Kampanya ve Vitrin Sloganları
    st.markdown("""
    <div class="hedef-card">
        <h4 style="font-weight: 900; color: #0f172a; font-size: 1.05rem; margin-bottom: 0.75rem;">📣 Hedef AVM Mağaza İçi Kampanya Kurguları</h4>
    """, unsafe_allow_html=True)

    for camp in res.get("campaigns", []):
        st.markdown(f"""
        <div style="background: #faf5f8; border: 1px solid #fce7f3; border-radius: 0.85rem; padding: 0.85rem; margin-bottom: 0.65rem;">
            <span class="hedef-pill">{camp.get('campaignType')}</span>
            <div style="font-weight: 900; color: #0f172a; font-size: 0.95rem; margin-top: 0.35rem; margin-bottom: 0.2rem;">{camp.get('title')}</div>
            <p style="font-size: 0.8rem; color: #475569; margin-bottom: 0.5rem;">{camp.get('description')}</p>
            <div style="background: #ffffff; border: 1px solid #fbcfe8; padding: 0.5rem 0.75rem; border-radius: 0.65rem; font-size: 0.8rem; color: #c81373; font-weight: 800; font-style: italic;">
                "{camp.get('bannerSlogan')}"
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # İndirme Butonu
    st.download_button(
        label="📥 Raporu JSON Olarak İndir",
        data=json.dumps(res, ensure_ascii=False, indent=2),
        file_name=f"Hedef_AVM_Rapor_{res.get('brand', 'Urun')}.json",
        mime="application/json"
    )

# Alt Bilgi (Footer)
st.markdown("""
<div style="text-align: center; padding: 2rem 0; color: #94a3b8; font-size: 0.75rem; border-top: 1px solid #fce7f3; margin-top: 2rem;">
    <strong>HEDEF ALIPVERİŞ MERKEZLERİ</strong> • Özel Ürün Piyasa Araştırması AI Yazılımı<br>
    Google Gemini 2.5 Vision & Canlı Arama İstihbarat Motoru ile güçlendirilmiştir.
</div>
""", unsafe_allow_html=True)
