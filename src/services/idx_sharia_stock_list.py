"""Load IDX sharia tickers from a user-provided public Google Sheet."""

from __future__ import annotations

import csv
import io
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_TICKER_PATTERN = re.compile(r"^[A-Z0-9]{2,5}$")
_SHEET_ID_PATTERN = re.compile(r"^/spreadsheets/d/([A-Za-z0-9_-]+)(?:/|$)")
DEFAULT_CACHE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "cache"
    / "idx_sharia_stock_list.json"
)


def _google_sheet_csv_url(sheet_url: str) -> str:
    parsed = urlparse((sheet_url or "").strip())
    if parsed.scheme != "https" or parsed.hostname != "docs.google.com":
        raise ValueError("IDX_SHARIA_STOCKS_SHEET_URL must be an HTTPS Google Sheets URL")
    match = _SHEET_ID_PATTERN.match(parsed.path)
    if not match:
        raise ValueError("IDX_SHARIA_STOCKS_SHEET_URL must point to a Google spreadsheet")
    return f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?format=csv"


def parse_idx_sharia_sheet_csv(payload: bytes) -> list[str]:
    """Parse a Google Sheets CSV with `Kode Saham` and `ISSI` columns."""
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("IDX sharia sheet is not valid UTF-8 CSV") from exc

    reader = csv.DictReader(io.StringIO(text))
    headers = {
        " ".join((header or "").strip().casefold().split()): header
        for header in (reader.fieldnames or [])
    }
    code_field = headers.get("kode saham")
    issi_field = headers.get("issi")
    if not code_field or not issi_field:
        raise ValueError("IDX sharia sheet must contain `Kode Saham` and `ISSI` columns")

    selected: list[str] = []
    seen: set[str] = set()
    row_count = 0
    for row_number, row in enumerate(reader, start=2):
        ticker = str(row.get(code_field) or "").strip().upper()
        status = str(row.get(issi_field) or "").strip().casefold()
        if not ticker and not status:
            continue
        row_count += 1
        if not _TICKER_PATTERN.fullmatch(ticker):
            raise ValueError(f"IDX sharia sheet has an invalid ticker on row {row_number}")
        if ticker in seen:
            raise ValueError(f"IDX sharia sheet has a duplicate ticker on row {row_number}")
        seen.add(ticker)
        if status not in {"ya", "tidak"}:
            raise ValueError(f"IDX sharia sheet has an invalid ISSI status on row {row_number}")
        if status == "ya":
            selected.append(f"{ticker}.JK")

    if row_count == 0 or not selected:
        raise ValueError("IDX sharia sheet contains no valid ISSI=Ya tickers")
    return selected


def _download_sheet_csv(csv_url: str) -> bytes:
    request = Request(
        csv_url,
        headers={"User-Agent": "daily-stock-analysis/idx-sharia-list"},
    )
    with urlopen(request, timeout=15) as response:
        return response.read()


def _load_cache(cache_path: Path) -> Optional[tuple[list[str], str]]:
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("IDX sharia stock-list cache could not be read: %s", exc)
        return None

    codes = payload.get("codes") if isinstance(payload, dict) else None
    fetched_at = payload.get("fetched_at") if isinstance(payload, dict) else None
    if (
        not isinstance(codes, list)
        or not codes
        or not isinstance(fetched_at, str)
        or any(
            not isinstance(code, str)
            or not code.endswith(".JK")
            or not _TICKER_PATTERN.fullmatch(code[:-3])
            for code in codes
        )
        or len(codes) != len(set(codes))
    ):
        logger.warning("IDX sharia stock-list cache has an invalid format: %s", cache_path)
        return None
    return codes, fetched_at


def _write_cache(cache_path: Path, codes: list[str]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = cache_path.with_suffix(f"{cache_path.suffix}.tmp")
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "codes": codes,
    }
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(cache_path)


def get_idx_sharia_stock_codes(
    sheet_url: str,
    *,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> list[str]:
    """Fetch and validate the user's sheet, using its last valid snapshot offline."""
    csv_url = _google_sheet_csv_url(sheet_url)
    try:
        codes = parse_idx_sharia_sheet_csv(_download_sheet_csv(csv_url))
    except (OSError, TimeoutError, URLError, ValueError, csv.Error) as exc:
        cached = _load_cache(cache_path)
        if cached is None:
            raise RuntimeError(
                "Could not load IDX sharia tickers from the configured Google Sheet "
                "and no valid local snapshot is available."
            ) from exc
        codes, fetched_at = cached
        logger.warning(
            "Could not refresh IDX sharia tickers from Google Sheets; using cached "
            "snapshot fetched at %s. Verify that the sharia list is still current. Cause: %s",
            fetched_at,
            exc,
        )
        return codes

    try:
        _write_cache(cache_path, codes)
    except OSError as exc:
        logger.warning("Could not save IDX sharia stock-list cache: %s", exc)
    return codes
