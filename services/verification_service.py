"""Offer Verification Service.
Coordinates live data fetching, store-specific parsing, product matching, and caching.
Enforces strict URL validation before setting source_url.
"""
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from services.models import ProductOffer, StockStatus, FetchStatus, VerificationMethod, UrlStatus
from services.cache_service import OfferCacheService
from services.live_fetcher import LiveProductFetcher
from services.adapters import get_adapter_for_url
from services.product_matcher import ProductMatcher
from services.normalizers import UrlNormalizer, PriceNormalizer
from services.url_validation_service import UrlValidationService

logger = logging.getLogger(__name__)

class OfferVerificationService:
    def __init__(self, cache_service: Optional[OfferCacheService] = None, live_fetcher: Optional[LiveProductFetcher] = None):
        self.cache = cache_service or OfferCacheService()
        self.fetcher = live_fetcher or LiveProductFetcher()

    def verify_single_offer(self, expected_product: str, candidate: Dict[str, Any]) -> ProductOffer:
        """Verify a single candidate offer against the live store page.
        Candidate URL is never passed directly to frontend as source_url without validation.
        """
        raw_url = candidate.get('url', '').strip()
        merchant = candidate.get('merchant') or candidate.get('platform') or 'Bilinmeyen Mağaza'
        initial_price = PriceNormalizer.parse(candidate.get('price'))

        if not raw_url:
            return ProductOffer(
                merchant=merchant,
                candidate_url='',
                source_url='',
                url_status=UrlStatus.INVALID_URL,
                url_verified=False,
                url_verified_at=datetime.now(timezone.utc).isoformat(),
                display_price=initial_price,
                stock_status=StockStatus.UNKNOWN,
                fetch_status=FetchStatus.FAILED,
                notes='Geçersiz veya boş URL'
            )

        # 1. Check cache
        cached = self.cache.get(raw_url)
        if cached:
            return cached

        # 2. Live fetch
        fetch_res = self.fetcher.fetch(raw_url)
        final_url = fetch_res.get('final_url') or raw_url
        status = fetch_res.get('status', FetchStatus.FAILED)

        # 3. Handle fetch failure or bot protection (403/Cloudflare/404)
        if status != FetchStatus.SUCCESS:
            url_status = UrlStatus.UNKNOWN
            if status == FetchStatus.BLOCKED:
                url_status = UrlStatus.BLOCKED
            elif status == FetchStatus.TIMEOUT:
                url_status = UrlStatus.TIMEOUT
            elif status == FetchStatus.FAILED:
                url_status = UrlStatus.NOT_FOUND

            offer = ProductOffer(
                merchant=merchant,
                candidate_url=raw_url,
                source_url="",  # Do NOT send dead/unverified URL to frontend
                final_url=final_url,
                canonical_url=UrlNormalizer.canonicalize(final_url),
                url_status=url_status,
                url_verified=False,
                url_verified_at=datetime.now(timezone.utc).isoformat(),
                regular_price=initial_price,
                display_price=initial_price,
                stock_status=StockStatus.UNKNOWN,  # Crucial: NEVER OUT_OF_STOCK on error
                verification_method=VerificationMethod.DISCOVERY_FALLBACK.value,
                fetch_status=status,
                verified=False,
                notes=f'Canlı teyit yapılamadı ({status.value}): Son tespit edilen fiyat gösterilmektedir'
            )
            # Short cache for failed fetches so we don't bombard
            self.cache.set(raw_url, offer)
            return offer

        # 4. Parse live page using matching adapter
        html = fetch_res.get('html', '')
        soup = BeautifulSoup(html, 'html.parser')
        adapter = get_adapter_for_url(final_url)
        
        try:
            offer = adapter.parse(final_url, html, soup, expected_product)
        except Exception as e:
            logger.warning(f'Adapter parse error for {raw_url}: {e}')
            offer = ProductOffer(
                merchant=merchant,
                candidate_url=raw_url,
                source_url="",
                final_url=final_url,
                canonical_url=UrlNormalizer.canonicalize(final_url),
                url_status=UrlStatus.UNKNOWN,
                url_verified=False,
                url_verified_at=datetime.now(timezone.utc).isoformat(),
                regular_price=initial_price,
                display_price=initial_price,
                stock_status=StockStatus.UNKNOWN,
                fetch_status=FetchStatus.PARSE_ERROR,
                notes=f'Sayfa ayrıştırma hatası: {str(e)}'
            )
            return offer

        offer.candidate_url = raw_url
        if not offer.merchant or offer.merchant == 'Genel Mağaza':
            offer.merchant = merchant

        # 5. Verify product match against expected product
        scraped_title = offer.model or ''
        confidence, reasons = ProductMatcher.match_product(expected_product, scraped_title)
        offer.match_confidence = confidence

        if confidence < 0.75:
            # Model mismatch detected (e.g. S25 instead of S25 FE, or wrong capacity/accessory)
            offer.fetch_status = FetchStatus.PRODUCT_MISMATCH
            offer.url_status = UrlStatus.PRODUCT_MISMATCH
            offer.url_verified = False
            offer.source_url = ""  # Block mismatch URL from frontend "Ürüne Git"
            offer.verified = False
            offer.notes = f'Ürün uyuşmazlığı ({confidence:.2f}): ' + ', '.join(reasons)
            if any('Aksesuar' in r or 'Seri' in r for r in reasons):
                offer.display_price = None
                offer.regular_price = None
        else:
            # Match is accepted
            offer.verified = True
            offer.url_verified = True
            offer.url_verified_at = datetime.now(timezone.utc).isoformat()
            offer.url_status = UrlStatus.REDIRECTED if (final_url != raw_url) else UrlStatus.VALID
            offer.source_url = final_url
            offer.final_url = final_url
            offer.canonical_url = UrlNormalizer.canonicalize(final_url)

            # If price was not found on live page, fallback to discovery price with clear note
            if not offer.display_price and initial_price:
                offer.regular_price = initial_price
                offer.display_price = initial_price
                offer.verification_method = VerificationMethod.DISCOVERY_FALLBACK.value
                offer.notes = 'Canlı fiyata ulaşılamadı; son indekslenen fiyat gösteriliyor'

        # 6. Cache and return
        self.cache.set(raw_url, offer)
        return offer

    def verify_offers(self, expected_product: str, candidates: List[Dict[str, Any]], max_workers: int = 5) -> List[ProductOffer]:
        """Concurrently verify a list of candidate offers."""
        if not candidates:
            return []

        results: List[Optional[ProductOffer]] = [None] * len(candidates)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(self.verify_single_offer, expected_product, cand): idx
                for idx, cand in enumerate(candidates)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as exc:
                    cand = candidates[idx]
                    results[idx] = ProductOffer(
                        merchant=cand.get('merchant', 'Bilinmeyen'),
                        candidate_url=cand.get('url', ''),
                        source_url='',
                        url_status=UrlStatus.UNKNOWN,
                        url_verified=False,
                        display_price=PriceNormalizer.parse(cand.get('price')),
                        stock_status=StockStatus.UNKNOWN,
                        fetch_status=FetchStatus.FAILED,
                        notes=f'İşlem hatası: {str(exc)}'
                    )

        return [r for r in results if r is not None]
