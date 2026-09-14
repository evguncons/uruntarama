import os
import json
import base64
from io import BytesIO
from PIL import Image
import streamlit as st
try:
    from google import genai
    from google.genai import types
    HAS_NEW_GENAI = True
except Exception as e:
    HAS_NEW_GENAI = False
    import google.generativeai as legacy_genai

# =========================================================================
# SAYFA VE TEMA YAPILANDIRMASI
# =========================================================================
st.set_page_config(
    page_title="Hedef AVM | AI Ürün Piyasa Radarı",
    page_icon="public/hedef-logo.png" if os.path.exists("public/hedef-logo.png") else "🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Özel Kurumsal Açık Magenta Stilleri
st.markdown("""
<style>
    :root {
        --hedef-magenta: #c81373;
        --hedef-rose: #e11d48;
    }
    .stApp {
        background-color: #faf5f8;
        color: #0f172a;
    }
    .hedef-card {
        background: #ffffff;
        border: 1px solid #fce7f3;
        border-radius: 1.25rem;
        padding: 1.5rem;
        box-shadow: 0 4px 20px -2px rgba(200, 19, 115, 0.05);
        margin-bottom: 1.25rem;
    }
    .hedef-badge {
        display: inline-block;
        background: #fdf2f8;
        color: #c81373;
        border: 1px solid #fbcfe8;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-weight: 800;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .hedef-price-tag {
        font-size: 1.75rem;
        font-weight: 900;
        color: #0f172a;
    }
    .hedef-senet-box {
        background: linear-gradient(135deg, #c81373 0%, #e11d48 50%, #db2777 100%);
        color: #ffffff !important;
        border-radius: 1rem;
        padding: 1.25rem;
        box-shadow: 0 10px 25px -5px rgba(200, 19, 115, 0.3);
    }
    .stButton>button {
        background: linear-gradient(to right, #c81373, #e11d48, #db2777) !important;
        color: white !important;
        font-weight: 800 !important;
        border-radius: 0.85rem !important;
        border: none !important;
        padding: 0.65rem 1.75rem !important;
        box-shadow: 0 8px 20px -4px rgba(200, 19, 115, 0.35) !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 12px 25px -4px rgba(200, 19, 115, 0.45) !important;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================================
# GÜVENLİK: GEMINI API KEY KORUMASI
# =========================================================================
def get_api_key():
    # 1. Streamlit Cloud Secrets (st.secrets["GEMINI_API_KEY"])
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    # 2. Ortam Değişkeni (os.environ["GEMINI_API_KEY"])
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ.get("GEMINI_API_KEY")

    # 3. Yerel .env.local dosyası kontrolü (Local geliştirme için)
    if os.path.exists(".env.local"):
        try:
            with open(".env.local", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        val = line.strip().split("=", 1)[1].strip("\"' ")
                        if val:
                            return val
        except Exception:
            pass

    return None

api_key = get_api_key()

# Kenar çubuğu ayarları ve API anahtarı kontrolü
with st.sidebar:
    st.markdown("### ⚙️ Ayarlar & Güvenlik")
    
    # Mevcut anahtarı al
    default_key = get_api_key() or ""
    
    # Kullanıcının manuel girmesine / değiştirmesine her zaman izin ver
    custom_key = st.text_input(
        "🔑 Gemini API Anahtarı",
        value=st.session_state.get("custom_api_key", default_key),
        type="password",
        help="Google AI Studio'dan (aistudio.google.com) aldığınız API anahtarı."
    )
    
    if custom_key.strip():
        api_key = custom_key.strip()
        st.session_state["custom_api_key"] = api_key
        st.success("✅ API Anahtarı Tanımlı")
    else:
        api_key = None
        st.warning("⚠️ Lütfen geçerli bir Gemini API anahtarı giriniz.")

    st.markdown("---")
    st.markdown("#### ℹ️ Hedef AVM Hakkında")
    st.caption("Bu yazılım züccaciye, küçük ev aletleri, beyaz eşya ve tüketici elektroniği ürünlerini canlı pazar aramasıyla değerlendirir.")

# =========================================================================
# 2 AŞAMALI CANLI GOOGLE SEARCH GROUNDING MOTORU
# =========================================================================
def analyze_product_2stage(product_name: str, pil_image: Image.Image, user_cost: float = None, extra_notes: str = None):
    if not api_key:
        raise ValueError("Lütfen geçerli bir Gemini API anahtarı sağlayınız.")

    client = genai.Client(api_key=api_key)

    # ---------------------------------------------------------------------
    # 1. AŞAMA: Canlı Google Search Grounding ile Piyasa Fiyatlarını Araştırma
    # ---------------------------------------------------------------------
    search_prompt = f"""Sen Türkiye perakende pazarında uzman bir fiyat ve piyasa araştırmacısısın.
Kullanıcı şu ürünü analiz ediyor: "{product_name}".

GÖREVİN:
Google Arama aracını kullanarak Türkiye'deki Akakçe, Cimri, Trendyol, Hepsiburada, Amazon Türkiye, Teknosa ve MediaMarkt sitelerindeki ŞU ANKİ EN GÜNCEL satış fiyatlarını araştır:
1. En ucuz fiyat (TL) ve hangi sitede satıldığı
2. Ortalama piyasa fiyatı (TL)
3. En yüksek yetkili satıcı / mağaza liste fiyatı (TL)
4. Trendyol ve Hepsiburada'daki güncel fiyatlar ve satıcı durumu
5. Ürünün güncel stok/satış durumu

Lütfen gerçek ve güncel rakamları net olarak listele."""

    search_response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=search_prompt,
        config=types.GenerateContentConfig(
            tools=[{"google_search": {}}],
            temperature=0.1
        )
    )
    live_findings = search_response.text or "Canlı arama tamamlandı."

    # ---------------------------------------------------------------------
    # 2. AŞAMA: Görsel İnceleme + Canlı Piyasa Verisi ile Hedef AVM Raporu
    # ---------------------------------------------------------------------
    system_instruction = f"""Sen Türkiye perakende pazarında uzmanlaşmış, "Hedef AVM" için çalışan kıdemli bir Satın Alma Direktörü ve Fiyatlandırma Stratejistisin.
Hedef AVM; züccaciye, küçük ev aletleri, beyaz eşya, tüketici elektroniği ve mobilya alanında hem peşin hem de Türkiye'ye özgü "elden senetli / taksitli" satış modeliyle çalışan güçlü bir mağazalar zinciridir.

Kullanıcı ürünün tam adını ve modelini belirtmiştir: "{product_name}".
Ayrıca ürünün fotoğrafı eklenmiştir.

Aşağıda canlı internet aramasından (Akakçe, Trendyol, Hepsiburada vb.) toplanan en güncel piyasa araştırması verileri yer almaktadır:
--- CANLI PİYASA İSTİHBARATI ---
{live_findings}
-------------------------------

GÖREVİN:
Yukarıdaki GERÇEK internet pazar verilerini ve yüklenen fotoğrafı harmanlayarak Hedef AVM için doğrulanmış, gerçekçi bir piyasa fizibilite raporu hazırla.

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
    if HAS_NEW_GENAI:
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
    else:
        legacy_genai.configure(api_key=api_key)
        model = legacy_genai.GenerativeModel("gemini-1.5-flash", generation_config={"response_mime_type": "application/json"})
        resp = model.generate_content([system_instruction, pil_image, json_schema_prompt])
        return json.loads(resp.text)

# =========================================================================
# ANA ARAYÜZ (HEADER & FORM)
# =========================================================================
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists("public/hedef-logo.png"):
        st.image("public/hedef-logo.png", width=180)
with col_title:
    st.markdown("<h1 style='color: #0f172a; margin-bottom: 0px;'>HEDEF AVM AI PİYASA RADARI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #c81373; font-weight: 700;'>Evinizin Rengi • Google Gemini 2.5 Canlı Pazar İstihbarat & Satılabilirlik Motoru</p>", unsafe_allow_html=True)

st.markdown("---")

# Giriş Kartı
with st.container():
    st.markdown("<div class='hedef-badge'>CANLI PİYASA TARAMASI</div>", unsafe_allow_html=True)
    st.markdown("### 📦 Ürün Bilgisini ve Fotoğrafını Girin")

    # ZORUNLU ÜRÜN ADI GİRİŞİ
    product_name_input = st.text_input(
        "Ürün Adı ve Modeli * (Zorunlu)",
        placeholder="Örn: iPhone 15 128GB, Philips HD9650 Airfryer, Karaca Hatır Hüps...",
        help="Model karışıklığını önlemek ve Trendyol/Hepsiburada fiyatlarını hatasız çekmek için model adını tam yazınız."
    )

    # Görsel Seçimi
    input_tab1, input_tab2 = st.tabs(["📸 Kamerayla Çek", "📁 Galeriden / Dosyadan Yükle"])
    uploaded_image = None

    with input_tab1:
        camera_pic = st.camera_input("Ürünün veya kutusunun fotoğrafını çekin")
        if camera_pic:
            uploaded_image = Image.open(camera_pic)

    with input_tab2:
        file_pic = st.file_uploader("Ürün fotoğrafı yükleyin (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"])
        if file_pic:
            uploaded_image = Image.open(file_pic)

    # Ek Parametreler
    col_cost, col_notes = st.columns(2)
    with col_cost:
        user_cost_val = st.number_input("Tedarikçi Alış Fiyatı (₺ - Opsiyonel)", min_value=0.0, step=50.0, value=0.0)
    with col_notes:
        notes_val = st.text_input("Ekstra Not / Durum (Opsiyonel)", placeholder="Örn: Sıfır kutulu, 2 yıl Türkiye garantili")

    start_btn = st.button("🚀 Canlı Piyasa Analizini Başlat", use_container_width=True)

# =========================================================================
# ANALİZ ÇALIŞTIRMA VE SONUÇ GÖSTERİMİ
# =========================================================================
if start_btn:
    if not product_name_input.strip():
        st.error("⚠️ Model karışıklığını önlemek için lütfen Ürün Adı ve Modelini giriniz (Örn: iPhone 15 128GB)!")
    elif uploaded_image is None:
        st.error("⚠️ Lütfen analiz edilecek ürünün fotoğrafını çekin veya yükleyin!")
    elif not api_key:
        st.error("⚠️ Gemini API anahtarı bulunamadı! Lütfen sol menüden API anahtarınızı girin.")
    else:
        with st.status("🔍 Canlı Piyasa Taraması Başlatılıyor...", expanded=True) as status:
            st.write("1. Aşama: Google üzerinden Akakçe, Trendyol ve Hepsiburada güncel fiyatları canlı taranıyor...")
            try:
                data = analyze_product_2stage(
                    product_name=product_name_input.strip(),
                    pil_image=uploaded_image,
                    user_cost=user_cost_val if user_cost_val > 0 else None,
                    extra_notes=notes_val.strip() if notes_val else None
                )
                st.write("2. Aşama: Görsel incelendi ve Hedef AVM taksit stratejisi oluşturuldu!")
                status.update(label="✅ Analiz Başarıyla Tamamlandı!", state="complete", expanded=False)
                st.session_state["last_analysis"] = data
                st.session_state["last_image"] = uploaded_image
            except Exception as e:
                status.update(label="❌ Analiz Sırasında Hata Oluştu", state="error")
                st.error(f"Hata detayı: {str(e)}")

# Sonuç Ekranı
if "last_analysis" in st.session_state and st.session_state["last_analysis"]:
    res = st.session_state["last_analysis"]

    st.markdown("---")
    st.markdown(f"## 📊 {res.get('productName', 'Ürün')} Fizibilite Raporu")

    # Üst Skor & Karar Kartı
    feasibility = res.get("feasibility", {})
    score = feasibility.get("score", 50)
    verdict = feasibility.get("verdict", "SATAR")

    col_score_l, col_score_r = st.columns([3, 1])
    with col_score_l:
        st.markdown(f"""
        <div class='hedef-card' style='border-left: 6px solid #c81373;'>
            <div class='hedef-badge'>{verdict}</div>
            <h3 style='margin-top: 0.5rem; color: #0f172a;'>{feasibility.get('headline', '')}</h3>
            <p style='color: #64748b; font-size: 0.85rem;'>Marka: <strong>{res.get('brand')}</strong> | Kategori: <strong>{res.get('category')}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    with col_score_r:
        st.metric(label="Satılabilirlik Skoru", value=f"{score} / 100", delta=f"{verdict}")

    # Piyasa Fiyatları ve Hedef AVM Stratejisi
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("### 🏪 Türkiye Piyasa Fiyat Skalası")
        mp = res.get("marketPrices", {})
        c1, c2, c3 = st.columns(3)
        c1.metric("En Düşük", f"{mp.get('min', 0):,} ₺".replace(",", "."))
        c2.metric("Piyasa Ortalaması", f"{mp.get('average', 0):,} ₺".replace(",", "."))
        c3.metric("En Yüksek", f"{mp.get('max', 0):,} ₺".replace(",", "."))

        st.markdown("#### Platform Örnekleri:")
        for comp in res.get("competitorBenchmarks", []):
            st.markdown(f"• **{comp.get('platform')}**: `{comp.get('estimatedPrice', 0):,} ₺` - *{comp.get('notes', '')}*")

    with col_p2:
        st.markdown("### 🎯 Hedef AVM Taksit & Senet Kurgusu")
        hp = res.get("hedefPricing", {})
        st.markdown(f"""
        <div class='hedef-senet-box'>
            <span style='font-size: 0.8rem; font-weight: 700; text-transform: uppercase;'>Elden Senetli (12 Taksit)</span>
            <div style='font-size: 2rem; font-weight: 900;'>{hp.get('installmentRecommendedPrice', 0):,} ₺</div>
            <div style='font-size: 1rem; margin-top: 0.25rem;'>Aylık: <strong>{hp.get('monthlyInstallmentPrice', 0):,} ₺</strong> x {hp.get('installmentCount', 12)} Ay</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**Peşin / Kredi Kartı Tavsiye Fiyatı:** `{hp.get('cashRecommendedPrice', 0):,} ₺`")
        st.caption(f"📌 **Satın Alma Tavsiyesi:** {hp.get('strategyNote', '')}")

    # Neden Satar vs Riskler
    col_reasons, col_risks = st.columns(2)
    with col_reasons:
        st.markdown("#### ✅ Neden Satar? (Fırsatlar)")
        for reason in feasibility.get("reasonsToSell", []):
            st.success(f"✓ {reason}")

    with col_risks:
        st.markdown("#### ⚠️ Riskler & Dikkat Edilecekler")
        for risk in feasibility.get("risksAndWatchouts", []):
            st.warning(f"! {risk}")

    # Kampanya Önerileri
    st.markdown("### 📣 Mağaza İçi Kampanya & Vitrin Sloganları")
    for camp in res.get("campaigns", []):
        with st.expander(f"✨ {camp.get('title')} ({camp.get('campaignType')})", expanded=True):
            st.write(camp.get("description"))
            if camp.get("bannerSlogan"):
                st.info(f"📢 **Afiş Sloganı:** \"{camp.get('bannerSlogan')}\"")

    # WhatsApp / Metin Paylaşımı
    st.markdown("---")
    st.download_button(
        label="📥 Raporu JSON Olarak İndir",
        data=json.dumps(res, ensure_ascii=False, indent=2),
        file_name=f"Hedef_AVM_Rapor_{res.get('brand', 'Urun')}.json",
        mime="application/json"
    )
