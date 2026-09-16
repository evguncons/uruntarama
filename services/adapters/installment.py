"""Installment Stores Adapters (Taşpınar, Yön AVM, Evkur)."""
from bs4 import BeautifulSoup
from services.adapters.base import BaseAdapter
from services.models import ProductOffer, StockStatus, FetchStatus, VerificationMethod
from services.normalizers import PriceNormalizer, StockNormalizer, UrlNormalizer

class TaspinarAdapter(BaseAdapter):
    MERCHANT_NAME = "Taşpınar"
    DOMAINS = ['taspinar.com']

    def parse(self, url: str, html: str, soup: BeautifulSoup, expected_product: str) -> ProductOffer:
        canonical = UrlNormalizer.canonicalize(url)
        offer = ProductOffer(
            merchant=self.MERCHANT_NAME,
            source_url=url,
            canonical_url=canonical,
            verification_method=VerificationMethod.HTML_PARSER.value
        )
        offer.model = soup.h1.get_text().strip() if soup.h1 else ""
        price_elem = soup.select_one('.product-price') or soup.select_one('.product-details-price')
        if price_elem:
            p = PriceNormalizer.parse(price_elem.get_text())
            if p:
                offer.regular_price = p
                offer.display_price = p
                offer.product_evidence = bool(offer.model)
        offer.stock_status = StockNormalizer.normalize(None, soup.get_text()[:3000])
        return offer

class YonavmAdapter(BaseAdapter):
    MERCHANT_NAME = "Yön AVM"
    DOMAINS = ['yonavm.com.tr']

    def parse(self, url: str, html: str, soup: BeautifulSoup, expected_product: str) -> ProductOffer:
        canonical = UrlNormalizer.canonicalize(url)
        offer = ProductOffer(
            merchant=self.MERCHANT_NAME,
            source_url=url,
            canonical_url=canonical,
            verification_method=VerificationMethod.HTML_PARSER.value
        )
        offer.model = soup.h1.get_text().strip() if soup.h1 else ""

        # Keep the last price visibly listed on the product page even when the
        # selected variant is sold out. Availability remains OUT_OF_STOCK, so
        # this value is not included in active market-price calculations.
        price_elem = soup.select_one('.spanFiyat') or soup.select_one('.product-price')
        if price_elem:
            p = PriceNormalizer.parse(price_elem.get_text())
            if p:
                offer.regular_price = p
                offer.display_price = p
                offer.product_evidence = bool(offer.model)

        # Strictly check "Gelince Haber Ver" button
        notice = soup.select_one('#aGelinceHaberVer')
        notice_visible = notice and not notice.has_attr('hidden') and notice.get('aria-hidden') != 'true' and 'display:none' not in notice.get('style', '').replace(' ', '').lower()
        if notice_visible:
            offer.stock_status = StockStatus.OUT_OF_STOCK
            offer.notes = "Tükendi / Gelince Haber Ver (Stokta Yok)"
            offer.product_evidence = bool(offer.model)
            return offer

        offer.stock_status = StockNormalizer.normalize(None, soup.get_text()[:3000])
        return offer

class EvkurAdapter(BaseAdapter):
    MERCHANT_NAME = "Evkur"
    DOMAINS = ['evkur.com.tr']

    def parse(self, url: str, html: str, soup: BeautifulSoup, expected_product: str) -> ProductOffer:
        canonical = UrlNormalizer.canonicalize(url)
        offer = ProductOffer(
            merchant=self.MERCHANT_NAME,
            source_url=url,
            canonical_url=canonical,
            verification_method=VerificationMethod.HTML_PARSER.value
        )
        offer.model = soup.h1.get_text().strip() if soup.h1 else ""
        price_elem = soup.select_one('.price-new') or soup.select_one('.product-price')
        if price_elem:
            p = PriceNormalizer.parse(price_elem.get_text())
            if p:
                offer.regular_price = p
                offer.display_price = p
                offer.product_evidence = bool(offer.model)
        offer.stock_status = StockNormalizer.normalize(None, soup.get_text()[:3000])
        return offer
