"""Merchant Adapters and Router."""
from typing import List, Type
from services.adapters.base import BaseAdapter
from services.adapters.generic import GenericAdapter
from services.adapters.trendyol import TrendyolAdapter
from services.adapters.hepsiburada import HepsiburadaAdapter
from services.adapters.vatan import VatanAdapter
from services.adapters.aggregators import AkakceAdapter, CimriAdapter
from services.adapters.installment import TaspinarAdapter, YonavmAdapter, EvkurAdapter
from services.adapters.general_mobile import GeneralMobileAdapter

ALL_ADAPTERS: List[Type[BaseAdapter]] = [
    GeneralMobileAdapter,
    TrendyolAdapter,
    HepsiburadaAdapter,
    VatanAdapter,
    AkakceAdapter,
    CimriAdapter,
    TaspinarAdapter,
    YonavmAdapter,
    EvkurAdapter,
]

def get_adapter_for_url(url: str) -> BaseAdapter:
    """Return matching adapter for URL or fallback to GenericAdapter."""
    if not url:
        return GenericAdapter()
    for adapter_cls in ALL_ADAPTERS:
        if adapter_cls.matches_url(url):
            return adapter_cls()
    return GenericAdapter()

__all__ = [
    "BaseAdapter",
    "GenericAdapter",
    "TrendyolAdapter",
    "HepsiburadaAdapter",
    "VatanAdapter",
    "AkakceAdapter",
    "CimriAdapter",
    "TaspinarAdapter",
    "YonavmAdapter",
    "EvkurAdapter",
    "get_adapter_for_url"
]
