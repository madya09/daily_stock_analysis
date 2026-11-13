# -*- coding: utf-8 -*-
"""Report-language normalization and localization helpers.

This module is imported by configuration, analysis, notification, and report
rendering at startup. Keep its public helper API backward compatible; the
import-contract test guards callers against accidental partial replacements.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Dict, Optional

from src.schemas.decision_scale import signal_key_for_score

SUPPORTED_REPORT_LANGUAGES = ("zh", "en", "ko", "id")
_REPORT_LANGUAGE_ALIASES = {
    "zh": "zh", "zh-cn": "zh", "zh_cn": "zh", "zh-hans": "zh", "zh_hans": "zh",
    "zh-tw": "zh", "zh_tw": "zh", "cn": "zh", "chinese": "zh", "中文": "zh",
    "en": "en", "english": "en", "en-us": "en", "en_us": "en", "en-gb": "en", "en_gb": "en",
    "ko": "ko", "korean": "ko", "ko-kr": "ko", "ko_kr": "ko", "kr": "ko", "한국어": "ko",
    "id": "id", "indonesian": "id", "bahasa_indonesia": "id", "id-id": "id", "id_id": "id",
}

_OPERATION = {
    "strong_buy": {"zh": "强烈买入", "en": "Strong Buy", "ko": "적극 매수", "id": "Sangat Disarankan Beli"},
    "buy": {"zh": "买入", "en": "Buy", "ko": "매수", "id": "Beli"},
    "hold": {"zh": "持有", "en": "Hold", "ko": "보유", "id": "Tahan"},
    "watch": {"zh": "观望", "en": "Watch", "ko": "관망", "id": "Pantau"},
    "reduce": {"zh": "减仓", "en": "Reduce", "ko": "비중축소", "id": "Kurangi Posisi"},
    "sell": {"zh": "卖出", "en": "Sell", "ko": "매도", "id": "Jual"},
    "strong_sell": {"zh": "强烈卖出", "en": "Strong Sell", "ko": "적극 매도", "id": "Sangat Disarankan Jual"},
}
_OPERATION_MAP = {
    "强烈买入": "strong_buy", "strong buy": "strong_buy", "strong_buy": "strong_buy",
    "买入": "buy", "buy": "buy", "加仓": "buy", "accumulate": "buy", "add position": "buy",
    "持有": "hold", "洗盘观察": "hold", "观察": "hold", "hold": "hold",
    "观望": "watch", "watch": "watch", "wait": "watch", "wait and see": "watch",
    "减仓": "reduce", "reduce": "reduce", "trim": "reduce", "卖出": "sell", "sell": "sell",
    "强烈卖出": "strong_sell", "strong sell": "strong_sell", "strong_sell": "strong_sell",
    "적극 매수": "strong_buy", "매수": "buy", "보유": "hold", "보유 관찰": "hold",
    "관망": "watch", "비중축소": "reduce", "매도": "sell", "적극 매도": "strong_sell",
    "sangat disarankan beli": "strong_buy", "beli": "buy", "tahan": "hold", "pantau": "watch",
    "kurangi posisi": "reduce", "jual": "sell", "sangat disarankan jual": "strong_sell",
}
_TREND = {
    "strong_bullish": {"zh": "强烈看多", "en": "Strong Bullish", "ko": "강한 상승", "id": "Sangat Bullish"},
    "bullish": {"zh": "看多", "en": "Bullish", "ko": "상승", "id": "Bullish"},
    "sideways": {"zh": "震荡", "en": "Sideways", "ko": "횡보", "id": "Mendatar"},
    "bearish": {"zh": "看空", "en": "Bearish", "ko": "하락", "id": "Bearish"},
    "strong_bearish": {"zh": "强烈看空", "en": "Strong Bearish", "ko": "강한 하락", "id": "Sangat Bearish"},
}
_TREND_MAP = {
    "强势空头": "strong_bearish", "强烈看多": "strong_bullish", "strong bullish": "strong_bullish",
    "very bullish": "strong_bullish", "强势多头": "strong_bullish", "多头排列": "bullish",
    "空头排列": "bearish", "弱势多头": "bullish", "弱势空头": "bearish", "看多": "bullish",
    "盘整": "sideways", "bullish": "bullish", "uptrend": "bullish", "震荡": "sideways",
    "neutral": "sideways", "sideways": "sideways", "range-bound": "sideways", "看空": "bearish",
    "bearish": "bearish", "downtrend": "bearish", "强烈看空": "strong_bearish",
    "strong bearish": "strong_bearish", "very bearish": "strong_bearish", "강한 상승": "strong_bullish",
    "상승": "bullish", "횡보": "sideways", "하락": "bearish", "강한 하락": "strong_bearish",
    "sangat bullish": "strong_bullish", "mendatar": "sideways", "sangat bearish": "strong_bearish",
}

_SENTIMENT = {
    "zh": {"very_bullish": "强烈看多", "bullish": "看多", "neutral": "中性", "bearish": "悲观", "very_bearish": "强烈看空"},
    "en": {"very_bullish": "Very Bullish", "bullish": "Bullish", "neutral": "Neutral", "bearish": "Bearish", "very_bearish": "Very Bearish"},
    "ko": {"very_bullish": "매우 낙관", "bullish": "낙관", "neutral": "중립", "bearish": "비관", "very_bearish": "매우 비관"},
    "id": {"very_bullish": "Sangat Bullish", "bullish": "Bullish", "neutral": "Netral", "bearish": "Bearish", "very_bearish": "Sangat Bearish"},
}

# Shared labels used by the legacy report paths. Missing/new keys are supplied
# by get_report_labels with a safe key fallback rather than raising KeyError.
_REPORT_LABELS: Dict[str, Dict[str, str]] = {
    "zh": {"report_title": "股票分析报告", "dashboard_title": "决策总览", "risk_alerts_label": "风险提醒", "data_sources_label": "数据来源", "market_summary_label": "市场概览", "action_advice_label": "操作建议", "trend_prediction_label": "趋势预测", "market_sentiment_label": "市场情绪", "strategy_points_label": "策略点位", "sniper_levels_label": "狙击点位", "no_analysis_summary": "暂无分析结论", "no_advice": "暂无建议", "no_prediction": "暂无预测", "not_available": "—", "signal_label": "信号", "confidence_label": "信心", "report_language_label": "报告语言"},
    "en": {"report_title": "Stock Analysis Report", "dashboard_title": "Decision Dashboard", "risk_alerts_label": "Risk Alerts", "data_sources_label": "Data Sources", "market_summary_label": "Market Summary", "action_advice_label": "Action Advice", "trend_prediction_label": "Trend Prediction", "market_sentiment_label": "Market Sentiment", "strategy_points_label": "Strategy Levels", "sniper_levels_label": "Sniper Levels", "no_analysis_summary": "No analysis summary yet", "no_advice": "No advice", "no_prediction": "No prediction", "not_available": "—", "signal_label": "Signal", "confidence_label": "Confidence", "report_language_label": "Report language"},
    "ko": {"report_title": "주식 분석 보고서", "dashboard_title": "결정 대시보드", "risk_alerts_label": "리스크 경보", "data_sources_label": "데이터 출처", "market_summary_label": "시장 요약", "action_advice_label": "대응 전략", "trend_prediction_label": "추세 예측", "market_sentiment_label": "시장 심리", "strategy_points_label": "전략 포인트", "sniper_levels_label": "타깃 레벨", "no_analysis_summary": "분석 요약 없음", "no_advice": "권장 사항 없음", "no_prediction": "예측 없음", "not_available": "—", "signal_label": "신호", "confidence_label": "신뢰도", "report_language_label": "보고서 언어"},
    "id": {"report_title": "Laporan Analisis Saham", "dashboard_title": "Dasbor Keputusan", "risk_alerts_label": "Peringatan Risiko", "data_sources_label": "Sumber Data", "market_summary_label": "Ringkasan Pasar", "action_advice_label": "Saran Tindakan", "trend_prediction_label": "Prediksi Tren", "market_sentiment_label": "Sentimen Pasar", "strategy_points_label": "Level Strategi", "sniper_levels_label": "Level Sniper", "no_analysis_summary": "Belum ada ringkasan analisis", "no_advice": "Belum ada saran", "no_prediction": "Belum ada prediksi", "not_available": "—", "signal_label": "Sinyal", "confidence_label": "Kepercayaan", "report_language_label": "Bahasa laporan"},
}
_LABEL_DEFAULTS = {
    "analyzed_prefix":"Analyzed", "stock_unit":"stocks", "stock_unit_compact":"stocks", "buy_label":"Buy", "watch_label":"Watch", "sell_label":"Sell", "summary_heading":"Summary", "info_heading":"Key Updates", "sentiment_summary_label":"Sentiment", "earnings_outlook_label":"Earnings Outlook", "positive_catalysts_label":"Positive Catalysts", "latest_news_label":"Latest News", "core_conclusion_heading":"Core Conclusion", "one_sentence_label":"One-line Decision", "time_sensitivity_label":"Time Sensitivity", "default_time_sensitivity":"This week", "position_status_label":"Position", "no_position_label":"No Position", "has_position_label":"Holding", "continue_holding":"Continue holding", "market_snapshot_heading":"Market Snapshot", "close_label":"Close", "prev_close_label":"Prev Close", "open_label":"Open", "high_label":"High", "low_label":"Low", "change_pct_label":"Change %", "change_amount_label":"Change", "amplitude_label":"Amplitude", "volume_label":"Volume", "amount_label":"Turnover", "current_price_label":"Price", "volume_ratio_label":"Volume Ratio", "turnover_rate_label":"Turnover Rate", "source_label":"Source", "data_perspective_heading":"Data View", "ma_alignment_label":"MA Alignment", "bullish_alignment_label":"Bullish Alignment", "yes_label":"Yes", "no_label":"No", "none_label":"None", "trend_strength_label":"Trend Strength", "price_metrics_label":"Price Metrics", "ma5_label":"MA5", "ma10_label":"MA10", "ma20_label":"MA20", "bias_ma5_label":"Bias (MA5)", "support_level_label":"Support", "resistance_level_label":"Resistance", "chip_label":"Chip Structure", "phase_decision_heading":"Phase Decision Guardrail", "action_window_label":"Action Window", "immediate_action_label":"Current Action", "watch_conditions_label":"Watch Conditions", "next_check_time_label":"Next Check", "confidence_reason_label":"Confidence Reason", "data_limitations_label":"Data Limitations", "battle_plan_heading":"Battle Plan", "ideal_buy_label":"Ideal Entry", "secondary_buy_label":"Secondary Entry", "stop_loss_label":"Stop Loss", "take_profit_label":"Target", "suggested_position_label":"Position Size", "entry_plan_label":"Entry Plan", "risk_control_label":"Risk Control", "checklist_heading":"Checklist", "failed_checks_heading":"Failed Checks", "history_compare_heading":"Historical Signal Comparison", "time_label":"Time", "score_label":"Score", "advice_label":"Advice", "trend_label":"Trend", "generated_at_label":"Generated At", "report_time_label":"Generated", "no_results":"No analysis results", "brief_title":"Decision Brief", "avg_score_label":"Avg Score", "action_points_heading":"Action Levels", "position_advice_heading":"Position Advice", "analysis_model_label":"Model", "not_investment_advice":"AI-generated content for reference only; not investment advice.", "details_report_hint":"See detailed report", "financial_summary_heading":"Financial Summary", "report_date_label":"Report Date", "revenue_label":"Revenue", "net_profit_label":"Net Profit", "operating_cash_flow_label":"Operating Cash Flow", "roe_label":"ROE", "revenue_yoy_label":"Revenue YoY", "net_profit_yoy_label":"Net Profit YoY", "gross_margin_label":"Gross Margin", "shareholder_return_heading":"Shareholder Return", "ttm_cash_dividend_label":"TTM Cash Dividend / Share", "ttm_event_count_label":"TTM Dividend Events", "ttm_dividend_yield_label":"TTM Dividend Yield", "latest_ex_dividend_label":"Latest Ex-dividend Date", "institutional_flow_heading":"Institutional Flows", "institutional_flow_note":"Positive = net buy; negative = net sell.", "inst_foreign_label":"Foreign", "inst_trust_label":"Trust", "inst_dealer_label":"Dealer", "inst_total_label":"Total", "related_boards_heading":"Related Boards", "industry_boards_heading":"Industry Sectors", "concept_boards_heading":"Concept Themes", "leading_board_label":"Leading", "lagging_board_label":"Lagging", "signal_attribution_heading":"Signal Attribution", "attribution_weights_label":"Attribution Weights", "technical_indicators_label":"Technical Indicators", "news_sentiment_label":"News Sentiment", "fundamentals_label":"Fundamentals", "market_conditions_label":"Market Conditions", "strongest_bullish_signal_label":"Strongest Bullish Signal", "strongest_bearish_signal_label":"Strongest Bearish Signal", "strategy_synthesis_heading":"Strategy Synthesis", "strategy_final_signal_label":"Final Signal", "strategy_consensus_level_label":"Consensus", "strategy_conflict_label":"Conflict", "strategy_confidence_label":"Confidence", "strategy_summary_label":"Summary", "strategy_supporting_skills_label":"Supporting Strategies", "strategy_opposing_skills_label":"Opposing Strategies", "strategy_invalid_opinions_label":"{count} additional strategies failed to produce valid signals"}


def normalize_report_language(value: Optional[str], default: str = "zh") -> str:
    """Normalize a supported language or locale alias to zh/en/ko/id."""
    if value is None or not str(value).strip():
        return default
    candidate = str(value).strip().lower().replace(" ", "_")
    if candidate in _REPORT_LANGUAGE_ALIASES:
        return _REPORT_LANGUAGE_ALIASES[candidate]
    # Accept recognized locale forms (e.g. en-AU), but not arbitrary strings
    # that merely start with a language code.
    match = re.fullmatch(r"(zh|en|ko|id)[-_][a-z]{2,8}", candidate)
    if match:
        return match.group(1)
    return candidate if candidate in SUPPORTED_REPORT_LANGUAGES else default


def is_supported_report_language_value(value: Optional[str]) -> bool:
    return normalize_report_language(value, default="") in SUPPORTED_REPORT_LANGUAGES


def normalize_report_language_value(value: Optional[str], default: str = "zh") -> str:
    return normalize_report_language(value, default)


def _normalize_lookup_key(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower().replace("_", " ").replace("-", " "))


def _canonicalize_lookup_value(value: Any, mapping: Dict[str, str]) -> Optional[str]:
    normalized = _normalize_lookup_key(value)
    if not normalized:
        return None
    for candidate, canonical in mapping.items():
        if _normalize_lookup_key(candidate) == normalized:
            return canonical
    return None


def _safe_language_lookup(mapping: Dict[str, str], language: Optional[str], *, fallback_order: tuple[str, ...] = ("zh", "en", "ko", "id")) -> Optional[str]:
    if not isinstance(mapping, dict):
        return None
    normalized = normalize_report_language(language)
    for key in (normalized, *fallback_order):
        if mapping.get(key) is not None:
            return mapping[key]
    return None


def get_report_labels(language: Optional[str]) -> Dict[str, str]:
    """Return a complete, renderer-safe label map for a supported language."""
    lang = normalize_report_language(language)
    labels = dict(_REPORT_LABELS.get(lang, _REPORT_LABELS["zh"]))
    for key, fallback in _LABEL_DEFAULTS.items():
        labels.setdefault(key, fallback if lang == "en" else key.replace("_", " ").capitalize())
    return labels


def _translate(value: Any, language: Optional[str], mapping: Dict[str, str], translations: Dict[str, Dict[str, str]]) -> str:
    raw = str(value or "").strip()
    canonical = _canonicalize_lookup_value(raw, mapping)
    if not raw or canonical is None:
        return raw
    return _safe_language_lookup(translations.get(canonical, {}), language) or raw


def localize_operation_advice(value: Any, language: Optional[str] = "zh") -> str:
    return _translate(value, language, _OPERATION_MAP, _OPERATION)


def localize_trend_prediction(value: Any, language: Optional[str] = "zh") -> str:
    return _translate(value, language, _TREND_MAP, _TREND)


def get_sentiment_label(score: Any, language: Optional[str] = "zh") -> str:
    try:
        value = int(float(score))
    except (TypeError, ValueError, OverflowError):
        value = 50
    key = "very_bullish" if value >= 80 else "bullish" if value >= 60 else "neutral" if value >= 40 else "bearish" if value >= 20 else "very_bearish"
    return _SENTIMENT.get(normalize_report_language(language), _SENTIMENT["zh"])[key]


def _is_placeholder_stock_name(value: Any, code: Any = None) -> bool:
    text = str(value or "").strip()
    return not text or text.lower() in {"n/a", "na", "none", "null", "unknown", "unnamed stock"} or text in {"—", "-", "未命名股票", "待确认股票", "待补充", "未知"} or text.startswith("股票") or (bool(code) and text.lower() == str(code).strip().lower())


def get_localized_stock_name(stock_name: Any, code: Any, language: Optional[str] = "zh") -> str:
    if not _is_placeholder_stock_name(stock_name, code):
        return str(stock_name).strip()
    return {"zh": "待确认股票", "en": "Unnamed Stock", "ko": "미확인 종목", "id": "Saham Tidak Dikenal"}[normalize_report_language(language)]


def _decision_canonical(value: Any) -> Optional[str]:
    raw = str(value or "").strip()
    if not raw:
        return None
    exact = _canonicalize_lookup_value(raw, _OPERATION_MAP)
    if exact:
        return exact
    # Compound advice: select the first recognized segment, preserving order.
    for part in re.split(r"[/|,，、;；]+", raw):
        canonical = _canonicalize_lookup_value(part, _OPERATION_MAP)
        if canonical:
            return canonical
    return None


def infer_decision_type_from_advice(value: Any, default: str = "hold") -> str:
    raw = str(value or "").strip()
    if not raw:
        return default
    lowered = raw.lower()
    if any(token in lowered for token in ("不建议", "不应", "不要", "避免", "未建议", "not recommend", "do not", "don't", "avoid")):
        return "hold"
    canonical = _decision_canonical(raw)
    if canonical in {"buy", "strong_buy"}:
        return "buy"
    if canonical in {"hold", "watch"}:
        return "hold"
    if canonical in {"reduce", "sell", "strong_sell"}:
        return "sell"
    return default


def get_signal_level(text: Any, score: Any, language: Optional[str] = "zh") -> tuple[str, str, str]:
    lang = normalize_report_language(language)
    canonical = _decision_canonical(text)
    if canonical is None:
        canonical = signal_key_for_score(score) or "hold"
    display = localize_operation_advice(canonical, lang)
    tags = {"strong_buy": ("🟢", "strong_buy"), "buy": ("🟢", "buy"), "hold": ("⚪", "hold"), "watch": ("⚪", "watch"), "reduce": ("🟠", "reduce"), "sell": ("🔴", "sell"), "strong_sell": ("🔴", "strong_sell")}
    emoji, tag = tags.get(canonical, ("⚪", "hold"))
    return display, emoji, tag


_CONFIDENCE = {"high": {"zh":"高", "en":"High", "ko":"높음", "id":"Tinggi"}, "medium": {"zh":"中", "en":"Medium", "ko":"보통", "id":"Sedang"}, "low": {"zh":"低", "en":"Low", "ko":"낮음", "id":"Rendah"}}

def localize_confidence_level(value: Any, language: Optional[str] = "zh") -> str:
    mapping = {"高":"high", "high":"high", "높음":"high", "中":"medium", "medium":"medium", "med":"medium", "보통":"medium", "低":"low", "low":"low", "낮음":"low"}
    canonical = _canonicalize_lookup_value(value, mapping)
    return _safe_language_lookup(_CONFIDENCE.get(canonical, {}), language) or str(value or "")


def get_placeholder_text(language: Optional[str]) -> str:
    return {"zh":"待补充", "en":"TBD", "ko":"미정", "id":"Belum tersedia"}[normalize_report_language(language)]

def get_unknown_text(language: Optional[str]) -> str:
    return {"zh":"未知", "en":"Unknown", "ko":"알 수 없음", "id":"Tidak diketahui"}[normalize_report_language(language)]

def get_no_data_text(language: Optional[str]) -> str:
    return {"zh":"数据缺失", "en":"Data unavailable", "ko":"데이터 없음", "id":"Data tidak tersedia"}[normalize_report_language(language)]

def get_chip_unavailable_text(language: Optional[str]) -> str:
    return {"zh":"筹码分布未启用或数据源暂不可用，未纳入筹码判断。", "en":"Chip distribution is disabled or unavailable; chip signals were not used.", "ko":"매물대 데이터가 없거나 사용할 수 없어 분석에 반영하지 않았습니다.", "id":"Data distribusi chip tidak tersedia dan tidak digunakan dalam analisis."}[normalize_report_language(language)]

_CHIP_FIELDS = ("profit_ratio", "avg_cost", "concentration")
_CHIP_REASON_KEYS = ("chip_unavailable_reason", "unavailable_reason", "chip_unavailable")
_CHIP_PLACEHOLDERS = {"", "n/a", "na", "none", "null", "unknown", "tbd", "数据缺失", "未知", "暂无", "待补充", "-", "—"}

def is_chip_placeholder_value(value: Any) -> bool:
    return value is None or (isinstance(value, (int, float)) and value == 0) or str(value).strip().lower() in _CHIP_PLACEHOLDERS or any(token in str(value or "").lower() for token in ("unavailable", "not supported", "数据缺失", "无法判断"))

def is_chip_structure_unavailable(value: Any) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    for key in _CHIP_REASON_KEYS:
        reason = value.get(key)
        if reason is True or (not isinstance(reason, bool) and str(reason or "").strip()):
            return True
    if any(key in value for key in _CHIP_FIELDS):
        return all(is_chip_placeholder_value(value.get(key)) for key in _CHIP_FIELDS)
    return all(is_chip_placeholder_value(item) for item in value.values())

def get_chip_unavailable_reason(value: Any, language: Optional[str] = "zh") -> str:
    if not isinstance(value, dict) or not value:
        return ""
    for key in _CHIP_REASON_KEYS:
        reason = value.get(key)
        if reason is True:
            return get_chip_unavailable_text(language)
        if not isinstance(reason, bool) and str(reason or "").strip():
            return str(reason).strip()
    return get_chip_unavailable_text(language) if is_chip_structure_unavailable(value) else ""

def localize_chip_health(value: Any, language: Optional[str] = "zh") -> str:
    mapping = {"健康":"healthy", "healthy":"healthy", "양호":"healthy", "一般":"average", "average":"average", "보통":"average", "警惕":"caution", "caution":"caution", "주의":"caution"}
    translations = {"healthy":{"zh":"健康","en":"Healthy","ko":"양호","id":"Sehat"}, "average":{"zh":"一般","en":"Average","ko":"보통","id":"Rata-rata"}, "caution":{"zh":"警惕","en":"Caution","ko":"주의","id":"Waspada"}}
    return _translate(value, language, mapping, translations)

_BIAS = {"safe":{"zh":"安全","en":"Safe","ko":"안전","id":"Aman"}, "caution":{"zh":"警戒","en":"Caution","ko":"주의","id":"Waspada"}, "danger":{"zh":"危险","en":"Danger","ko":"위험","id":"Bahaya"}}
_BIAS_MAP = {"安全":"safe", "safe":"safe", "稳定":"safe", "안전":"safe", "aman":"safe", "警戒":"caution", "警惕":"caution", "caution":"caution", "주의":"caution", "waspada":"caution", "危险":"danger", "risk":"danger", "danger":"danger", "위험":"danger"}
def localize_bias_status(value: Any, language: Optional[str] = "zh") -> str:
    return _translate(value, language, _BIAS_MAP, _BIAS)
def get_bias_status_emoji(value: Any) -> str:
    canonical = _canonicalize_lookup_value(value, _BIAS_MAP)
    return "✅" if canonical == "safe" else "⚠️" if canonical == "caution" else "🚨" if canonical == "danger" else "ℹ️"

_STRATEGY_SIGNAL_MAP = {**_OPERATION_MAP, "strong buy":"strong_buy", "strong sell":"strong_sell"}
_STRATEGY_SIGNALS = {key: value for key, value in _OPERATION.items()}
def localize_strategy_signal(value: Any, language: Optional[str] = "zh") -> str:
    return _translate(value, language, _STRATEGY_SIGNAL_MAP, _STRATEGY_SIGNALS)
def localize_consensus_level(value: Any, language: Optional[str] = "zh") -> str:
    mapping={"high":"high","高":"high","높음":"high","medium":"medium","中":"medium","보통":"medium","low":"low","低":"low","낮음":"low","insufficient":"insufficient","证据不足":"insufficient","증거 부족":"insufficient"}
    translations={"high":{"zh":"高","en":"High","ko":"높음","id":"Tinggi"},"medium":{"zh":"中","en":"Medium","ko":"보통","id":"Sedang"},"low":{"zh":"低","en":"Low","ko":"낮음","id":"Rendah"},"insufficient":{"zh":"证据不足","en":"Insufficient","ko":"증거 부족","id":"Tidak cukup bukti"}}
    return _translate(value, language, mapping, translations)
def localize_conflict_severity(value: Any, language: Optional[str] = "zh") -> str:
    mapping={"none":"none","无":"none","없음":"none","low":"low","低":"low","낮음":"low","medium":"medium","中":"medium","보통":"medium","high":"high","高":"high","높음":"high"}
    translations={"none":{"zh":"无","en":"None","ko":"없음","id":"Tidak ada"},"low":{"zh":"低","en":"Low","ko":"낮음","id":"Rendah"},"medium":{"zh":"中","en":"Medium","ko":"보통","id":"Sedang"},"high":{"zh":"高","en":"High","ko":"높음","id":"Tinggi"}}
    return _translate(value, language, mapping, translations)

_SKILL_LABELS = {"bull_trend":"Bull Trend", "hot_theme":"Hot Theme", "volume_breakout":"Volume Breakout", "ma_golden_cross":"MA Golden Cross", "growth_quality":"Growth Quality", "bottom_volume":"Bottom Volume", "box_oscillation":"Box Oscillation", "chan_theory":"Chan Theory", "dragon_head":"Dragon Head", "emotion_cycle":"Emotion Cycle", "event_driven":"Event Driven", "expectation_repricing":"Expectation Repricing", "one_yang_three_yin":"One Yang Three Yin", "shrink_pullback":"Shrink Pullback", "wave_theory":"Wave Theory"}
def localize_strategy_skill(value: Any, language: Optional[str] = "zh") -> str:
    raw=str(value or "").strip()
    canonical=_normalize_lookup_key(raw).replace(" ","_")
    if not raw: return raw
    zh={"bull_trend":"默认多头趋势","hot_theme":"热点题材","volume_breakout":"放量突破","ma_golden_cross":"均线金叉","growth_quality":"成长质量","bottom_volume":"底部放量","box_oscillation":"箱体震荡","chan_theory":"缠论结构","dragon_head":"龙头战法","emotion_cycle":"情绪周期","event_driven":"事件驱动","expectation_repricing":"预期重估","one_yang_three_yin":"一阳三阴","shrink_pullback":"缩量回踩","wave_theory":"波浪理论"}
    ko={"bull_trend":"기본 상승 추세","hot_theme":"핫 테마","volume_breakout":"거래량 돌파","ma_golden_cross":"이평선 골든크로스","growth_quality":"성장 품질","bottom_volume":"저점 거래량","box_oscillation":"박스권 등락","chan_theory":"찬 이론 구조","dragon_head":"대장주 전략","emotion_cycle":"심리 사이클","event_driven":"이벤트 드리븐","expectation_repricing":"기대 재평가","one_yang_three_yin":"일양삼음","shrink_pullback":"거래량 축소 눌림","wave_theory":"파동 이론"}
    lang=normalize_report_language(language)
    return {"zh":zh,"en":_SKILL_LABELS,"ko":ko,"id":_SKILL_LABELS}.get(lang, _SKILL_LABELS).get(canonical, raw)

def localize_strategy_conflict_description(value: Any, language: Optional[str] = "zh") -> str:
    key=str(value or "").strip()
    descriptions={"directional_opposition":{"zh":"策略方向出现对立，应降低结论确定性。","en":"Strategy directions diverge; conviction should be reduced.","ko":"전략 방향이 엇갈려 확신도를 낮춰야 합니다.","id":"Arah strategi berbeda; tingkat keyakinan perlu diturunkan."},"wide_score_dispersion":{"zh":"策略信号分布较宽，存在明显分歧。","en":"Strategy scores are widely dispersed, indicating disagreement.","ko":"전략 점수 분포가 넓어 의견 차이가 큽니다.","id":"Skor strategi tersebar luas dan menunjukkan perbedaan."},"high_confidence_dissent":{"zh":"高置信少数派策略与综合信号不一致。","en":"A high-confidence minority strategy disagrees with the final signal.","ko":"높은 확신도의 소수 전략이 종합 신호와 다릅니다.","id":"Strategi minoritas berkeyakinan tinggi berbeda dari sinyal akhir."},"adjustment_contradiction":{"zh":"不同策略的评分调整方向相互矛盾。","en":"Strategy score adjustments contradict each other.","ko":"전략별 점수 조정 방향이 충돌합니다.","id":"Penyesuaian skor antarstrategi saling bertentangan."}}
    return descriptions.get(key, {}).get(normalize_report_language(language), key)

def normalize_strategy_synthesis_payload(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict) or not value: return {}
    result=dict(value)
    for key in ("supporting_skills","opposing_skills","conflicts"):
        items=result.get(key)
        result[key]=[item for item in items if isinstance(item,dict)] if isinstance(items,list) else []
    return result

def strategy_invalid_opinion_count(value: Any) -> int:
    payload=normalize_strategy_synthesis_payload(value)
    params=payload.get("summary_params")
    if not isinstance(params,dict): return 0
    count=params.get("invalid_opinion_count")
    if isinstance(count,bool): return 0
    if isinstance(count,int): return max(count,0)
    if isinstance(count,str) and count.strip().isascii() and count.strip().isdecimal(): return int(count.strip())
    return 0

def localize_strategy_synthesis_summary(value: Any, language: Optional[str] = "zh") -> str:
    payload=normalize_strategy_synthesis_payload(value)
    if not payload: return ""
    lang=normalize_report_language(language)
    params=payload.get("summary_params")
    if not isinstance(params,dict): params={}
    count=params.get("opinion_count")
    if not isinstance(count,int): count=len(payload.get("supporting_skills",[]))+len(payload.get("opposing_skills",[]))
    signal=localize_strategy_signal(payload.get("final_signal","N/A"),lang)
    consensus=localize_consensus_level(payload.get("consensus_level","N/A"),lang)
    severity=localize_conflict_severity(payload.get("conflict_severity","none"),lang)
    conflicts=payload.get("conflict_count",0)
    if lang=="en": return f"Strategy synthesis from {count} strategies: final signal is {signal}, consensus is {consensus}, conflict severity is {severity}." if conflicts else f"Strategy synthesis from {count} strategies: final signal is {signal}, consensus is {consensus}, with no detected conflicts."
    if lang=="ko": return f"{count}개 전략 종합: 신호 {signal}, 공감도 {consensus}, 충돌 강도 {severity}." if conflicts else f"{count}개 전략 종합: 신호 {signal}, 공감도 {consensus}, 감지된 충돌이 없습니다."
    if lang=="id": return f"Sintesis {count} strategi: sinyal {signal}, konsensus {consensus}, tingkat konflik {severity}." if conflicts else f"Sintesis {count} strategi: sinyal {signal}, konsensus {consensus}, tanpa konflik terdeteksi."
    return f"来自 {count} 个策略的综合判断：综合信号为{signal}，共识度为{consensus}，冲突强度为{severity}。" if conflicts else f"来自 {count} 个策略的综合判断：综合信号为{signal}，共识度为{consensus}，未检测到策略冲突。"


# Historical private spelling retained for downstream integrations.
_is_supported_report_language_value = is_supported_report_language_value

__all__ = [name for name in globals() if not name.startswith("__") and name not in {"Any", "Dict", "Optional", "Mapping", "re"}]
