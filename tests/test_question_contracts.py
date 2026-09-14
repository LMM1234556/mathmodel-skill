"""Behavioral tests for per-question data isolation and approval gates."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_auditor():
    path = ROOT / "scripts" / "audit_question_contracts.py"
    spec = importlib.util.spec_from_file_location("mathmodel_question_auditor", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


auditor = load_auditor()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_contract(workspace: Path, question: str = "Q1") -> dict:
    data_dir = workspace / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    data_path = data_dir / f"{question.lower()}.csv"
    data_path.write_text("time,value\n1,2\n", encoding="utf-8")

    contract = json.loads(
        (ROOT / "templates" / "shared" / "question_contract.json").read_text(
            encoding="utf-8"
        )
    )
    contract["question_id"] = question
    contract["status"] = "completed"
    contract["source"] = {
        "requirement_ids": ["R01"],
        "source_anchors": ["p.1 paragraph 2"],
        "team_interpretation": "Estimate the requested quantity for the stated period.",
        "deliverables": ["validated estimate"],
        "ambiguities": [],
    }
    contract["dependencies"] = {
        "upstream_results": [],
        "independence_rationale": "This question uses only its declared raw attachment.",
        "forbidden_inputs": ["data/labels.csv"],
    }
    contract["data_contract"] = {
        "datasets": [
            {
                "path": f"data/{question.lower()}.csv",
                "sha256": sha256(data_path),
                "sheet_or_table": "CSV table",
                "fields": [
                    {"name": "time", "meaning": "ordered time index", "unit": "period", "role": "feature"},
                    {"name": "value", "meaning": "observed value", "unit": "unit", "role": "target"},
                ],
                "row_scope": "all two fixture rows",
                "filters": [],
                "preprocessing": [],
                "exclusions": [],
                "purpose": "fit and validate the Q1 model",
            }
        ],
        "no_data_reason": "",
        "observed_accesses": [
            {
                "path": f"data/{question.lower()}.csv",
                "sha256": sha256(data_path),
                "sheet_or_table": "CSV table",
                "fields": ["time", "value"],
                "row_scope": "all two fixture rows",
                "filters": [],
                "preprocessing": [],
                "exclusions": [],
            }
        ],
    }
    contract["model_plan"] = {
        "candidates": [
            {
                "id": "M0",
                "name": "Mean baseline",
                "family": "constant predictor",
                "role": "baseline",
                "fit_evidence": "Provides a valid low-complexity comparison.",
                "assumptions": ["stable mean"],
                "data_requirements": ["observed value"],
                "implementation": "deterministic Python function",
                "validation": "same holdout MAE",
                "risks": ["ignores trend"],
                "references": [],
            },
            {
                "id": "M1",
                "name": "Linear trend",
                "family": "regression",
                "role": "mainstream",
                "fit_evidence": "Matches the ordered numeric target.",
                "assumptions": ["approximately linear trend"],
                "data_requirements": ["time and value"],
                "implementation": "least squares",
                "validation": "same holdout MAE",
                "risks": ["poor nonlinear extrapolation"],
                "references": [],
            },
        ],
        "single_candidate_justification": "",
        "recommended_candidate_id": "M1",
        "selection_criteria": ["holdout MAE", "interpretability"],
        "validation_plan": {
            "metrics": ["MAE"],
            "split_or_scenarios": "ordered holdout",
            "baseline_candidate_id": "M0",
            "failure_conditions": ["worse MAE than baseline"],
        },
    }
    contract["figure_plan"] = {
        "evidence_questions": ["Does the fitted trend follow observations?"],
        "candidate_chart_types": ["line with observed markers", "residual plot"],
        "preliminary_recommendation": "line with observed markers",
        "no_figure_reason": "",
        "final_chart_types": ["line with observed markers"],
        "rationale": "Ordered observations and fit share a common time axis.",
        "result_ids": [f"{question}-R01"],
    }
    contract["execution"] = {
        "chosen_model_id": "M1",
        "code_paths": [f"results/{question}_solve.py"],
        "result_ids": [f"{question}-R01"],
        "observed_upstream_result_ids": [],
        "validation_status": "passed",
    }
    contract["invalidation"] = {
        "status": "current",
        "reason": None,
        "invalidated_at": None,
        "downstream_questions": [],
    }
    for name in ("pre_execution", "final_model", "final_figures"):
        contract["approvals"][name] = {
            "status": "approved",
            "approved_by": "team",
            "approved_at": "2026-09-14T10:00:00+08:00",
            "contract_digest": auditor.contract_digest(contract, name),
            "notes": "fixture approval",
        }
    return contract


def write_contract(workspace: Path, contract: dict) -> Path:
    path = workspace / "state" / "questions" / contract["question_id"] / "question_contract.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


class QuestionContractAuditTests(unittest.TestCase):
    def test_blank_template_fails_plan_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            template = json.loads(
                (ROOT / "templates" / "shared" / "question_contract.json").read_text(encoding="utf-8")
            )
            write_contract(workspace, template)
            findings = auditor.audit(workspace, "plan")
            self.assertTrue(any(item.severity == "error" for item in findings))
            self.assertTrue(any(item.field == "source.team_interpretation" for item in findings))

    def test_execute_requires_explicit_preapproval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            contract = valid_contract(workspace)
            contract["approvals"]["pre_execution"]["status"] = "pending"
            write_contract(workspace, contract)
            findings = auditor.audit(workspace, "execute", "Q1")
            self.assertTrue(any(item.field == "approvals.pre_execution" for item in findings))

    def test_approval_digest_detects_post_approval_plan_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            contract = valid_contract(workspace)
            contract["data_contract"]["datasets"][0]["row_scope"] = "only the first row"
            write_contract(workspace, contract)
            findings = auditor.audit(workspace, "execute", "Q1")
            self.assertTrue(any(item.field == "approvals.pre_execution" for item in findings))

    def test_final_blocks_undeclared_and_forbidden_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            forbidden = workspace / "data" / "labels.csv"
            forbidden.parent.mkdir(parents=True, exist_ok=True)
            forbidden.write_text("label\n1\n", encoding="utf-8")
            contract = valid_contract(workspace)
            contract["data_contract"]["observed_accesses"].append(
                {
                    "path": "data/labels.csv",
                    "sha256": sha256(forbidden),
                    "sheet_or_table": "CSV table",
                    "fields": ["label"],
                    "row_scope": "all rows",
                    "filters": [],
                    "preprocessing": [],
                    "exclusions": [],
                }
            )
            write_contract(workspace, contract)
            findings = auditor.audit(workspace, "final", "Q1")
            messages = "\n".join(item.message for item in findings)
            self.assertIn("undeclared input", messages)
            self.assertIn("forbidden input observed", messages)

    def test_final_blocks_undeclared_field_in_approved_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            contract = valid_contract(workspace)
            contract["data_contract"]["observed_accesses"][0]["fields"].append("future_label")
            write_contract(workspace, contract)
            findings = auditor.audit(workspace, "final", "Q1")
            self.assertTrue(any(item.message == "undeclared field: future_label" for item in findings))

    def test_final_blocks_changed_exclusions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            contract = valid_contract(workspace)
            contract["data_contract"]["observed_accesses"][0]["exclusions"] = [
                "drop negative values"
            ]
            write_contract(workspace, contract)
            findings = auditor.audit(workspace, "final", "Q1")
            self.assertTrue(
                any(
                    item.field.endswith(".exclusions")
                    and item.message == "does not match approved data contract"
                    for item in findings
                )
            )

    def test_valid_final_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            contract = valid_contract(workspace)
            write_contract(workspace, contract)
            self.assertEqual(auditor.audit(workspace, "final", "Q1"), [])

    def test_dependency_cycle_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            q1 = valid_contract(workspace, "Q1")
            q2 = valid_contract(workspace, "Q2")
            q1["dependencies"]["upstream_results"] = [
                {"question_id": "Q2", "result_id": "Q2-R01", "rationale": "test", "meaning": "value", "unit": "unit"}
            ]
            q1["dependencies"]["independence_rationale"] = ""
            q2["dependencies"]["upstream_results"] = [
                {"question_id": "Q1", "result_id": "Q1-R01", "rationale": "test", "meaning": "value", "unit": "unit"}
            ]
            q2["dependencies"]["independence_rationale"] = ""
            write_contract(workspace, q1)
            write_contract(workspace, q2)
            findings = auditor.audit(workspace, "plan")
            self.assertTrue(any("cycle" in item.message for item in findings))


if __name__ == "__main__":
    unittest.main()
