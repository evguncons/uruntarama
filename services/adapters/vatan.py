"""Vatan Bilgisayar Adapter."""
import re
from bs4 import BeautifulSoup
from services.adapters.base import BaseAdapter
from services.models import ProductOffer, StockStatus, FetchStatus, VerificationMethod
from services.normalizers import PriceNormalizer, StockNormalizer, UrlNormalizer

class VatanAdapter(BaseAdapter):
    MERCHANT_NAME = "Vatan Bilgisayar"
    DOMAINS = ['vatanbilgisayar.com']

    def parse(self, url: str, html: str, soup: BeautifulSoup, expected_product: str) -> ProductOffer:
        canonical = UrlNormalizer.canonicalize(url)
        offer = ProductOffer(
            merchant=self.MERCHANT_NAME,
            source_url=url,
            canonical_url=canonical,
            verification_method=VerificationMethod.HTML_PARSER.value
        )

        title = soup.h1.get_text().strip() if soup.h1 else ""
        offer.model = title

        # Check JSON-LD
        products = self.extract_json_ld(soup)
        for p in products:
            offer.model = str(p.get('name') or offer.model)
            offers_data = p.get('offers', {})
            if isinstance(offers_data, list) and offers_data:
                offers_data = offers_data[0]
            if isinstance(offers_data, dict):
                raw_price = offers_data.get('price')
                p_num = PriceNormalizer.parse(raw_price)
                if p_num:
                    offer.regular_price = p_num
                    offer.display_price = p_num
                    offer.verification_method = VerificationMethod.JSON_LD.value
                avail = offers_data.get('availability', '')
                if avail:
                    offer.stock_status = StockNormalizer.normalize(avail, html)

        # HTML Selector fallback
        if not offer.display_price:
            price_elem = soup.select_one('.product-list__price') or soup.select_one('.product-price')
            if price_elem:
                p_num = PriceNormalizer.parse(price_elem.get_text())
                if p_num:
                    offer.regular_price = p_num
                    offer.display_price = p_num

        if offer.stock_status == StockStatus.UNKNOWN:
            offer.stock_status = StockNormalizer.normalize(None, soup.get_text()[:4000])

        return offer
