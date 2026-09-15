"""Data models and enums for product verification and pricing."""
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

class StockStatus(str, Enum):
    IN_STOCK = "IN_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    LOW_STOCK = "LOW_STOCK"
    PREORDER = "PREORDER"
    VARIANT_OUT_OF_STOCK = "VARIANT_OUT_OF_STOCK"
    UNKNOWN = "UNKNOWN"

class UrlStatus(str, Enum):
    VALID = "VALID"
    REDIRECTED = "REDIRECTED"
    NOT_FOUND = "NOT_FOUND"
    GONE = "GONE"
    BLOCKED = "BLOCKED"
    TIMEOUT = "TIMEOUT"
    INVALID_URL = "INVALID_URL"
    PRODUCT_MISMATCH = "PRODUCT_MISMATCH"
    NON_PRODUCT_PAGE = "NON_PRODUCT_PAGE"
    UNKNOWN = "UNKNOWN"

class FetchStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    TIMEOUT = "TIMEOUT"
    PARSE_ERROR = "PARSE_ERROR"
    PRODUCT_MISMATCH = "PRODUCT_MISMATCH"

class VerificationMethod(str, Enum):
    STORE_API = "STORE_API"
    JSON_LD = "JSON_LD"
    EMBEDDED_STATE = "EMBEDDED_STATE"
    HTML_PARSER = "HTML_PARSER"
    TEXT_FALLBACK = "TEXT_FALLBACK"
    DISCOVERY_FALLBACK = "DISCOVERY_FALLBACK"

@dataclass
class ProductOffer:
    merchant: str
    candidate_url: str = ""
    source_url: str = ""
    final_url: str = ""
    canonical_url: str = ""
    url_status: UrlStatus = UrlStatus.UNKNOWN
    url_verified: bool = False
    url_verified_at: str = ""
    seller: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    mpn: Optional[str] = None
    gtin: Optional[str] = None
    variant: Optional[str] = None
    regular_price: Optional[float] = None
    sale_price: Optional[float] = None
    cart_price: Optional[float] = None
    member_price: Optional[float] = None
    coupon_price: Optional[float] = None
    display_price: Optional[float] = None
    currency: str = "TRY"
    price_condition: Optional[str] = None
    stock_status: StockStatus = StockStatus.UNKNOWN
    stock_quantity: Optional[int] = None
    match_confidence: float = 0.0
    verification_method: str = VerificationMethod.DISCOVERY_FALLBACK.value
    verified: bool = False
    checked_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str = ""
    fetch_status: FetchStatus = FetchStatus.SUCCESS
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['stock_status'] = self.stock_status.value if isinstance(self.stock_status, StockStatus) else self.stock_status
        d['fetch_status'] = self.fetch_status.value if isinstance(self.fetch_status, FetchStatus) else self.fetch_status
        d['url_status'] = self.url_status.value if isinstance(self.url_status, UrlStatus) else self.url_status
        return d
