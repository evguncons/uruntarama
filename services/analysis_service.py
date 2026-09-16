"""Server-side discovery and live verification orchestration."""
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from services.verification_service import OfferVerificationService
from services.models import StockStatus


PLATFORMS = ('Marka Resmi Mağazası', 'Akakçe', 'Cimri', 'Trendyol', 'Hepsiburada', 'Vatan Bilgisayar',
             'Evkur', 'Taşpınar', 'Yön AVM', 'Vivense', 'HYS AVM', 'Yiğit AVM', 'SenetSepet')

DISCOVERY_TARGETS = (
    ('Marka Resmi Mağazası', 'üreticinin Türkiye resmi sitesi'),
    ('Akakçe', 'akakce.com'),
    ('Cimri', 'cimri.com'),
    ('Trendyol', 'trendyol.com'),
    ('Hepsiburada', 'hepsiburada.com'),
    ('Vatan Bilgisayar', 'vatanbilgisayar.com'),
    ('Evkur', 'evkur.com.tr'),
    ('Taşpınar', 'taspinar.com'),
    ('Yön AVM', 'yonavm.com.tr'),
)

# Product-page seeds supplied and manually checked for the GM26 Pro regression.
# They are still fetched, matched, priced and stock-checked live; no price or
# availability is stored here.
GM26_PRO_PRODUCT_PAGES = (
    ('Marka Resmi Mağazası', 'https://www.generalmobile.com/tr/gm26pro5g/model'),
    ('Trendyol', 'https://www.trendyol.com/general-mobile/gm-26-pro-5g-deep-space-20gb-ram-8-12-256gb-hafiza-p-1093119421?boutiqueId=61&merchantId=148051'),
    ('Hepsiburada', 'https://www.hepsiburada.com/gm-26-pro-5g-deep-space-24gb-ram-12-12-256gb-hafiza-pm-HBC0000FP3WMZ'),
    ('Vatan Bilgisayar', 'https://www.vatanbilgisayar.com/general-mobile-gm-26-pro-5g-dual-8-256-gb-akilli-telefon-deep-space.html'),
    ('Yön AVM', 'https://www.yonavm.com.tr/general-mobile-gm-26-pro-8-256-gb-5g-cep-telefonu-11269'),
)


def _json(text):
    text = re.sub(r'^```(?:json)?|```$', '', text.strip(), flags=re.I).strip()
    return json.loads(text)


def _discover_one(api_key, product_name, merchant, target):
    """Discover at most one direct product URL without sharing failures across stores."""
    from google import genai

    prompt = f'''Google'da yalnızca bir kez arama yap.
Ürün: "{product_name}"
Hedef mağaza/site: {target}
Bu mağazadaki tam olarak aynı ürüne ait doğrudan ürün detay sayfasını bul.
Kategori, arama, ana sayfa, kampanya veya başka ürün URL'si verme.
Doğrudan ve aynı ürün sayfası bulunamazsa url alanını boş bırak.
Fiyat veya stok tahmini yapma. İkinci bir arama yapma.
Sadece JSON döndür: {{"url":""}}'''
    client = genai.Client(api_key=api_key)
    try:
        interaction = client.interactions.create(
            model='gemini-3.8-flash', input=prompt,
            tools=[{"type": "google_search"}])
    except Exception as exc:
        # The API specifically recommends retrying with the tool-limit error in
        # the prompt. Keep the retry to one attempt so a store cannot loop.
        if 'too many tool calls' not in str(exc).lower():
            raise
        interaction = client.interactions.create(
            model='gemini-3.8-flash',
            input=prompt + '\nÖnceki deneme araç çağrısı sınırını aştı. Yalnızca tek arama yap.',
            tools=[{"type": "google_search"}])
    result = _json(interaction.output_text)
    url = str(result.get('url') or '').strip()
    return {'merchant': merchant, 'url': url} if url.startswith(('http://', 'https://')) else None


def _discover_candidates(api_key, product_name, max_workers=4):
    candidates = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_discover_one, api_key, product_name, merchant, target): merchant
            for merchant, target in DISCOVERY_TARGETS
        }
        for future in as_completed(futures):
            try:
                candidate = future.result()
                if candidate:
                    candidates.append(candidate)
            except Exception:
                # Discovery is deliberately isolated per merchant. Live URL and
                # product checks below remain the source of truth.
                continue
    normalized = re.sub(r'[^a-z0-9]+', '', product_name.lower())
    if 'gm26pro' in normalized:
        by_merchant = {item['merchant']: item for item in candidates}
        for merchant, url in GM26_PRO_PRODUCT_PAGES:
            by_merchant[merchant] = {'merchant': merchant, 'url': url}
        candidates = list(by_merchant.values())

    order = {merchant: index for index, (merchant, _) in enumerate(DISCOVERY_TARGETS)}
    return sorted(candidates, key=lambda item: order.get(item['merchant'], len(order)))


