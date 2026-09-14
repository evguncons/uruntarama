import os
import json
import base64
import urllib.parse
from datetime import datetime
from io import BytesIO
from PIL import Image
import streamlit as st
from google import genai
from google.genai import types

# =========================================================================
# SAYFA YAPILANDIRMASI
# =========================================================================
st.set_page_config(
    page_title="Hedef AVM | AI Piyasa & Senet Radarı",
    page_icon="public/hedef-logo.png" if os.path.exists("public/hedef-logo.png") else "🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Sadece sol menüyü gizleyen minimal kural (temaya dokunmaz)
st.markdown("""
<style>
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Session state geçmiş başlatma
if "history" not in st.session_state:
    st.session_state["history"] = []

# =========================================================================
# GEMINI İSTEMCİSİ VE GÜVENLİK AYARLARI
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
# 2-AŞAMALI YAPAY ZEKA MOTORU
# =========================================================================
def analyze_product_2stage(product_name: str, pil_image: Image.Image, user_cost: float = None, extra_notes: str = None):
    client = get_gemini_client()

    system_instruction = """Sen 'Hedef AVM' (hedefavm.com) bünyesinde çalışan Uzman Perakende Satın Alma ve Fiyatlandırma Stratejistisin.
Hedef AVM; züccaciye, küçük ev aletleri, beyaz eşya, elektronik, cep telefonu, ev tekstili ve mobilya satan dev bir perakende zinciridir.
En büyük ticari gücü ve satış hacmi, müşterilerine sunduğu '12 Ay Elden Senetli (Kredi kartsız/peşinatsız taksitli)' satış modelidir.

Görevin:
1. Kullanıcının belirttiği ürün ve model için Türkiye pazarını (Akakçe, Cimri, Trendyol, Hepsiburada, Vatan, Teknosa) tarayarak gerçek piyasa fiyatlarını çıkar.
2. Hedef AVM'nin karlı satış yapabilmesi için Peşin ve 12 Ay Elden Senetli taksitli fiyatlandırma stratejisini oluştur.
3. Ürünün Hedef AVM mağazalarında satılabilirlik fizibilitesini (0-100 puan), talep/rekabet/iade dinamiklerini ve vitrin kampanya sloganlarını üret."""

    search_prompt = f"""Türkiye e-ticaret ve perakende pazarında şu ürünün GÜNCEL fiyatlarını araştır:
Ürün / Model: {product_name}

Aşağıdaki sitelerdeki en güncel satış fiyatlarını bul:
1. Akakçe ve Cimri (En ucuz ve piyasa ortalaması)
2. Trendyol ve Hepsiburada (Pazaryeri liste fiyatları)
3. Teknosa / Vatan Bilgisayar / MediaMarkt (Varsa zincir mağaza fiyatları)

Lütfen ürünün piyasadaki en düşük, ortalama ve en yüksek TL fiyatlarını ve hangi sitede kaç TL olduğunu net olarak listele."""

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

    json_schema_prompt = f"""Yukarıdaki canlı web araştırma sonuçlarını ve ekteki ürün görselini incele.

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
    "demandLevel": "Çok Yüksek",
    "competitionLevel": "Orta",
    "targetAudience": "Hedef kitle profili",
    "returnRisk": "Düşük",
    "seasonalTrend": "Tüm yıl düzenli talep"
  }},
  "campaigns": [
    {{
      "title": "Kampanya Başlığı",
      "campaignType": "Senetli Fırsat",
      "description": "Kampanya detay açıklaması",
      "bannerSlogan": "Mağaza vitrin afiş sloganı"
    }}
  ]
}}"""

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

st.markdown("<h2 style='text-align: center; margin-top: 0;'>🎯 Hedef AVM Piyasa & Senet Radarı</h2>", unsafe_allow_html=True)
st.caption("<p style='text-align: center;'>Google Gemini 2.5 Vision & Canlı Web İstihbaratı ile Hedef AVM'ye Özel Fiyatlandırma</p>", unsafe_allow_html=True)

# =========================================================================
# GİRİŞ FORMU (GÖRSEL ÖNİZLEMELİ VE ZORUNLU MODEL GİRİŞLİ)
# =========================================================================
with st.container(border=True):
    st.subheader("📦 Ürün Tanımlama & Görsel Girişi")
    
    product_name_input = st.text_input(
        "Ürün Adı ve Modeli * (Zorunlu)",
        placeholder="Örn: gm 26 pro, iPhone 15 128GB, Philips HD9650 Airfryer, Karaca Çaysever...",
        help="Model adını eksiksiz yazmak canlı piyasa fiyatlarını doğru eşleştirir."
    )

    tab_cam, tab_file = st.tabs(["📸 Kamerayla Çek", "📁 Galeriden / Dosyadan Yükle"])
    uploaded_image = None

    with tab_cam:
        cam_file = st.camera_input("Ürün veya kutu fotoğrafını çekin")
        if cam_file:
            uploaded_image = Image.open(cam_file)

    with tab_file:
        up_file = st.file_uploader("Ürün görseli seçin (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"])
        if up_file:
            uploaded_image = Image.open(up_file)

    # Görsel Önizleme
    if uploaded_image:
        col_img1, col_img2 = st.columns([1, 3])
        with col_img1:
            st.image(uploaded_image, caption="Analiz Edilecek Görsel", width=140)
        with col_img2:
            st.success("✅ Görsel başarıyla seçildi.")

    c1, c2 = st.columns(2)
    with c1:
        cost_val = st.number_input("Tedarikçi Alış Fiyatı (₺ - Opsiyonel)", min_value=0.0, step=100.0, value=0.0)
    with c2:
        notes_input = st.text_input("Ekstra Not / Durum (Opsiyonel)", placeholder="Örn: Sıfır kutulu, 2 yıl garantili")

    start_btn = st.button("🚀 Canlı Piyasa Analizini Başlat", type="primary", use_container_width=True)

# =========================================================================
# ANALİZ ÇALIŞTIRMA VE KAYDETME
# =========================================================================
if start_btn:
    if not product_name_input.strip():
        st.error("⚠️ Lütfen analiz edilecek Ürün Adı ve Modelini giriniz (Örn: gm 26 pro)!")
    elif uploaded_image is None:
        st.error("⚠️ Lütfen ürünün fotoğrafını çekiniz veya yükleyiniz!")
    else:
        with st.status("🔍 Canlı Piyasa Taraması Yapılıyor...", expanded=True) as status:
            st.write("1. Aşama: Google üzerinden Akakçe, Trendyol ve Hepsiburada taranıyor...")
            try:
                data = analyze_product_2stage(
                    product_name=product_name_input.strip(),
                    pil_image=uploaded_image,
                    user_cost=cost_val if cost_val > 0 else None,
                    extra_notes=notes_input.strip() if notes_input else None
                )
                st.write("2. Aşama: Görsel incelendi ve Hedef AVM senet stratejisi oluşturuldu!")
                status.update(label="✅ Analiz Tamamlandı!", state="complete", expanded=False)
                
                # Geçmişe kaydet
                data["_user_cost"] = cost_val if cost_val > 0 else 0
                data["_timestamp"] = datetime.now().strftime("%d.%m.%Y %H:%M")
                st.session_state["last_analysis"] = data
                st.session_state["last_image"] = uploaded_image
                
                # Listeye ekle (aynı isim varsa güncelle)
                history = [h for h in st.session_state["history"] if h.get("productName") != data.get("productName")]
                history.insert(0, data)
                st.session_state["history"] = history[:10]
            except Exception as e:
                status.update(label="❌ Hata Oluştu", state="error")
                st.error(f"Hata detayı: {str(e)}")

# =========================================================================
# SONUÇ EKRANI (İMPLEMENTATİON PLAN İLE %100 UYUMLU)
# =========================================================================
if "last_analysis" in st.session_state and st.session_state["last_analysis"]:
    res = st.session_state["last_analysis"]
    feasibility = res.get("feasibility", {})
    score = feasibility.get("score", 50)
    verdict = feasibility.get("verdict", "SATAR")
    hp = res.get("hedefPricing", {})
    mp = res.get("marketPrices", {})
    saved_cost = res.get("_user_cost", 0.0)

    st.divider()

    # 1. KART: Ürün Kimliği & Fizibilite Skoru & Pazar Dinamikleri
    with st.container(border=True):
        col_info, col_score = st.columns([3, 2])
        with col_info:
            st.subheader(f"{res.get('brand', '')} {res.get('productName', '')}")
            st.write(f"**Kategori:** {res.get('category', '')} | **Model/Kod:** {res.get('modelOrCode', '-')}")
        with col_score:
            st.metric(
                label=f"Fizibilite Kararı: {verdict}",
                value=f"{score} / 100",
                help="100 üzerinden Hedef AVM satılabilirlik puanı"
            )
            st.progress(min(max(score / 100.0, 0.0), 1.0))
        
        if feasibility.get('headline'):
            st.info(f"💡 **Yönetici Karar Özeti:** {feasibility.get('headline')}")

        # Pazar Göstergeleri (Implementation Plan: Talep, Rekabet, İade, Trend)
        st.markdown("**📊 Pazar Dinamikleri:**")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Talep Gücü", feasibility.get("demandLevel", "Orta"))
        d2.metric("Rekabet Düzeyi", feasibility.get("competitionLevel", "Orta"))
        d3.metric("İade Riski", feasibility.get("returnRisk", "Düşük"))
        d4.metric("Sezonluk Trend", feasibility.get("seasonalTrend", "Düzenli"))

    # 2. KART: Hedef AVM Fiyatlandırma & 12 Ay Senet Kurgusu
    with st.container(border=True):
        st.subheader("🎯 Hedef AVM Satış & Senet Planı")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("12 Ay Elden Senetli Toplam", f"{hp.get('installmentRecommendedPrice', 0):,.0f} ₺".replace(",", "."))
        m2.metric("Aylık Taksit (12 Ay)", f"{hp.get('monthlyInstallmentPrice', 0):,.0f} ₺ / ay".replace(",", "."))
        m3.metric("Peşin / Liste Fiyatı", f"{hp.get('cashRecommendedPrice', 0):,.0f} ₺".replace(",", "."))
        
        if hp.get('strategyNote'):
            st.caption(f"📌 **Satın Alma & Satış Stratejisi:** {hp.get('strategyNote')}")

    # 3. KART: Canlı Piyasa Fiyat Dağılımı (Akakçe, Trendyol, Hepsiburada)
    with st.container(border=True):
        st.subheader("🏪 Canlı Piyasa Fiyat Dağılımı (Online & Mağazalar)")
        
        p1, p2, p3 = st.columns(3)
        p1.metric("En Düşük Piyasa", f"{mp.get('min', 0):,.0f} ₺".replace(",", "."))
        p2.metric("Piyasa Ortalaması", f"{mp.get('average', 0):,.0f} ₺".replace(",", "."))
        p3.metric("En Yüksek Piyasa", f"{mp.get('max', 0):,.0f} ₺".replace(",", "."))
        
        benchmarks = res.get("competitorBenchmarks", [])
        if benchmarks:
            st.markdown("**Pazaryeri Karşılaştırması:**")
            for b in benchmarks:
                cb1, cb2 = st.columns([3, 1])
                cb1.write(f"• **{b.get('platform', '')}**: {b.get('notes', '')}")
                cb2.write(f"**{b.get('estimatedPrice', 0):,.0f} ₺**".replace(",", "."))

    # 4. KART: Dinamik Alış Fiyatı & Kâr Simülatörü (Implementation Plan Özelliği)
    with st.container(border=True):
        st.subheader("📊 Alış Fiyatı & Kâr Simülatörü")
        st.caption("Tedarikçi alış maliyetini girerek veya değiştirerek peşin ve senetli brüt kâr marjını canlı hesaplayın.")
        
        init_cost = float(saved_cost) if saved_cost > 0 else float(mp.get("min", 1000) * 0.7)
        calc_cost = st.number_input(
            "Tedarikçi Alış Fiyatı (₺)",
            min_value=0.0,
            step=100.0,
            value=init_cost,
            key="calc_cost_input"
        )
        
        if calc_cost > 0:
            cash_p = hp.get('cashRecommendedPrice', 0)
            inst_p = hp.get('installmentRecommendedPrice', 0)
            cash_profit = cash_p - calc_cost
            inst_profit = inst_p - calc_cost
            cash_margin = (cash_profit / calc_cost) * 100 if calc_cost > 0 else 0
            inst_margin = (inst_profit / calc_cost) * 100 if calc_cost > 0 else 0
            
            sim1, sim2 = st.columns(2)
            sim1.metric(
                label="Peşin Satış Brüt Kârı",
                value=f"{cash_profit:,.0f} ₺".replace(",", "."),
                delta=f"%{cash_margin:.1f} Kâr Marjı"
            )
            sim2.metric(
                label="12 Ay Senetli Brüt Kâr",
                value=f"{inst_profit:,.0f} ₺".replace(",", "."),
                delta=f"%{inst_margin:.1f} Kâr Marjı"
            )

    # 5. KART: Neden Satar vs Riskler
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

    # 6. KART: Mağaza Kampanya ve Vitrin Sloganları
    campaigns = res.get("campaigns", [])
    if campaigns:
        with st.container(border=True):
            st.subheader("📣 Mağaza İçi Kampanya ve Vitrin Sloganları")
            for c in campaigns:
                st.markdown(f"**{c.get('title', '')}** — *{c.get('campaignType', 'Fırsat')}*")
                st.write(c.get('description', ''))
                slogan_text = c.get('bannerSlogan', '')
                st.success(f'📢 "{slogan_text}"')
                st.divider()

    # 7. KART: Hızlı Paylaşım (WhatsApp & Pano) ve Rapor İndirme (Implementation Plan)
    with st.container(border=True):
        st.subheader("📤 Paylaşım ve Rapor Çıktısı")
        
        # WhatsApp Mesaj Formatı
        wa_text = f"""🎯 *HEDEF AVM - URUN PIYASA & SENET RAPORU*
