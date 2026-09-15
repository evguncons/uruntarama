"""Hepsiburada Adapter."""
import re
import json
from bs4 import BeautifulSoup
from services.adapters.base import BaseAdapter
from services.models import ProductOffer, StockStatus, FetchStatus, VerificationMethod
from services.normalizers import PriceNormalizer, StockNormalizer, UrlNormalizer

class HepsiburadaAdapter(BaseAdapter):
    MERCHANT_NAME = "Hepsiburada"
    DOMAINS = ['hepsiburada.com', 'hb.biz']

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

        # 1. Check Next.js state <script id="__NEXT_DATA__">
        next_script = soup.find('script', id='__NEXT_DATA__')
        if next_script and next_script.string:
            try:
                nd = json.loads(next_script.string.strip())
                props = nd.get('props', {}).get('pageProps', {})
                product = props.get('product') or props.get('initialData', {}).get('product') or {}
                if product:
                    offer.model = product.get('name') or offer.model
                    offer.brand = product.get('brand') or offer.brand
                    offer.sku = product.get('sku')
                    listings = product.get('listings', [])
                    if listings:
                        l0 = listings[0]
                        price_num = PriceNormalizer.parse(l0.get('price'))
                        if price_num:
                            offer.regular_price = price_num
                            offer.display_price = price_num
                            offer.verification_method = VerificationMethod.EMBEDDED_STATE.value
                        merchant = l0.get('merchantName') or l0.get('merchant', {}).get('name')
                        if merchant:
                            offer.seller = str(merchant)
                        if l0.get('isSalable'):
                            offer.stock_status = StockStatus.IN_STOCK
            except Exception:
                pass

        # 2. JSON-LD Fallback
        if not offer.display_price:
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

        # 3. Check for sepette discount
        sepette_match = re.search(r'sepette\s*([\d.,]+)\s*(?:tl|₺)', html, re.I)
        if sepette_match:
            c_price = PriceNormalizer.parse(sepette_match.group(1))
            if c_price and offer.display_price and c_price < offer.display_price:
                offer.cart_price = c_price
                offer.display_price = c_price
                offer.price_condition = "Sepette İndirimli"

        if offer.stock_status == StockStatus.UNKNOWN:
            offer.stock_status = StockNormalizer.normalize(None, soup.get_text()[:4000])

        return offer
