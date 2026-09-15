#!/usr/bin/env python3
"""Fail-closed audit for a contest-rule verification snapshot."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any


COMPETITIONS = {"huawei"}
PHASES = {"kickoff", "writing", "final"}
CATEGORY_NAMES = (
    "eligibility_and_team",
    "schedule",
    "problem_and_download",
    "official_template_and_cover",
    "typography_and_paragraphs",
    "pagination_and_page_limits",
    "anonymity",
    "appendix_and_supporting_materials",
    "submission_files",
    "submission_process",
    "ai_use",
    "citation_and_originality",
)
CATEGORY_STATUSES = {"confirmed", "unknown", "not_applicable"}
BASIS_STATUSES = {"current_official", "prior_year_provisional"}


@dataclass(frozen=True)
class Finding:
    severity: str
    field: str
    message: str


def _finding(severity: str, field: str, message: str) -> Finding:
    return Finding(severity=severity, field=field, message=message)


def _nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return value is not None


def _valid_year(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 2000 <= value <= 2200


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def audit(
    snapshot: Any,
    phase: str,
    decision_log: Any | None = None,
) -> list[Finding]:
    """Return structured findings; any error means the requested phase is blocked."""

    if phase not in PHASES:
        raise ValueError(f"unknown phase: {phase}")
    if not isinstance(snapshot, dict):
        return [_finding("error", "root", "snapshot root must be an object")]

    findings: list[Finding] = []
    if snapshot.get("_schema_version") != "1.1":
        findings.append(_finding("error", "_schema_version", "expected 1.1"))

    competition = snapshot.get("competition")
    competition_year = snapshot.get("competition_year")
    basis_year = snapshot.get("basis_year")
    basis_status = snapshot.get("basis_status")
    replacement_required = snapshot.get("replacement_required")

    if competition not in COMPETITIONS:
        findings.append(_finding("error", "competition", "must name a supported contest"))
    if not _valid_year(competition_year):
        findings.append(_finding("error", "competition_year", "must be an explicit four-digit contest year"))
    if not _valid_year(basis_year):
        findings.append(_finding("error", "basis_year", "must identify the year of the rules actually used"))
    if basis_status not in BASIS_STATUSES:
        findings.append(_finding("error", "basis_status", "must be current_official or prior_year_provisional"))
    if not isinstance(replacement_required, bool):
        findings.append(_finding("error", "replacement_required", "must be boolean"))
    if not _valid_timestamp(snapshot.get("verified_at")):
        findings.append(_finding("error", "verified_at", "must be an ISO 8601 timestamp with timezone"))

    if basis_status == "current_official":
        if _valid_year(competition_year) and basis_year != competition_year:
            findings.append(_finding("error", "basis_year", "current_official must use the target contest year"))
        if replacement_required is not False:
            findings.append(_finding("error", "replacement_required", "current_official cannot require replacement"))
    elif basis_status == "prior_year_provisional":
        if _valid_year(competition_year) and _valid_year(basis_year) and basis_year >= competition_year:
            findings.append(_finding("error", "basis_year", "a prior-year basis must be earlier than the contest year"))
        if replacement_required is not True:
            findings.append(_finding("error", "replacement_required", "a provisional basis must require replacement"))
        approval = snapshot.get("participant_decision")
        approved = (
            isinstance(approval, dict)
            and approval.get("status") == "approved_provisional"
            and _nonempty(approval.get("approved_by"))
            and _valid_timestamp(approval.get("approved_at"))
        )
        if not approved:
            findings.append(_finding("error", "participant_decision", "prior-year fallback requires explicit participant approval"))
        severity = "error" if phase == "final" else "warning"
        findings.append(_finding(severity, "basis_status", "prior-year rules support preparation only, never final submission"))
    if phase == "final" and basis_status != "current_official":
        findings.append(_finding("error", "basis_status", "final submission requires current official rules"))

    sources = snapshot.get("sources")
    source_ids: set[str] = set()
    if not isinstance(sources, list) or not sources:
        findings.append(_finding("error", "sources", "at least one opened official source is required"))
        sources = []
    for index, source in enumerate(sources):
        field = f"sources[{index}]"
        if not isinstance(source, dict):
            findings.append(_finding("error", field, "must be an object"))
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id.strip():
            findings.append(_finding("error", f"{field}.id", "must be a non-empty string"))
        elif source_id in source_ids:
            findings.append(_finding("error", f"{field}.id", "duplicate source id"))
        else:
            source_ids.add(str(source_id))
        for key in ("title", "url", "applies_to_year"):
            if not _nonempty(source.get(key)):
                findings.append(_finding("error", f"{field}.{key}", "required"))
        if not _valid_timestamp(source.get("accessed_at")):
            findings.append(_finding("error", f"{field}.accessed_at", "must be an ISO 8601 timestamp with timezone"))
        if _nonempty(source.get("url")) and not str(source["url"]).startswith("https://"):
            findings.append(_finding("error", f"{field}.url", "official source URL must use https"))
        if source.get("official") is not True:
            findings.append(_finding("error", f"{field}.official", "must be true; secondary summaries are not rule authority"))
        applies_to_year = source.get("applies_to_year")
        if _nonempty(applies_to_year) and not _valid_year(applies_to_year):
            findings.append(_finding("error", f"{field}.applies_to_year", "must be a four-digit year"))
    source_years = {
        source.get("applies_to_year")
        for source in sources
        if isinstance(source, dict) and source.get("official") is True
    }
    required_source_year = (
        competition_year if basis_status == "current_official" else basis_year
    )
    if _valid_year(required_source_year) and required_source_year not in source_years:
        findings.append(
            _finding(
                "error",
                "sources",
                f"no official source is marked as applying to basis year {required_source_year}",
            )
        )

    categories = snapshot.get("categories")
    if not isinstance(categories, dict):
        findings.append(_finding("error", "categories", "must be an object"))
        categories = {}
    for name in CATEGORY_NAMES:
        category = categories.get(name)
        field = f"categories.{name}"
        if not isinstance(category, dict):
            findings.append(_finding("error", field, "required category object"))
            continue
        status = category.get("status")
        if status not in CATEGORY_STATUSES:
            findings.append(_finding("error", f"{field}.status", "must be confirmed, unknown, or not_applicable"))
            continue
        facts = category.get("facts")
        refs = category.get("source_ids")
        if not isinstance(facts, list):
            findings.append(_finding("error", f"{field}.facts", "must be a list"))
            facts = []
        if not isinstance(refs, list):
            findings.append(_finding("error", f"{field}.source_ids", "must be a list"))
            refs = []
        elif any(not isinstance(item, str) or not item.strip() for item in refs):
            findings.append(_finding("error", f"{field}.source_ids", "must contain non-empty string ids"))
        unknown_refs = sorted({str(item) for item in refs if str(item) not in source_ids})
        if unknown_refs:
            findings.append(_finding("error", f"{field}.source_ids", f"unknown source ids: {unknown_refs}"))
        if status == "confirmed" and (
            not facts
            or any(not isinstance(item, str) or not item.strip() for item in facts)
            or not refs
        ):
            findings.append(_finding("error", field, "confirmed requires non-empty facts and official source ids"))
        if status == "not_applicable" and (not refs or not _nonempty(category.get("notes"))):
            findings.append(_finding("error", field, "not_applicable requires an official source and rationale"))
        if status == "unknown":
            severity = "error" if phase == "final" else "warning"
            findings.append(_finding(severity, field, "rule category remains unknown"))

    unresolved = snapshot.get("unresolved_items")
    if not isinstance(unresolved, list):
        findings.append(_finding("error", "unresolved_items", "must be a list"))
        unresolved = []
    for index, item in enumerate(unresolved):
        field = f"unresolved_items[{index}]"
        if not isinstance(item, dict):
            findings.append(_finding("error", field, "must be an object"))
            continue
        for key in ("item", "impact", "blocking_phases"):
            if not _nonempty(item.get(key)):
                findings.append(_finding("error", f"{field}.{key}", "required"))
        blocking_phases = item.get("blocking_phases", [])
        if not isinstance(blocking_phases, list):
            findings.append(_finding("error", f"{field}.blocking_phases", "must contain only kickoff, writing, or final"))
            blocking_phases = []
        elif any(value not in PHASES for value in blocking_phases):
            findings.append(_finding("error", f"{field}.blocking_phases", "must contain only kickoff, writing, or final"))
        severity = "error" if phase == "final" or phase in blocking_phases else "warning"
        findings.append(_finding(severity, field, "unresolved rule item"))

    conflicts = snapshot.get("conflicts")
    if not isinstance(conflicts, list):
        findings.append(_finding("error", "conflicts", "must be a list"))
    elif conflicts:
        findings.append(_finding("error", "conflicts", "official-source or repository conflicts must be resolved and recorded before continuing"))

    if decision_log is not None:
        if not isinstance(decision_log, dict):
            findings.append(_finding("error", "decision_log", "root must be an object"))
        else:
            compliance = decision_log.get("compliance")
            if not isinstance(compliance, dict):
                findings.append(_finding("error", "decision_log.compliance", "must be an object"))
                compliance = {}
            ruleset = compliance.get("ruleset")
            if not isinstance(ruleset, dict):
                findings.append(_finding("error", "decision_log.compliance.ruleset", "must be an object"))
                ruleset = {}
            expected = {
                "competition": competition,
                "competition_year": competition_year,
                "basis_year": basis_year,
                "basis_status": basis_status,
                "replacement_required": replacement_required,
            }
            actual = {
                "competition": decision_log.get("competition"),
                "competition_year": ruleset.get("competition_year"),
                "basis_year": ruleset.get("basis_year"),
                "basis_status": ruleset.get("basis_status"),
                "replacement_required": ruleset.get("replacement_required"),
            }
            for key, value in expected.items():
                if actual.get(key) != value:
                    findings.append(_finding("error", f"decision_log.{key}", "does not match rules_snapshot.json"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=Path("state/rules_snapshot.json"))
    parser.add_argument("--phase", choices=sorted(PHASES), required=True)
    parser.add_argument("--decision-log", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    try:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
        decision_log = (
            json.loads(args.decision_log.read_text(encoding="utf-8"))
            if args.decision_log else None
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] 无法读取规则状态: {exc}")
        return 1

    findings = audit(snapshot, args.phase, decision_log)
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    else:
        for item in findings:
            print(f"[{item.severity.upper()}] {item.field}: {item.message}")
        errors = sum(item.severity == "error" for item in findings)
        warnings = sum(item.severity == "warning" for item in findings)
        print(f"Summary: {errors} errors, {warnings} warnings")
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
