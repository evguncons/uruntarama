"""URL Validation and Redirect Verification Service.
Enforces that no URL reaches the frontend without thorough HTTP status,
redirect tracking, non-product/404 detection, and product matching verification.
"""
import re
import socket
import ipaddress
import urllib.request
import urllib.parse
import urllib.error
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from bs4 import BeautifulSoup

from services.models import UrlStatus, ProductOffer, StockStatus, FetchStatus, VerificationMethod
from services.normalizers import UrlNormalizer
from services.product_matcher import ProductMatcher

logger = logging.getLogger(__name__)

# Soft 404 / Non-product page signals (even on HTTP 200)
NON_PRODUCT_SIGNALS = [
    'ürün bulunamadı',
    'aradığınız ürün bulunamadı',
    'aradığınız sayfa bulunamadı',
    'bu ürün artık mevcut değil',
    'sayfa bulunamadı',
    'aradığınız kriterlere uygun ürün bulunamadı',
    'böyle bir ürün bulunmuyor',
    'product not found',
    'page not found',
    'item unavailable',
    'item not found',
    '404 - sayfa bulunamadı',
    '404 not found'
]

# Category and generic listing URL patterns
CATEGORY_PATTERNS = [
    re.compile(r'-c-\d+', re.I),
    re.compile(r'/c-\d+', re.I),
    re.compile(r'/kategori/', re.I),
    re.compile(r'/category/', re.I),
    re.compile(r'/katalog/', re.I),
    re.compile(r'/tum-urunler', re.I),
    re.compile(r'/smartphones/all', re.I)
]

SEARCH_PATTERNS = [
    re.compile(r'/sr\?', re.I),
    re.compile(r'/sr/', re.I),
    re.compile(r'/ara\?', re.I),
    re.compile(r'/arama\?', re.I),
    re.compile(r'/search\?', re.I),
    re.compile(r'[?&]q=', re.I),
    re.compile(r'searchterm=', re.I)
]

# Known store search URL templates
STORE_SEARCH_TEMPLATES = {
    'trendyol.com': 'https://www.trendyol.com/sr?q={query}',
    'hepsiburada.com': 'https://www.hepsiburada.com/ara?q={query}',
    'vatanbilgisayar.com': 'https://www.vatanbilgisayar.com/search/?q={query}',
    'taspinar.com': 'https://taspinar.com/ara?q={query}',
    'evkur.com.tr': 'https://www.evkur.com.tr/arama?q={query}',
    'yonavm.com.tr': 'https://yonavm.com.tr/Arama?q={query}',
    'vivense.com': 'https://www.vivense.com/arama?q={query}',
    'hysavm.com': 'https://hysavm.com/search?q={query}',
    'akakce.com': 'https://www.akakce.com/arama/?q={query}',
    'cimri.com': 'https://www.cimri.com/arama?q={query}'
}


