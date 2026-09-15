"""Trendyol Adapter."""
import re
import json
from bs4 import BeautifulSoup
from services.adapters.base import BaseAdapter
from services.models import ProductOffer, StockStatus, FetchStatus, VerificationMethod
from services.normalizers import PriceNormalizer, StockNormalizer, UrlNormalizer

class TrendyolAdapter(BaseAdapter):
    MERCHANT_NAME = "Trendyol"
    DOMAINS = ['trendyol.com', 'ty.gl']

    def parse(self, url: str, html: str, soup: BeautifulSoup, expected_product: str) -> ProductOffer:
        canonical = UrlNormalizer.canonicalize(url)
        offer = ProductOffer(
            merchant=self.MERCHANT_NAME,
            source_url=url,
            canonical_url=canonical,
            verification_method=VerificationMethod.HTML_PARSER.value
        )

        title = soup.h1.get_text().strip() if soup.h1 else (soup.title.get_text().strip() if soup.title else "")
        offer.model = title

        # 1. Check window.__INITIAL_STATE__
        for script in soup.find_all('script'):
            txt = script.string or ''
            if '__INITIAL_STATE__' in txt:
                try:
                    m = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', txt, re.DOTALL)
                    if m:
                        st = json.loads(m.group(1))
                        prod = st.get('product', {})
                        if prod:
                            offer.model = prod.get('name') or offer.model
                            offer.brand = prod.get('brand', {}).get('name') if isinstance(prod.get('brand'), dict) else ''
                            price_info = prod.get('price', {})
                            sale_p = PriceNormalizer.parse(price_info.get('discountedPrice', {}).get('value'))
                            orig_p = PriceNormalizer.parse(price_info.get('originalPrice', {}).get('value'))
                            
                            offer.regular_price = orig_p or sale_p
                            offer.sale_price = sale_p
                            offer.display_price = sale_p or orig_p
                            offer.verification_method = VerificationMethod.EMBEDDED_STATE.value

                            if prod.get('inStock'):
                                offer.stock_status = StockStatus.IN_STOCK
                            else:
                                offer.stock_status = StockStatus.OUT_OF_STOCK

                            merchant_obj = prod.get('merchant', {})
                            if merchant_obj:
                                offer.seller = merchant_obj.get('name')
                except Exception:
                    pass

        # 2. Check JSON-LD if not found
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

        # 3. Check promotion badge: "Sepette %X İndirim"
        sepette_match = re.search(r'sepette\s*(?:ek)?\s*([\d.,]+)\s*(?:tl|₺)', html, re.I)
        if sepette_match:
            c_price = PriceNormalizer.parse(sepette_match.group(1))
            if c_price and offer.display_price and c_price < offer.display_price:
                offer.cart_price = c_price
                offer.display_price = c_price
                offer.price_condition = "Sepette İndirimli"

        if offer.stock_status == StockStatus.UNKNOWN:
            offer.stock_status = StockNormalizer.normalize(None, soup.get_text()[:4000])

        return offer