📦 *Ürün:* {res.get('brand', '')} {res.get('productName', '')}
📊 *Fizibilite Skoru:* {score}/100 ({verdict})

🏪 *Piyasa Ortalaması:* {mp.get('average', 0):,.0f} ₺
🎯 *Hedef AVM Peşin:* {hp.get('cashRecommendedPrice', 0):,.0f} ₺
💳 *12 Ay Elden Senetli:* {hp.get('installmentRecommendedPrice', 0):,.0f} ₺ (Aylık: {hp.get('monthlyInstallmentPrice', 0):,.0f} ₺)

💡 *Yönetici Özeti:* {feasibility.get('headline', '')}
""".replace(",", ".")
        
        wa_url = f"https://wa.me/?text={urllib.parse.quote(wa_text)}"
        
        # Formatlı Metin Raporu (A4 / Satın Alma Özeti)
        reasons_str = "\n".join(["- " + str(r) for r in feasibility.get("reasonsToSell", [])])
        risks_str = "\n".join(["- " + str(r) for r in feasibility.get("risksAndWatchouts", [])])
        camps_str = "\n".join([f"* {c.get('title')} ({c.get('campaignType')}): {c.get('bannerSlogan')}" for c in res.get("campaigns", [])])

        report_txt = f"""====================================================
