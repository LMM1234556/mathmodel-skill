"""Behavioral tests for contest-rule verification gates."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_auditor():
    path = ROOT / "scripts" / "audit_ruleset.py"
    spec = importlib.util.spec_from_file_location("mathmodel_ruleset_auditor", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


auditor = load_auditor()


def valid_snapshot() -> dict:
    snapshot = json.loads(
        (ROOT / "templates" / "shared" / "rules_snapshot.json").read_text(
            encoding="utf-8"
        )
    )
    snapshot.update(
        {
            "competition": "huawei",
            "competition_year": 2026,
            "basis_year": 2026,
            "basis_status": "current_official",
            "replacement_required": False,
            "verified_at": "2026-09-23T08:30:00+08:00",
            "sources": [
                {
                    "id": "S1",
                    "title": "2026 official opening notice",
                    "url": "https://example.edu/official-2026",
                    "official": True,
                    "published_at": "2026-09-23",
                    "accessed_at": "2026-09-23T08:30:00+08:00",
                    "applies_to_year": 2026,
                }
            ],
        }
    )
    for category in snapshot["categories"].values():
        category.update(
            {
                "status": "confirmed",
                "facts": ["Verified against the official opening notice."],
                "source_ids": ["S1"],
            }
        )
    return snapshot


class RulesetAuditTests(unittest.TestCase):
    def test_blank_template_fails_final_gate(self) -> None:
        snapshot = json.loads(
            (ROOT / "templates" / "shared" / "rules_snapshot.json").read_text(
                encoding="utf-8"
            )
        )
        findings = auditor.audit(snapshot, "final")
        self.assertTrue(any(item.severity == "error" for item in findings))
        self.assertTrue(any(item.field == "competition" for item in findings))
        self.assertTrue(
            any(item.field == "categories.typography_and_paragraphs" for item in findings)
        )

    def test_format_categories_cannot_be_collapsed_into_one_generic_status(self) -> None:
        snapshot = valid_snapshot()
        snapshot["categories"].pop("pagination_and_page_limits")
        findings = auditor.audit(snapshot, "final")
        self.assertTrue(
            any(
                item.field == "categories.pagination_and_page_limits"
                and item.severity == "error"
                for item in findings
            )
        )

    def test_complete_current_official_snapshot_passes_final(self) -> None:
        self.assertEqual(auditor.audit(valid_snapshot(), "final"), [])

    def test_prior_year_fallback_is_preparation_only(self) -> None:
        snapshot = valid_snapshot()
        snapshot["basis_year"] = 2025
        snapshot["basis_status"] = "prior_year_provisional"
        snapshot["replacement_required"] = True
        snapshot["sources"][0]["applies_to_year"] = 2025
        snapshot["participant_decision"] = {
            "status": "approved_provisional",
            "approved_by": "team",
            "approved_at": "2026-09-14T10:00:00+08:00",
            "notes": "Use only for rehearsal.",
        }
        kickoff = auditor.audit(snapshot, "kickoff")
        self.assertFalse(any(item.severity == "error" for item in kickoff))
        self.assertTrue(any(item.severity == "warning" for item in kickoff))
        final = auditor.audit(snapshot, "final")
        self.assertTrue(any(item.field == "basis_status" and item.severity == "error" for item in final))

    def test_decision_log_mismatch_is_blocking(self) -> None:
        snapshot = valid_snapshot()
        decision_log = {
            "competition": "cumcm",
            "compliance": {
                "ruleset": {
                    "competition_year": 2026,
                    "basis_year": 2026,
                    "basis_status": "current_official",
                    "replacement_required": False,
                }
            },
        }
        findings = auditor.audit(snapshot, "final", decision_log)
        self.assertTrue(any(item.field == "decision_log.competition" for item in findings))

    def test_current_official_requires_a_source_for_the_target_year(self) -> None:
        snapshot = valid_snapshot()
        snapshot["sources"][0]["applies_to_year"] = 2025
        findings = auditor.audit(snapshot, "final")
        self.assertTrue(
            any(
                item.field == "sources" and "basis year 2026" in item.message
                for item in findings
            )
        )

    def test_any_unresolved_item_blocks_final(self) -> None:
        snapshot = valid_snapshot()
        snapshot["unresolved_items"] = [
            {
                "item": "filename rule not confirmed",
                "impact": "submission may be rejected",
                "blocking_phases": [],
            }
        ]
        findings = auditor.audit(snapshot, "final")
        self.assertTrue(
            any(
                item.field == "unresolved_items[0]"
                and item.severity == "error"
                for item in findings
            )
        )

    def test_malformed_unresolved_item_and_state_fail_without_crashing(self) -> None:
        snapshot = valid_snapshot()
        snapshot["unresolved_items"] = [
            {
                "item": "AI notice missing",
                "impact": "disclosure unknown",
                "blocking_phases": None,
            }
        ]
        findings = auditor.audit(snapshot, "kickoff", {"competition": "huawei"})
        self.assertTrue(
            any(item.field == "unresolved_items[0].blocking_phases" for item in findings)
        )
        self.assertTrue(
            any(item.field == "decision_log.compliance" for item in findings)
        )


if __name__ == "__main__":
    unittest.main()
