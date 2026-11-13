"""Guard report-language imports and behavior used by production modules."""

import ast
import importlib
from pathlib import Path
import re
import unittest

from src import report_language


_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_IGNORED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "tests",
    "venv",
}
_LABEL_CONSUMERS = (
    "src/notification.py",
    "src/services/history_service.py",
    "src/services/report_renderer.py",
)
_TEMPLATE_LABEL_REFERENCE = re.compile(
    r"\blabels(?:\.([A-Za-z_][A-Za-z0-9_]*)|\[['\"]([^'\"]+)['\"]\])"
)


def _literal_module_import(call: ast.Call) -> bool:
    if not call.args or not isinstance(call.args[0], ast.Constant):
        return False
    module_name = call.args[0].value
    if not isinstance(module_name, str) or module_name != "src.report_language":
        return False
    return (
        isinstance(call.func, ast.Name) and call.func.id == "__import__"
    ) or (
        isinstance(call.func, ast.Attribute) and call.func.attr == "import_module"
    )


def _production_report_language_imports() -> tuple[set[str], bool]:
    imported_names: set[str] = set()
    has_dynamic_import = False
    for path in _REPOSITORY_ROOT.rglob("*.py"):
        if _IGNORED_DIRECTORIES.intersection(path.relative_to(_REPOSITORY_ROOT).parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents = {
            child: node
            for node in ast.walk(tree)
            for child in ast.iter_child_nodes(node)
        }
        dynamic_aliases: set[str] = set()
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "src.report_language":
                imported_names.update(alias.name for alias in node.names if alias.name != "*")
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                if isinstance(value, ast.Call) and _literal_module_import(value):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    dynamic_aliases.update(
                        target.id
                        for target in targets
                        if isinstance(target, ast.Name)
                    )

        for call in calls:
            if not _literal_module_import(call):
                continue
            has_dynamic_import = True
            parent = parents.get(call)
            if isinstance(parent, ast.Attribute) and parent.value is call:
                imported_names.add(parent.attr)

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id in dynamic_aliases:
                    imported_names.add(node.attr)
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "getattr"
                and len(node.args) > 1
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id in dynamic_aliases
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            ):
                imported_names.add(node.args[1].value)

    return imported_names, has_dynamic_import


def _literal_label_keys(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    keys: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id in {"labels", "report_labels"}
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        ):
            keys.add(node.slice.value)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in {"labels", "report_labels"}
            and node.func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            keys.add(node.args[0].value)
    return keys


def _template_label_keys(path: Path) -> set[str]:
    return {
        attribute or key
        for attribute, key in _TEMPLATE_LABEL_REFERENCE.findall(
            path.read_text(encoding="utf-8")
        )
    }