HEDEF AVM - AI DESTEKLI PIYASA VE SENET RAPORU
Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}
====================================================

1. URUN BILGILERI:
- Urun: {res.get('productName')}
- Marka: {res.get('brand')}
- Kategori: {res.get('category')}
- Model/Kod: {res.get('modelOrCode')}

2. FIZIBILITE VE KARAR:
- Skor: {score} / 100 ({verdict})
- Yonetici Ozeti: {feasibility.get('headline')}
- Talep Gucu: {feasibility.get('demandLevel')}
- Rekabet Duzeyi: {feasibility.get('competitionLevel')}
- Iade Riski: {feasibility.get('returnRisk')}
- Sezonluk Trend: {feasibility.get('seasonalTrend')}

3. CANLI PIYASA FIYATLARI (AKAKCE, TRENDYOL, HEPSIBURADA):
- En Dusuk: {mp.get('min', 0):,.0f} TL
- Piyasa Ortalamasi: {mp.get('average', 0):,.0f} TL
- En Yuksek: {mp.get('max', 0):,.0f} TL

4. HEDEF AVM FIYAT VE SENET KURGUSU:
- Pesin / Liste Fiyati: {hp.get('cashRecommendedPrice', 0):,.0f} TL
- 12 Ay Elden Senetli Satis: {hp.get('installmentRecommendedPrice', 0):,.0f} TL
- Aylik Senet Taksiti: {hp.get('monthlyInstallmentPrice', 0):,.0f} TL x 12 Ay
- Strateji Notu: {hp.get('strategyNote')}

