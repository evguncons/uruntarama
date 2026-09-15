"""Unit tests for URL Validation and Alternative URL Discovery Service.
Covers 7 critical scenarios:
1. Candidate URL -> 404 -> url_verified = False, url_status = NOT_FOUND
2. Candidate URL -> 301 -> new URL -> 200 -> source_url = new_url, url_status = REDIRECTED, url_verified = True
3. URL -> 200 with soft 404 ("Ürün bulunamadı") -> NON_PRODUCT_PAGE, url_verified = False
4. URL -> 200 with product mismatch (S25 FE vs A15 Kılıf) -> PRODUCT_MISMATCH, url_verified = False
5. URL with variant/sku parameters preserved by UrlNormalizer
6. URL with tracking parameters stripped by UrlNormalizer
7. 404 alternative URL discovery -> finds new valid URL and sets source_url
"""
import unittest
from unittest.mock import patch, MagicMock

from services.models import UrlStatus, ProductOffer
from services.normalizers import UrlNormalizer
from services.url_validation_service import UrlValidationService


class TestUrlValidationService(unittest.TestCase):

    @patch.object(UrlValidationService, '_http_get')
    def test_1_candidate_url_404_not_found(self, mock_http):
        """1. Candidate URL returning HTTP 404 -> url_verified = False, url_status = NOT_FOUND."""
        mock_http.return_value = (404, "https://www.taspinar.com/olmayan-urun-p-999", "", None, UrlStatus.NOT_FOUND)
        
        offer = UrlValidationService.validate_product_url(
            candidate_url="https://www.taspinar.com/olmayan-urun-p-999",
            expected_product="Samsung Galaxy S25 FE 128GB",
            attempt_recovery=False
        )

        self.assertFalse(offer.url_verified)
        self.assertEqual(offer.url_status, UrlStatus.NOT_FOUND)
        self.assertEqual(offer.source_url, "")

    @patch.object(UrlValidationService, '_http_get')
    def test_2_candidate_url_redirect_301_to_valid_product(self, mock_http):
        """2. Candidate URL returning 301 -> follows redirect -> source_url = final_url, url_status = REDIRECTED."""
        orig_url = "https://www.hepsiburada.com/eski-link-p-100"
        final_url = "https://www.hepsiburada.com/samsung-galaxy-s25-fe-128-gb-p-HBCV0000XYZ"
        valid_html = """
        <html>
            <head>
                <title>Samsung Galaxy S25 FE 128 GB Fiyatı</title>
                <link rel="canonical" href="https://www.hepsiburada.com/samsung-galaxy-s25-fe-128-gb-p-HBCV0000XYZ" />
            </head>
            <body>
                <h1>Samsung Galaxy S25 FE 128 GB</h1>
            </body>
        </html>
        """
        mock_http.return_value = (200, final_url, valid_html, final_url, None)

        offer = UrlValidationService.validate_product_url(
            candidate_url=orig_url,
            expected_product="Samsung Galaxy S25 FE 128GB"
        )

        self.assertTrue(offer.url_verified)
        self.assertEqual(offer.url_status, UrlStatus.REDIRECTED)
        self.assertEqual(offer.source_url, final_url)
        self.assertEqual(offer.canonical_url, final_url)

    @patch.object(UrlValidationService, '_http_get')
    def test_3_soft_404_on_http_200(self, mock_http):
        """3. URL returning HTTP 200 with soft-404 text -> NON_PRODUCT_PAGE, url_verified = False."""
        soft_404_html = """
        <html>
            <head><title>Aradığınız Sayfa Bulunamadı - Trendyol</title></head>
            <body>
                <h1>Üzgünüz, aradığınız ürün bulunamadı!</h1>
                <p>Bu ürün artık mevcut değil veya satıştan kaldırılmıştır.</p>
            </body>
        </html>
        """
        mock_http.return_value = (200, "https://www.trendyol.com/brand/old-item-p-123", soft_404_html, None, None)

        offer = UrlValidationService.validate_product_url(
            candidate_url="https://www.trendyol.com/brand/old-item-p-123",
            expected_product="Samsung Galaxy S25 FE 128GB",
            attempt_recovery=False
        )

        self.assertFalse(offer.url_verified)
        self.assertEqual(offer.url_status, UrlStatus.NON_PRODUCT_PAGE)
        self.assertEqual(offer.source_url, "")

    @patch.object(UrlValidationService, '_http_get')
    def test_4_product_mismatch_detected(self, mock_http):
        """4. URL returning HTTP 200 with product mismatch -> PRODUCT_MISMATCH, url_verified = False."""
        mismatch_html = """
        <html>
            <head><title>Samsung Galaxy A15 Uyumlu Şeffaf Silikon Kılıf</title></head>
            <body>
                <h1>Samsung Galaxy A15 Uyumlu Şeffaf Silikon Kılıf ve Kamera Koruma</h1>
            </body>
        </html>
        """
        mock_http.return_value = (200, "https://www.trendyol.com/kilif-p-555", mismatch_html, None, None)

        offer = UrlValidationService.validate_product_url(
            candidate_url="https://www.trendyol.com/kilif-p-555",
            expected_product="Samsung Galaxy S25 FE 128GB",
            attempt_recovery=False
        )

        self.assertFalse(offer.url_verified)
        self.assertEqual(offer.url_status, UrlStatus.PRODUCT_MISMATCH)
        self.assertEqual(offer.source_url, "")

    def test_5_url_normalizer_preserves_variant_and_sku(self):
        """5. URL with variant, sku, color, and capacity parameters is preserved by UrlNormalizer."""
        url = "https://www.trendyol.com/samsung/s25-p-123?variant=987&sku=SAM-S25-128&color=siyah&capacity=128gb"
        normalized = UrlNormalizer.normalize(url)
        self.assertIn("variant=987", normalized)
        self.assertIn("sku=SAM-S25-128", normalized)
        self.assertIn("color=siyah", normalized)
        self.assertIn("capacity=128gb", normalized)

    def test_6_url_normalizer_strips_tracking_params(self):
        """6. URL with tracking parameters (utm_*, gclid, fbclid, ref) has them stripped."""
        url = "https://www.hepsiburada.com/samsung-s25-p-456?utm_source=google&utm_medium=cpc&utm_campaign=winter&gclid=ABC123XYZ&ref=affiliate&variant=55"
        normalized = UrlNormalizer.normalize(url)
        self.assertNotIn("utm_source", normalized)
        self.assertNotIn("utm_medium", normalized)
        self.assertNotIn("utm_campaign", normalized)
        self.assertNotIn("gclid", normalized)
        self.assertNotIn("ref=", normalized)
        self.assertIn("variant=55", normalized)

    @patch.object(UrlValidationService, '_http_get')
    def test_7_alternative_url_discovery_on_404(self, mock_http):
        """7. When candidate URL gives 404, alternative URL recovery finds and validates new product URL."""
        bad_url = "https://www.trendyol.com/samsung/s25-fe-old-dead-link-p-0000"
        search_url = "https://www.trendyol.com/sr?q=Samsung%20Galaxy%20S25%20FE%20128GB"
        good_url = "https://www.trendyol.com/samsung/galaxy-s25-fe-128gb-5g-akilli-telefon-p-88888"

        search_html = f"""
        <html>
            <body>
                <div class="search-results">
                    <a href="{good_url}">Samsung Galaxy S25 FE 128GB 5G Akıllı Telefon</a>
                </div>
            </body>
        </html>
        """

        product_html = """
        <html>
            <head><title>Samsung Galaxy S25 FE 128GB 5G Akıllı Telefon</title></head>
            <body>
                <h1>Samsung Galaxy S25 FE 128GB 5G Akıllı Telefon</h1>
            </body>
        </html>
        """

        def fake_http_get(url):
            if url == bad_url:
                return (404, bad_url, "", None, UrlStatus.NOT_FOUND)
            elif "sr?q=" in url:
                return (200, url, search_html, None, None)
            elif url == good_url:
                return (200, good_url, product_html, None, None)
            return (404, url, "", None, UrlStatus.NOT_FOUND)

        mock_http.side_effect = fake_http_get

        offer = UrlValidationService.validate_product_url(
            candidate_url=bad_url,
            expected_product="Samsung Galaxy S25 FE 128GB",
            attempt_recovery=True
        )

        self.assertTrue(offer.url_verified)
        self.assertEqual(offer.url_status, UrlStatus.VALID)
        self.assertEqual(offer.source_url, good_url)
        self.assertEqual(offer.candidate_url, bad_url)


if __name__ == '__main__':
    unittest.main()
