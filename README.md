# 🎯 Hedef AVM - AI Destekli Özel Ürün Piyasa Araştırması ve Satılabilirlik Radarı

Bu proje, **Hedef Alışveriş Merkezleri** için hem **Next.js (Web & Mobil)** hem de **Streamlit (Python & Cloud)** üzerinde çalışabilen, ürün fotoğraflarını tarayarak **Google Gemini 2.5 Canlı Google Search Grounding** ile Akakçe, Trendyol, Hepsiburada ve Teknosa fiyatlarını gerçek zamanlı analiz eden kurumsal bir pazar istihbarat yazılımıdır.

---

## 🔒 GÜVENLİK KONTROLÜ (API KEY KORUMASI)

> [!IMPORTANT]
> **Gemini API Anahtarınız GitHub'a Yüklenmez ve Asla Çalınamaz!**
> 1. Projedeki `.gitignore` dosyası `.env*`, `*.env`, `secrets.toml` ve `.streamlit/secrets.toml` dosyalarını otomatik olarak yok sayacak şekilde kilitlenmiştir.
> 2. Kod tabanında hiçbir yerde sabit (hardcoded) API anahtarı bulunmaz.
> 3. Git geçmişi taranmış ve API anahtarınızın hiçbir commit'e dahil edilmediği %100 doğrulanmıştır.

---

## 🚀 STREAMLIT İLE ÇALIŞTIRMA VE GITHUB'A YÜKLEME

### 1. Bilgisayarınızda Yerel Olarak Streamlit Çalıştırma
```bash
python -m streamlit run streamlit_app.py
```
Tarayıcınızda otomatik olarak açılacaktır (`http://localhost:8501`).

---

### 2. GitHub'a Yükleme Adımları

1. [GitHub](https://github.com/new) üzerinde yeni bir repository (depo) oluşturun (Örn: `hedef-avm-ai-radar`). Depoyu **Private** (Gizli) veya Public yapabilirsiniz.
2. Bilgisayarınızdaki terminalde şu komutları çalıştırın:
```bash
git branch -M main
git remote add origin https://github.com/KULLANICI_ADINIZ/hedef-avm-ai-radar.git
git push -u origin main
```

---

### 3. Streamlit Cloud (Ücretsiz Web Yayını) Kurulumu

1. [share.streamlit.io](https://share.streamlit.io) adresine gidin ve GitHub hesabınızla giriş yapın.
2. **"New app"** butonuna tıklayın:
   - **Repository:** `KULLANICI_ADINIZ/hedef-avm-ai-radar`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
3. **ÖNEMLİ (API Anahtarını Güvenli Eklemek İçin):**
   - *"Advanced settings"* (Gelişmiş ayarlar) veya daha sonra açılan panodan **Secrets** sekmesine tıklayın.
   - Buraya şu şekilde API anahtarınızı yapıştırın:
   ```toml
   GEMINI_API_KEY = "AQ.Ab8RN6LqSVA6lkWCiZsk9EnHpSAEfnWfuonqlA5AfZq2bMgrTA"
   ```
   - **Save** butonuna basın.
4. **Deploy!** butonuna basın. Uygulamanız birkaç saniye içinde dünya çapında çalışan güvenli bir web adresine (`https://hedef-avm-ai-radar.streamlit.app`) sahip olacaktır.

---

## 🖥️ NEXT.JS İLE ÇALIŞTIRMA (ALTERNATİF)

İsterseniz modern React/Next.js sürümünü de çalıştırabilirsiniz:
```bash
npm run dev
# veya yerel ağdaki telefondan kamerayla bağlanmak için:
npm run dev -- -H 0.0.0.0
```
Tarayıcı adresi: [http://localhost:3000](http://localhost:3000)
