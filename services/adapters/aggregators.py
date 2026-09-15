"""Akakce and Cimri Aggregator Adapters."""
from bs4 import BeautifulSoup
from services.adapters.base import BaseAdapter
from services.models import ProductOffer, StockStatus, FetchStatus, VerificationMethod
from services.normalizers import PriceNormalizer, StockNormalizer, UrlNormalizer

class AkakceAdapter(BaseAdapter):
    MERCHANT_NAME = "Akakçe"
    DOMAINS = ['akakce.com']

    def parse(self, url: str, html: str, soup: BeautifulSoup, expected_product: str) -> ProductOffer:
        canonical = UrlNormalizer.canonicalize(url)
        offer = ProductOffer(
            merchant=self.MERCHANT_NAME,
            source_url=url,
            canonical_url=canonical,
            verification_method=VerificationMethod.HTML_PARSER.value
        )
        offer.model = soup.h1.get_text().strip() if soup.h1 else ""
        price_elem = soup.select_one('.pt_v8') or soup.select_one('.price')
        if price_elem:
            p = PriceNormalizer.parse(price_elem.get_text())
            if p:
                offer.regular_price = p
                offer.display_price = p
                offer.stock_status = StockStatus.IN_STOCK

        if not offer.display_price:
            products = self.extract_json_ld(soup)
            for prod in products:
                o = prod.get('offers', {})
                if isinstance(o, dict):
                    p = PriceNormalizer.parse(o.get('lowPrice') or o.get('price'))
                    if p:
                        offer.regular_price = p
                        offer.display_price = p
                        offer.stock_status = StockStatus.IN_STOCK
        return offer

class CimriAdapter(BaseAdapter):
    MERCHANT_NAME = "Cimri"
    DOMAINS = ['cimri.com']

    def parse(self, url: str, html: str, soup: BeautifulSoup, expected_product: str) -> ProductOffer:
        canonical = UrlNormalizer.canonicalize(url)
        offer = ProductOffer(
            merchant=self.MERCHANT_NAME,
            source_url=url,
            canonical_url=canonical,
            verification_method=VerificationMethod.HTML_PARSER.value
        )
        offer.model = soup.h1.get_text().strip() if soup.h1 else ""
        products = self.extract_json_ld(soup)
        for prod in products:
            o = prod.get('offers', {})
            if isinstance(o, dict):
                p = PriceNormalizer.parse(o.get('lowPrice') or o.get('price'))
                if p:
                    offer.regular_price = p
                    offer.display_price = p
                    offer.stock_status = StockStatus.IN_STOCK
        return offer
