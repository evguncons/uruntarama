"""Price, Stock and URL Normalizers."""
import re
import unicodedata
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from typing import Optional, Tuple
from services.models import StockStatus

class PriceNormalizer:
    @staticmethod
    def parse(value) -> Optional[float]:
        """Normalizes any price string or number to a clean float in TRY."""
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            val = float(value)
            return val if 0 < val < 1_000_000_000 else None

        s = str(value).strip()
        # Remove currency symbols and non-numeric characters except comma and period
        s = re.sub(r'[^0-9,.]', '', s)
        if not s:
            return None

        # Handle Turkish decimal format: 24.999,50 -> 24999.50
        if ',' in s and '.' in s:
            # If comma appears after period: 24.999,50
            if s.rfind(',') > s.rfind('.'):
                s = s.replace('.', '').replace(',', '.')
            else: # 24,999.50
                s = s.replace(',', '')
        elif ',' in s:
            # 24999,50 or 24,999
            parts = s.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                s = parts[0] + '.' + parts[1]
            elif len(parts) == 2 and len(parts[1]) == 3: # thousands separator: 24,000
                s = parts[0] + parts[1]
            else:
                s = s.replace(',', '.')
        elif '.' in s:
            # Check if it's thousands separator: 24.999 or 24.999.000
            if re.fullmatch(r'\d{1,3}(?:\.\d{3})+', s):
                s = s.replace('.', '')
            elif s.count('.') == 1 and len(s.split('.')[1]) == 3 and int(s.split('.')[0]) < 1000:
                # e.g. 24.000 -> 24000
                s = s.replace('.', '')

        try:
            num = float(s)
            return num if 0 < num < 1_000_000_000 else None
        except ValueError:
            return None

class StockNormalizer:
    @staticmethod
    def normalize(availability_str: Optional[str] = None, html_text: Optional[str] = None) -> StockStatus:
        """Determines StockStatus from availability string and/or HTML text signals."""
        if availability_str:
            avail = availability_str.rsplit('/', 1)[-1].lower()
            if 'instock' in avail:
                return StockStatus.IN_STOCK
            if 'outofstock' in avail or 'soldout' in avail or 'discontinued' in avail:
                return StockStatus.OUT_OF_STOCK
            if 'limitedavailability' in avail:
                return StockStatus.LOW_STOCK
            if 'preorder' in avail:
                return StockStatus.PREORDER

        if not html_text:
            return StockStatus.UNKNOWN

        text = html_text.lower()

        # Check explicit out of stock first
        if any(term in text for term in [
            'stokta yok', 'tükendi', 'tükenmiştir', 'ürün tükendi',
            'satışa kapalı', 'satışı yoktur', 'gelince haber ver',
            'bu ürün geçici olarak temin edilememektedir', 'stokta bulunmamaktadır'
        ]):
            # If it's specifically a variant out of stock
            if 'bu varyant' in text or 'seçilen seçenek tükendi' in text:
                return StockStatus.VARIANT_OUT_OF_STOCK
            return StockStatus.OUT_OF_STOCK

        # Preorder signals
        if 'ön sipariş' in text or 'on siparis' in text:
            return StockStatus.PREORDER

        # Low stock signals
        if any(term in text for term in ['son 1 ürün', 'son 2 ürün', 'son 3 ürün', 'tükenmek üzere', 'kritik stok', 'sınırlı stok']):
            return StockStatus.LOW_STOCK

        # In stock signals
        if any(term in text for term in ['sepete ekle', 'satın al', 'hemen al', 'şimdi al', 'stokta var']):
            return StockStatus.IN_STOCK

        return StockStatus.UNKNOWN

class UrlNormalizer:
    # Query parameters to drop (strictly analytics, advertising and affiliate tracking)
    DROP_PARAMS = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'ref', 'gclid', 'fbclid', 'adjust_t', 'adjust_tracker',
        'yclid', 'dclid', 'msclkid', 'zanpid', 'igshid'
    }

    # Query parameters that define the actual product, variant, SKU or seller (MUST BE PRESERVED)
    KEEP_PARAMS = {
        'variant', 'sku', 'productid', 'product_id', 'item', 'itemid',
        'seller', 'merchant', 'color', 'renk', 'size', 'beden', 'v', 'model', 'hafiza', 'ram', 'capacity'
    }

    # Query parameters stripped during canonical deduplication (seller/campaign tags)
    CANONICAL_STRIP_PARAMS = set()

    @classmethod
    def normalize(cls, url: str) -> str:
        """Removes tracking/ad query parameters while strictly preserving variant, SKU, and product IDs."""
        if not url or not isinstance(url, str):
            return ""
        url = url.strip()
        if not (url.startswith('http://') or url.startswith('https://')):
            return ""

        if 'vertexaisearch.cloud.google.com/grounding-api-redirect' in url:
            return url

        try:
            parsed = urlparse(url)
            if not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 80, 443):
                return ""
            query_tuples = parse_qsl(parsed.query, keep_blank_values=True)
            filtered_query = [
                (k, v) for k, v in query_tuples
                if k.lower() not in cls.DROP_PARAMS and not k.lower().startswith('utm_') and k.lower() != 'srsltid'
            ]
            clean_query = urlencode(filtered_query)
            return urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),
                parsed.path,
                parsed.params,
                clean_query,
                parsed.fragment
            ))
        except Exception:
            return ""

    @classmethod
    def canonicalize(cls, url: str) -> str:
        """Removes tracking/ad query parameters and marketplace campaign/seller IDs for canonical product matching."""
        if not url or not isinstance(url, str):
            return ""
        url = url.strip()
        if not (url.startswith('http://') or url.startswith('https://')):
            return url

        # Google Grounding redirect URLs are kept as is
        if 'vertexaisearch.cloud.google.com/grounding-api-redirect' in url:
            return url

        try:
            parsed = urlparse(url)
            query_tuples = parse_qsl(parsed.query, keep_blank_values=False)
            filtered_query = [
                (k, v) for k, v in query_tuples
                if k.lower() not in cls.DROP_PARAMS and k.lower() not in cls.CANONICAL_STRIP_PARAMS
            ]
            clean_query = urlencode(filtered_query)
            canonical = urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),
                parsed.path.rstrip('/') if len(parsed.path) > 1 else parsed.path,
                parsed.params,
                clean_query,
                '' # Drop hash anchor unless it specifies an element
            ))
            return canonical
        except Exception:
            return url

    @classmethod
    def is_product_url(cls, url: str) -> bool:
        """Determines whether a URL points to a direct product page rather than a generic search or category list."""
        if not url or not isinstance(url, str):
            return False
        u = url.lower()
        # Search page patterns
        if any(sp in u for sp in ['/sr?q=', '/sr?', '/ara?q=', '/ara?', '/search?', 'searchTerm=', '?q=']):
            return False
        # Specific known product patterns
        if any(pp in u for pp in ['-p-', '/p/', '/urun/', '/product/', '.html', '/dp/']):
            return True
        # If it has a path with at least 2 segments and not a search root
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        return len(path_parts) >= 1
