"""Generic Adapter using Schema.org JSON-LD, OpenGraph and Meta tags."""
import re
from bs4 import BeautifulSoup
from services.adapters.base import BaseAdapter
from services.models import ProductOffer, StockStatus, FetchStatus, VerificationMethod
from services.normalizers import PriceNormalizer, StockNormalizer, UrlNormalizer

class GenericAdapter(BaseAdapter):
    MERCHANT_NAME = "Genel Mağaza"
    DOMAINS = []

    def parse(self, url: str, html: str, soup: BeautifulSoup, expected_product: str) -> ProductOffer:
        canonical = UrlNormalizer.canonicalize(url)
        offer = ProductOffer(
            merchant=self.MERCHANT_NAME,
            source_url=url,
            canonical_url=canonical,
            verification_method=VerificationMethod.HTML_PARSER.value
        )

        title = ""
        if soup.title:
            title = soup.title.get_text().strip()
        if soup.h1:
            title = soup.h1.get_text().strip() or title
        offer.model = title

        # 1. Try JSON-LD
        products = self.extract_json_ld(soup)
        for p in products:
            name = p.get('name')
            if name:
                offer.model = str(name)
            offer.brand = str(p.get('brand', {}).get('name', '') if isinstance(p.get('brand'), dict) else p.get('brand', '')) or offer.brand
            offer.gtin = str(p.get('gtin') or p.get('gtin13') or p.get('ean') or '') or offer.gtin
            offer.sku = str(p.get('sku') or '') or offer.sku
            offer.mpn = str(p.get('mpn') or '') or offer.mpn

            offers_data = p.get('offers', {})
            if isinstance(offers_data, list) and offers_data:
                offers_data = offers_data[0]
            if isinstance(offers_data, dict):
                raw_price = offers_data.get('price') or offers_data.get('lowPrice')
                parsed_p = PriceNormalizer.parse(raw_price)
                if parsed_p:
                    offer.regular_price = parsed_p
                    offer.display_price = parsed_p
                    offer.verification_method = VerificationMethod.JSON_LD.value

                avail = offers_data.get('availability', '')
                if avail:
                    offer.stock_status = StockNormalizer.normalize(avail, html)

                seller = offers_data.get('seller', {})
                if isinstance(seller, dict):
                    offer.seller = str(seller.get('name', ''))
                elif isinstance(seller, str):
                    offer.seller = seller

        # 2. Meta tags fallback (OpenGraph)
        if not offer.display_price:
            og_price = soup.find('meta', property='og:price:amount') or soup.find('meta', property='product:price:amount')
            if og_price and og_price.get('content'):
                p = PriceNormalizer.parse(og_price['content'])
                if p:
                    offer.regular_price = p
                    offer.display_price = p
                    offer.verification_method = VerificationMethod.HTML_PARSER.value

        if offer.stock_status == StockStatus.UNKNOWN:
            offer.stock_status = StockNormalizer.normalize(None, soup.get_text()[:4000])

        return offer
