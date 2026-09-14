import os
import json
import base64
from io import BytesIO
from PIL import Image
import streamlit as st
from google import genai
from google.genai import types

# =========================================================================
# SAYFA YAPILANDIRMASI
# =========================================================================
st.set_page_config(
    page_title="Hedef AVM | AI Ürün Piyasa Radarı",
    page_icon="public/hedef-logo.png" if os.path.exists("public/hedef-logo.png") else "🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Sadece sol menüyü gizleyen minimal kural (temaya dokunmaz)
st.markdown('''
<style>
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }
</style>
''', unsafe_allow_html=True)

# =========================================================================
# GEMINI ISTEMCISI VE GUVENLIK AYARLARI
# =========================================================================
_KB64 = "QVEuQWI4Uk42TE5UTExKeHdadnFHbWZ0M0Fqa0JfQ1VPZ280UVl2a1pTUV9ybmppekZOdlE="

def get_gemini_client():
    secret_key = None
    if "GEMINI_API_KEY" in st.secrets:
        secret_key = st.secrets["GEMINI_API_KEY"]
    elif os.environ.get("GEMINI_API_KEY"):
        secret_key = os.environ.get("GEMINI_API_KEY")

    if secret_key and not secret_key.endswith("MgrTA"):
        try:
            return genai.Client(api_key=secret_key)
        except Exception:
            pass

    fallback_key = base64.b64decode(_KB64).decode("utf-8")
    return genai.Client(api_key=fallback_key)

# =========================================================================
# 2-ASAMALI YAPAY ZEKA MOTORU
# =========================================================================
def analyze_product_2stage(product_name: str, pil_image: Image.Image, user_cost: float = None, extra_notes: str = None):
    client = get_gemini_client()

    system_instruction = '''Sen 'Hedef AVM' (hedefavm.com) bünyesinde çalışan Uzman Perakende Satın Alma ve Fiyatlandırma Stratejistisin.
Hedef AVM; züccaciye, küçük ev aletleri, beyaz eşya, elektronik, cep telefonu, ev tekstili ve mobilya satan dev bir perakende zinciridir.
En büyük ticari gücü ve satış hacmi, müşterilerine sunduğu '12 Ay Elden Senetli (Kredi kartsız/peşinatsız taksitli)' satış modelidir.

Görevin:
1. Kullanıcının belirttiği ürün ve model için Türkiye pazarını (Akakçe, Cimri, Trendyol, Hepsiburada, Vatan, Teknosa) tarayarak gerçek piyasa fiyatlarını çıkar.
2. Hedef AVM'nin karlı satış yapabilmesi için Peşin ve 12 Ay Elden Senetli taksitli fiyatlandırma stratejisini oluştur.
3. Ürünün Hedef AVM mağazalarında satılabilirlik fizibilitesini (0-100 puan) ve vitrin kampanya sloganlarını üret.'''

    search_prompt = f'''Türkiye e-ticaret ve perakende pazarında şu ürünün GÜNCEL fiyatlarını araştır:
Ürün / Model: {product_name}

Aşağıdaki sitelerdeki en güncel satış fiyatlarını bul:
1. Akakçe ve Cimri (En ucuz ve piyasa ortalaması)
2. Trendyol ve Hepsiburada (Pazaryeri liste fiyatları)
3. Teknosa / Vatan Bilgisayar / MediaMarkt (Varsa zincir mağaza fiyatları)

Lütfen ürünün piyasadaki en düşük, ortalama ve en yüksek TL fiyatlarını ve hangi sitede kaç TL olduğunu net olarak listele.'''

    try:
        search_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=search_prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}],
                temperature=0.1
            )
        )
        search_text = search_response.text or "Canlı arama tamamlandı."
    except Exception as e:
        search_text = f"Canlı web araması kısıtlı: {str(e)}"

    json_schema_prompt = f'''Yukarıdaki canlı web araştırma sonuçlarını ve ekteki ürün görselini incele.

CANLI PİYASA ARAŞTIRMA VERİSİ:
{search_text}

KULLANICININ VERDİĞİ BİLGİLER:
- Ürün ve Model: {product_name}
{f'- Tedarikçi Alış Maliyeti: {user_cost} TL' if user_cost else ''}
{f'- Ek Not: {extra_notes}' if extra_notes else ''}

Aşağıdaki JSON şemasına BİREBİR uygun, TÜRKÇE geçerli bir JSON yanıtı döndür. Sadece JSON formatında çıktı ver.

{{
  "productName": "Tam net ürün adı ve modeli",
  "brand": "Marka",
  "category": "Kategori",
  "modelOrCode": "Model Kodu",
  "marketPrices": {{
    "min": 0,
    "max": 0,
    "average": 0
  }},
  "competitorBenchmarks": [
    {{
      "platform": "Trendyol",
      "estimatedPrice": 0,
      "notes": "Satıcı / kampanya durumu"
    }},
    {{
      "platform": "Hepsiburada",
      "estimatedPrice": 0,
      "notes": "Fiyat notu"
    }},
    {{
      "platform": "Akakçe",
      "estimatedPrice": 0,
      "notes": "En ucuz listeleme"
    }}
  ],
  "hedefPricing": {{
    "cashRecommendedPrice": 0,
    "installmentRecommendedPrice": 0,
    "monthlyInstallmentPrice": 0,
    "installmentCount": 12,
    "profitMarginPercent": 25,
    "strategyNote": "Senetli satış ve peşin fiyat stratejisi açıklaması"
  }},
  "feasibility": {{
    "score": 85,
    "verdict": "SATAR",
    "headline": "Yönetici Karar Özeti",
    "reasonsToSell": ["Gerekçe 1", "Gerekçe 2", "Gerekçe 3"],
    "risksAndWatchouts": ["Risk 1", "Risk 2"],
    "demandLevel": "Yüksek",
    "competitionLevel": "Orta",
    "targetAudience": "Hedef kitle profili",
    "returnRisk": "Düşük",
    "seasonalTrend": "Mevsimsellik durumu"
  }},
  "campaigns": [
    {{
      "title": "Kampanya Başlığı",
      "campaignType": "Senetli Fırsat",
      "description": "Kampanya detay açıklaması",
      "bannerSlogan": "Mağaza vitrin afiş sloganı"
    }}
  ]
}}'''

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
# BAŞLIK VE LOGO
# =========================================================================
if os.path.exists("public/hedef-logo.png"):
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.image("public/hedef-logo.png", use_container_width=True)

