"""Product-page evidence. Search results supply candidates, never prices."""
import concurrent.futures
from contextlib import closing
import ipaddress
import json
import re
import socket
import unicodedata
from datetime import datetime, timezone
from urllib.parse import unquote, urljoin, urlparse

import requests
from curl_cffi import requests as browser_requests
from bs4 import BeautifulSoup

STORES = {
    'official': ('Marka Resmi Mağazası', None),
    'akakce': ('Akakçe', 'akakce.com'), 'cimri': ('Cimri', 'cimri.com'),
    'trendyol': ('Trendyol', 'trendyol.com'),
    'hepsiburada': ('Hepsiburada', 'hepsiburada.com'),
    'vatan': ('Vatan Bilgisayar', 'vatanbilgisayar.com'),
    'evkur': ('Evkur', 'evkur.com.tr'), 'taspinar': ('Taşpınar', 'taspinar.com'),
    'vivense': ('Vivense', 'vivense.com'), 'hysavm': ('HYS AVM', 'hysavm.com'),
    'yonavm': ('Yön AVM', 'yonavm.com.tr'), 'yigitavm': ('Yiğit AVM', 'yigitavm.com.tr'),
    'senetsepet': ('SenetSepet', 'senetsepet.com'),
}
OFFICIAL_DOMAINS = {
    'generalmobile.com', 'samsung.com', 'apple.com', 'mi.com',
    'philips.com.tr', 'philips.com', 'arcelik.com.tr', 'beko.com.tr',
    'vestel.com.tr', 'karaca.com', 'korkmaz.com.tr', 'tefal.com.tr',
    'bosch-home.com.tr', 'siemens-home.bsh-group.com', 'dyson.com.tr',
}
# User-reported URLs are discovery hints only. Always fetch and validate afresh.
GM26_HINTS = {
    'official': 'https://www.generalmobile.com/tr/gm26pro5g/model',
    'trendyol': 'https://www.trendyol.com/general-mobile/gm-26-pro-5g-deep-space-20gb-ram-8-12-256gb-hafiza-p-1093119421?boutiqueId=61&merchantId=148051',
    'hepsiburada': 'https://www.hepsiburada.com/gm-26-pro-5g-deep-space-24gb-ram-12-12-256gb-hafiza-pm-HBC0000FP3WMZ',
    'vatan': 'https://www.vatanbilgisayar.com/general-mobile-gm-26-pro-5g-dual-8-256-gb-akilli-telefon-deep-space.html',
    'yonavm': 'https://www.yonavm.com.tr/general-mobile-gm-26-pro-8-256-gb-5g-cep-telefonu-11269',
    'cimri': 'https://www.cimri.com/cep-telefonlari/en-ucuz-general-mobile-gm-26-pro-5g-256gb-8gb-ram-fiyatlari,a2562232095',
    'akakce': 'https://www.akakce.com/cep-telefonu/en-ucuz-general-mobile-gm-26-pro-256-gb-fiyati,1430127216.html',
}

def norm(value):
    value = str(value).lower().replace('ı', 'i')
    return ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c))

def model_matches(query, title):
    q, t = norm(query), norm(title)
    # Space/hyphen insensitive model identifiers: GM26 == GM 26, Pro != base model.
    compact = lambda x: re.sub(r'[^a-z0-9]', '', x)
    if re.search(r'kilif|ekran koruyucu|lens koruma|sarj aleti', t) and not re.search(r'kilif|koruyucu|sarj', q):
        return False
    def model_codes(text):
        return {compact(prefix + number + suffix) for prefix, number, suffix in
                re.findall(r'([a-z]+)[\s-]*(\d+)([a-z0-9]*)', text)
                if prefix not in ('pro', 'plus', 'ultra', 'max', 'lite', 'ram', 'gb', 'tb')}
    codes = model_codes(q)
    title_codes = model_codes(t)
    if not codes or not all(compact(c) in title_codes for c in codes):
        return False
    for suffix in ('pro', 'plus', 'ultra', 'max', 'lite'):
        if bool(re.search(r'\b' + suffix + r'\b', q)) != bool(re.search(r'\b' + suffix + r'\b', t)):
            return False
    capacities = re.findall(r'\b(\d+)\s*(?:gb|tb)\b', q)
    return all(re.search(r'\b' + c + r'\s*(?:gb|tb)\b', t) for c in capacities)

