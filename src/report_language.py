# -*- coding: utf-8 -*-
"""Helpers for report output language selection and localization."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from src.schemas.decision_scale import signal_key_for_score

SUPPORTED_REPORT_LANGUAGES = ("zh", "en", "ko", "id")

_REPORT_LANGUAGE_ALIASES = {
    "zh": "zh",
    "zh-cn": "zh",
    "zh_cn": "zh",
    "zh-hans": "zh",
    "zh_hans": "zh",
    "zh-tw": "zh",
    "zh_tw": "zh",
    "cn": "zh",
    "chinese": "zh",
    "中文": "zh",
    "en": "en",
    "english": "en",
    "en-us": "en",
    "en_us": "en",
    "en-gb": "en",
    "en_gb": "en",
    "ko": "ko",
    "korean": "ko",
    "ko-kr": "ko",
    "ko_kr": "ko",
    "kr": "ko",
    "한국어": "ko",
    "id": "id",
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

_BIAS_STATUS_CANONICAL_MAP = {
    "safe": "safe",
    "safety": "safe",
    "normal": "safe",
    "稳定": "safe",
    "安全": "safe",
    "안전": "safe",
    "aman": "safe",
    "caution": "caution",
    "警戒": "caution",
    "주의": "caution",
    "waspada": "caution",
    "high risk": "caution",
}

_BIAS_STATUS_TRANSLATIONS = {
    "safe": {"zh": "安全", "en": "Safe", "ko": "안전", "id": "Aman"},
    "caution": {"zh": "警戒", "en": "Caution", "ko": "주의", "id": "Waspada"},
}

_SENTIMENT_LABELS = {
    "zh": {
        "very_bullish": "强烈看多",
        "bullish": "看多",
        "neutral": "中性",
        "bearish": "悲观",
        "very_bearish": "强烈看空",
    },
    "en": {
        "very_bullish": "Very Bullish",
        "bullish": "Bullish",
        "neutral": "Neutral",
        "bearish": "Bearish",
        "very_bearish": "Very Bearish",
    },
    "ko": {
        "very_bullish": "매우 낙관",
        "bullish": "낙관",
        "neutral": "중립",
        "bearish": "비관",
        "very_bearish": "매우 비관",
    },
    "id": {
        "very_bullish": "Sangat Bullish",
        "bullish": "Bullish",
        "neutral": "Netral",
        "bearish": "Bearish",
        "very_bearish": "Sangat Bearish",
    },
}

_REPORT_LABELS = {
    "zh": {
        "report_title": "股票分析报告",
        "dashboard_title": "决策总览",
        "risk_alerts_label": "风险提醒",
        "data_sources_label": "数据来源",
        "market_summary_label": "市场概览",
        "action_advice_label": "操作建议",
        "trend_prediction_label": "趋势预测",
        "market_sentiment_label": "市场情绪",
        "strategy_points_label": "策略点位",
        "sniper_levels_label": "狙击点位",
        "no_analysis_summary": "暂无分析结论",
        "no_advice": "暂无建议",
        "no_prediction": "暂无预测",
        "not_available": "—",
        "signal_label": "信号",
        "confidence_label": "信心",
        "report_language_label": "报告语言",
    },
    "en": {
        "report_title": "Stock Analysis Report",
        "dashboard_title": "Decision Dashboard",
        "risk_alerts_label": "Risk Alerts",
        "data_sources_label": "Data Sources",
        "market_summary_label": "Market Summary",
        "action_advice_label": "Action Advice",
        "trend_prediction_label": "Trend Prediction",
        "market_sentiment_label": "Market Sentiment",
        "strategy_points_label": "Strategy Levels",
        "sniper_levels_label": "Sniper Levels",
        "no_analysis_summary": "No analysis summary yet",
        "no_advice": "No advice",
        "no_prediction": "No prediction",
        "not_available": "—",
        "signal_label": "Signal",
        "confidence_label": "Confidence",
        "report_language_label": "Report language",
    },
    "ko": {
        "report_title": "주식 분석 보고서",
        "dashboard_title": "결정 대시보드",
        "risk_alerts_label": "리스크 경보",
        "data_sources_label": "데이터 출처",
        "market_summary_label": "시장 요약",
        "action_advice_label": "대응 전략",
        "trend_prediction_label": "추세 예측",
        "market_sentiment_label": "시장 심리",
        "strategy_points_label": "전략 포인트",
        "sniper_levels_label": "타깃 레벨",
        "no_analysis_summary": "분석 요약 없음",
        "no_advice": "권장 사항 없음",
        "no_prediction": "예측 없음",
        "not_available": "—",
        "signal_label": "신호",
        "confidence_label": "신뢰도",
        "report_language_label": "보고서 언어",
    },
    "id": {
        "report_title": "Laporan Analisis Saham",
        "dashboard_title": "Dasbor Keputusan",
        "risk_alerts_label": "Peringatan Risiko",
        "data_sources_label": "Sumber Data",
        "market_summary_label": "Ringkasan Pasar",
        "action_advice_label": "Saran Tindakan",
        "trend_prediction_label": "Prediksi Tren",
        "market_sentiment_label": "Sentimen Pasar",
        "strategy_points_label": "Level Strategi",
        "sniper_levels_label": "Level Sniper",
        "no_analysis_summary": "Belum ada ringkasan analisis",
        "no_advice": "Belum ada saran",
        "no_prediction": "Belum ada prediksi",
        "not_available": "—",
        "signal_label": "Sinyal",
        "confidence_label": "Kepercayaan",
        "report_language_label": "Bahasa laporan",
    },
}


def _normalize_lookup_key(raw_value: Any) -> str:
    text = str(raw_value or "").strip().lower().replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", text)


def _canonicalize_lookup_value(raw_value: Any, canonical_map: Dict[str, str]) -> Optional[str]:
    if raw_value is None:
        return None
    normalized = _normalize_lookup_key(raw_value)
    if not normalized:
        return None
    if normalized in canonical_map:
        return canonical_map[normalized]
    for key, value in canonical_map.items():
        if _normalize_lookup_key(key) == normalized:
            return value
    return None


def normalize_report_language(value: Optional[str], default: str = "zh") -> str:
    """Normalize report language values like zh-cn / ko-KR / id_ID to a supported code."""
    if value is None:
        return default
    raw = str(value).strip()
    if not raw:
        return default
    normalized = raw.lower().replace("_", "-")
    if normalized in _REPORT_LANGUAGE_ALIASES:
        return _REPORT_LANGUAGE_ALIASES[normalized]
    for alias, canonical in _REPORT_LANGUAGE_ALIASES.items():
        if alias == normalized:
            return canonical
    for prefix in ("zh", "en", "ko", "id"):
        if normalized.startswith(prefix):
            return prefix
    return default


def is_supported_report_language_value(value: Optional[str]) -> bool:
    if value is None:
        return False
    return normalize_report_language(value, default="") in SUPPORTED_REPORT_LANGUAGES


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


def get_sentiment_label(score: Any, language: Optional[str] = "zh") -> str:
    """Return a human-friendly sentiment label for a 0..100 score."""
    try:
        numeric = int(float(score))
    except (TypeError, ValueError):
        numeric = 50
    normalized = normalize_report_language(language)
    if numeric >= 80:
        key = "very_bullish"
    elif numeric >= 60:
        key = "bullish"
    elif numeric >= 40:
        key = "neutral"
    elif numeric >= 20:
        key = "bearish"
    else:
        key = "very_bearish"
    return _SENTIMENT_LABELS.get(normalized, _SENTIMENT_LABELS["zh"]).get(key, _SENTIMENT_LABELS["zh"][key])


def get_localized_stock_name(stock_name: Any, code: Any, language: Optional[str] = "zh") -> str:
    """Return a localized placeholder when stock names are missing or generic."""
    raw_name = str(stock_name or "").strip()
    if raw_name and raw_name != "Unnamed Stock" and raw_name != "未命名股票":
        return raw_name
    language_code = normalize_report_language(language)
    placeholders = {
        "zh": "未命名股票",
        "en": "Unnamed Stock",
        "ko": "미확인 종목",
        "id": "Saham Tidak Dikenal",
    }
    return placeholders.get(language_code, placeholders["zh"])


def get_bias_status_emoji(status: Any) -> str:
    """Return a UI emoji for a bias / alert status."""
    text = str(status or "").strip().lower()
    if text in {"safe", "stability", "stable", "安全", "안전", "aman"}:
        return "✅"
    if text in {"caution", "warning", "warn", "警戒", "주의", "waspada"}:
        return "⚠️"
    return "ℹ️"


def localize_bias_status(value: Any, language: Optional[str] = "zh") -> str:
    """Normalize a bias status to a localized display string."""
    raw = str(value or "").strip()
    if not raw:
        return raw
    canonical = _canonicalize_lookup_value(raw, _BIAS_STATUS_CANONICAL_MAP)
    if canonical is None:
        return raw
    translation = _BIAS_STATUS_TRANSLATIONS.get(canonical, {})
    localized = _safe_language_lookup(translation, language)
    if localized is not None:
        return localized
    return raw


def _canonicalize_decision_text(raw_value: Any, canonical_map: Dict[str, str]) -> Optional[str]:
    value = str(raw_value or "").strip()
    if not value:
        return None
    normalized = _normalize_lookup_key(value)
    if normalized in canonical_map:
        return canonical_map[normalized]
    for key in sorted(canonical_map, key=lambda item: len(item), reverse=True):
        if normalized == _normalize_lookup_key(key):
            return canonical_map[key]
    return None


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

    canonical = _canonicalize_decision_text(raw_text, canonical_map)
    if canonical:
        translated = translations.get(canonical, {})
        result = _safe_language_lookup(translated, normalized_language)
        if result is not None:
            return result
    return raw_text


def localize_operation_advice(value: Any, language: Optional[str] = "zh") -> str:
    """Translate operation advice to the requested report language."""
    return _translate_from_map(
        value,
        language,
        canonical_map=_OPERATION_ADVICE_CANONICAL_MAP,
        translations=_OPERATION_ADVICE_TRANSLATIONS,
    )


def localize_trend_prediction(value: Any, language: Optional[str] = "zh") -> str:
    """Translate trend prediction phrases to the requested report language."""
    return _translate_from_map(
        value,
        language,
        canonical_map=_TREND_PREDICTION_CANONICAL_MAP,
        translations=_TREND_PREDICTION_TRANSLATIONS,
    )


def infer_decision_type_from_advice(value: Any, default: str = "hold") -> str:
    """Infer a canonical decision type from advice text."""
    raw = str(value or "").strip()
    if not raw:
        return default
    canonical = _canonicalize_decision_text(raw, _OPERATION_ADVICE_CANONICAL_MAP)
    if canonical in {"strong_buy", "buy"}:
        return "buy"
    if canonical in {"hold", "watch"}:
        return "hold"
    if canonical in {"reduce", "sell", "strong_sell"}:
        return "sell"
    if any(token in raw.lower() for token in ("买入", "buy", "beli", "매수", "구매")):
        return "buy"
    if any(token in raw.lower() for token in ("持有", "观望", "hold", "watch", "tahan", "pantau", "보유", "관망")):
        return "hold"
    if any(token in raw.lower() for token in ("减仓", "卖出", "reduce", "sell", "kurangi", "jual", "매도", "비중축소")):
        return "sell"
    return default


def get_signal_level(text: Any, score: Any, language: Optional[str] = "zh") -> tuple[str, str, str]:
    """Return a localized signal label, emoji, and canonical decision tag."""
    language_code = normalize_report_language(language)
    raw_text = str(text or "").strip()
    if raw_text:
        candidates = [segment.strip() for segment in re.split(r"[\/、,]", raw_text) if segment.strip()]
        for candidate in candidates:
            canonical = _canonicalize_decision_text(candidate, _OPERATION_ADVICE_CANONICAL_MAP)
            if canonical:
                translated = localize_operation_advice(candidate, language_code)
                tag = infer_decision_type_from_advice(candidate, default="hold")
                if tag == "buy":
                    return translated, "🟢", "buy"
                if tag == "sell":
                    return translated, "🔴", "sell"
                return translated, "⚪", "hold"
    signal_key = signal_key_for_score(score)
    if signal_key == "strong_buy":
        return localize_operation_advice("strong buy", language_code), "🟢", "buy"
    if signal_key == "buy":
        return localize_operation_advice("buy", language_code), "🟢", "buy"
    if signal_key == "watch":
        return localize_operation_advice("watch", language_code), "⚪", "hold"
    if signal_key == "reduce":
        return localize_operation_advice("reduce", language_code), "🟠", "sell"
    if signal_key == "sell":
        return localize_operation_advice("sell", language_code), "🔴", "sell"
    if signal_key == "strong_sell":
        return localize_operation_advice("strong sell", language_code), "🔴", "sell"
    return localize_operation_advice("hold", language_code), "⚪", "hold"


def normalize_report_language_value(value: Optional[str], default: str = "zh") -> str:
    return normalize_report_language(value, default)


# Back-compat alias for older imports.
_is_supported_report_language_value = is_supported_report_language_value


__all__ = [
    "SUPPORTED_REPORT_LANGUAGES",
    "normalize_report_language",
    "normalize_report_language_value",
    "is_supported_report_language_value",
    "_safe_language_lookup",
    "get_report_labels",
    "get_sentiment_label",
    "get_localized_stock_name",
    "get_bias_status_emoji",
    "localize_bias_status",
    "infer_decision_type_from_advice",
    "localize_operation_advice",
    "localize_trend_prediction",
    "get_signal_level",
]
