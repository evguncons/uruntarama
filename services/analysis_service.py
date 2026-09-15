"""Server-side discovery and live verification orchestration."""
import json
import re
import base64
from datetime import datetime
from services.verification_service import OfferVerificationService
from services.models import StockStatus


PLATFORMS = ('Marka Resmi Mağazası', 'Akakçe', 'Cimri', 'Trendyol', 'Hepsiburada', 'Vatan Bilgisayar',
             'Evkur', 'Taşpınar', 'Yön AVM', 'Vivense', 'HYS AVM', 'Yiğit AVM', 'SenetSepet')


def _json(text):
    text = re.sub(r'^```(?:json)?|```$', '', text.strip(), flags=re.I).strip()
    return json.loads(text)


def analyze_product(product_name, api_key, user_cost=0, notes='', image_data=None):
    from google import genai
    from google.genai import types
    if not api_key:
        raise RuntimeError('Sunucuda GEMINI_API_KEY tanımlı değil')
    prompt = f'''Türkiye'de "{product_name}" için sadece doğrudan ürün sayfası adaylarını keşfet.
N11 ve Teknosa dahil etme. Kategori, arama ve ana sayfa URL'si verme. Fiyat ve stok hakkında karar verme.
Marka resmi sitesi, Akakçe, Cimri, Trendyol, Hepsiburada, Vatan, Evkur, Taşpınar ve Yön AVM'yi ara.
Sadece JSON döndür: {{"brand":"", "category":"", "modelOrCode":"", "candidates":[{{"merchant":"", "url":""}}]}}'''
    client = genai.Client(api_key=api_key)
    contents = [prompt]
    if image_data and ',' in image_data:
        header, encoded = image_data.split(',', 1)
        mime = header.split(';', 1)[0].split(':', 1)[-1]
        contents.append(types.Part.from_bytes(data=base64.b64decode(encoded), mime_type=mime))
    response = client.models.generate_content(
        model='gemini-2.5-flash', contents=contents,
        config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())], temperature=0))
    discovery = _json(response.text)
    candidates = [c for c in discovery.get('candidates', []) if c.get('merchant') not in ('N11', 'Teknosa')]
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
        'productName': product_name, 'brand': discovery.get('brand', ''), 'category': discovery.get('category', ''),
        'modelOrCode': discovery.get('modelOrCode', ''),
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
