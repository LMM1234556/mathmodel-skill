"""Regression tests for problem, paper, and visualization quality gates."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_migrate_state():
    path = ROOT / "scripts" / "migrate_state.py"
    spec = importlib.util.spec_from_file_location("mathmodel_migrate_state", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migrate_state = load_migrate_state()


def load_render_paper():
    path = ROOT / "scripts" / "render_paper.py"
    spec = importlib.util.spec_from_file_location("mathmodel_render_quality", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


render_paper = load_render_paper()


class QualityGatePackageTests(unittest.TestCase):
    def test_stage_files_route_to_new_protocols(self) -> None:
        stage2 = (ROOT / "references" / "stage_02_analysis.md").read_text(
            encoding="utf-8"
        )
        stage8 = (ROOT / "references" / "stage_08_writing.md").read_text(
            encoding="utf-8"
        )
        stage9 = (ROOT / "references" / "stage_09_review.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("problem_understanding_protocol.md", stage2)
        self.assertIn("question_contract_protocol.md", stage2)
        self.assertIn("paper_quality_protocol.md", stage8)
        self.assertIn("visualization_protocol.md", stage8)
        self.assertIn("evidence_traceability_passed", stage9)

    def test_decision_log_v33_exposes_quality_gate_state(self) -> None:
        state = json.loads(
            (ROOT / "templates" / "shared" / "decision_log.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(state["_schema_version"], "3.3")
        self.assertIn("requirement_traceability", state["stages"]["2"])
        self.assertIn("question_contracts", state["stages"]["2"])
        self.assertIn("interpretation_approval", state["stages"]["2"])
        self.assertIn("question_contracts_plan_audit", state["stages"]["3"])
        self.assertEqual(state["stages"]["5"]["question_contracts_dir"], "state/questions")
        self.assertIn("claim_evidence_matrix_path", state["stages"]["8"])
        self.assertIn("figure_audit_passed", state["stages"]["9"])
        self.assertEqual(
            state["stages"]["5"]["figure_policy"]["final_quantitative_renderer"],
            "MATLAB",
        )
        self.assertIn(
            "matlab_final_figures_only",
            state["stages"]["8"]["paper_quality_checks"],
        )


class MatlabFigurePipelineTests(unittest.TestCase):
    def test_matlab_helpers_and_test_exist(self) -> None:
        helper = ROOT / "templates" / "shared" / "matlab"
        for name in (
            "mm_style.m",
            "mm_choose_chart.m",
            "mm_audit_figure.m",
            "mm_export_figure.m",
        ):
            self.assertTrue((helper / name).is_file(), name)
        self.assertTrue(
            (ROOT / "tests" / "matlab" / "test_mm_figure_pipeline.m").is_file()
        )

    def test_protocol_requires_matlab_and_chart_rationale(self) -> None:
        protocol = (ROOT / "references" / "visualization_protocol.md").read_text(
            encoding="utf-8"
        )
        self.assertIn('renderer != "MATLAB"', protocol)
        self.assertIn("chart_type_rationale", protocol)
        self.assertIn("mm_choose_chart", protocol)
        self.assertNotIn("plot_style.py", protocol)

    def test_python_starters_do_not_plot(self) -> None:
        starters = ROOT / "templates" / "shared" / "code_starter"
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in starters.glob("*.py")
        )
        self.assertNotIn("matplotlib", combined)
        self.assertNotIn("seaborn", combined)
        self.assertNotIn("plt.", combined)

    def test_export_helper_fails_closed_on_evidence_fields(self) -> None:
        helper = (
            ROOT / "templates" / "shared" / "matlab" / "mm_export_figure.m"
        ).read_text(encoding="utf-8")
        for field in (
            "figure_id",
            "claim",
            "decision",
            "source_paths",
            "generator",
            "chart_type",
            "chart_type_rationale",
            "encoding",
            "uncertainty",
            "caption",
        ):
            self.assertIn(f'"{field}"', helper)
        self.assertIn("record.renderer = 'MATLAB'", helper)


class StateMigrationTests(unittest.TestCase):
    def test_v31_state_is_backed_up_and_merged_to_v33(self) -> None:
        template = json.loads(
            (ROOT / "templates" / "shared" / "decision_log.json").read_text(
                encoding="utf-8"
            )
        )
        legacy = json.loads(json.dumps(template))
        legacy["_schema_version"] = "3.1"
        legacy["problem"] = "A"
        legacy["stages"]["2"].pop("requirement_traceability")
        legacy["custom_extension"] = {"keep": True}

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "decision_log.json"
            path.write_text(
                json.dumps(legacy, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            backup = migrate_state.migrate(path)
            self.assertIsNotNone(backup)
            self.assertTrue(backup.is_file())
            migrated = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(migrated["_schema_version"], "3.3")
            self.assertEqual(migrated["problem"], "A")
            self.assertEqual(migrated["stages"]["2"]["requirement_traceability"], [])
            self.assertEqual(migrated["stages"]["2"]["question_contracts"], {})
            self.assertEqual(migrated["custom_extension"], {"keep": True})

    def test_v32_state_adds_question_contract_fields(self) -> None:
        template = json.loads(
            (ROOT / "templates" / "shared" / "decision_log.json").read_text(
                encoding="utf-8"
            )
        )
        legacy = json.loads(json.dumps(template))
        legacy["_schema_version"] = "3.2"
        legacy["stages"]["2"].pop("question_contracts")
        legacy["stages"]["3"].pop("question_contracts_plan_audit")
        legacy["stages"]["5"].pop("question_contracts_dir")

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "decision_log.json"
            path.write_text(json.dumps(legacy, ensure_ascii=False), encoding="utf-8")
            backup = migrate_state.migrate(path)
            self.assertIsNotNone(backup)
            migrated = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(migrated["_schema_version"], "3.3")
            self.assertEqual(migrated["stages"]["2"]["question_contracts"], {})
            self.assertEqual(
                migrated["stages"]["3"]["question_contracts_plan_audit"]["status"],
                "pending",
            )
            self.assertEqual(migrated["stages"]["5"]["question_contracts_dir"], "state/questions")


class HuaweiPackTests(unittest.TestCase):
    def test_internal_review_template_wires_all_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "paper_workspace"
            workspace.mkdir()
            for section, filename in render_paper.SECTION_TO_FILE.items():
                text = "Internal abstract.\n" if section == "abstract" else (
                    f"# {section}\n\nInternal content.\n"
                )
                (workspace / filename).write_text(text, encoding="utf-8")

            main_path, engine = render_paper.fill_template(
                "huawei",
                workspace,
                root / "paper_output",
                prefer_pandoc=False,
                allow_placeholders=True,
            )
            main_text = main_path.read_text(encoding="utf-8")
            self.assertEqual(engine, "xelatex")
            self.assertIn("内部评阅稿", main_text)
            self.assertIsNone(render_paper.SECTION_MARKER_RE.search(main_text))
            for section in render_paper.SECTION_TO_FILE:
                self.assertIn(rf"\input{{sections/{section}}}", main_text)
            self.assertFalse(
                render_paper.compile_pdf(main_path, engine="xelatex", runs=1)
            )


if __name__ == "__main__":
    unittest.main()