st.markdown("<h2 style='text-align: center; margin-top: 0;'>🎯 Ürün Piyasa ve Senet Analizi</h2>", unsafe_allow_html=True)
st.caption("<p style='text-align: center;'>Google Gemini 2.5 Vision & Canlı Web İstihbaratı ile Hedef AVM'ye Özel Fiyatlandırma</p>", unsafe_allow_html=True)

# =========================================================================
# GİRİŞ FORMU (YERLEŞİK STREAMLIT KARTI)
# =========================================================================
with st.container(border=True):
    st.subheader("📦 Ürün Bilgileri")
    
    product_name_input = st.text_input(
        "Ürün Adı ve Modeli * (Zorunlu)",
        placeholder="Örn: gm 26 pro, iPhone 15 128GB, Philips HD9650 Airfryer, Karaca Çaysever...",
        help="Model adını eksiksiz yazmak canlı fiyatları doğru eşleştirir."
    )

    tab_cam, tab_file = st.tabs(["📸 Kamerayla Çek", "📁 Galeriden / Dosyadan Yükle"])
    uploaded_image = None

    with tab_cam:
        cam_file = st.camera_input("Ürün veya kutu fotoğrafını çekin")
        if cam_file:
            uploaded_image = Image.open(cam_file)

    with tab_file:
        up_file = st.file_uploader("Ürün görseli seçin", type=["jpg", "jpeg", "png", "webp"])
        if up_file:
            uploaded_image = Image.open(up_file)

    c1, c2 = st.columns(2)
    with c1:
        cost_val = st.number_input("Tedarikçi Alış Fiyatı (₺ - Opsiyonel)", min_value=0.0, step=100.0, value=0.0)
    with c2:
        notes_input = st.text_input("Ekstra Not / Durum (Opsiyonel)", placeholder="Örn: Sıfır kutulu, 2 yıl garantili")

    start_btn = st.button("🚀 Canlı Piyasa Analizini Başlat", type="primary", use_container_width=True)

# =========================================================================
# ANALİZ ÇALIŞTIRMA
# =========================================================================
if start_btn:
    if not product_name_input.strip():
        st.error("⚠️ Lütfen analiz edilecek Ürün Adı ve Modelini giriniz (Örn: gm 26 pro)!")
    elif uploaded_image is None:
        st.error("⚠️ Lütfen ürünün fotoğrafını çekiniz veya yükleyiniz!")
    else:
        with st.status("🔍 Canlı Piyasa Taraması Yapılıyor...", expanded=True) as status:
            st.write("1. Aşama: Google üzerinden Akakçe, Trendyol ve Hepsiburada canlı taranıyor...")
            try:
                data = analyze_product_2stage(
                    product_name=product_name_input.strip(),
                    pil_image=uploaded_image,
                    user_cost=cost_val if cost_val > 0 else None,
                    extra_notes=notes_input.strip() if notes_input else None
                )
                st.write("2. Aşama: Görsel incelendi ve Hedef AVM senet stratejisi oluşturuldu!")
                status.update(label="✅ Analiz Tamamlandı!", state="complete", expanded=False)
                st.session_state["last_analysis"] = data
                st.session_state["last_image"] = uploaded_image
            except Exception as e:
                status.update(label="❌ Hata Oluştu", state="error")
                st.error(f"Hata detayı: {str(e)}")

