import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.services.idx_sharia_stock_list import (
    _google_sheet_csv_url,
    get_idx_sharia_stock_codes,
    parse_idx_sharia_sheet_csv,
)
from src.config import Config


def test_google_sheet_url_is_converted_to_csv_export() -> None:
    assert _google_sheet_csv_url(
        "https://docs.google.com/spreadsheets/d/sheet-id/edit?gid=10"
    ) == "https://docs.google.com/spreadsheets/d/sheet-id/export?format=csv"


def test_google_sheet_url_rejects_non_google_hosts() -> None:
    with pytest.raises(ValueError, match="HTTPS Google Sheets URL"):
        _google_sheet_csv_url("https://example.com/spreadsheets/d/id")


def test_parser_selects_only_issi_yes_and_adds_yahoo_suffix() -> None:
    payload = (
        "No.,Kode  Saham,Nama Penerbit Efek,ISSI\n"
        "1,BBCA,Bank Central Asia Tbk,Ya\n"
        "2,BBNI,Bank Negara Indonesia Tbk,Tidak\n"
    ).encode()

    assert parse_idx_sharia_sheet_csv(payload) == ["BBCA.JK"]


@pytest.mark.parametrize(
    "payload",
    [
        b"ticker,name\nBBCA,Bank\n",
        b"Kode Saham,ISSI\nBBCA,Mungkin\n",
        b"Kode Saham,ISSI\nBBCA,Ya\nBBCA,Tidak\n",
        b"Kode Saham,ISSI\nBBCA,Tidak\n",
    ],
)
def test_parser_rejects_invalid_or_empty_issi_lists(payload: bytes) -> None:
    with pytest.raises(ValueError):
        parse_idx_sharia_sheet_csv(payload)


def test_fetch_uses_cached_snapshot_when_sheet_is_unavailable(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(
        json.dumps({"fetched_at": "2026-08-11T00:00:00+00:00", "codes": ["BBCA.JK"]}),
        encoding="utf-8",
    )

    with patch(
        "src.services.idx_sharia_stock_list._download_sheet_csv",
        side_effect=OSError("offline"),
    ):
        assert get_idx_sharia_stock_codes(
            "https://docs.google.com/spreadsheets/d/id/edit",
            cache_path=cache_path,
        ) == ["BBCA.JK"]


def test_fetch_fails_explicitly_without_sheet_or_cache(tmp_path: Path) -> None:
    with patch(
        "src.services.idx_sharia_stock_list._download_sheet_csv",
        side_effect=OSError("offline"),
    ):
        with pytest.raises(RuntimeError, match="no valid local snapshot"):
            get_idx_sharia_stock_codes(
                "https://docs.google.com/spreadsheets/d/id/edit",
                cache_path=tmp_path / "missing.json",
            )


def test_fetch_rejects_invalid_configured_url_even_when_cache_exists(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(
        json.dumps({"fetched_at": "2026-08-11T00:00:00+00:00", "codes": ["BBCA.JK"]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="HTTPS Google Sheets URL"):
        get_idx_sharia_stock_codes("https://example.com/sheets", cache_path=cache_path)


def test_config_refresh_uses_sheet_over_stock_list(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "STOCK_LIST=600519\n"
        "IDX_SHARIA_STOCKS_SHEET_URL=https://docs.google.com/spreadsheets/d/sheet-id/edit\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ENV_FILE", str(env_file))
    monkeypatch.delenv("STOCK_LIST", raising=False)
    monkeypatch.delenv("IDX_SHARIA_STOCKS_SHEET_URL", raising=False)
    monkeypatch.setattr(
        "src.services.idx_sharia_stock_list.get_idx_sharia_stock_codes",
        lambda url: ["BBCA.JK"] if "sheet-id" in url else [],
    )
    config = Config(stock_list=["600519"])

    config.refresh_stock_list()

    assert config.stock_list == ["BBCA.JK"]
    assert config.idx_sharia_stocks_sheet_url.endswith("/sheet-id/edit")


def test_config_refresh_does_not_keep_unfiltered_list_after_sheet_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "STOCK_LIST=600519\n"
        "IDX_SHARIA_STOCKS_SHEET_URL=https://docs.google.com/spreadsheets/d/sheet-id/edit\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ENV_FILE", str(env_file))
    monkeypatch.delenv("STOCK_LIST", raising=False)
    monkeypatch.delenv("IDX_SHARIA_STOCKS_SHEET_URL", raising=False)

    def fail_refresh(url: str) -> list[str]:
        raise RuntimeError("no valid local snapshot")

    monkeypatch.setattr(
        "src.services.idx_sharia_stock_list.get_idx_sharia_stock_codes",
        fail_refresh,
    )
    config = Config(stock_list=["600519"])

    with pytest.raises(RuntimeError, match="no valid local snapshot"):
        config.refresh_stock_list()

    assert config.stock_list == []