def direct_url(url, key):
    try:
        u = urlparse(url)
        host = (u.hostname or '').lower()
        if u.scheme != 'https' or u.username or u.password or u.port not in (None, 443):
            return False
        domain = STORES[key][1]
        if key == 'official' and host.removeprefix('www.') not in OFFICIAL_DOMAINS:
            return False
        if domain and host not in (domain, 'www.' + domain):
            return False
        if not domain and (host in ('google.com', 'www.google.com') or any(x in host for x in ('vertexaisearch', 'n11.', 'teknosa.')) or any(d and host in (d, 'www.' + d) for _, d in STORES.values())):
            return False
        if len(u.path.strip('/')) < 5 or re.search(r'/(?:arama|search|ara|sr|liste|kategori)(?:/|$)', u.path, re.I) or re.search(r'(?:^|&)(q|query|search)=', u.query):
            return False
        patterns = {'trendyol': r'-p-\d+', 'hepsiburada': r'-p[m]?-\w+', 'vatan': r'\.html$', 'taspinar': r'-p-\d+', 'akakce': r'fiyati,\d+', 'cimri': r'fiyatlari[-,]a?\d+'}
        return not patterns.get(key) or bool(re.search(patterns[key], unquote(u.path)))
    except (ValueError, KeyError):
        return False

def fetch_page(url, key):
    # Validate every redirect and reject private network destinations.
    for _ in range(5):
        if not direct_url(url, key):
            raise ValueError('Ürün sayfası olmayan veya yanlış mağazaya ait bağlantı')
        host = urlparse(url).hostname
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
            raise ValueError('Geçersiz ağ adresi')
        with closing(browser_requests.get(url, impersonate='chrome', timeout=(8, 18), allow_redirects=False, stream=True,
                          headers={'Accept-Language': 'tr-TR,tr;q=0.9', 'Cache-Control': 'no-cache'})) as r:
            if r.is_redirect:
                url = urljoin(url, r.headers['Location'])
                continue
            r.raise_for_status()
            chunks, size = [], 0
            for chunk in r.iter_content(65536):
                size += len(chunk)
                if size > 6_000_000:
                    raise ValueError('Sayfa boyutu sınırı aşıldı')
                chunks.append(chunk)
            return url, b''.join(chunks).decode(r.encoding if r.encoding and r.encoding != 'ISO-8859-1' else 'utf-8', errors='replace')
    raise ValueError('Yönlendirme sınırı aşıldı')

def money(value):
    if isinstance(value, (int, float)):
        return float(value) if 0 < value < 100_000_000 else None
    s = re.sub(r'[^\d,.]', '', str(value or ''))
    if ',' in s:
        s = s.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'\d{1,3}(?:\.\d{3})+', s):
        s = s.replace('.', '')
    try:
        return money(float(s))
    except ValueError:
        return None

def objects(value):
    if isinstance(value, list):
        for item in value:
            yield from objects(item)
    elif isinstance(value, dict):
        yield value
        if '@graph' in value:
            yield from objects(value['@graph'])