class ReportLanguageImportContractTest(unittest.TestCase):
    def test_all_production_imports_resolve(self):
        imported_names, has_dynamic_import = _production_report_language_imports()
        module = importlib.import_module("src.report_language")
        missing = sorted(name for name in imported_names if not hasattr(module, name))
        self.assertTrue(imported_names)
        self.assertEqual(missing, [])
        if has_dynamic_import:
            self.assertIs(module, report_language)

    def test_language_aliases_and_validation(self):
        aliases = {
            "zh-CN": "zh",
            "English": "en",
            "ko_KR": "ko",
            "Indonesian": "id",
            "id-ID": "id",
        }
        for raw, expected in aliases.items():
            with self.subTest(raw=raw):
                self.assertTrue(report_language.is_supported_report_language_value(raw))
                self.assertEqual(report_language.normalize_report_language(raw), expected)
                self.assertEqual(report_language.normalize_report_language_value(raw), expected)
        self.assertFalse(report_language.is_supported_report_language_value("english-invalid"))
        self.assertEqual(report_language.normalize_report_language("english-invalid"), "zh")

    def test_report_labels_cover_notification_and_rendering_keys(self):
        label_keys = {
            key
            for relative_path in _LABEL_CONSUMERS
            for key in _literal_label_keys(_REPOSITORY_ROOT / relative_path)
        }
        label_keys.update(
            key
            for path in (_REPOSITORY_ROOT / "templates").glob("*.j2")
            for key in _template_label_keys(path)
        )
        language_label_sets = []
        for language in report_language.SUPPORTED_REPORT_LANGUAGES:
            with self.subTest(language=language):
                labels = report_language.get_report_labels(language)
                language_label_sets.append(set(labels))
                self.assertTrue(label_keys.issubset(labels.keys()))
                self.assertEqual(labels["report_title"], {
                    "zh": "股票分析报告",
                    "en": "Stock Analysis Report",
                    "ko": "종목 분석 리포트",
                    "id": "Laporan Analisis Saham",
                }[language])
                self.assertTrue(labels["strategy_synthesis_heading"])
        self.assertTrue(all(keys == language_label_sets[0] for keys in language_label_sets))

    def test_language_specific_sentiment_stock_name_and_localization(self):
        expected = {
            "zh": ("中性", "待确认股票", "买入", "强烈看空"),
            "en": ("Neutral", "Unnamed Stock", "Buy", "Strong Bearish"),
            "ko": ("중립", "미확인 종목", "매수", "강한 하락"),
            "id": ("Netral", "Saham Belum Dikenal", "Beli", "Sangat Bearish"),
        }
        for language, (sentiment, stock_name, advice, trend) in expected.items():
            with self.subTest(language=language):
                self.assertEqual(report_language.get_sentiment_label(40, language), sentiment)
                self.assertEqual(
                    report_language.get_localized_stock_name("股票AAPL", "AAPL", language),
                    stock_name,
                )
                self.assertEqual(report_language.localize_operation_advice("买入", language), advice)
                self.assertEqual(
                    report_language.localize_trend_prediction("强烈看空", language),
                    trend,
                )
        self.assertEqual(report_language.get_localized_stock_name("Apple", "AAPL", "en"), "Apple")
        self.assertEqual(report_language.get_sentiment_label("invalid", "id"), "Netral")

    def test_confidence_and_chip_unavailable_localization(self):
        expected_confidence = {"zh": "高", "en": "High", "ko": "높음", "id": "Tinggi"}
        unavailable_chip = {
            "profit_ratio": "N/A",
            "avg_cost": "Unknown",
            "concentration": "Data unavailable",
        }
        self.assertTrue(report_language.is_chip_placeholder_value("Data unavailable"))
        self.assertTrue(report_language.is_chip_structure_unavailable(unavailable_chip))
        self.assertFalse(
            report_language.is_chip_structure_unavailable(
                {"profit_ratio": "70%", "avg_cost": 10, "concentration": "0.5"}
            )
        )
        for language in ("zh", "en", "ko", "id"):
            with self.subTest(language=language):
                self.assertEqual(report_language.localize_confidence_level("high", language), expected_confidence[language])
                reason = report_language.get_chip_unavailable_reason(unavailable_chip, language)
                self.assertTrue(reason)
                self.assertEqual(reason, report_language.get_chip_unavailable_text(language))
                self.assertEqual(
                    report_language.get_chip_unavailable_reason({"chip_unavailable": True}, language),
                    report_language.get_chip_unavailable_text(language),
                )
        explicit_reason = {"unavailable_reason": "provider disabled"}
        self.assertEqual(
            report_language.get_chip_unavailable_reason(explicit_reason, "en"),
            "provider disabled",
        )

    def test_strategy_synthesis_payload_helpers_and_localization(self):
        payload = {
            "final_signal": "buy",
            "consensus_level": "high",
            "conflict_severity": "none",
            "conflict_count": 0,
            "supporting_skills": [{"skill_id": "bull_trend"}, "invalid"],
            "opposing_skills": [{"skill_id": "event_driven"}],
            "conflicts": [None],
            "summary_params": {"opinion_count": 2, "invalid_opinion_count": "3"},
        }
        normalized = report_language.normalize_strategy_synthesis_payload(payload)
        self.assertEqual(len(normalized["supporting_skills"]), 1)
        self.assertEqual(len(normalized["opposing_skills"]), 1)
        self.assertEqual(normalized["conflicts"], [])
        self.assertEqual(report_language.strategy_invalid_opinion_count(payload), 3)
        self.assertEqual(report_language.strategy_invalid_opinion_count({"summary_params": "bad"}), 0)
        expected_signal = {"zh": "买入", "en": "Buy", "ko": "매수", "id": "Beli"}
        expected_skill = {
            "zh": "默认多头趋势",
            "en": "Bull Trend",
            "ko": "기본 상승 추세",
            "id": "Tren Bullish",
        }
        for language, signal in expected_signal.items():
            with self.subTest(language=language):
                summary = report_language.localize_strategy_synthesis_summary(payload, language)
                self.assertIn(signal, summary)
                self.assertTrue(summary)
                self.assertEqual(
                    report_language.localize_strategy_skill("bull_trend", language),
                    expected_skill[language],
                )


if __name__ == "__main__":
    unittest.main()