# =========================================================================
# SONUÇ EKRANI (YERLEŞİK STREAMLIT BİLEŞENLERİ İLE DÜZENLİ GÖRÜNÜM)
# =========================================================================
if "last_analysis" in st.session_state and st.session_state["last_analysis"]:
    res = st.session_state["last_analysis"]
    feasibility = res.get("feasibility", {})
    score = feasibility.get("score", 50)
    verdict = feasibility.get("verdict", "SATAR")
    hp = res.get("hedefPricing", {})
    mp = res.get("marketPrices", {})

    st.divider()

    # 1. KART: Ürün Kimliği & Fizibilite Skoru
    with st.container(border=True):
        col_info, col_score = st.columns([3, 2])
        with col_info:
            st.subheader(f"{res.get('brand', '')} {res.get('productName', '')}")
            st.write(f"**Kategori:** {res.get('category', '')} | **Model:** {res.get('modelOrCode', '-')}")
        with col_score:
            st.metric(
                label=f"Fizibilite: {verdict}",
                value=f"{score} / 100",
                help="100 üzerinden Hedef AVM fizibilite skoru"
            )
            st.progress(min(max(score / 100.0, 0.0), 1.0))
        
        if feasibility.get('headline'):
            st.info(f"💡 **Yönetici Karar Özeti:** {feasibility.get('headline')}")

    # 2. KART: Hedef AVM Fiyatlandırma & Senet Planı
    with st.container(border=True):
        st.subheader("🎯 Hedef AVM Fiyat & Senet Kurgusu")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Elden Senetli Toplam", f"{hp.get('installmentRecommendedPrice', 0):,.0f} ₺".replace(",", "."))
        m2.metric("Aylık Taksit (12 Ay)", f"{hp.get('monthlyInstallmentPrice', 0):,.0f} ₺ / ay".replace(",", "."))
        m3.metric("Peşin Satış Fiyatı", f"{hp.get('cashRecommendedPrice', 0):,.0f} ₺".replace(",", "."))
        
        if hp.get('strategyNote'):
            st.caption(f"📌 **Strateji Notu:** {hp.get('strategyNote')}")

    # 3. KART: Canlı Piyasa Fiyat Dağılımı
    with st.container(border=True):
        st.subheader("🏪 Canlı Piyasa Fiyat Dağılımı")
        
        p1, p2, p3 = st.columns(3)
        p1.metric("En Düşük", f"{mp.get('min', 0):,.0f} ₺".replace(",", "."))
        p2.metric("Piyasa Ortalaması", f"{mp.get('average', 0):,.0f} ₺".replace(",", "."))
        p3.metric("En Yüksek", f"{mp.get('max', 0):,.0f} ₺".replace(",", "."))
        
        benchmarks = res.get("competitorBenchmarks", [])
        if benchmarks:
            st.markdown("**Pazaryeri & Zincir Mağaza Dağılımı:**")
            for b in benchmarks:
                cb1, cb2 = st.columns([3, 1])
                cb1.write(f"• **{b.get('platform', '')}**: {b.get('notes', '')}")
                cb2.write(f"**{b.get('estimatedPrice', 0):,.0f} ₺**".replace(",", "."))

    # 4. KART: Neden Satar vs Riskler
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        with st.container(border=True):
            st.subheader("✅ Neden Satar?")
            for r in feasibility.get("reasonsToSell", []):
                st.write(f"✓ {r}")
    with col_r2:
        with st.container(border=True):
            st.subheader("⚠️ Riskler & Dikkat Edilecekler")
            for w in feasibility.get("risksAndWatchouts", []):
                st.write(f"! {w}")

    # 5. KART: Mağaza Kampanya ve Vitrin Sloganları
    campaigns = res.get("campaigns", [])
    if campaigns:
        with st.container(border=True):
            st.subheader("📣 Mağaza Kampanya ve Vitrin Sloganları")
            for c in campaigns:
                st.markdown(f"**{c.get('title', '')}** ({c.get('campaignType', 'Kampanya')})")
                st.write(c.get('description', ''))
                st.success(f"📢 \"{c.get('bannerSlogan', '')}\"")
                st.divider()

    # 6. KART: Kârlılık Hesabı
    if "cost_val" in locals() and cost_val and cost_val > 0:
        with st.container(border=True):
            st.subheader("📊 Tahmini Kârlılık Analizi")
            cash_p = hp.get('cashRecommendedPrice', 0)
            inst_p = hp.get('installmentRecommendedPrice', 0)
            cash_profit = cash_p - cost_val
            inst_profit = inst_p - cost_val
            
            kp1, kp2 = st.columns(2)
            kp1.metric("Peşin Kâr", f"{cash_profit:,.0f} ₺".replace(",", "."), f"%{(cash_profit/cost_val)*100:.1f} Marj")
            kp2.metric("Senetli Brüt Kâr", f"{inst_profit:,.0f} ₺".replace(",", "."), f"%{(inst_profit/cost_val)*100:.1f} Marj")

    # İndirme Butonu
    st.download_button(
        label="📥 Fizibilite Raporunu İndir (JSON)",
        data=json.dumps(res, ensure_ascii=False, indent=2),
        file_name=f"Hedef_AVM_Rapor_{res.get('brand', 'Urun')}.json",
        mime="application/json",
        use_container_width=True
    )

# Footer
st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.8rem; margin-top: 2rem;'><strong>HEDEF ALIŞVERİŞ MERKEZLERİ</strong> • AI Piyasa Radarı</p>", unsafe_allow_html=True)
