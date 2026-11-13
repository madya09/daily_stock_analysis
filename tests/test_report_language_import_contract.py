"""Guard the report-language API used by production importers.

This contract catches failures at test time instead of letting a scheduled run
fail during application startup with an ImportError.
"""

import unittest


class ReportLanguageImportContractTest(unittest.TestCase):
    def test_all_runtime_imported_helpers_are_available(self):
        from src import report_language as language

        expected = (
            "SUPPORTED_REPORT_LANGUAGES",
            "get_bias_status_emoji",
            "get_chip_unavailable_reason",
            "get_chip_unavailable_text",
            "get_localized_stock_name",
            "get_no_data_text",
            "get_placeholder_text",
            "get_report_labels",
            "get_sentiment_label",
            "get_signal_level",
            "get_unknown_text",
            "infer_decision_type_from_advice",
            "is_chip_placeholder_value",
            "is_chip_structure_unavailable",
            "is_supported_report_language_value",
            "localize_bias_status",
            "localize_chip_health",
            "localize_confidence_level",
            "localize_conflict_severity",
            "localize_consensus_level",
            "localize_operation_advice",
            "localize_strategy_conflict_description",
            "localize_strategy_signal",
            "localize_strategy_skill",
            "localize_strategy_synthesis_summary",
            "localize_trend_prediction",
            "normalize_report_language",
            "normalize_strategy_synthesis_payload",
            "strategy_invalid_opinion_count",
        )
        missing = [name for name in expected if not callable(getattr(language, name, None)) and name != "SUPPORTED_REPORT_LANGUAGES"]
        missing_constants = [name for name in expected if name == "SUPPORTED_REPORT_LANGUAGES" and not hasattr(language, name)]
        self.assertEqual(missing + missing_constants, [])

    def test_language_alias_validation_is_consistent(self):
        from src.report_language import (
            is_supported_report_language_value,
            normalize_report_language,
        )

        for raw, expected in (("zh-CN", "zh"), ("en_US", "en"), ("ko-KR", "ko"), ("id-ID", "id")):
            self.assertTrue(is_supported_report_language_value(raw))
            self.assertEqual(normalize_report_language(raw), expected)
        self.assertFalse(is_supported_report_language_value("english-invalid"))

    def test_legacy_and_indonesian_localization_regressions(self):
        from src.report_language import (
            get_localized_stock_name,
            get_report_labels,
            get_signal_level,
            infer_decision_type_from_advice,
            localize_operation_advice,
            localize_trend_prediction,
        )

        self.assertEqual(get_localized_stock_name("股票AAPL", "AAPL", "en"), "Unnamed Stock")
        self.assertEqual(get_signal_level("", 28, "zh"), ("减仓", "🟠", "reduce"))
        self.assertEqual(get_signal_level("Buy / Watch", 40, "en"), ("Buy", "🟢", "buy"))
        self.assertEqual(infer_decision_type_from_advice("不建议买入"), "hold")
        self.assertEqual(localize_operation_advice("买入", "id"), "Beli")
        self.assertEqual(localize_trend_prediction("看多", "id"), "Bullish")
        self.assertEqual(get_report_labels("id")["report_title"], "Laporan Analisis Saham")


if __name__ == "__main__":
    unittest.main()
