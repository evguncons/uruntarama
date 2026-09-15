"""General Mobile product-page variant parser."""
import re
from services.adapters.generic import GenericAdapter
from services.models import ProductOffer, StockStatus, VerificationMethod
from services.normalizers import PriceNormalizer
from services.product_matcher import ProductMatcher


class GeneralMobileAdapter(GenericAdapter):
    MERCHANT_NAME = 'General Mobile Resmi Mağazası'
    DOMAINS = ['generalmobile.com']

    def parse(self, url, html, soup, expected_product):
        base_title = soup.h1.get_text(' ', strip=True) if soup.h1 else 'General Mobile GM 26 Pro 5G'
        matching = []
        bare_ram = re.search(r'\b(8|12)\s+(?:128|256|512)\s*(?:gb)?\b', expected_product.casefold())
        for card in soup.select('.payment-1'):
            text = card.get_text(' ', strip=True)
            confidence, _ = ProductMatcher.match_product(expected_product, base_title + ' ' + text)
            if confidence >= .75 and (not bare_ram or re.search(r'\b' + bare_ram.group(1) + r'\s*gb\b', text, re.I)):
                matching.append((card, text))
        offer = ProductOffer(merchant=self.MERCHANT_NAME, model=base_title)
        if not matching:
            return offer
        prices = set()
        statuses = set()
        for card, text in matching:
            node = card.select_one('.money_payment')
            prices.add(PriceNormalizer.parse(node.get_text(' ', strip=True) if node else None))
            statuses.add(StockStatus.OUT_OF_STOCK if 'stokta yok' in text.casefold() else StockStatus.IN_STOCK)
        # If an unspecified colour maps to equivalent offers, the model/capacity remains unambiguous.
        prices.discard(None)
        if len(prices) == 1 and len(statuses) == 1:
            offer.regular_price = offer.display_price = next(iter(prices))
            offer.stock_status = next(iter(statuses))
            offer.product_evidence = True
            offer.verification_method = VerificationMethod.HTML_PARSER.value
        return offer
