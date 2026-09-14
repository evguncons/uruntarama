# 🎯 Hedef AVM - AI Destekli Özel Ürün Piyasa Araştırması ve Satılabilirlik Radarı

Bu yazılım, **Hedef AVM** mağazaları, satın alma ekipleri ve e-ticaret operasyonları için geliştirilmiş; mobil ve masaüstü uyumlu, ürün fotoğraflarını tarayarak saniyeler içinde **Google Gemini 2.5 Flash Vision** yapay zeka motoru ile Türkiye perakende piyasa analizi, rakip fiyat benchmarkı, **elden senetli ve peşin fiyat stratejisi**, "Satar / Satmaz" fizibilite puanı ve kampanya önerileri üreten profesyonel bir pazar istihbarat platformudur.

---

## 🚀 Öne Çıkan Özellikler

- 📸 **Mobil & Masaüstü Canlı Kamera ve Galeri Entegrasyonu:**
  - Mobil cihazlarda tek dokunuşla arka kamerayı açıp ürünü veya kutu barkodunu çekebilme.
  - Canlı kamera vizörü (WebRTC) veya yerel dosya seçici / sürükle-bırak desteği.
  - İstemci taraflı otomatik görsel optimizasyonu (mobil internet kotasını korur ve yükleme süresini 0.5 saniyenin altına indirir).

- 🧠 **Google Gemini 2.5 AI Analiz Motoru:**
  - **Ürün Tespiti:** Marka, model, seri, kategori, teknik özellikler ve barkod okuma.
  - **Piyasa Fiyat Dağılımı:** Trendyol, Hepsiburada, Amazon TR ve zincir mağazalardaki güncel min, ortalama ve max fiyatlar.
  - **Hedef AVM Taksit & Senet Stratejisi:** Peşin liste fiyatı ve Hedef AVM'ye özel 12-15 ay vadeli elden senetli toplam satış ve aylık taksit hesaplama.
  - **"Satar mı / Satmaz mı?" Fizibilite Kararı:** 0-100 Satılabilirlik Puanı, talep seviyesi, pazar rekabeti, mevsimsellik ve iade riski analizi.
  - **Somut Nedenler & Riskler:** Ürünün mağazada neden satacağı ve dikkat edilmesi gereken riskler (2 sütunlu detaylı fizibilite).
  - **Kampanya ve Reklam Sloganları:** Mağaza içi vitrin, çeyiz paketi, afiş ve sosyal medya reklam sloganı önerileri.

- 🧮 **Kârlılık ve Marj Simülatörü:**
  - Kullanıcı tedarikçi alış maliyetini girdiğinde, anında peşin ve vadeli senetli brüt kâr (₺) ve kâr marjını (%) hesaplar.

- 📄 **Raporlama ve Paylaşım:**
  - **PDF Rapor İndir:** Tek tıkla yönetim ve satın alma için A4 kurumsal analiz raporu oluşturur.
  - **WhatsApp Paylaş:** Mağaza çalışanlarının tek dokunuşla WhatsApp üzerinden satın alma birimine formatlı özet göndermesini sağlar.
  - **Tarama Geçmişi:** Yapılan tüm taramalar tarayıcıda saklanır, aranabilir ve tekrar incelenebilir.

- 🛡️ **Kurumsal Güvenlik:**
  - `GEMINI_API_KEY` sunucu tarafında (`.env.local`) saklanır, hiçbir istemci koduna sızdırılmaz.
  - MIME-type doğrulaması ve 10MB dosya boyutu sınırı ile güvenli yükleme mimarisi.

---

## 🛠️ Kurulum ve Çalıştırma

### 1. Ortam Değişkenleri
Proje kök dizinindeki `.env.local` dosyasına Gemini API anahtarınızı ekleyin:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Geliştirme Sunucusunu Başlatma
```bash
npm run dev
```
Tarayıcınızda [http://localhost:3000](http://localhost:3000) adresini açın.

### 3. Cep Telefonundan veya Mağaza Tabletinden Bağlanma
Telefonunuzla aynı Wi-Fi ağına bağlıyken bilgisayarınızın yerel IP adresinden erişmek için:
```bash
npm run dev -- -H 0.0.0.0
```
Telefon tarayıcınızdan `http://[BILGISAYAR_IP_ADRESINIZ]:3000` adresine girerek kamerayı doğrudan test edebilirsiniz.

### 4. Prodüksiyon Derlemesi
```bash
npm run build
npm start
```
