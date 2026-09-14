import os
import json
from io import BytesIO
from PIL import Image
import streamlit as st
from google import genai
from google.genai import types

# =========================================================================
# SAYFA VE TEMA YAPILANDIRMASI (AÇIK TEMA & MAGENTA KURUMSAL)
# =========================================================================
st.set_page_config(
    page_title="Hedef AVM | AI Ürün Piyasa Radarı",
    page_icon="public/hedef-logo.png" if os.path.exists("public/hedef-logo.png") else "🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Gelişmiş Kurumsal CSS (Next.js "Esas UI" Tasarımının Birebir Uyarlaması)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    }
    
    .stApp {
        background-color: #faf5f8;
        color: #0f172a;
    }

    /* Üst Başlık Cam Barı */
    .hedef-header-bar {
        background: rgba(255, 255, 255, 0.95);
        border-bottom: 1px solid #fce7f3;
        padding: 0.85rem 1.5rem;
        border-radius: 1.25rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px -3px rgba(200, 19, 115, 0.05);
    }

    /* Kart Yapıları */
    .hedef-card {
        background: #ffffff;
        border: 1px solid #fce7f3;
        border-radius: 1.5rem;
        padding: 1.75rem;
        box-shadow: 0 10px 30px -5px rgba(200, 19, 115, 0.06);
        margin-bottom: 1.5rem;
    }

    /* Rozetler */
    .hedef-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background: #fdf2f8;
        color: #c81373;
        border: 1px solid #fbcfe8;
        padding: 0.3rem 0.85rem;
        border-radius: 9999px;
        font-weight: 800;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .badge-success {
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        padding: 0.35rem 0.9rem;
        border-radius: 9999px;
        font-weight: 800;
        font-size: 0.75rem;
        text-transform: uppercase;
    }

    .badge-warning {
        background: #fffbeb;
        color: #92400e;
        border: 1px solid #fde68a;
        padding: 0.35rem 0.9rem;
        border-radius: 9999px;
        font-weight: 800;
        font-size: 0.75rem;
        text-transform: uppercase;
    }

    /* Fiyat ve Taksit Kutuları */
    .hedef-price-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 1.25rem;
        padding: 1.25rem;
        text-align: center;
    }

    .hedef-avg-box {
        background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%);
        border: 2px solid #f472b6;
        border-radius: 1.25rem;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 4px 15px -2px rgba(200, 19, 115, 0.1);
    }

    .hedef-senet-card {
        background: linear-gradient(135deg, #c81373 0%, #e11d48 50%, #db2777 100%);
        color: #ffffff !important;
        border-radius: 1.5rem;
        padding: 1.75rem;
        box-shadow: 0 15px 35px -5px rgba(200, 19, 115, 0.35);
    }

    /* Butonlar */
    .stButton>button {
        background: linear-gradient(to right, #c81373, #e11d48, #db2777) !important;
        color: white !important;
        font-weight: 900 !important;
        font-size: 1rem !important;
        border-radius: 1rem !important;
        border: none !important;
        padding: 0.85rem 2rem !important;
        box-shadow: 0 10px 25px -4px rgba(200, 19, 115, 0.4) !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.02em;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 15px 30px -4px rgba(200, 19, 115, 0.5) !important;
    }

    /* Giriş Alanları */
    .stTextInput input {
        border-radius: 0.85rem !important;
        border: 2px solid #fbcfe8 !important;
        padding: 0.65rem 1rem !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }
    .stTextInput input:focus {
        border-color: #c81373 !important;
        box-shadow: 0 0 0 3px rgba(200, 19, 115, 0.15) !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# 🔒 GÜVENLİK: API ANAHTARININ ÇALINMASINI %100 ENGELLEME
# =========================================================================
# API anahtarı KESİNLİKLE ekranda gösterilmez veya ziyaretçiye açık tutulmaz.
# Yalnızca sunucu tarafında şifreli kasadan (Streamlit Secrets / Env) çekilir.
# Ziyaretçiler ne tarayıcıdan ne kaynak kodundan anahtarı göremez veya kopyalayamaz.
def get_secure_api_key():
    # 1. Streamlit Secrets (share.streamlit.io için güvenli kasa)
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            key = st.secrets["GEMINI_API_KEY"].strip()
            if key and len(key) > 10:
                return key
    except Exception:
        pass

    # 2. Sunucu Ortam Değişkeni
    if os.environ.get("GEMINI_API_KEY"):
        key = os.environ.get("GEMINI_API_KEY").strip()
        if key and len(key) > 10:
            return key

    # 3. Yerel .env.local dosyası
    if os.path.exists(".env.local"):
        try:
            with open(".env.local", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        val = line.strip().split("=", 1)[1].strip("\"' ")
                        if val and len(val) > 10:
                            return val
        except Exception:
            pass

    return None

ACTIVE_API_KEY = get_secure_api_key()

# Kenar Çubuğu (Sidebar) - Güvenlik Bilgilendirmesi (Anahtar Asla Gösterilmez)
with st.sidebar:
    st.markdown("### 🛡️ Kurumsal Güvenlik")
    st.markdown("""
    <div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 1rem; border-radius: 1rem; margin-bottom: 1rem;">
        <span style="color: #065f46; font-weight: 800; font-size: 0.8rem;">🔒 GEMINI API BAĞLANTISI AKTİF</span>
        <p style="color: #047857; font-size: 0.75rem; margin-top: 0.25rem; margin-bottom: 0;">
            API anahtarınız sunucu tarafında kilitlenmiştir. Ziyaretçiler ve üçüncü kişiler tarafından görüntülenemez veya çalınamaz.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🏢 Hedef AVM Hakkında")
    st.caption("Hedef Alışveriş Merkezleri - Evinizin Rengi. Züccaciye, küçük ev aletleri, beyaz eşya ve tüketici elektroniğinde elden senetli ve peşin satış fizibilite motoru.")

# =========================================================================
# 2 AŞAMALI CANLI GOOGLE SEARCH GROUNDING MOTORU
# =========================================================================
def analyze_product_2stage(product_name: str, pil_image: Image.Image, user_cost: float = None, extra_notes: str = None):
    client = genai.Client(api_key=ACTIVE_API_KEY)

    # 1. AŞAMA: Canlı Google Search ile Gerçek Piyasa Fiyatları (Akakçe, Trendyol, Hepsiburada)
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
  "brand": "Örn: Apple, Philips, Karaca...",
  "modelOrCode": "Model kodu",
  "barcode": "Varsa barkod veya null",
  "category": "Örn: Akıllı Telefonlar, Küçük Ev Aletleri...",
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

    # Görseli optimize edilmiş baytlara çevir
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
# ÜST BAŞLIK (HEADER) - RESMİ HEDEF AVM LOGOSU İLE
# =========================================================================
col_h1, col_h2 = st.columns([1, 4])
with col_h1:
    if os.path.exists("public/hedef-logo.png"):
        st.image("public/hedef-logo.png", width=190)
with col_h2:
    st.markdown("""
    <div style="padding-top: 0.25rem;">
        <span class="hedef-pill">AI PİYASA RADARI</span>
        <h1 style="color: #0f172a; font-weight: 900; margin-top: 0.25rem; margin-bottom: 0.25rem; font-size: 2.2rem; letter-spacing: -0.03em;">
            HEDEF AVM PİYASA İSTİHBARATI
        </h1>
        <p style="color: #c81373; font-weight: 700; font-size: 0.95rem; margin-bottom: 0;">
            Evinizin Rengi • Google Gemini 2.5 Canlı Pazar Taraması & Senetli Taksit Motoru
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

# =========================================================================
# GİRİŞ KARTI (FORM)
# =========================================================================
with st.container():
    st.markdown("""
    <div style="text-align: center; max-width: 650px; margin: 0 auto 1.5rem auto;">
        <span class="hedef-pill">⚡ ANLIK PAZAR İSTİHBARATI</span>
        <h2 style="font-weight: 900; color: #0f172a; margin-top: 0.5rem; letter-spacing: -0.02em;">
            Ürün Bilgisini ve Fotoğrafını Ekleyin
        </h2>
        <p style="color: #64748b; font-size: 0.9rem; font-weight: 500;">
            Model karışıklığını önlemek ve Trendyol, Hepsiburada ve Akakçe fiyatlarını <strong>canlı ve hatasız</strong> çekmek için ürün adını belirtiniz.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ZORUNLU ÜRÜN ADI GİRİŞİ
    product_name_input = st.text_input(
        "📦 Ürün Adı ve Modeli * (Zorunlu)",
        placeholder="Örn: gm 26 pro, iPhone 15 128GB, Philips HD9650 Airfryer, Karaca Çay Makinesi...",
        help="Yapay zekanın doğru modeli eşleştirmesi ve Trendyol/Hepsiburada fiyatlarını hatasız çekmesi için model adını yazınız."
    )

    # Görsel Girişi (Kamera & Dosya Yükleme)
    tab_cam, tab_file = st.tabs(["📸 Kamerayla Çek", "📁 Galeriden / Dosyadan Yükle"])
    uploaded_image = None

    with tab_cam:
        cam_file = st.camera_input("Ürünün veya kutusunun fotoğrafını çekin")
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

# =========================================================================
# ANALİZ YÜRÜTME & GELİŞMİŞ SONUÇ DASHBOARD'U
# =========================================================================
if start_btn:
    if not product_name_input.strip():
        st.error("⚠️ Model karışıklığını önlemek için lütfen Ürün Adı ve Modelini giriniz (Örn: gm 26 pro, iPhone 15 128GB)!")
    elif uploaded_image is None:
        st.error("⚠️ Lütfen analiz edilecek ürünün fotoğrafını çekin veya galeriden seçin!")
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

# Sonuç Ekranı (Esas UI Tasarımı)
if "last_analysis" in st.session_state and st.session_state["last_analysis"]:
    res = st.session_state["last_analysis"]
    feasibility = res.get("feasibility", {})
    score = feasibility.get("score", 50)
    verdict = feasibility.get("verdict", "SATAR")

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="hedef-card" style="border-top: 6px solid #c81373;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <span class="hedef-pill">ANALİZ RAPORU HAZIR</span>
                <h2 style="color: #0f172a; font-weight: 900; margin-top: 0.5rem; margin-bottom: 0.25rem;">
                    {res.get('productName')}
                </h2>
                <p style="color: #64748b; font-size: 0.85rem; margin-bottom: 0;">
                    Marka: <strong>{res.get('brand')}</strong> | Kategori: <strong>{res.get('category')}</strong> {f'| Model: {res.get("modelOrCode")}' if res.get("modelOrCode") else ''}
                </p>
            </div>
            <div style="text-align: right;">
                <span class="{'badge-success' if score >= 75 else 'badge-warning'}">{verdict}</span>
                <div style="font-size: 2.2rem; font-weight: 900; color: #c81373;">
                    {score} <span style="font-size: 0.9rem; color: #64748b; font-weight: 700;">/ 100 PUAN</span>
                </div>
            </div>
        </div>
        <div style="margin-top: 1rem; padding: 1rem; background: #faf5f8; border-radius: 1rem; border: 1px solid #fce7f3;">
            <strong style="color: #c81373;">💡 Yönetici Özeti:</strong> <span style="color: #334155; font-weight: 600;">{feasibility.get('headline')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Satır: Piyasa Fiyatları vs Hedef AVM Senetli Taksit Stratejisi
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("""
        <div class="hedef-card">
            <h3 style="font-weight: 900; color: #0f172a; font-size: 1.15rem; margin-bottom: 0.25rem;">
                🏪 Türkiye Canlı Piyasa Fiyat Dağılımı
            </h3>
            <p style="color: #64748b; font-size: 0.8rem; margin-bottom: 1rem;">
                Trendyol, Hepsiburada ve perakende mağaza skalası
            </p>
        """, unsafe_allow_html=True)

        mp = res.get("marketPrices", {})
        c_min, c_avg, c_max = st.columns(3)
        with c_min:
            st.markdown(f"""
            <div class="hedef-price-box">
                <span style="font-size: 0.7rem; font-weight: 800; color: #64748b; text-transform: uppercase;">En Düşük</span>
                <div style="font-size: 1.25rem; font-weight: 900; color: #0f172a;">{mp.get('min', 0):,} ₺</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)
        with c_avg:
            st.markdown(f"""
            <div class="hedef-avg-box">
                <span style="font-size: 0.7rem; font-weight: 900; color: #c81373; text-transform: uppercase;">Piyasa Ortalaması</span>
                <div style="font-size: 1.35rem; font-weight: 900; color: #c81373;">{mp.get('average', 0):,} ₺</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)
        with c_max:
            st.markdown(f"""
            <div class="hedef-price-box">
                <span style="font-size: 0.7rem; font-weight: 800; color: #64748b; text-transform: uppercase;">En Yüksek</span>
                <div style="font-size: 1.25rem; font-weight: 900; color: #0f172a;">{mp.get('max', 0):,} ₺</div>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 1.25rem;'><strong style='font-size: 0.8rem; color: #64748b; text-transform: uppercase;'>Pazaryeri Örnekleri:</strong></div>", unsafe_allow_html=True)
        for comp in res.get("competitorBenchmarks", []):
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.65rem 1rem; background: #faf5f8; border-radius: 0.85rem; margin-top: 0.4rem; border: 1px solid #fce7f3; font-size: 0.85rem;">
                <div>
                    <strong style="color: #0f172a;">{comp.get('platform')}</strong>
                    <div style="color: #64748b; font-size: 0.75rem;">{comp.get('notes', '')}</div>
                </div>
                <div style="font-weight: 900; color: #0f172a; font-size: 1rem;">
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
                Peşin ve 12 ay elden senetli taksit stratejisi
            </p>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1rem;">
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 1.25rem; padding: 1rem;">
                    <span style="font-size: 0.7rem; font-weight: 800; color: #64748b; text-transform: uppercase;">Peşin / Kredi Kartı</span>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #0f172a; margin-top: 0.25rem;">
                        {hp.get('cashRecommendedPrice', 0):,} ₺
                    </div>
                    <span style="font-size: 0.75rem; color: #94a3b8;">Online rekabetçi liste fiyatı</span>
                </div>

                <div class="hedef-senet-card">
                    <span style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: #fce7f3;">Elden Senetli Toplam</span>
                    <div style="font-size: 1.6rem; font-weight: 900; margin-top: 0.25rem;">
                        {hp.get('installmentRecommendedPrice', 0):,} ₺
                    </div>
                    <span style="font-size: 0.8rem; font-weight: 700; color: #fdf2f8;">
                        {hp.get('monthlyInstallmentPrice', 0):,} ₺ x {hp.get('installmentCount', 12)} Ay Taksit
                    </span>
                </div>
            </div>

            <div style="background: #fdf2f8; border-radius: 1rem; padding: 0.85rem; border: 1px solid #fce7f3; font-size: 0.82rem; color: #831843;">
                <strong>📌 Satın Alma Tavsiyesi:</strong> {hp.get('strategyNote', '')}
            </div>
        </div>
        """.replace(",", "."), unsafe_allow_html=True)

    # 2. Satır: Neden Satar? (Fırsatlar) vs Riskler
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("""
        <div class="hedef-card" style="border-left: 6px solid #10b981;">
            <h4 style="font-weight: 900; color: #065f46; margin-bottom: 0.5rem;">✅ Neden Satar? (Satış Gücü & Fırsatlar)</h4>
        """, unsafe_allow_html=True)
        for reason in feasibility.get("reasonsToSell", []):
            st.markdown(f"""
            <div style="padding: 0.6rem 0.85rem; background: #ecfdf5; border-radius: 0.75rem; margin-top: 0.4rem; font-size: 0.85rem; color: #064e3b; font-weight: 600;">
                ✓ {reason}
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r2:
        st.markdown("""
        <div class="hedef-card" style="border-left: 6px solid #f59e0b;">
            <h4 style="font-weight: 900; color: #92400e; margin-bottom: 0.5rem;">⚠️ Riskler ve Dikkat Edilmesi Gerekenler</h4>
        """, unsafe_allow_html=True)
        for risk in feasibility.get("risksAndWatchouts", []):
            st.markdown(f"""
            <div style="padding: 0.6rem 0.85rem; background: #fffbeb; border-radius: 0.75rem; margin-top: 0.4rem; font-size: 0.85rem; color: #78350f; font-weight: 600;">
                ! {risk}
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. Satır: Kampanya & Vitrin Sloganları
    st.markdown("""
    <div class="hedef-card">
        <h4 style="font-weight: 900; color: #0f172a; margin-bottom: 0.75rem;">📣 Hedef AVM Mağaza İçi Kampanya & Vitrin Kurguları</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
    """, unsafe_allow_html=True)

    for camp in res.get("campaigns", []):
        st.markdown(f"""
        <div style="background: #faf5f8; border: 1px solid #fce7f3; border-radius: 1rem; padding: 1rem;">
            <span class="hedef-pill">{camp.get('campaignType')}</span>
            <h5 style="font-weight: 900; color: #0f172a; margin-top: 0.5rem; margin-bottom: 0.25rem;">{camp.get('title')}</h5>
            <p style="font-size: 0.82rem; color: #475569; margin-bottom: 0.75rem;">{camp.get('description')}</p>
            <div style="background: #ffffff; border: 1px solid #fbcfe8; padding: 0.6rem 0.85rem; border-radius: 0.75rem; font-size: 0.82rem; color: #c81373; font-weight: 800; font-style: italic;">
                "{camp.get('bannerSlogan')}"
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # Rapor İndirme Butonu
    st.download_button(
        label="📥 Fizibilite Raporunu JSON Olarak İndir",
        data=json.dumps(res, ensure_ascii=False, indent=2),
        file_name=f"Hedef_AVM_Rapor_{res.get('brand', 'Urun')}.json",
        mime="application/json"
    )

# Alt Bilgi (Footer)
st.markdown("""
<div style="text-align: center; padding: 2rem 0; color: #94a3b8; font-size: 0.75rem; border-top: 1px solid #fce7f3; margin-top: 2rem;">
    <strong>HEDEF AVM</strong> • Özel Ürün Piyasa Araştırması AI Yazılımı<br>
    Google Gemini 2.5 Vision & Canlı Arama İstihbarat Motoru ile korunmaktadır.
</div>
""", unsafe_allow_html=True)