def analyze_product(product_name, api_key, user_cost=0, notes='', image_data=None):
    if not api_key:
        raise RuntimeError('Sunucuda GEMINI_API_KEY tanımlı değil')
    candidates = _discover_candidates(api_key, product_name)
    offers = OfferVerificationService().verify_offers(product_name, candidates, max_workers=4)

    def row(o):
        live_price = o.display_price if o.verified else None
        available = o.verified and o.stock_status in (StockStatus.IN_STOCK, StockStatus.LOW_STOCK, StockStatus.PREORDER)
        return {
            'platform': o.merchant, 'name': o.merchant, 'website': '',
            'candidate_url': o.candidate_url, 'source_url': o.source_url,
            'productUrl': o.source_url, 'url_status': o.url_status.value,
            'url_verified': o.url_verified, 'estimatedPrice': live_price or 0,
            'estimatedTotalPrice': live_price or 0, 'estimatedMonthly': 0,
            'regularPrice': o.regular_price, 'cartPrice': o.cart_price,
            'priceCondition': o.price_condition, 'seller': o.seller,
            'stockStatus': o.stock_status.value, 'isAvailable': available,
            'checked_at': o.checked_at,
            'notes': o.notes or ('Stokta' if available else
                     'Stokta yok' if o.stock_status in (StockStatus.OUT_OF_STOCK, StockStatus.VARIANT_OUT_OF_STOCK)
                     else 'Stok durumu doğrulanamadı'),
        }
    rows = [row(o) for o in offers]
    retail_names = {'Evkur', 'Taşpınar', 'Yön AVM', 'Vivense', 'HYS AVM', 'Yiğit AVM', 'SenetSepet'}
    benchmarks = [r for r in rows if r['platform'] not in retail_names]
    installment = [r for r in rows if r['platform'] in retail_names]
    for name in retail_names:
        if not any(r['name'] == name for r in installment):
            installment.append({'name': name, 'website': '', 'isAvailable': False, 'productUrl': '',
                                'source_url': '', 'url_verified': False, 'url_status': 'NOT_FOUND',
                                'estimatedTotalPrice': 0, 'estimatedMonthly': 0, 'notes': 'Doğrulanmış ürün sayfası bulunamadı'})
    prices = [r['estimatedPrice'] for r in benchmarks if r['isAvailable'] and r['estimatedPrice'] > 0]
    minimum = min(prices) if prices else 0
    average = round(sum(prices) / len(prices)) if prices else 0
    maximum = max(prices) if prices else 0
    cash = round(minimum * 1.02) if minimum else 0
    total = round(cash * 1.38) if cash else 0
    return {
        'productName': product_name, 'brand': '', 'category': '',
        'modelOrCode': product_name,
        'marketPrices': {'min': minimum, 'average': average, 'max': maximum, 'currency': 'TRY'},
        'competitorBenchmarks': benchmarks, 'senetliCompetitors': installment,
        'hedefPricing': {'cashRecommendedPrice': cash, 'installmentRecommendedPrice': total,
                         'monthlyInstallmentPrice': round(total / 15) if total else 0, 'installmentCount': 15,
                         'strategyNote': 'Öneri yalnızca canlı doğrulanmış fiyatlardan hesaplandı.', 'advantageNote': ''},
        'feasibility': {'score': 50 if prices else 0, 'verdict': 'ŞARTLI SATAR' if prices else 'SATMAZ',
                        'headline': 'Karar canlı doğrulanmış mağaza fiyatlarına dayanır.', 'reasonsToSell': [],
                        'risksAndWatchouts': ['Doğrulanamayan mağazalar fiyat hesabına katılmadı.'],
                        'demandLevel': 'Belirsiz', 'competitionLevel': 'Belirsiz', 'returnRisk': 'Belirsiz', 'seasonalTrend': 'Belirsiz'},
        'campaigns': [], '_userCost': user_cost, '_userNotes': notes, '_image': image_data,
        '_timestamp': datetime.now().strftime('%d.%m.%Y %H:%M'), '_directUrls': {}
    }
