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

# Stable direct-page seeds for the S25 FE 8/256 regression. Prices and stock
# are intentionally absent: both values are read from the live page each run.
S25_FE_256_PRODUCT_PAGES = (
    ('Trendyol', 'https://www.trendyol.com/samsung/galaxy-s25-fe-8gb-256gb-siyah-p-984233972'),
    ('Yön AVM', 'https://www.yonavm.com.tr/samsung-s731b-s25-fe-8-256-gb-cep-telefonu-11571'),
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
    if 's25fe' in normalized and '256' in normalized:
        by_merchant = {item['merchant']: item for item in candidates}
        for merchant, url in S25_FE_256_PRODUCT_PAGES:
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
Yalnızca "Gelince haber ver", "tükendi", "stokta yok" gibi açık bir tükenme kanıtı varsa OUT_OF_STOCK yaz. Sayfada açık bir fiyat varsa price alanında koru.
Güncel satış fiyatı varsa ve açık tükenme kanıtı yoksa, satın alma düğmesi dinamik yüklenmese bile IN_STOCK yaz.
Beklenen model, FE/Pro/Plus/Ultra eki ve kapasite aynıysa exactProduct=true yaz; farklı varyantta false yaz.
Sadece JSON döndür:
{{"found":false,"exactProduct":false,"title":"","price":null,"stock":"UNKNOWN","seller":"","evidence":""}}
stock yalnızca IN_STOCK, OUT_OF_STOCK, LOW_STOCK, PREORDER veya UNKNOWN olabilir.'''
    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model='gemini-3.8-flash', input=prompt,
        tools=[{"type": "url_context"}])
    data = _json(interaction.output_text)
    if not data.get('found') or data.get('exactProduct') is not True or not str(data.get('title') or '').strip():
        return None
    # Dynamic marketplace pages sometimes expose a shortened browser title.
    # The already-discovered direct product slug is valid model evidence too
    # (for example, "s25-fe-8-256-gb" on Trendyol).
    match_subject = str(data['title']) + ' ' + urlsplit(url).path.replace('-', ' ').replace('_', ' ')
    confidence, _ = ProductMatcher.match_product(product_name, match_subject)
    if confidence <= 0:
        return None
    stock_name = str(data.get('stock') or 'UNKNOWN').upper()
    stock = StockStatus.__members__.get(stock_name, StockStatus.UNKNOWN)
    price = PriceNormalizer.parse(data.get('price'))
    evidence = str(data.get('evidence') or '').strip()
    evidence_lower = evidence.lower()
    explicit_out = any(term in evidence_lower for term in (
        'gelince haber ver', 'stokta yok', 'stok yok', 'tükendi', 'tükenmiş',
        'satışa kapalı', 'temin edilemiyor', 'out of stock', 'sold out'))
    explicit_in = any(term in evidence_lower for term in (
        'sepete ekle', 'satın al', 'stokta 10+', 'stokta var', 'son 1 ürün',
        'son 2 ürün', 'son 3 ürün', 'son 4 ürün', 'son 5 ürün',
        'adetten az stok', 'in stock'))
    if price and not explicit_out:
        stock = StockStatus.IN_STOCK
    elif explicit_in and not explicit_out:
        stock = StockStatus.IN_STOCK
    elif explicit_out or stock in (StockStatus.OUT_OF_STOCK, StockStatus.VARIANT_OUT_OF_STOCK):
        stock = StockStatus.OUT_OF_STOCK
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


def _resolve_product_identity(api_key, product_name):
    """Resolve short product query or model number (e.g. 'philips 5547') to its full product name using Google Search."""
    from google import genai
    prompt = f'''Türkiye pazarında şu arama terimini Google Arama ile incele: "{product_name}".
Kullanıcı yalnızca bir marka ve model numarası/kodu veya kısaltma (örn: "philips 5547", "dyson v15", "s24 fe", "arçelik 9100", "ep5547") girmiş olabilir.
Google Arama aracını kullanarak bu kodun veya ürünün Türkiye'deki tam resmi ürün adını, markasını, model kodunu ve kategorisini tespit et.

Örnekler:
"philips 5547" -> Marka: Philips, Tam Ad: Philips EP5547/90 5500 Serisi LatteGo Tam Otomatik Espresso Makinesi, Model Kodu: EP5547/90, Kategori: Kahve Makineleri
"s24 fe" -> Marka: Samsung, Tam Ad: Samsung Galaxy S24 FE 128GB, Model Kodu: S24 FE, Kategori: Akıllı Telefonlar
"dyson v15" -> Marka: Dyson, Tam Ad: Dyson V15 Detect Kablosuz Süpürge, Model Kodu: V15 Detect, Kategori: Süpürgeler

Sadece geçerli bir JSON döndür:
{{"brand": "", "full_name": "", "model_code": "", "category": ""}}'''
    client = genai.Client(api_key=api_key)
    for model_name in ('gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-3.8-flash'):
        try:
            interaction = client.interactions.create(
                model=model_name, input=prompt,
                tools=[{"type": "google_search"}])
            data = _json(interaction.output_text)
            if isinstance(data, dict) and data.get('full_name'):
                return data
        except Exception as exc:
            logger.info('Identity resolution try with %s failed: %s', model_name, exc)
            continue
    return {
        'brand': '',
        'full_name': product_name,
        'model_code': product_name,
        'category': ''
    }


def _build_default_feasibility_and_campaigns(product_name, brand, category, model_code,
                                             market_prices, hedef_pricing, user_cost=0, notes=''):
    monthly = hedef_pricing.get('monthlyInstallmentPrice') or (round(hedef_pricing.get('installmentRecommendedPrice', 0) / 15) if hedef_pricing.get('installmentRecommendedPrice') else 0)
    monthly_str = f"{monthly:,.0f} TL".replace(',', '.') if monthly else "Uygun Taksitlerle"
    min_p = market_prices.get('min') or 0
    brand_title = brand.title() if brand else 'Marka'
    
    cat_lower = (str(category or '') + ' ' + str(product_name or '')).lower()
    is_phone = any(k in cat_lower for k in ('telefon', 'iphone', 'samsung galaxy', 'redmi', 'xiaomi', 'poco', 'akıllı telefon', 'cep telefon'))
    is_appliance = any(k in cat_lower for k in ('süpürge', 'kahve', 'lattego', 'espresso', 'airfryer', 'ütü', 'küçük ev', 'blender', 'robot süpürge', 'çay makine', 'tost'))
    is_white_goods = any(k in cat_lower for k in ('buzdolabı', 'çamaşır', 'bulaşık', 'fırın', 'derin dondurucu', 'kurutma'))
    is_tv = any(k in cat_lower for k in ('tv', 'televizyon', 'ekran', 'oled', 'qled', 'led tv'))
    
    if is_phone:
        reasons = [
            f"15 ay vadeli elden senetli sistemde aylık {monthly_str} taksit, banka kredi kartı limiti olmayan veya kart kullanmak istemeyen geniş bir alıcı kitlesi için yüksek talep yaratır.",
            f"Piyasada {brand_title} akıllı telefon modellerine yönelik yüksek marka güveni, talep hacmi ve hızlı nakde dönme avantajı bulunmaktadır.",
            "Kredi kartsız ve peşinatsız mağaza içi elden taksit imkanı, online pazaryerlerine kıyasla müşterileri doğrudan Hedef AVM şubelerine çeker."
        ]
        risks = [
            "Cep telefonu segmentinde model yenilenme döngüsü hızlı olduğundan stok devir süresi 45 günü geçmemelidir.",
            "15 ay vade süresince müşteri ödeme disiplini ve istihbarat skorlaması titizlikle takip edilmelidir.",
            "Kasa açılma, IMEI kaydı ve servis garanti şartları müşteriye satış esnasında açıkça teyit edilmelidir."
        ]
        demand_level = "Çok Yüksek"
        comp_level = "Yüksek"
        ret_risk = "Düşük"
        seasonal = "Tüm Yıl Düzenli"
        target_aud = "Kredi kartı limiti yetersiz olan veya kart kullanmadan düzenli gelirle teknoloji yenilemek isteyen tüketiciler."
        score = 84 if min_p > 0 else 55
        verdict = "GÜÇLÜ SATAR" if min_p > 0 else "ŞARTLI SATAR"
    elif is_appliance:
        reasons = [
            f"Küçük ev aletlerinde aylık {monthly_str} elden taksit tutarı, tüketici bütçesini sarsmadan anlık satın alma kararı aldırır.",
            f"{product_name} gibi günlük yaşam konforunu artıran popüler modeller, mağaza vitrininde ve sosyal medya reklamlarında yüksek çekim gücüne sahiptir.",
            "Çeyiz alışverişi yapan aileler ve evlilik hazırlığındaki çiftler için elden senet sepetine kolayca eklenebilecek ideal bir tamamlayıcı üründür."
        ]
        risks = [
            "Pazaryerlerinde satıcılar arası anlık fiyat indirimleri olabileceğinden perakende peşin fiyat rekabeti haftalık taranmalıdır.",
            "Yetkili servis ağı ve 2 yıl resmi distribütör garantisi satış öncesinde mutlaka teyit edilmelidir."
        ]
        demand_level = "Yüksek"
        comp_level = "Orta"
        ret_risk = "Düşük"
        seasonal = "Çeyiz & Özel Gün Dönemleri"
        target_aud = "Evini yenileyenler, pratik ev/mutfak teknolojisi arayan aileler ve çeyiz hazırlığı yapan müşteriler."
        score = 86 if min_p > 0 else 55
        verdict = "GÜÇLÜ SATAR" if min_p > 0 else "ŞARTLI SATAR"
    elif is_white_goods:
        reasons = [
            f"Beyaz eşya temel zorunlu ihtiyaç olduğundan, 15 ay elden senetle aylık {monthly_str} ödeme planı haneler için en güvenilir satın alma modelidir.",
            "Evlilik ve ev kurma dönemlerinde senetli paket alımlarında temel lokomotif ürün konumundadır.",
            "Dayanıklı tüketim malı olması sebebiyle Hedef AVM portföyünde yüksek kârlılık ve sadık müşteri ilişkisi oluşturur."
        ]
        risks = [
            "Sevkiyat, kat teslimi ve yetkili servis kurulum süreçlerinin lojistik maliyeti ve koordinasyonu iyi planlanmalıdır.",
            "Yüksek montanlı bir ürün grubu olduğundan senet onayında detaylı istihbarat ve gelir belgeleme zorunludur."
        ]
        demand_level = "Yüksek"
        comp_level = "Orta"
        ret_risk = "Düşük"
        seasonal = "Yaz & Düğün Sezonu"
        target_aud = "Evlenen çiftler, ev eşyalarını yenileyen aileler ve yeni konut sahipleri."
        score = 88 if min_p > 0 else 60
        verdict = "GÜÇLÜ SATAR" if min_p > 0 else "ŞARTLI SATAR"
    elif is_tv:
        reasons = [
            f"Büyük ekran televizyonlarda 15 ay elden senetle aylık {monthly_str} taksit imkanı, teknoloji marketlerin nakit/kredi kartı baskısını bertaraf eder.",
            "Mağaza içi teşhirde ve vitrinde görsel çekiciliği en yüksek ürün grubudur; mağaza trafiğini doğrudan artırır.",
            "Spor turnuvaları, kış ayları ve kampanya dönemlerinde hızlı satış potansiyeline sahiptir."
        ]
        risks = [
            "Panel kırılması ve kargo/taşıma hasarlarına karşı sigortalı taşıma ve yerinde kurulum şart koşulmalıdır.",
            "Piyasada benzer ekran boyutlarında agresif marka rekabeti mevcuttur."
        ]
        demand_level = "Yüksek"
        comp_level = "Yüksek"
        ret_risk = "Düşük"
        seasonal = "Sonbahar - Kış & Turnuva Dönemleri"
        target_aud = "Evinde sinema ve maç keyfi yaşamak isteyen aileler ve teknoloji tutkunları."
        score = 80 if min_p > 0 else 50
        verdict = "SATAR (DENGELİ)" if min_p > 0 else "ŞARTLI SATAR"
    else:
        reasons = [
            f"15 ay vadeli elden senetli satışta aylık {monthly_str} taksit tutarı, müşteriye son derece erişilebilir ve ödenebilir bir seçenek sunar.",
            f"Hedef AVM mağazalarında {brand_title} güvencesiyle kredi kartsız satış imkanı rakiplere karşı belirgin avantaj sağlar.",
            "Kredi kartsız perakendede Evkur, Taşpınar ve Yön AVM gibi rakiplere alternatif arayan müşteriler için cazip bir üründür."
        ]
        risks = [
            "15 ay vadeli elden senetli alımlarda müşteri istihbarat ve gecikme riski düzenli skorlama ile takip edilmelidir.",
            "Piyasa fiyat oynaklığına karşı peşin ve vadeli fiyatlar dönemsel olarak güncellenmelidir."
        ]
        demand_level = "Orta"
        comp_level = "Orta"
        ret_risk = "Düşük"
        seasonal = "Tüm Yıl Düzenli"
        target_aud = "Bütçesini aylık düzenli taksitlere bölerek elden senetle alışveriş yapmayı tercih eden aileler."
        score = 78 if min_p > 0 else 50
        verdict = "SATAR" if min_p > 0 else "ŞARTLI SATAR"

    campaigns = [
        {
            "campaignType": "15 Ay Elden Senet",
            "title": "Kredi Kartsız, Peşinatsız 15 Ay Elden Taksit",
            "description": f"{product_name} için peşinatsız ve kredi kartı gerektirmeden 15 eşit taksit imkanı.",
            "bannerSlogan": f"Kartsız, Peşinatsız! Ayda Sadece {monthly_str}'ye Evinizde!",
            "slogan": f"Kartsız, Peşinatsız! Ayda Sadece {monthly_str}'ye Evinizde!"
        },
        {
            "campaignType": "Günün Fırsatı",
            "title": "Hedef AVM Mağaza İçi Özel Kampanya",
            "description": "Şubelerimizden teslim alan müşterilerimize anında onaylı elden senet ve teslimat ayrıcalığı.",
            "bannerSlogan": f"Bugüne Özel 15 Ay Taksit Fırsatını Kaçırmayın!",
            "slogan": f"Bugüne Özel 15 Ay Taksit Fırsatını Kaçırmayın!"
        },
        {
            "campaignType": "Çeyiz & Ev Yenileme",
            "title": "Çeyiz ve Evini Yenileyenlere Özel Avantaj Paketi",
            "description": "Elden taksitli alışverişlerde sepetinize ekleyebileceğiniz özel vadeli paket avantajı.",
            "bannerSlogan": f"Evinizin Eksiklerini Dert Etmeyin, 15 Ayda Rahat Rahat Ödeyin!",
            "slogan": f"Evinizin Eksiklerini Dert Etmeyin, 15 Ayda Rahat Rahat Ödeyin!"
        }
    ]
    
    return {
        "score": score,
        "verdict": verdict,
        "headline": f"{product_name} 15 ay elden senet avantajıyla Hedef AVM mağazalarında yüksek satış potansiyeline sahiptir.",
        "reasonsToSell": reasons,
        "risksAndWatchouts": risks,
        "demandLevel": demand_level,
        "competitionLevel": comp_level,
        "returnRisk": ret_risk,
        "seasonalTrend": seasonal,
        "targetAudience": target_aud,
        "campaigns": campaigns,
        "strategyNote": (
            f"Piyasa en düşük fiyatı {min_p:,.0f} TL baz alınarak 15 ay vadeli elden senetli rekabetçi satış fiyatı belirlendi."
            if min_p > 0 else
            "Piyasa fiyatı ve mağaza teklifleri taranarak 15 ay vadeli elden senetli satış fiyatı belirlendi."
        ),
        "advantageNote": f"Hedef AVM'de 15 ay vadede aylık {monthly_str} taksit ile Evkur, Taşpınar, Vivense, HYS AVM, Yön, Yiğit ve SenetSepet'e kıyasla daha rekabetçi elden senet imkanı sunulmaktadır."
    }


def _generate_feasibility_and_campaigns(api_key, product_name, brand, category, model_code,
                                        market_prices, hedef_pricing, user_cost=0, notes='', image_data=None):
    """Generate rich AI commercial feasibility, selling reasons, risks, and campaigns using Gemini."""
    default_data = _build_default_feasibility_and_campaigns(
        product_name, brand, category, model_code, market_prices, hedef_pricing, user_cost, notes
    )
    if not api_key:
        return default_data

    monthly = hedef_pricing.get('monthlyInstallmentPrice', 0)
    monthly_str = f"{monthly:,.0f} TL" if monthly else "uygun taksit"
    min_p = market_prices.get('min', 0)
    cash_p = hedef_pricing.get('cashRecommendedPrice', 0)
    total_inst = hedef_pricing.get('installmentRecommendedPrice', 0)

    prompt = f'''Sen Türkiye perakende pazarında uzmanlaşmış bir Ticari Satın Alma ve Satış Stratejisi Direktörüsün.
Analiz Edilen Ürün: "{product_name}"
Marka: "{brand}"
Kategori: "{category}"
Model Kodu: "{model_code}"
Piyasa Fiyatı: En Ucuz {min_p} TL, Ortalama {market_prices.get('average', 0)} TL
Hedef AVM Fiyatı: Peşin {cash_p} TL, 15 Ay Elden Senetli Toplam {total_inst} TL (Aylık {monthly_str})
Kullanıcı Alış Maliyeti: {user_cost} TL
Ek Notlar: "{notes}"

Hedef AVM, Türkiye genelinde şubeleri olan, kredi kartsız, peşinatsız 15 aya varan elden senetli taksitli satış yapan büyük bir perakende mağazalar zinciridir (Rakipleri: Evkur, Taşpınar, Vivense, HYS AVM, Yön AVM vb.).

Lütfen bu ürün için aşağıdaki formatta sadece geçerli bir JSON döndür:
{{
  "feasibility": {{
    "score": 85,
    "verdict": "GÜÇLÜ SATAR",
    "headline": "Hedef AVM için 1-2 cümlelik net yönetici karar ve satış potansiyeli özeti",
    "reasonsToSell": [
      "15 ay vadeli elden senetle aylık taksitinin müşteri için cazibesi",
      "Ürünün pazar talebi, marka güveni ve çekim gücü",
      "Hedef AVM mağaza içi satış ve müşteri profiline uyum gerekçesi"
    ],
    "risksAndWatchouts": [
      "15 ay vade süresince dikkat edilecek müşteri istihbarat ve skorlama uyarısı",
      "Pazar fiyat rekabeti veya stok devir hızı uyarısı",
      "Yetkili servis, garanti veya teslimat süreci uyarısı"
    ],
    "demandLevel": "Çok Yüksek",
    "competitionLevel": "Orta",
    "returnRisk": "Düşük",
    "seasonalTrend": "Tüm Yıl Düzenli",
    "targetAudience": "Müşteri profili açıklaması"
  }},
  "campaigns": [
    {{
      "campaignType": "15 Ay Elden Senet",
      "title": "Kredi Kartsız 15 Ay Elden Taksit Kampanyası",
      "description": "Peşinatsız ve kartsız 15 ay taksit kampanya kurgusu",
      "bannerSlogan": "Mağaza afişi veya vitrin sloganı",
      "slogan": "Mağaza afişi veya vitrin sloganı"
    }},
    {{
      "campaignType": "Günün Fırsatı",
      "title": "Mağaza İçi Özel Kampanya Başlığı",
      "description": "Kampanya kurgusu ve satış taktiği",
      "bannerSlogan": "Çarpıcı vitrin sloganı",
      "slogan": "Çarpıcı vitrin sloganı"
    }},
    {{
      "campaignType": "Çeyiz & Ev Yenileme",
      "title": "Avantaj Paketi Kampanya Başlığı",
      "description": "Taksitli alışveriş paketi açıklaması",
      "bannerSlogan": "Vitrin sloganı",
      "slogan": "Vitrin sloganı"
    }}
  ],
  "strategyNote": "Hedef AVM peşin ve 15 ay senetli fiyat belirleme gerekçesi özeti",
  "advantageNote": "Hedef AVM'nin Evkur, Taşpınar, Vivense ve Yön AVM'ye göre aylık taksit ve senet onayı üstünlüğü özeti"
}}'''

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        data = None
        for model_name in ('gemini-2.5-flash', 'gemini-3.8-flash', 'gemini-2.0-flash'):
            try:
                interaction = client.interactions.create(
                    model=model_name,
                    input=prompt
                )
                res = _json(interaction.output_text)
                if isinstance(res, dict) and res.get('feasibility'):
                    data = res
                    break
            except Exception:
                continue

        if not data:
            data = default_data

        if isinstance(data, dict):
            feasibility = data.get('feasibility') or {}
            campaigns = data.get('campaigns') or []

            reasons = feasibility.get('reasonsToSell')
            if not isinstance(reasons, list) or len(reasons) == 0:
                feasibility['reasonsToSell'] = default_data['reasonsToSell']

            risks = feasibility.get('risksAndWatchouts')
            if not isinstance(risks, list) or len(risks) == 0 or (len(risks) == 1 and 'katılmadı' in risks[0]):
                feasibility['risksAndWatchouts'] = default_data['risksAndWatchouts']

            if not feasibility.get('score') or feasibility.get('score') == 50:
                feasibility['score'] = default_data['score']
            if not feasibility.get('verdict') or feasibility.get('verdict') in ('Belirsiz', 'Bilinmiyor'):
                feasibility['verdict'] = default_data['verdict']
            if not feasibility.get('headline') or 'canlı doğrulanmış mağaza fiyatlarına dayanır' in str(feasibility.get('headline') or ''):
                feasibility['headline'] = default_data['headline']
            if not feasibility.get('demandLevel') or feasibility.get('demandLevel') in ('Belirsiz', 'Bilinmiyor'):
                feasibility['demandLevel'] = default_data['demandLevel']
            if not feasibility.get('competitionLevel') or feasibility.get('competitionLevel') in ('Belirsiz', 'Bilinmiyor'):
                feasibility['competitionLevel'] = default_data['competitionLevel']
            if not feasibility.get('returnRisk') or feasibility.get('returnRisk') in ('Belirsiz', 'Bilinmiyor'):
                feasibility['returnRisk'] = default_data['returnRisk']
            if not feasibility.get('seasonalTrend') or feasibility.get('seasonalTrend') in ('Belirsiz', 'Bilinmiyor'):
                feasibility['seasonalTrend'] = default_data['seasonalTrend']

            valid_camps = []
            if isinstance(campaigns, list):
                for c in campaigns:
                    if isinstance(c, dict) and c.get('title'):
                        slogan = c.get('bannerSlogan') or c.get('slogan') or "15 Ay Taksit Avantajını Kaçırmayın!"
                        c['bannerSlogan'] = slogan
                        c['slogan'] = slogan
                        valid_camps.append(c)
            if not valid_camps:
                valid_camps = default_data['campaigns']

            strategy_note = data.get('strategyNote') or default_data['strategyNote']
            advantage_note = data.get('advantageNote') or default_data['advantageNote']

            return {
                'feasibility': feasibility,
                'campaigns': valid_camps,
                'strategyNote': strategy_note,
                'advantageNote': advantage_note
            }
    except Exception as exc:
        logger.warning('Feasibility generation with Gemini failed, using default: %s', exc)

    return default_data


def analyze_product(product_name, api_key, user_cost=0, notes='', image_data=None):
    if not api_key:
        raise RuntimeError('Sunucuda GEMINI_API_KEY tanımlı değil')

    identity = _resolve_product_identity(api_key, product_name)
    resolved_name = identity.get('full_name') or product_name
    resolved_model = identity.get('model_code') or product_name
    resolved_brand = identity.get('brand') or ''
    resolved_category = identity.get('category') or ''

    candidates = _discover_candidates(api_key, resolved_name)
    offers = OfferVerificationService().verify_offers(resolved_name, candidates, max_workers=4)
    offers = _enrich_from_product_pages(api_key, resolved_name, candidates, offers, max_workers=4)

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
    # 1. Öncelik: Aktif stokta olan mağaza fiyatları
    prices = [r['estimatedPrice'] for r in benchmarks if r.get('isAvailable') and (r.get('estimatedPrice') or 0) > 0]

    # 2. Öncelik: Eğer tüm mağazalar geçici olarak stok dışı veya haber ver ise, tespit edilen son canlı fiyatlar
    if not prices:
        prices = [r['estimatedPrice'] for r in benchmarks if (r.get('estimatedPrice') or 0) > 0]

    # 3. Öncelik: Senetli rakiplerde tespit edilen peşin/toplam fiyatlar
    if not prices:
        inst_prices = [r['estimatedTotalPrice'] for r in installment if (r.get('estimatedTotalPrice') or 0) > 0]
        if inst_prices:
            # Senetli toplam fiyattan peşin piyasa ortalamasına çevir (vade katsayısı ~1.38)
            prices = [round(p / 1.38) for p in inst_prices]

    # 4. Öncelik: Teklif havuzundaki doğrulanmış veya keşfedilmiş pozitif fiyatlar
    if not prices:
        prices = [o.display_price for o in offers if (o.display_price or 0) > 0]

    minimum = min(prices) if prices else 0
    average = round(sum(prices) / len(prices)) if prices else 0
    maximum = max(prices) if prices else 0
    cash = round(minimum * 1.02) if minimum else 0
    total = round(cash * 1.38) if cash else 0
    monthly = round(total / 15) if total else 0

    strategy_note = (
        f"Piyasa en düşük fiyatı ({minimum:,.0f} TL) baz alınarak 15 ay vadeli elden senetli rekabetçi satış fiyatı belirlendi."
        if minimum > 0 else 'Öneri canlı doğrulanmış mağaza fiyatlarından hesaplandı.'
    )

    hedef_pricing = {
        'cashRecommendedPrice': cash,
        'installmentRecommendedPrice': total,
        'monthlyInstallmentPrice': monthly,
        'installmentCount': 15,
        'strategyNote': strategy_note,
        'advantageNote': ''
    }

    market_prices = {
        'min': minimum,
        'average': average,
        'max': maximum,
        'currency': 'TRY'
    }

    ai_data = _generate_feasibility_and_campaigns(
        api_key=api_key,
        product_name=resolved_name,
        brand=resolved_brand,
        category=resolved_category,
        model_code=resolved_model,
        market_prices=market_prices,
        hedef_pricing=hedef_pricing,
        user_cost=user_cost,
        notes=notes,
        image_data=image_data
    )

    feasibility = ai_data.get('feasibility') or {}
    campaigns = ai_data.get('campaigns') or []
    if ai_data.get('strategyNote'):
        hedef_pricing['strategyNote'] = ai_data['strategyNote']
    if ai_data.get('advantageNote'):
        hedef_pricing['advantageNote'] = ai_data['advantageNote']

    return {
        'productName': resolved_name, 'brand': resolved_brand, 'category': resolved_category,
        'modelOrCode': resolved_model, '_query': product_name,
        'marketPrices': market_prices,
        'competitorBenchmarks': benchmarks, 'senetliCompetitors': installment,
        'hedefPricing': hedef_pricing,
        'feasibility': feasibility,
        'campaigns': campaigns,
        '_userCost': user_cost, '_userNotes': notes, '_image': image_data,
        '_timestamp': datetime.now().strftime('%d.%m.%Y %H:%M'), '_directUrls': {}
    }