class UrlValidationService:
    TIMEOUT = 10  # seconds
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

    @classmethod
    def is_safe_url(cls, url: str) -> bool:
        """SSRF protection: Only allow public HTTP/HTTPS URLs."""
        if not url or not isinstance(url, str):
            return False
        url = url.strip()
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        try:
            parsed = urllib.parse.urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return False
            # Block localhost and private/reserved hostnames
            if hostname.lower() in ('localhost', '127.0.0.1', 'metadata.google.internal', '169.254.169.254'):
                return False
            addr_info = socket.getaddrinfo(hostname, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                if not ip_obj.is_global or ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local:
                    return False
            return True
        except Exception:
            return False

    @classmethod
    def is_category_url(cls, url: str) -> bool:
        """Detect if URL points to a category listing rather than a single product."""
        if not url:
            return True
        u = url.lower()
        if 'vertexaisearch.cloud.google.com' in u:
            return True
        for pat in CATEGORY_PATTERNS:
            if pat.search(u):
                return True
        return False

    @classmethod
    def is_search_url(cls, url: str) -> bool:
        """Detect if URL is an internal search query page."""
        if not url:
            return True
        for pat in SEARCH_PATTERNS:
            if pat.search(url):
                return True
        return False

    @classmethod
    def is_homepage_url(cls, url: str) -> bool:
        """Detect if redirect ended up on the store's homepage."""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.path in ('', '/', '/tr', '/tr/', '/index.html', '/home')
        except Exception:
            return False

    @classmethod
    def _http_get(cls, url: str) -> Tuple[int, str, str, Optional[str], Optional[UrlStatus]]:
        """Executes HTTP GET with SSRF protection, redirect tracking, and error mapping.
        Returns: (status_code, final_url, html_content, redirect_target, url_status)
        """
        redirect_info = None

        class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                nonlocal redirect_info
                redirect_info = newurl
                if not UrlValidationService.is_safe_url(newurl):
                    return None  # abort if redirected to unsafe IP/host
                return super().redirect_request(req, fp, code, msg, headers, newurl)

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": cls.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        )

        try:
            opener = urllib.request.build_opener(SafeRedirectHandler)
            with opener.open(req, timeout=cls.TIMEOUT) as resp:
                status_code = resp.getcode()
                final_url = resp.geturl()
                html_bytes = resp.read()
                html = html_bytes.decode('utf-8', errors='replace')
                return status_code, final_url, html, redirect_info, None

        except urllib.error.HTTPError as he:
            status_code = he.code
            if status_code == 404:
                url_status = UrlStatus.NOT_FOUND
            elif status_code == 410:
                url_status = UrlStatus.GONE
            elif status_code == 403:
                url_status = UrlStatus.BLOCKED
            elif status_code >= 400:
                url_status = UrlStatus.INVALID_URL
            else:
                url_status = UrlStatus.UNKNOWN
            return status_code, url, "", redirect_info, url_status

        except (urllib.error.URLError, socket.timeout):
            return 0, url, "", redirect_info, UrlStatus.TIMEOUT
        except Exception:
            return 0, url, "", redirect_info, UrlStatus.UNKNOWN

    @classmethod
    def validate_product_url(
        cls,
        candidate_url: str,
        expected_product: str,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        attempt_recovery: bool = True
    ) -> ProductOffer:
        """Validates a candidate URL with real HTTP request, redirect checking,
        soft-404 detection, canonical URL verification, and product matching.
        If candidate URL is 404/not found and attempt_recovery is True, attempts
        alternative URL recovery via the store's search engine.
        """
        candidate_url = (candidate_url or '').strip()
        offer = ProductOffer(
            merchant="Bilinmeyen",
            candidate_url=candidate_url,
            source_url="",
            final_url="",
            canonical_url="",
            url_status=UrlStatus.UNKNOWN,
            url_verified=False,
            url_verified_at=datetime.now(timezone.utc).isoformat()
        )

        # 1. Format & SSRF Check
        if not candidate_url or not cls.is_safe_url(candidate_url):
            offer.url_status = UrlStatus.INVALID_URL
            cls._log_debug(candidate_url, 0, None, "", "", expected_product, "", offer.url_status, False)
            return offer

        # 2. Category check on candidate URL directly
        if cls.is_category_url(candidate_url) or cls.is_search_url(candidate_url):
            offer.url_status = UrlStatus.NON_PRODUCT_PAGE
            cls._log_debug(candidate_url, 0, None, candidate_url, "", expected_product, "", offer.url_status, False)
            return offer

        # 3. HTTP Request with Redirect Tracking
        status_code, final_url, html, redirect_info, http_err_status = cls._http_get(candidate_url)

        if http_err_status is not None:
            offer.url_status = http_err_status
            cls._log_debug(candidate_url, status_code, redirect_info, candidate_url, "", expected_product, "", offer.url_status, False)

            # Alternative URL discovery on 404
            if offer.url_status == UrlStatus.NOT_FOUND and attempt_recovery:
                alt_offer = cls.recover_alternative_url(candidate_url, expected_product, brand, model)
                if alt_offer and alt_offer.url_verified:
                    return alt_offer
            return offer

        offer.final_url = final_url

        # 4. Check if final destination is homepage, search, or category
        if cls.is_homepage_url(final_url) or cls.is_category_url(final_url) or cls.is_search_url(final_url):
            offer.url_status = UrlStatus.NON_PRODUCT_PAGE
            cls._log_debug(candidate_url, status_code, redirect_info, final_url, "", expected_product, "", offer.url_status, False)
            return offer

        # 5. Empty body check
        if not html.strip():
            offer.url_status = UrlStatus.NOT_FOUND
            cls._log_debug(candidate_url, status_code, redirect_info, final_url, "", expected_product, "", offer.url_status, False)
            return offer

        # 6. Parse HTML and check for Soft-404 / Non-product page text signals
        soup = BeautifulSoup(html, 'html.parser')
        page_title = soup.title.get_text().strip() if soup.title else ""
        h1_text = soup.h1.get_text().strip() if soup.h1 else ""
        page_text_lower = (page_title + " " + h1_text + " " + soup.get_text()[:3000]).lower()

        for signal in NON_PRODUCT_SIGNALS:
            if signal in page_text_lower:
                offer.url_status = UrlStatus.NON_PRODUCT_PAGE
                cls._log_debug(candidate_url, status_code, redirect_info, final_url, "", expected_product, page_title, offer.url_status, False)
                return offer

        # 7. Extract Detected Product Title & Verify Product Match
        detected_title = h1_text or page_title
        for script in soup.find_all('script', type='application/ld+json'):
            if script.string and '"name"' in script.string:
                name_match = re.search(r'"name"\s*:\s*"([^"]+)"', script.string)
                if name_match:
                    detected_title = name_match.group(1)
                    break

        offer.model = detected_title
        confidence, reasons = ProductMatcher.match_product(expected_product, detected_title)
        offer.match_confidence = confidence

        if confidence < 0.75:
            offer.url_status = UrlStatus.PRODUCT_MISMATCH
            cls._log_debug(candidate_url, status_code, redirect_info, final_url, "", expected_product, detected_title, offer.url_status, False)
            return offer

        # 8. Inspect <link rel="canonical"> safely
        canonical_link = soup.find('link', rel='canonical')
        canonical_url = ""
        if canonical_link and canonical_link.get('href'):
            can_href = canonical_link['href'].strip()
            if cls.is_safe_url(can_href):
                can_score, _ = ProductMatcher.match_product(expected_product, can_href)
                if can_score >= 0.70:
                    canonical_url = UrlNormalizer.canonicalize(can_href)
                    offer.canonical_url = canonical_url

        # 9. Set Verified URL and Status
        offer.source_url = final_url
        if redirect_info and final_url != candidate_url:
            offer.url_status = UrlStatus.REDIRECTED
        else:
            offer.url_status = UrlStatus.VALID

        offer.url_verified = True
        offer.verified = True

        cls._log_debug(candidate_url, status_code, redirect_info, final_url, canonical_url, expected_product, detected_title, offer.url_status, True)
        return offer

    @classmethod
    def recover_alternative_url(
        cls,
        candidate_url: str,
        expected_product: str,
        brand: Optional[str] = None,
        model: Optional[str] = None
    ) -> Optional[ProductOffer]:
        """Attempts to discover a working product URL by performing a store search when candidate URL is 404."""
        parsed = urllib.parse.urlparse(candidate_url)
        domain = parsed.netloc.lower().replace('www.', '')

        search_template = None
        for k, v in STORE_SEARCH_TEMPLATES.items():
            if k in domain:
                search_template = v
                break

        if not search_template:
            return None

        query = (f"{brand or ''} {model or ''}").strip() or expected_product
        clean_query = re.sub(r'\s+(kılıf|kilif|cam|kapak|koruyucu|şarj|sarj).*$', '', query, flags=re.I).strip()
        search_url = search_template.format(query=urllib.parse.quote(clean_query))

        status_code, final_url, html, _, err = cls._http_get(search_url)
        if status_code != 200 or not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        discovered_links: List[str] = []

        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            full_link = urllib.parse.urljoin(search_url, href)

            if not cls.is_safe_url(full_link):
                continue
            if cls.is_category_url(full_link) or cls.is_search_url(full_link):
                continue

            if 'trendyol.com' in domain and ('-p-' in full_link or '/p/' in full_link):
                discovered_links.append(full_link)
            elif 'hepsiburada.com' in domain and ('-p-' in full_link or '-pm-' in full_link):
                discovered_links.append(full_link)
            elif 'vatanbilgisayar.com' in domain and full_link.endswith('.html'):
                discovered_links.append(full_link)
            elif 'taspinar.com' in domain and '-p-' in full_link:
                discovered_links.append(full_link)
            elif UrlNormalizer.is_product_url(full_link):
                discovered_links.append(full_link)

        for alt_url in discovered_links[:5]:
            alt_offer = cls.validate_product_url(
                alt_url,
                expected_product=expected_product,
                brand=brand,
                model=model,
                attempt_recovery=False
            )
            if alt_offer.url_verified and (alt_offer.url_status in (UrlStatus.VALID, UrlStatus.REDIRECTED)):
                alt_offer.candidate_url = candidate_url
                logger.info(f"[URL_VERIFY_RECOVERY] Discovered valid alternative for {candidate_url} -> {alt_offer.source_url}")
                return alt_offer

        return None

    @classmethod
    def _log_debug(
        cls,
        candidate: str,
        status: int,
        redirect: Optional[str],
        final: str,
        canonical: str,
        expected: str,
        detected: str,
        url_status: UrlStatus,
        verified: bool
    ):
        """Prints debug log in the exact required format."""
        msg = f"""
[URL_VERIFY]
Candidate: {candidate}
HTTP Status: {status}
Redirect: {redirect or 'None'}
Final: {final}
Canonical: {canonical or 'None'}
Expected Product: {expected}
Detected Product: {detected}
URL Status: {url_status.value}
Verified: {str(verified).lower()}
"""
        print(msg.strip())
        logger.info(msg.strip())
