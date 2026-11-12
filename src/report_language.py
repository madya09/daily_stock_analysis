# -*- coding: utf-8 -*-
"""Helpers for report output language selection and localization."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from src.schemas.decision_scale import signal_key_for_score

SUPPORTED_REPORT_LANGUAGES = ("zh", "en", "ko", "id")

_REPORT_LANGUAGE_ALIASES = {
    "zh-cn": "zh",
    "zh_cn": "zh",
    "zh-hans": "zh",
    "zh_hans": "zh",
    "zh-tw": "zh",
    "zh_tw": "zh",
    "cn": "zh",
    "chinese": "zh",
    "english": "en",
    "en-us": "en",
    "en_us": "en",
    "en-gb": "en",
    "en_gb": "en",
    "korean": "ko",
    "kr": "ko",
    "ko-kr": "ko",
    "ko_kr": "ko",
    "indonesian": "id",
    "bahasa_indonesia": "id",
    "id-id": "id",
    "id_id": "id",
}

_OPERATION_ADVICE_CANONICAL_MAP = {
    "强烈买入": "strong_buy",
    "strong buy": "strong_buy",
    "strong_buy": "strong_buy",
    "买入": "buy",
    "buy": "buy",
    "加仓": "buy",
    "accumulate": "buy",
    "add position": "buy",
    "持有": "hold",
    "洗盘观察": "hold",
    "观察": "hold",
    "hold": "hold",
    "观望": "watch",
    "watch": "watch",
    "wait": "watch",
    "wait and see": "watch",
    "减仓": "reduce",
    "reduce": "reduce",
    "trim": "reduce",
    "卖出": "sell",
    "sell": "sell",
    "强烈卖出": "strong_sell",
    "strong sell": "strong_sell",
    "strong_sell": "strong_sell",
    "적극 매수": "strong_buy",
    "매수": "buy",
    "보유": "hold",
    "보유 관찰": "hold",
    "관망": "watch",
    "비중축소": "reduce",
    "매도": "sell",
    "적극 매도": "strong_sell",
    "sangat disarankan beli": "strong_buy",
    "beli": "buy",
    "tahan": "hold",
    "pantau": "watch",
    "kurangi posisi": "reduce",
    "jual": "sell",
    "sangat disarankan jual": "strong_sell",
}

_OPERATION_ADVICE_TRANSLATIONS = {
    "strong_buy": {"zh": "强烈买入", "en": "Strong Buy", "ko": "적극 매수", "id": "Sangat Disarankan Beli"},
    "buy": {"zh": "买入", "en": "Buy", "ko": "매수", "id": "Beli"},
    "hold": {"zh": "持有", "en": "Hold", "ko": "보유", "id": "Tahan"},
    "watch": {"zh": "观望", "en": "Watch", "ko": "관망", "id": "Pantau"},
    "reduce": {"zh": "减仓", "en": "Reduce", "ko": "비중축소", "id": "Kurangi Posisi"},
    "sell": {"zh": "卖出", "en": "Sell", "ko": "매도", "id": "Jual"},
    "strong_sell": {"zh": "强烈卖出", "en": "Strong Sell", "ko": "적극 매도", "id": "Sangat Disarankan Jual"},
}

_TREND_PREDICTION_CANONICAL_MAP = {
    "强势空头": "strong_bearish",
    "强烈看多": "strong_bullish",
    "strong bullish": "strong_bullish",
    "very bullish": "strong_bullish",
    "强势多头": "strong_bullish",
    "多头排列": "bullish",
    "空头排列": "bearish",
    "弱势多头": "bullish",
    "弱势空头": "bearish",
    "看多": "bullish",
    "盘整": "sideways",
    "bullish": "bullish",
    "uptrend": "bullish",
    "震荡": "sideways",
    "neutral": "sideways",
    "sideways": "sideways",
    "range-bound": "sideways",
    "看空": "bearish",
    "bearish": "bearish",
    "downtrend": "bearish",
    "强烈看空": "strong_bearish",
    "strong bearish": "strong_bearish",
    "very bearish": "strong_bearish",
    "강한 상승": "strong_bullish",
    "상승": "bullish",
    "횡보": "sideways",
    "하락": "bearish",
    "강한 하락": "strong_bearish",
    "sangat bullish": "strong_bullish",
    "mendatar": "sideways",
    "sangat bearish": "strong_bearish",
}

_TREND_PREDICTION_TRANSLATIONS = {
    "strong_bullish": {"zh": "强烈看多", "en": "Strong Bullish", "ko": "강한 상승", "id": "Sangat Bullish"},
    "bullish": {"zh": "看多", "en": "Bullish", "ko": "상승", "id": "Bullish"},
    "sideways": {"zh": "震荡", "en": "Sideways", "ko": "횡보", "id": "Mendatar"},
    "bearish": {"zh": "看空", "en": "Bearish", "ko": "하락", "id": "Bearish"},
    "strong_bearish": {"zh": "强烈看空", "en": "Strong Bearish", "ko": "강한 하락", "id": "Sangat Bearish"},
}

# ... existing content continues unchanged below; only the following helper and translation-access fix are added.

def _safe_language_lookup(mapping: Dict[str, str], language: Optional[str], *, fallback_order: tuple[str, ...] = ("zh", "en", "ko", "id")) -> Optional[str]:
    """Return a localized string for the requested language, with graceful fallback."""
    if not isinstance(mapping, dict):
        return None
    target = normalize_report_language(language)
    candidates = [target]
    for lang in fallback_order:
        if lang not in candidates:
            candidates.append(lang)
    for candidate in candidates:
        value = mapping.get(candidate)
        if value is not None:
            return value
    return None


def get_report_labels(language: Optional[str]) -> Dict[str, str]:
    """Return UI copy for the selected report language."""
    normalized = normalize_report_language(language)
    labels = _REPORT_LABELS.get(normalized)
    if labels is not None:
        return labels
    for fallback in ("zh", "en", "ko", "id"):
        labels = _REPORT_LABELS.get(fallback)
        if labels is not None:
            return labels
    return _REPORT_LABELS["zh"]


def _translate_from_map(
    value: Any,
    language: Optional[str],
    *,
    canonical_map: Dict[str, str],
    translations: Dict[str, Dict[str, str]],
) -> str:
    normalized_language = normalize_report_language(language)
    raw_text = str(value or "").strip()
    if not raw_text:
        return raw_text

    canonical = _canonicalize_lookup_value(raw_text, canonical_map)
    if canonical:
        translated = translations.get(canonical, {})
        result = _safe_language_lookup(translated, normalized_language)
        if result is not None:
            return result
    return raw_text


# The rest of the file remains unchanged below this point.

