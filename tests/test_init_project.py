"""Behavioral tests for deterministic Stage 0 initialization."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_initializer():
    path = ROOT / "scripts" / "init_project.py"
    spec = importlib.util.spec_from_file_location("mathmodel_initializer", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


initializer = load_initializer()


class ProjectInitializationTests(unittest.TestCase):
    def test_cli_requires_explicit_competition_and_year(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "init_project.py"),
                    "--workspace",
                    temp,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("--competition", result.stderr)
            self.assertIn("--year", result.stderr)
            self.assertFalse((Path(temp) / "state").exists())

    def test_huawei_2026_smoke_initializes_only_confirmed_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            decision_path, rules_path = initializer.initialize_project(
                workspace,
                "huawei",
                2026,
                started_at="2026-09-14T10:00:00+08:00",
            )
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            rules = json.loads(rules_path.read_text(encoding="utf-8"))

            self.assertEqual(decision["competition"], "huawei")
            self.assertEqual(decision["problem_meta"]["year"], 2026)
            self.assertEqual(
                decision["compliance"]["ruleset"]["competition_year"], 2026
            )
            self.assertIsNone(decision["problem_meta"]["letter"])
            self.assertIsNone(decision["stages"]["0"]["problem_scan"]["subproblem_count"])
            self.assertIsNone(decision["stages"]["5"]["qi_count"])
            self.assertEqual(rules["competition"], "huawei")
            self.assertEqual(rules["competition_year"], 2026)
            self.assertIsNone(rules["basis_status"])
            self.assertEqual(rules["sources"], [])
            self.assertTrue(
                all((workspace / name).is_dir() for name in initializer.WORKSPACE_DIRS)
            )

    def test_existing_state_is_preserved_and_not_partially_reinitialized(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            state_dir = workspace / "state"
            state_dir.mkdir()
            decision_path = state_dir / "decision_log.json"
            decision_path.write_text('{"sentinel": true}\n', encoding="utf-8")

            with self.assertRaises(FileExistsError):
                initializer.initialize_project(workspace, "cumcm", 2026)

            self.assertEqual(
                json.loads(decision_path.read_text(encoding="utf-8")),
                {"sentinel": True},
            )
            self.assertFalse((state_dir / "rules_snapshot.json").exists())

    def test_invalid_competition_or_year_is_rejected_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            with self.assertRaises(ValueError):
                initializer.initialize_project(workspace, "", 2026)
            with self.assertRaises(ValueError):
                initializer.initialize_project(workspace, "mcm", True)
            with self.assertRaises(ValueError):
                initializer.initialize_project(workspace, "mcm", 1999)
            self.assertFalse((workspace / "state").exists())


if __name__ == "__main__":
    unittest.main()
