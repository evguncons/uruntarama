# Ürün sayfasından fiyat doğrulaması

Aktif pazaryeri/perakende radarları `app.py` ve `streamlit_app.py` tarafından gösterilen `index.html` içindedir. Her iki giriş aynı `radar_component.py` köprüsünü ve `radar.py` doğrulamasını kullanır. `src/` altındaki ayrı Next.js prototipi bu radar ekranını sunmaz.

## Çalıştırma

```sh
pip install -r requirements.txt
streamlit run app.py
```

HTML tek başına açıldığında sunucu doğrulaması çalışmaz. Streamlit üzerinden açılmalıdır.

## Veri kuralları

- Google yalnızca aday ürün adreslerini keşfeder. Arama metnindeki fiyat ve stok bilgileri kullanılmaz.
- Kaynak yönlendirmesinin son hedefi mağaza alan adı ve ürün yolu açısından kontrol edilir. Kategori/arama bağlantısı gösterilmez.
- Ürün başlığı/modeli eşleşmeden fiyat veya bağlantı yayımlanmaz. GM26 ile GM260, GM26 ile GM26 Pro ve aksesuarlar birbirinden ayrılır.
- Fiyat ve stok aynı ürün sayfasındaki Product/Offer verisinden okunur. Birden fazla farklı teklif belirsizse fiyat verilmez. AggregateOffer en düşük fiyatı kullanılmaz.
- General Mobile model seçenekleri kendi fiyat/stok bloklarından okunur. Yön AVM gelince haber ver uyarısı satış fiyatını bastırır.
- `in_stock`, `out_of_stock`, `unverified`, `mismatch` ayrı durumlardır. HTTP/erişim hatası stokta yok anlamına gelmez.
- Model raporu mağaza fiyatını değiştiremez; 15 ay çarpanı ve fiyat tavanı uygulanmaz. Rakiplerin doğrulanmamış taksitleri türetilmez.
- n11 ve Teknosa kaynak listesinde yoktur. Vatan ayrı kaynaktır.
- Fiyatlar kontrol anına aittir; satıcı, varyant veya sonraki fiyat değişiklikleri mümkündür. Kontrol zamanı ve okunan varyant kartta gösterilir. Eski doğrulanmamış geçmiş raporları yeniden analiz gerektirir.

## Test

```sh
python -m unittest discover -s tests -v
python scripts/check_radar_live.py
```

15 Eylül 2026 yerel GM26 Pro uçtan uca analizinde Trendyol 22.880 TL, Hepsiburada 23.499 TL, Vatan 24.999 TL, General Mobile stoktaki 24GB/256GB seçenek 26.999 TL okundu. Trendyol ve Hepsiburada tarayıcı sayfalarıyla karşılaştırıldı. Yön AVM fiyatı bastırıldı; GM26 8/128GB Taşpınar sayfası model uyuşmazlığı, Cimri cep telefonları sayfası kategori olarak reddedildi. Bunlar sabit fiyat verisi değil, test anındaki sonuçlardır.

Yeni siteler farklı sayfa yapısı kullandığında yeni ayrıştırıcı gerekebilir; doğrulanamayan sitelerde tahmini fiyat yayımlanmaz. Resmî mağazalar `OFFICIAL_DOMAINS` izin listesiyle sınırlıdır; yeni marka alan adları doğrulandıktan sonra eklenmelidir.
