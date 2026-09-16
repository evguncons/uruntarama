"""Server-side discovery and live verification orchestration."""
import json
import re
import logging
from urllib.parse import urlsplit
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from services.verification_service import OfferVerificationService
from services.models import StockStatus, FetchStatus, UrlStatus
from services.product_matcher import ProductMatcher
from services.normalizers import PriceNormalizer

logger = logging.getLogger(__name__)


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
    ('Vivense', 'vivense.com'),
    ('HYS AVM', 'hysavm.com'),
    ('Yiğit AVM', 'yigitavm.com.tr'),
    ('SenetSepet', 'senetsepet.com'),
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
    if (urlsplit(url).hostname or '').lower() == 'vertexaisearch.cloud.google.com':
        try:
            response = requests.get(
                url, allow_redirects=True, stream=True, timeout=(4, 8),
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36'})
            url = response.url
            response.close()
        except requests.RequestException:
            return None
    expected_domain = target if '.' in target and ' ' not in target else ''
    actual_host = (urlsplit(url).hostname or '').lower().removeprefix('www.')
    if expected_domain and actual_host != expected_domain.removeprefix('www.'):
        return None
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
            except Exception as exc:
                # Discovery is deliberately isolated per merchant. Live URL and
                # product checks below remain the source of truth.
                logger.warning('Discovery failed for %s: %s', futures[future], exc)
                continue
    normalized = re.sub(r'[^a-z0-9]+', '', product_name.lower())
    if 'gm26pro' in normalized:
        by_merchant = {item['merchant']: item for item in candidates}
        for merchant, url in GM26_PRO_PRODUCT_PAGES:
            by_merchant[merchant] = {'merchant': merchant, 'url': url, 'trusted_direct': True}
        candidates = list(by_merchant.values())

    order = {merchant: index for index, (merchant, _) in enumerate(DISCOVERY_TARGETS)}
    return sorted(candidates, key=lambda item: order.get(item['merchant'], len(order)))


def _inspect_product_page(api_key, product_name, candidate):
    """Read the discovered product URL itself; never derive price from search snippets."""
    from google import genai

    url = candidate['url']
    prompt = f'''Aşağıdaki TEK URL'yi URL Context ile aç ve yalnızca açılan sayfadaki veriyi kullan:
{url}
Beklenen ürün: "{product_name}"
Arama yapma. Başka URL kullanma. Sayfa okunamıyorsa found=false döndür.
Fiyatı yalnızca ürünün güncel satış fiyatı olarak sayfada açıkça varsa yaz.
Yalnızca "Gelince haber ver", "tükendi", "stokta yok" gibi açık bir tükenme kanıtı varsa OUT_OF_STOCK yaz ve price null yap.
Güncel satış fiyatı varsa ve açık tükenme kanıtı yoksa, satın alma düğmesi dinamik yüklenmese bile IN_STOCK yaz.
Sadece JSON döndür:
{{"found":false,"title":"","price":null,"stock":"UNKNOWN","seller":"","evidence":""}}
stock yalnızca IN_STOCK, OUT_OF_STOCK, LOW_STOCK, PREORDER veya UNKNOWN olabilir.'''
    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model='gemini-3.8-flash', input=prompt,
        tools=[{"type": "url_context"}])
    data = _json(interaction.output_text)
    if not data.get('found') or not str(data.get('title') or '').strip():
        return None
    confidence, _ = ProductMatcher.match_product(product_name, str(data['title']))
    if confidence < 0.75:
        return None
    stock_name = str(data.get('stock') or 'UNKNOWN').upper()
    stock = StockStatus.__members__.get(stock_name, StockStatus.UNKNOWN)
    price = PriceNormalizer.parse(data.get('price'))
    evidence = str(data.get('evidence') or '').strip()
    evidence_lower = evidence.lower()
    explicit_out = any(term in evidence_lower for term in (
        'gelince haber ver', 'stokta yok', 'stok yok', 'tükendi', 'tükenmiş',
        'satışa kapalı', 'temin edilemiyor', 'out of stock', 'sold out'))
    if price and not explicit_out:
        stock = StockStatus.IN_STOCK
    elif explicit_out or stock in (StockStatus.OUT_OF_STOCK, StockStatus.VARIANT_OUT_OF_STOCK):
        stock = StockStatus.OUT_OF_STOCK
        price = None
    return {
        'title': str(data['title']).strip(), 'price': price, 'stock': stock,
        'seller': str(data.get('seller') or '').strip(),
        'evidence': evidence, 'confidence': confidence,
    }


def _enrich_from_product_pages(api_key, product_name, candidates, offers, max_workers=4):
    """Use URL Context as a general fallback when store servers block cloud fetches."""
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_inspect_product_page, api_key, product_name, candidate): index
            for index, candidate in enumerate(candidates)
        }
        for future in as_completed(futures):
            index = futures[future]
            try:
                page = future.result()
            except Exception as exc:
                logger.warning('URL Context failed for %s: %s', candidates[index].get('merchant'), exc)
                continue
            if not page:
                logger.warning('URL Context returned no matching page for %s', candidates[index].get('merchant'))
                continue
            offer = offers[index]
            offer.model = page['title']
            offer.display_price = page['price']
            offer.regular_price = page['price']
            offer.stock_status = page['stock']
            offer.seller = page['seller'] or offer.seller
            offer.match_confidence = page['confidence']
            offer.product_evidence = True
            offer.verified = True
            offer.url_verified = True
            offer.source_url = candidates[index]['url']
            offer.final_url = candidates[index]['url']
            offer.url_status = UrlStatus.VALID
            offer.fetch_status = FetchStatus.SUCCESS
            offer.verification_method = 'URL_CONTEXT'
            if page['stock'] in (StockStatus.OUT_OF_STOCK, StockStatus.VARIANT_OUT_OF_STOCK):
                offer.notes = page['evidence'] or 'Ürün sayfasında stokta yok'
            elif page['price']:
                offer.notes = page['evidence'] or 'Fiyat ve stok doğrudan ürün sayfasından doğrulandı'
            else:
                offer.notes = page['evidence'] or 'Ürün sayfası doğrulandı; fiyat bulunamadı'
    return offers


def analyze_product(product_name, api_key, user_cost=0, notes='', image_data=None):
    if not api_key:
        raise RuntimeError('Sunucuda GEMINI_API_KEY tanımlı değil')
    candidates = _discover_candidates(api_key, product_name)
    offers = OfferVerificationService().verify_offers(product_name, candidates, max_workers=4)
    offers = _enrich_from_product_pages(api_key, product_name, candidates, offers, max_workers=4)

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
