"""Regression tests for Indonesia Stock Exchange (.JK) market support."""

from unittest.mock import patch

import pandas as pd

from data_provider.base import BaseFetcher, DataFetchError, DataFetcherManager, normalize_stock_code
from data_provider.yfinance_fetcher import YfinanceFetcher
from src.core.trading_calendar import MARKET_EXCHANGE, MARKET_TIMEZONE, get_market_for_stock
from src.market_context import detect_market, get_market_guidelines
from src.services.portfolio_service import PortfolioService, VALID_MARKETS
from src.services.stock_code_utils import is_code_like, normalize_code
from src.services.stock_list_parser import ParseStatus, parse_analysis_target


class _FakeFetcher(BaseFetcher):
    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.priority = 0 if name != "YfinanceFetcher" else 4
        self.calls = []
        self.should_fail = should_fail

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        raise NotImplementedError

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        raise NotImplementedError

    def get_daily_data(self, stock_code, start_date=None, end_date=None, days=30):
        self.calls.append(stock_code)
        if self.should_fail:
            raise DataFetchError(f"{self.name} should not be called for {stock_code}")
        return pd.DataFrame(
            {
                "date": [pd.Timestamp("2026-08-11")],
                "open": [1.0],
                "high": [1.0],
                "low": [1.0],
                "close": [1.0],
                "volume": [100],
                "amount": [100.0],
                "pct_chg": [0.0],
            }
        )


def test_idx_symbols_are_normalized_and_classified_as_indonesia() -> None:
    assert normalize_stock_code("bbca.jk") == "BBCA.JK"
    assert normalize_code("bbca.jk") == "BBCA.JK"
    assert is_code_like("bbca.jk") is True
    assert detect_market("BBCA.JK") == "id"
    assert get_market_for_stock("BBCA.JK") == "id"
    assert parse_analysis_target("BBCA.JK").asset_type == ParseStatus.STOCK


def test_yfinance_keeps_idx_suffix_and_routes_daily_data_only_to_yfinance() -> None:
    yfinance = YfinanceFetcher()
    assert yfinance._convert_stock_code("BBCA.JK") == "BBCA.JK"

    efinance = _FakeFetcher("EfinanceFetcher", should_fail=True)
    akshare = _FakeFetcher("AkshareFetcher", should_fail=True)
    yfinance_stub = _FakeFetcher("YfinanceFetcher")
    manager = DataFetcherManager(fetchers=[efinance, akshare, yfinance_stub])

    with patch("data_provider.base.record_provider_run_started"), patch(
        "data_provider.base.record_provider_run"
    ):
        data, source = manager.get_daily_data("BBCA.JK")

    assert source == "YfinanceFetcher"
    assert not data.empty
    assert efinance.calls == []
    assert akshare.calls == []
    assert yfinance_stub.calls == ["BBCA.JK"]


def test_idx_market_context_and_currency_are_not_treated_as_a_shares() -> None:
    assert "Indonesian stock" in get_market_guidelines("BBCA.JK", lang="en")
    assert "A-share" in get_market_guidelines("BBCA.JK", lang="en")
    assert "id" in VALID_MARKETS
    assert PortfolioService._default_currency_for_market("id") == "IDR"


def test_idx_trading_calendar_uses_jakarta_timezone() -> None:
    assert MARKET_EXCHANGE["id"] == "XIDX"
    assert MARKET_TIMEZONE["id"] == "Asia/Jakarta"
