"""Base Adapter for Merchant-specific page parsing."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import json
import re
from bs4 import BeautifulSoup

from services.models import ProductOffer, StockStatus, FetchStatus, VerificationMethod
from services.normalizers import PriceNormalizer, StockNormalizer, UrlNormalizer

class BaseAdapter(ABC):
    MERCHANT_NAME = "Generic"
    DOMAINS: List[str] = []

    @classmethod
    def matches_url(cls, url: str) -> bool:
        if not url:
            return False
        u = url.lower()
        return any(d in u for d in cls.DOMAINS)

    @classmethod
    def extract_json_ld(cls, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract all JSON-LD Product objects from page."""
        products = []
        for script in soup.find_all('script', type='application/ld+json'):
            if not script.string:
                continue
            try:
                data = json.loads(script.string.strip())
                cls._collect_products(data, products)
            except Exception:
                pass
        return products

    @classmethod
    def _collect_products(cls, obj, results):
        if isinstance(obj, list):
            for item in obj:
                cls._collect_products(item, results)
        elif isinstance(obj, dict):
            # Check @type
            t = obj.get('@type', '')
            types = t if isinstance(t, list) else [t]
            if any('Product' in str(x) for x in types):
                results.append(obj)
            if '@graph' in obj:
                cls._collect_products(obj['@graph'], results)

    @abstractmethod
    def parse(self, url: str, html: str, soup: BeautifulSoup, expected_product: str) -> ProductOffer:
        """Parse HTML and return ProductOffer."""
        pass
