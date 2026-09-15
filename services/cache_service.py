"""Thread-safe in-memory and disk-backed cache for verified product offers."""
import threading
import time
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
from services.models import ProductOffer, StockStatus, FetchStatus, UrlStatus
from services.normalizers import UrlNormalizer

class OfferCacheService:
    DEFAULT_TTL_SECONDS = 900 # 15 minutes
    STABLE_STORE_TTL_SECONDS = 1800 # 30 minutes for official/stable sites

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(OfferCacheService, cls).__new__(cls)
                    cls._instance._init_cache()
        return cls._instance

    def _init_cache(self):
        self._cache: Dict[str, Dict] = {}
        self._cache_lock = threading.RLock()
        self._cache_file = os.path.join(os.path.dirname(__file__), '..', '.offer_cache.json')
        self._load_disk_cache()

    def _load_disk_cache(self):
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
        except Exception:
            self._cache = {}

    def _save_disk_cache(self):
        try:
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False)
        except Exception:
            pass

    def _cache_key(self, url: str, product_context: str = "") -> str:
        canonical = UrlNormalizer.canonicalize(url)
        base = canonical if canonical else url.strip()
        return base + ('||' + product_context.casefold().strip() if product_context else '')

    def get(self, url: str, product_context: str = "") -> Optional[ProductOffer]:
        key = self._cache_key(url, product_context)
        with self._cache_lock:
            entry = self._cache.get(key)
            if not entry:
                return None

            expires_at = entry.get('expires_at')
            if expires_at:
                try:
                    exp_dt = datetime.fromisoformat(expires_at)
                    if datetime.now(timezone.utc) > exp_dt:
                        # Expired
                        return None
                except Exception:
                    return None

            # Reconstruct ProductOffer
            try:
                data = entry.copy()
                data['stock_status'] = StockStatus(data['stock_status'])
                data['fetch_status'] = FetchStatus(data['fetch_status'])
                data['url_status'] = UrlStatus(data.get('url_status', 'UNKNOWN'))
                return ProductOffer(**data)
            except Exception:
                return None

    def set(self, offer_or_url, offer_obj=None, ttl_seconds: Optional[int] = None, product_context: str = ""):
        if isinstance(offer_or_url, str) and offer_obj is not None:
            offer = offer_obj
            url = offer_or_url
        elif hasattr(offer_or_url, 'source_url'):
            offer = offer_or_url
            url = offer.source_url
            if isinstance(offer_obj, (int, float)):
                ttl_seconds = int(offer_obj)
        else:
            return

        key = self._cache_key(url, product_context)
        if not key:
            return

        now = datetime.now(timezone.utc)
        if offer.expires_at and ttl_seconds is None:
            expires_str = offer.expires_at
        else:
            ttl = ttl_seconds if ttl_seconds is not None else self.DEFAULT_TTL_SECONDS
            expires = now + timedelta(seconds=ttl)
            expires_str = expires.isoformat()
            offer.checked_at = now.isoformat()

        offer.expires_at = expires_str

        with self._cache_lock:
            self._cache[key] = offer.to_dict()
            self._save_disk_cache()

    def clear(self):
        with self._cache_lock:
            self._cache.clear()
            self._save_disk_cache()
