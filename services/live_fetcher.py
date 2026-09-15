"""Live Product Fetcher with SSRF protection, timeout, and adapter routing."""
import ipaddress
import socket
import urllib.parse
from typing import Optional, Tuple
import requests
from bs4 import BeautifulSoup

from services.models import ProductOffer, StockStatus, FetchStatus, VerificationMethod
from services.normalizers import UrlNormalizer
from services.adapters.base import BaseAdapter
from services.adapters.trendyol import TrendyolAdapter
from services.adapters.hepsiburada import HepsiburadaAdapter
from services.adapters.vatan import VatanAdapter
from services.adapters.aggregators import AkakceAdapter, CimriAdapter
from services.adapters.installment import TaspinarAdapter, YonavmAdapter, EvkurAdapter
from services.adapters.generic import GenericAdapter
from services.adapters.general_mobile import GeneralMobileAdapter
from services.safe_http import fetch_page

ADAPTERS = [
    GeneralMobileAdapter,
    TrendyolAdapter,
    HepsiburadaAdapter,
    VatanAdapter,
    AkakceAdapter,
    CimriAdapter,
    TaspinarAdapter,
    YonavmAdapter,
    EvkurAdapter,
]

class LiveProductFetcher:
    DEFAULT_TIMEOUT = (5, 10) # 5s connect, 10s read
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    @classmethod
    def fetch(cls, url: str):
        """Compatibility fetch used by the verifier, backed by the bounded transport."""
        result = fetch_page(url)
        code = result['code']
        if code == 200:
            status = FetchStatus.SUCCESS
        elif code in (401, 403, 429, 503):
            status = FetchStatus.BLOCKED
        elif result.get('error') == 'TIMEOUT':
            status = FetchStatus.TIMEOUT
        else:
            status = FetchStatus.FAILED
        return {'status': status, 'http_status': code, 'final_url': result['final_url'],
                'html': result['html'], 'error': result.get('error')}

    @classmethod
    def is_safe_url(cls, url: str) -> Tuple[bool, str]:
        """Validates URL against SSRF and private networks."""
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                return False, "Geçersiz URL şeması"
            if parsed.port not in (None, 80, 443):
                return False, "Geçersiz port"
            host = parsed.hostname
            if not host:
                return False, "Host bulunamadı"

            # Check localhost and common internal names
            if host.lower() in ('localhost', '127.0.0.1', 'metadata.google.internal', 'instance-data'):
                return False, "Özel ağ adresi engellendi"

            # Resolve IP
            addr_info = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                if not ip_obj.is_global or ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                    return False, f"Özel/yerel IP engellendi ({ip_str})"

            return True, "OK"
        except Exception as e:
            return False, f"URL doğrulama hatası: {e}"

    @classmethod
    def get_adapter_for_url(cls, url: str) -> BaseAdapter:
        for ad_cls in ADAPTERS:
            if ad_cls.matches_url(url):
                return ad_cls()
        return GenericAdapter()

    @classmethod
    def fetch_live_data(cls, url: str, expected_product: str) -> ProductOffer:
        """Fetches product page and returns populated ProductOffer."""
        canonical = UrlNormalizer.canonicalize(url)
        adapter = cls.get_adapter_for_url(url)

        offer = ProductOffer(
            merchant=adapter.MERCHANT_NAME,
            source_url=url,
            canonical_url=canonical,
            verification_method=VerificationMethod.HTML_PARSER.value
        )

        is_safe, reason = cls.is_safe_url(url)
        if not is_safe:
            offer.fetch_status = FetchStatus.FAILED
            offer.notes = f"SSRF Güvenlik Engeli: {reason}"
            return offer

        headers = {
            'User-Agent': cls.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1'
        }

        current_url = url
        response = None

        try:
            session = requests.Session()
            for _ in range(4): # Max 4 redirects
                resp = session.get(
                    current_url,
                    headers=headers,
                    timeout=cls.DEFAULT_TIMEOUT,
                    allow_redirects=False,
                    stream=True
                )
                if resp.is_redirect or 300 <= resp.status_code < 400:
                    next_url = urllib.parse.urljoin(current_url, resp.headers.get('Location', ''))
                    is_next_safe, _ = cls.is_safe_url(next_url)
                    if not is_next_safe:
                        offer.fetch_status = FetchStatus.FAILED
                        offer.notes = "Yönlendirme sırasında güvenli olmayan adrese ulaşıldı."
                        return offer
                    current_url = next_url
                    continue
                else:
                    response = resp
                    break

            if not response:
                offer.fetch_status = FetchStatus.FAILED
                offer.notes = "Maksimum yönlendirme sınırı aşıldı."
                return offer

            if response.status_code in (403, 429, 503):
                offer.fetch_status = FetchStatus.BLOCKED
                offer.stock_status = StockStatus.UNKNOWN
                offer.notes = f"Mağaza bot koruması/erişim engeli döndü (HTTP {response.status_code})."
                return offer

            if response.status_code == 404:
                offer.fetch_status = FetchStatus.FAILED
                offer.stock_status = StockStatus.UNKNOWN
                offer.notes = "Ürün sayfası bulunamadı (404)."
                return offer

            response.raise_for_status()

            # Read text (limit max size to 4MB)
            content_bytes = response.raw.read(4 * 1024 * 1024)
            encoding = response.encoding if response.encoding and response.encoding.lower() != 'iso-8859-1' else 'utf-8'
            html = content_bytes.decode(encoding, errors='replace')

            soup = BeautifulSoup(html, 'html.parser')
            parsed_offer = adapter.parse(current_url, html, soup, expected_product)
            parsed_offer.fetch_status = FetchStatus.SUCCESS
            return parsed_offer

        except requests.Timeout:
            offer.fetch_status = FetchStatus.TIMEOUT
            offer.stock_status = StockStatus.UNKNOWN
            offer.notes = "Mağaza sayfası zaman aşımına uğradı."
            return offer
        except requests.RequestException as e:
            offer.fetch_status = FetchStatus.FAILED
            offer.stock_status = StockStatus.UNKNOWN
            offer.notes = f"Ağ bağlantı hatası: {e}"
            return offer
        except Exception as e:
            offer.fetch_status = FetchStatus.PARSE_ERROR
            offer.stock_status = StockStatus.UNKNOWN
            offer.notes = f"Sayfa ayrıştırma hatası: {e}"
            return offer
