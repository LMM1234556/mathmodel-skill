"""Regression tests for problem, paper, and visualization quality gates."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mathmodel-matplotlib-tests")

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]


def load_plot_style():
    path = ROOT / "templates" / "shared" / "plot_style.py"
    spec = importlib.util.spec_from_file_location("mathmodel_plot_style", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plot_style = load_plot_style()


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
        self.assertIn("paper_quality_protocol.md", stage8)
        self.assertIn("visualization_protocol.md", stage8)
        self.assertIn("evidence_traceability_passed", stage9)

    def test_decision_log_v32_exposes_quality_gate_state(self) -> None:
        state = json.loads(
            (ROOT / "templates" / "shared" / "decision_log.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(state["_schema_version"], "3.2")
        self.assertIn("requirement_traceability", state["stages"]["2"])
        self.assertIn("claim_evidence_matrix_path", state["stages"]["8"])
        self.assertIn("figure_audit_passed", state["stages"]["9"])


class PlotStyleTests(unittest.TestCase):
    def tearDown(self) -> None:
        plt.close("all")

    def test_missing_evidence_metadata_fails_closed(self) -> None:
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        ax.set(xlabel="x", ylabel="y")
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "figure_id"):
                plot_style.save_figure(
                    fig,
                    Path(temp) / "bad",
                    figure_id="",
                    claim="claim",
                    caption="caption",
                    source_paths=["results/source.csv"],
                    generator="results/plot.py",
                )

    def test_save_figure_writes_outputs_sidecar_and_registry(self) -> None:
        selected_font = plot_style.configure_matplotlib("en")
        self.assertIsInstance(selected_font, str)
        self.assertTrue(selected_font)

        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], [0, 1, 4], label="model")
        ax.set(xlabel="Time (h)", ylabel="Objective (unit)")
        ax.legend()

        with tempfile.TemporaryDirectory() as temp:
            stem = Path(temp) / "figures" / "q1_result"
            record = plot_style.save_figure(
                fig,
                stem,
                figure_id="Q1-F01",
                claim="The objective increases across the tested times.",
                caption="Objective values for the three tested times.",
                source_paths=["results/q1.csv"],
                generator="results/plot_q1.py",
            )

            self.assertTrue(stem.with_suffix(".png").is_file())
            self.assertTrue(stem.with_suffix(".pdf").is_file())
            self.assertTrue(stem.with_suffix(".figure.json").is_file())
            registry = stem.parent / "figure_registry.json"
            self.assertTrue(registry.is_file())
            data = json.loads(registry.read_text(encoding="utf-8"))
            self.assertEqual(data["figures"][0]["figure_id"], "Q1-F01")
            self.assertEqual(record["audit_issues"], [])

    def test_audit_reports_missing_axis_labels(self) -> None:
        fig, ax = plt.subplots()
        ax.plot([0, 1], [1, 2])
        issues = plot_style.audit_figure(fig)
        problems = " ".join(item["problem"] for item in issues)
        self.assertIn("x 轴", problems)
        self.assertIn("y 轴", problems)


class StateMigrationTests(unittest.TestCase):
    def test_v31_state_is_backed_up_and_merged(self) -> None:
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
            self.assertEqual(migrated["_schema_version"], "3.2")
            self.assertEqual(migrated["problem"], "A")
            self.assertEqual(migrated["stages"]["2"]["requirement_traceability"], [])
            self.assertEqual(migrated["custom_extension"], {"keep": True})


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