def parse_page(query, key, url, html):
    result = {'key': key, 'platform': STORES[key][0], 'productUrl': '', 'status': 'unverified', 'price': None,
              'isAvailable': None, 'checkedAt': datetime.now(timezone.utc).isoformat(), 'notes': 'Ürün sayfasındaki fiyat ve stok doğrulanamadı.'}
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.h1.get_text(' ', strip=True) if soup.h1 else ''
    products = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            products.extend(p for p in objects(json.loads(script.get_text())) if 'Product' in ([p.get('@type')] if isinstance(p.get('@type'), str) else p.get('@type', [])))
        except (ValueError, TypeError):
            pass
    if not title and len(products) == 1:
        title = str(products[0].get('name', ''))
    has_gm_variants = key == 'official' and urlparse(url).hostname in ('generalmobile.com', 'www.generalmobile.com') and bool(soup.select('.payment-1'))
    title_query = re.sub(r'\b\d+\s*(?:gb|tb)\b', '', query, flags=re.I) if has_gm_variants else query
    if not model_matches(title_query, title):
        result.update(status='mismatch', notes='Sayfanın ürün modeli/varyantı eşleşmedi veya ürün başlığı okunamadı.')
        return result
    result.update(productUrl=url, title=title)
    if key == 'official' and urlparse(url).hostname in ('generalmobile.com', 'www.generalmobile.com'):
        variants = []
        for card in soup.select('.payment-1'):
            description = ' '.join(x.get_text(' ', strip=True) for x in card.select('span:not(.fw-bold)'))
            if not model_matches(query, title + ' ' + description):
                continue
            amount = card.select_one('.money_payment')
            price = money(amount.get_text()) if amount else None
            available = bool(card.select_one('a[onclick^="SetSelectedProductIds"]'))
            variants.append((available, price, description, card.get('id')))
        active = [v for v in variants if v[0] and v[1]]
        if len(active) == 1:
            _, price, description, anchor = active[0]
            result.update(status='in_stock', price=price, isAvailable=True, variant=description,
                          productUrl=url + '#' + str(anchor), notes='Sayfadaki stokta olan seçenek: ' + description)
        elif variants and not active:
            result.update(status='out_of_stock', isAvailable=False, notes='Eşleşen seçenekler stokta yok.')
        else:
            result['notes'] = 'Birden fazla seçenek var; fiyat için RAM/hafıza/renk belirtin.'
        return result
    for tag in soup.select('script, style, template, [hidden], [aria-hidden="true"], .d-none'):
        tag.decompose()
    for tag in soup.select('[style]'):
        if tag.attrs and re.search(r'display\s*:\s*none|visibility\s*:\s*hidden', tag.get('style', ''), re.I):
            tag.decompose()
    if key == 'yonavm' and soup.select_one('#aGelinceHaberVer'):
        result.update(status='out_of_stock', isAvailable=False, notes='Ürün sayfasında Gelince Haber Ver uyarısı var; fiyat karşılaştırmaya alınmadı.')
        return result
    # Scope stock notices to the current product, not recommendations/navigation.
    scope = soup.select_one('[itemtype$="/Product"]') or soup.select_one('.product-detail') or soup.select_one('main') or soup
    text = norm(scope.get_text(' ', strip=True))
    offers = []
    for p in products:
        if model_matches(query, p.get('name', '')):
            offers.extend(o for o in objects(p.get('offers', [])) if o.get('@type') == 'Offer')
    # Never take AggregateOffer.lowPrice (a different seller/variant may own it).
    prices = {(money(o.get('price')), o.get('availability', '').rsplit('/', 1)[-1]) for o in offers if o.get('priceCurrency') in ('TRY', 'TL') and money(o.get('price'))}
    if len(prices) == 1:
        price, availability = next(iter(prices))
    else:
        price, availability = None, ''
    notice = re.search(r'gelince haber ver|stokta yok|stok yok|tukendi|tukenmistir', text)
    # A mixed-variant model selector needs variant-specific extraction.
    if notice and re.search(r'sepete ekle|hemen al|\bdevam\b', text):
        result['notes'] = 'Sayfada birden fazla varyant/stok durumu var; seçili teklif doğrulanamadı.'
        return result
    if notice or availability in ('OutOfStock', 'SoldOut', 'Discontinued'):
        result.update(status='out_of_stock', isAvailable=False, notes='Stokta yok / gelince haber ver. Satış fiyatı karşılaştırmaya alınmadı.')
        return result
    if price and availability == 'InStock':
        result.update(status='in_stock', price=price, isAvailable=True, notes='Ürün sayfasından okundu: ' + title)
    return result

def verify_one(query, key, urls):
    fallback = {'key': key, 'platform': STORES[key][0], 'status': 'unverified', 'price': None, 'productUrl': '', 'isAvailable': None,
                'checkedAt': datetime.now(timezone.utc).isoformat(), 'notes': 'Doğrudan ürün sayfası doğrulanamadı; stok hakkında hüküm verilmedi.'}
    for url in list(dict.fromkeys(urls))[:3]:
        if not direct_url(url, key):
            continue
        try:
            final, html = fetch_page(url, key)
            row = parse_page(query, key, final, html)
            if row['status'] in ('in_stock', 'out_of_stock'):
                return row
            if row['productUrl'] or not fallback['productUrl']:
                fallback = row
        except (requests.RequestException, browser_requests.RequestsError, ValueError, OSError):
            pass
    return fallback

def verify_radar(query, candidates):
    candidates = candidates if isinstance(candidates, dict) else {}
    # Grounding redirects are candidate locators, not product links or price evidence.
    def resolve_source(source):
        url = source.get('uri', '') if isinstance(source, dict) else ''
        try:
            u = urlparse(url)
            if u.scheme == 'https' and u.hostname == 'vertexaisearch.cloud.google.com' and u.path.startswith('/grounding-api-redirect/'):
                with closing(browser_requests.get(url, impersonate='chrome', timeout=10, allow_redirects=False)) as response:
                    url = urljoin(url, response.headers.get('Location', '')) if response.is_redirect else ''
            host = urlparse(url).hostname
            for key, (_, domain) in STORES.items():
                if domain and host in (domain, 'www.' + domain) and direct_url(url, key):
                    return key, url
            if host in ('generalmobile.com', 'www.generalmobile.com') and direct_url(url, 'official'):
                return 'official', url
        except (browser_requests.RequestsError, ValueError, OSError):
            pass
        return None
    sources = candidates.get('_grounding', [])
    if isinstance(sources, list):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            for resolved in pool.map(resolve_source, sources[:20]):
                if resolved:
                    key, url = resolved
                    previous = candidates.get(key, [])
                    candidates[key] = [url] + (previous if isinstance(previous, list) else [previous])
    def run(key):
        values = candidates.get(key, [])
        values = values if isinstance(values, list) else [values]
        values = [u for u in values if isinstance(u, str) and len(u) < 3000]
        if model_matches('GM26 Pro', query) and key in GM26_HINTS:
            values.insert(0, GM26_HINTS[key])
        return verify_one(query[:200], key, values)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(run, STORES))