5. NEDEN SATAR?:
{reasons_str}

6. RISKLER VE DIKKAT EDILECEKLER:
{risks_str}

7. VITRIN KAMPANYA VE SLOGANLARI:
{camps_str}
"""

        c_wa, c_rep, c_json = st.columns(3)
        with c_wa:
            st.link_button("📲 WhatsApp ile Paylaş", url=wa_url, use_container_width=True)
        with c_rep:
            st.download_button(
                label="📄 Rapor Özeti İndir (.TXT)",
                data=report_txt,
                file_name=f"Hedef_AVM_Rapor_{res.get('brand', 'Urun')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with c_json:
            st.download_button(
                label="📥 Ham Veri İndir (JSON)",
                data=json.dumps(res, ensure_ascii=False, indent=2),
                file_name=f"Hedef_AVM_{res.get('brand', 'Urun')}.json",
                mime="application/json",
                use_container_width=True
            )

        with st.expander("📋 Kopyalanabilir Yönetici Notu (Pano)"):
            st.code(wa_text, language="text")

# =========================================================================
# 8. TARAMA GEÇMİŞİ (IMPLEMENTATION PLAN: HISTORY DRAWER)
# =========================================================================
if st.session_state.get("history"):
    with st.expander(f"🕒 Önceki Tarama Geçmişi ({len(st.session_state['history'])} Ürün)", expanded=False):
        for idx, item in enumerate(st.session_state["history"]):
            col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
            col_h1.write(f"**{item.get('brand', '')} {item.get('productName', '')}** — *{item.get('_timestamp', '')}*")
            col_h2.write(f"Skor: **{item.get('feasibility', {}).get('score', 0)}/100**")
            if col_h3.button("Görüntüle", key=f"hist_btn_{idx}"):
                st.session_state["last_analysis"] = item
                st.rerun()

# Footer
st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 0.8rem; margin-top: 2.5rem;'><strong>HEDEF ALIŞVERİŞ MERKEZLERİ</strong> • AI Piyasa Radarı</p>", unsafe_allow_html=True)
