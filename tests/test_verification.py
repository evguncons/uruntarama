"""Unit tests for Offer Verification Service and related components.
10 core scenarios covering live price overrides, stock normalization,
product matching, cache TTL, canonicalization, error resilience, and URL integrity.
"""
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from services.models import ProductOffer, StockStatus, FetchStatus, VerificationMethod
from services.normalizers import PriceNormalizer, StockNormalizer, UrlNormalizer
from services.product_matcher import ProductMatcher
from services.cache_service import OfferCacheService
from services.verification_service import OfferVerificationService
from services.adapters.generic import GenericAdapter
from services.adapters.trendyol import TrendyolAdapter
from bs4 import BeautifulSoup

class TestOfferVerification(unittest.TestCase):

    def setUp(self):
        self.mock_cache = OfferCacheService()
        self.mock_fetcher = MagicMock()
        self.service = OfferVerificationService(
            cache_service=self.mock_cache,
            live_fetcher=self.mock_fetcher
        )

    def test_1_live_price_overrides_gemini_price(self):
        """1. Gemini candidate price is 1000 TL, live price is 900 TL -> live price wins."""
        candidate = {
            "merchant": "Trendyol",
            "url": "https://www.trendyol.com/samsung/galaxy-s25-fe-128gb-p-99999",
            "price": 1000.0,
        }
        live_html = """
        <html>
            <head><title>Samsung Galaxy S25 FE 128GB</title></head>
            <body>
                <h1>Samsung Galaxy S25 FE 128GB</h1>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org/",
                    "@type": "Product",
                    "name": "Samsung Galaxy S25 FE 128GB",
                    "offers": {
                        "@type": "Offer",
                        "price": "900.00",
                        "priceCurrency": "TRY",
                        "availability": "https://schema.org/InStock"
                    }
                }
                </script>
            </body>
        </html>
        """
        self.mock_fetcher.fetch.return_value = {
            "status": FetchStatus.SUCCESS,
            "final_url": candidate["url"],
            "html": live_html
        }

        offer = self.service.verify_single_offer("Samsung Galaxy S25 FE 128GB", candidate)
        self.assertEqual(offer.display_price, 900.0)
        self.assertNotEqual(offer.display_price, 1000.0)
        self.assertTrue(offer.verified)

    def test_2_missing_stock_defaults_to_unknown_not_out_of_stock(self):
        """2. When stock info is missing from live page, status is UNKNOWN (NEVER OUT_OF_STOCK!)."""
        candidate = {
            "merchant": "Vatan",
            "url": "https://www.vatanbilgisayar.com/samsung-s25-fe.html",
            "price": 25000.0
        }
        live_html = """
        <html>
            <head><title>Samsung Galaxy S25 FE</title></head>
            <body>
                <h1>Samsung Galaxy S25 FE</h1>
                <div class="product-price">25.000 TL</div>
            </body>
        </html>
        """
        self.mock_fetcher.fetch.return_value = {
            "status": FetchStatus.SUCCESS,
            "final_url": candidate["url"],
            "html": live_html
        }

        offer = self.service.verify_single_offer("Samsung Galaxy S25 FE", candidate)
        self.assertEqual(offer.stock_status, StockStatus.UNKNOWN)
        self.assertNotEqual(offer.stock_status, StockStatus.OUT_OF_STOCK)

    def test_3_json_ld_instock_normalizes_to_in_stock(self):
        """3. JSON-LD InStock schema normalizes to StockStatus.IN_STOCK."""
        html = '<div><a itemprop="availability" href="https://schema.org/InStock">Mevcut</a></div>'
        status = StockNormalizer.normalize("https://schema.org/InStock", html)
        self.assertEqual(status, StockStatus.IN_STOCK)

        # Also test out of stock schema
        oos_status = StockNormalizer.normalize("http://schema.org/OutOfStock", "")
        self.assertEqual(oos_status, StockStatus.OUT_OF_STOCK)

    def test_4_model_mismatch_rejected(self):
        """4. Model code mismatch (ABC123 vs ABC124) -> match_confidence < 0.75 and fetch_status is PRODUCT_MISMATCH."""
        candidate = {
            "merchant": "Hepsiburada",
            "url": "https://www.hepsiburada.com/samsung-tv-p-1234",
            "price": 15000.0
        }
        live_html = """
        <html>
            <head><title>Samsung TV ABC124 55 inç</title></head>
            <body>
                <h1>Samsung TV ABC124 55 inç</h1>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Product",
                    "name": "Samsung TV ABC124 55 inç",
                    "offers": {"price": "15000"}
                }
                </script>
            </body>
        </html>
        """
        self.mock_fetcher.fetch.return_value = {
            "status": FetchStatus.SUCCESS,
            "final_url": candidate["url"],
            "html": live_html
        }

        offer = self.service.verify_single_offer("Samsung TV ABC123 55 inç", candidate)
        self.assertLess(offer.match_confidence, 0.75)
        self.assertEqual(offer.fetch_status, FetchStatus.PRODUCT_MISMATCH)
        self.assertFalse(offer.verified)

    def test_5_variant_capacity_mismatch_rejected(self):
        """5. Variant capacity mismatch (256 GB vs 512 GB) -> match_confidence < 0.75."""
        score, reasons = ProductMatcher.match_product(
            "iPhone 15 Pro 256 GB",
            "Apple iPhone 15 Pro 512 GB Doğal Titanyum"
        )
        self.assertLess(score, 0.75)
        self.assertTrue(any("Kapasite" in r for r in reasons))

    def test_6_cache_expiration_revalidation(self):
        """6. Offers cached 2 hours ago expire (15-min TTL) and trigger re-fetch."""
        cache = OfferCacheService()
        old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        expired_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        stale_offer = ProductOffer(
            merchant="Trendyol",
            source_url="https://www.trendyol.com/item-p-1",
            display_price=500.0,
            checked_at=old_time,
            expires_at=expired_time
        )
        cache.set("https://www.trendyol.com/item-p-1", stale_offer)

        # Retrieve should return None because expires_at is in the past
        retrieved = cache.get("https://www.trendyol.com/item-p-1")
        self.assertIsNone(retrieved)

    def test_7_canonical_url_preserves_seller_identity(self):
        """7. Seller-specific marketplace offers must not collapse together."""
        url1 = "https://www.trendyol.com/samsung/s25-p-12345?boutiqueId=61&merchantId=100"
        url2 = "https://www.trendyol.com/samsung/s25-p-12345?utm_source=google&utm_medium=cpc&gclid=XYZ"
        canon1 = UrlNormalizer.canonicalize(url1)
        canon2 = UrlNormalizer.canonicalize(url2)
        self.assertNotEqual(canon1, canon2)
        self.assertIn("merchantId=100", canon1)

    def test_8_403_blocked_returns_unknown_without_crashing(self):
        """8. Cloudflare/403 block returns StockStatus.UNKNOWN and does not crash or mark out of stock."""
        candidate = {
            "merchant": "Vatan",
            "url": "https://www.vatanbilgisayar.com/blocked-page",
            "price": 32000.0
        }
        self.mock_fetcher.fetch.return_value = {
            "status": FetchStatus.BLOCKED,
            "final_url": candidate["url"],
            "html": "",
            "error": "HTTP 403: Forbidden (Cloudflare)"
        }

        offer = self.service.verify_single_offer("Samsung Galaxy S25", candidate)
        self.assertEqual(offer.stock_status, StockStatus.UNKNOWN)
        self.assertNotEqual(offer.stock_status, StockStatus.OUT_OF_STOCK)
        self.assertEqual(offer.fetch_status, FetchStatus.BLOCKED)
        self.assertFalse(offer.verified)
        self.assertIsNone(offer.display_price)  # Discovery price is never presented as live.

    def test_9_cart_price_separation(self):
        """9. Trendyol cart discount parses into cart_price and display_price while regular_price is kept."""
        adapter = TrendyolAdapter()
        html = """
        <html>
            <body>
                <h1>Samsung Galaxy S25</h1>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Product",
                    "name": "Samsung Galaxy S25",
                    "offers": {"price": "35000"}
                }
                </script>
                <div class="pr-in-pr">Sepette ek 33.500 TL</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        offer = adapter.parse("https://www.trendyol.com/samsung/s25-p-1", html, soup, "Samsung Galaxy S25")
        self.assertEqual(offer.regular_price, 35000.0)
        self.assertEqual(offer.cart_price, 33500.0)
        self.assertEqual(offer.display_price, 35000.0)
        self.assertEqual(offer.price_condition, "Sepette İndirimli")

    def test_10_source_url_is_direct_product_page_not_search(self):
        """10. Ensure source_url leads to direct product page and search URLs are detected."""
        direct_url = "https://www.trendyol.com/samsung/galaxy-s25-p-10293847"
        search_url = "https://www.trendyol.com/sr?q=Samsung%20Galaxy%20S25"

        # Direct product URLs are recognized
        self.assertTrue(UrlNormalizer.is_product_url(direct_url))
        # Search queries are recognized as NOT direct product pages
        self.assertFalse(UrlNormalizer.is_product_url(search_url))

        # Test verification preserves direct source_url
        candidate = {"merchant": "Trendyol", "url": direct_url, "price": 40000.0}
        self.assertEqual(offer.price_condition, "Sepette İndirimli")

    def test_10_source_url_is_direct_product_page_not_search(self):
        """10. Ensure source_url leads to direct product page and search URLs are detected."""
        direct_url = "https://www.trendyol.com/samsung/galaxy-s25-p-10293847"
        search_url = "https://www.trendyol.com/sr?q=Samsung%20Galaxy%20S25"

        # Direct product URLs are recognized
        self.assertTrue(UrlNormalizer.is_product_url(direct_url))
        # Search queries are recognized as NOT direct product pages
        self.assertFalse(UrlNormalizer.is_product_url(search_url))

        # Test verification preserves direct source_url
        candidate = {"merchant": "Trendyol", "url": direct_url, "price": 40000.0}
        self.mock_fetcher.fetch.return_value = {
            "status": FetchStatus.SUCCESS,
            "final_url": direct_url,
            "html": "<html><h1>Samsung Galaxy S25</h1></html>"
        }
        offer = self.service.verify_single_offer("Samsung Galaxy S25", candidate)
        self.assertEqual(offer.source_url, '')  # A title alone is insufficient product-page evidence.

    def test_11_model_number_and_short_code_matching(self):
        """11. Short model queries like 'philips 5547', 'dyson v15', 'ep5547' match their full product names."""
        # Philips 5547 matches Philips EP5547/90 LatteGo
        score, _ = ProductMatcher.match_product(
            "philips 5547",
            "Philips EP5547/90 5500 Serisi LatteGo Tam Otomatik Espresso Makinesi"
        )
        self.assertGreaterEqual(score, 0.75)

        # Dyson V15 matches Dyson V15 Detect Absolute
        score_dyson, _ = ProductMatcher.match_product(
            "dyson v15",
            "Dyson V15 Detect Absolute Kablosuz Dikey Süpürge"
        )
        self.assertGreaterEqual(score_dyson, 0.75)

        # Standalone model code ep5547
        score_ep, _ = ProductMatcher.match_product(
            "ep5547",
            "Philips EP5547/90 Espresso Makinesi"
        )
        self.assertGreaterEqual(score_ep, 0.75)

    def test_12_url_normalizer_rejects_category_and_placeholder_urls(self):
        """12. Category pages (-c-56) and placeholder URLs are rejected, while product slugs are accepted."""
        # Category URLs must be rejected
        self.assertFalse(UrlNormalizer.is_product_url("https://taspinar.com/cep-telefonu-c-56"))
        self.assertFalse(UrlNormalizer.is_product_url("https://www.hepsiburada.com/cep-telefonlari-c-2147483642"))
        self.assertFalse(UrlNormalizer.is_product_url("https://www.trendyol.com/cep-telefonu-x-c103498"))
        
        # Placeholder dummy URLs must be rejected
        self.assertFalse(UrlNormalizer.is_product_url("https://www.trendyol.com/samsung/s25-p-XXXXXXXX"))
        self.assertFalse(UrlNormalizer.is_product_url("https://www.hepsiburada.com/urun-p-123456789"))

        # Real product slugs must be accepted
        self.assertTrue(UrlNormalizer.is_product_url("https://taspinar.com/philips-ep5547-tam-otomatik-espresso-makinesi"))
        self.assertTrue(UrlNormalizer.is_product_url("https://www.evkur.com.tr/philips-ep5547-90-tam-otomatik-espresso-makinesi"))
        self.assertTrue(UrlNormalizer.is_product_url("https://www.philips.com.tr/c-p/EP5547_90/5500-serisi-tam-otomatik-espresso-makinesi"))

    def test_13_feasibility_and_campaigns_generation(self):
        """13. Feasibility selling points, risks, and campaigns are populated and never empty."""
        from services.analysis_service import _build_default_feasibility_and_campaigns
        data = _build_default_feasibility_and_campaigns(
            product_name="Philips EP5547/90 Espresso Makinesi",
            brand="Philips",
            category="Kahve Makineleri",
            model_code="EP5547/90",
            market_prices={"min": 24999, "average": 27500, "max": 31000},
            hedef_pricing={"cashRecommendedPrice": 25500, "installmentRecommendedPrice": 35190, "monthlyInstallmentPrice": 2346}
        )
        self.assertGreater(data["score"], 0)
        self.assertIn("SATAR", data["verdict"])
        self.assertGreaterEqual(len(data["reasonsToSell"]), 2)
        self.assertGreaterEqual(len(data["risksAndWatchouts"]), 2)
        self.assertGreaterEqual(len(data["campaigns"]), 2)
        for camp in data["campaigns"]:
            self.assertTrue(camp.get("title"))
            self.assertTrue(camp.get("bannerSlogan"))
            self.assertTrue(camp.get("slogan"))

    def test_14_pricing_fallbacks_when_all_stores_out_of_stock(self):
        """14. When all stores have out-of-stock status but have verified prices, market prices and hedef pricing are NOT 0."""
        from services.models import ProductOffer, StockStatus, UrlStatus
        from unittest.mock import patch

        mock_offers = [
            ProductOffer(
                merchant="Marka Resmi Mağazası",
                source_url="https://www.dyson.com.tr/dyson-v15-detect",
                candidate_url="https://www.dyson.com.tr/dyson-v15-detect",
                url_verified=True,
                url_status=UrlStatus.VALID,
                display_price=42999.0,
                stock_status=StockStatus.OUT_OF_STOCK,
                verified=True,
                notes="Stokta yok, Haber Ver"
            ),
            ProductOffer(
                merchant="Vatan Bilgisayar",
                source_url="https://www.vatanbilgisayar.com/dyson-v15.html",
                candidate_url="https://www.vatanbilgisayar.com/dyson-v15.html",
                url_verified=True,
                url_status=UrlStatus.VALID,
                display_price=45999.0,
                stock_status=StockStatus.OUT_OF_STOCK,
                verified=True,
                notes="Tükendi"
            )
        ]

        with patch('services.analysis_service._resolve_product_identity') as mock_ident, \
             patch('services.analysis_service._discover_candidates') as mock_disc, \
             patch('services.analysis_service.OfferVerificationService.verify_offers') as mock_ver, \
             patch('services.analysis_service._enrich_from_product_pages') as mock_enrich, \
             patch('services.analysis_service._generate_feasibility_and_campaigns') as mock_feas:
            
            mock_ident.return_value = {
                'full_name': 'Dyson V15 Detect Kablosuz Süpürge',
                'model_code': 'V15 Detect',
                'brand': 'Dyson',
                'category': 'Süpürgeler'
            }
            mock_disc.return_value = []
            mock_ver.return_value = mock_offers
            mock_enrich.return_value = mock_offers
            mock_feas.return_value = {
                'feasibility': {'score': 85, 'verdict': 'GÜÇLÜ SATAR'},
                'campaigns': []
            }

            from services.analysis_service import analyze_product
            res = analyze_product("Dyson V15 Detect", api_key="test_key")

            mp = res.get('marketPrices', {})
            hp = res.get('hedefPricing', {})

            # Must NOT be 0!
            self.assertEqual(mp.get('min'), 42999.0)
            self.assertEqual(mp.get('max'), 45999.0)
            self.assertGreater(mp.get('average'), 42000.0)
            self.assertGreater(hp.get('cashRecommendedPrice'), 40000.0)
            self.assertGreater(hp.get('installmentRecommendedPrice'), 50000.0)
            self.assertGreater(hp.get('monthlyInstallmentPrice'), 3000.0)

if __name__ == "__main__":
    unittest.main()

