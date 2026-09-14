#!/usr/bin/env python3
"""Fail-closed audit for per-question modeling contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


QUESTION_ID_RE = re.compile(r"Q[1-9][0-9]*\Z")
APPROVED = "approved"


@dataclass(frozen=True)
class Finding:
    severity: str
    question: str
    field: str
    message: str


def _finding(severity: str, question: str, field: str, message: str) -> Finding:
    return Finding(severity=severity, question=question, field=field, message=message)


def _nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return value is not None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(workspace: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (workspace / path).resolve()


def contract_digest(contract: dict[str, Any], name: str) -> str:
    """Bind an approval to the decision fields it authorizes."""

    data_contract = contract.get("data_contract", {})
    figure_plan = contract.get("figure_plan", {})
    execution = contract.get("execution", {})
    common = {
        "question_id": contract.get("question_id"),
        "source": contract.get("source"),
        "dependencies": contract.get("dependencies"),
        "data_contract": {
            "datasets": data_contract.get("datasets") if isinstance(data_contract, dict) else None,
            "no_data_reason": data_contract.get("no_data_reason") if isinstance(data_contract, dict) else None,
        },
        "model_plan": contract.get("model_plan"),
    }
    if name == "pre_execution":
        common["figure_plan"] = {
            key: figure_plan.get(key) if isinstance(figure_plan, dict) else None
            for key in (
                "evidence_questions",
                "candidate_chart_types",
                "preliminary_recommendation",
                "no_figure_reason",
            )
        }
    elif name == "final_model":
        common["execution"] = {
            key: execution.get(key) if isinstance(execution, dict) else None
            for key in (
                "chosen_model_id",
                "result_ids",
                "observed_upstream_result_ids",
                "validation_status",
            )
        }
    elif name == "final_figures":
        common["figure_plan"] = figure_plan
        common["model_result"] = {
            "chosen_model_id": execution.get("chosen_model_id") if isinstance(execution, dict) else None,
            "result_ids": execution.get("result_ids") if isinstance(execution, dict) else None,
        }
    else:
        raise ValueError(f"unknown approval gate: {name}")
    encoded = json.dumps(common, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _approval_ok(contract: dict[str, Any], name: str) -> bool:
    approval = contract.get("approvals", {}).get(name, {})
    return (
        isinstance(approval, dict)
        and approval.get("status") == APPROVED
        and _nonempty(approval.get("approved_by"))
        and _nonempty(approval.get("approved_at"))
        and approval.get("contract_digest") == contract_digest(contract, name)
    )


def _audit_dataset(
    workspace: Path,
    question: str,
    dataset: Any,
    phase: str,
    index: int,
) -> list[Finding]:
    findings: list[Finding] = []
    field = f"data_contract.datasets[{index}]"
    if not isinstance(dataset, dict):
        return [_finding("error", question, field, "dataset entry must be an object")]

    for key in ("path", "sha256", "sheet_or_table", "fields", "row_scope", "purpose"):
        if key not in dataset or not _nonempty(dataset[key]):
            findings.append(_finding("error", question, f"{field}.{key}", "required"))
    for key in ("filters", "preprocessing", "exclusions"):
        if key not in dataset or not isinstance(dataset[key], list):
            findings.append(_finding("error", question, f"{field}.{key}", "must be a list; [] means none"))

    fields = dataset.get("fields", [])
    if isinstance(fields, list):
        for field_index, item in enumerate(fields):
            field_path = f"{field}.fields[{field_index}]"
            if not isinstance(item, dict):
                findings.append(_finding("error", question, field_path, "must be an object"))
                continue
            for key in ("name", "meaning", "unit", "role"):
                if not _nonempty(item.get(key)):
                    findings.append(_finding("error", question, f"{field_path}.{key}", "required"))
    elif "fields" in dataset:
        findings.append(_finding("error", question, f"{field}.fields", "must be a list"))

    expected = str(dataset.get("sha256") or "").lower().strip()
    if expected and not re.fullmatch(r"[0-9a-f]{64}", expected):
        findings.append(_finding("error", question, f"{field}.sha256", "must be 64 hexadecimal characters"))

    if phase in {"execute", "final"} and _nonempty(dataset.get("path")):
        data_path = _resolve(workspace, str(dataset["path"]))
        if not data_path.is_file():
            findings.append(_finding("error", question, f"{field}.path", f"file not found: {data_path}"))
        else:
            if not expected:
                findings.append(_finding("error", question, f"{field}.sha256", "required before execution"))
            elif re.fullmatch(r"[0-9a-f]{64}", expected) and _sha256(data_path) != expected:
                findings.append(_finding("error", question, f"{field}.sha256", "does not match the current file"))
    return findings


def _audit_contract(workspace: Path, contract: Any, phase: str, source_path: Path) -> tuple[list[Finding], dict[str, Any] | None]:
    if not isinstance(contract, dict):
        return [_finding("error", source_path.parent.name, "root", "contract root must be an object")], None

    question = str(contract.get("question_id") or source_path.parent.name)
    findings: list[Finding] = []
    if contract.get("_schema_version") != "1.0":
        findings.append(_finding("error", question, "_schema_version", "expected 1.0"))
    if not QUESTION_ID_RE.fullmatch(question):
        findings.append(_finding("error", question, "question_id", "must match Q1, Q2, ..."))
    if source_path.parent.name != question:
        findings.append(_finding("error", question, "question_id", "must match its state/questions/<Qi> directory"))
    if contract.get("status") not in {"draft", "awaiting_approval", "approved", "completed", "invalidated"}:
        findings.append(_finding("error", question, "status", "invalid status"))

    source = contract.get("source", {})
    if not isinstance(source, dict):
        findings.append(_finding("error", question, "source", "must be an object"))
        source = {}
    for key in ("requirement_ids", "source_anchors", "team_interpretation", "deliverables"):
        if not _nonempty(source.get(key)):
            findings.append(_finding("error", question, f"source.{key}", "required"))
    for index, ambiguity in enumerate(source.get("ambiguities", [])):
        if not isinstance(ambiguity, dict) or ambiguity.get("status") not in {"resolved", "accepted_low_risk"}:
            findings.append(_finding("error", question, f"source.ambiguities[{index}]", "unresolved or malformed ambiguity"))

    dependencies = contract.get("dependencies", {})
    if not isinstance(dependencies, dict):
        findings.append(_finding("error", question, "dependencies", "must be an object"))
        dependencies = {}
    upstream = dependencies.get("upstream_results", [])
    if not isinstance(upstream, list):
        findings.append(_finding("error", question, "dependencies.upstream_results", "must be a list"))
        upstream = []
    if not upstream and not _nonempty(dependencies.get("independence_rationale")):
        findings.append(_finding("error", question, "dependencies.independence_rationale", "required when no upstream result is used"))
    for index, item in enumerate(upstream):
        path = f"dependencies.upstream_results[{index}]"
        if not isinstance(item, dict):
            findings.append(_finding("error", question, path, "must be an object"))
            continue
        for key in ("question_id", "result_id", "rationale", "meaning", "unit"):
            if not _nonempty(item.get(key)):
                findings.append(_finding("error", question, f"{path}.{key}", "required"))

    data_contract = contract.get("data_contract", {})
    if not isinstance(data_contract, dict):
        findings.append(_finding("error", question, "data_contract", "must be an object"))
        data_contract = {}
    datasets = data_contract.get("datasets", [])
    if not isinstance(datasets, list):
        findings.append(_finding("error", question, "data_contract.datasets", "must be a list"))
        datasets = []
    if not datasets and not _nonempty(data_contract.get("no_data_reason")):
        findings.append(_finding("error", question, "data_contract", "declare datasets or a no-data reason"))
    for index, dataset in enumerate(datasets):
        findings.extend(_audit_dataset(workspace, question, dataset, phase, index))

    model_plan = contract.get("model_plan", {})
    if not isinstance(model_plan, dict):
        findings.append(_finding("error", question, "model_plan", "must be an object"))
        model_plan = {}
    candidates = model_plan.get("candidates", [])
    if not isinstance(candidates, list) or not candidates:
        findings.append(_finding("error", question, "model_plan.candidates", "at least one real candidate is required"))
        candidates = []
    if len(candidates) == 1 and not _nonempty(model_plan.get("single_candidate_justification")):
        findings.append(_finding("error", question, "model_plan.single_candidate_justification", "required when only one candidate remains"))
    candidate_ids: set[str] = set()
    for index, item in enumerate(candidates):
        path = f"model_plan.candidates[{index}]"
        if not isinstance(item, dict):
            findings.append(_finding("error", question, path, "must be an object"))
            continue
        for key in ("id", "name", "family", "role", "fit_evidence", "assumptions", "data_requirements", "implementation", "validation", "risks"):
            if not _nonempty(item.get(key)):
                findings.append(_finding("error", question, f"{path}.{key}", "required"))
        if item.get("role") not in {"baseline", "mainstream", "advanced"}:
            findings.append(_finding("error", question, f"{path}.role", "must be baseline, mainstream, or advanced"))
        if "references" not in item or not isinstance(item.get("references"), list):
            findings.append(_finding("error", question, f"{path}.references", "must be a list; [] means no external source was required"))
        candidate_id = str(item.get("id") or "")
        if candidate_id in candidate_ids:
            findings.append(_finding("error", question, f"{path}.id", "duplicate candidate id"))
        candidate_ids.add(candidate_id)

    recommended = model_plan.get("recommended_candidate_id")
    if recommended not in candidate_ids:
        findings.append(_finding("error", question, "model_plan.recommended_candidate_id", "must reference a candidate"))
    if not _nonempty(model_plan.get("selection_criteria")):
        findings.append(_finding("error", question, "model_plan.selection_criteria", "required"))
    validation = model_plan.get("validation_plan", {})
    if not isinstance(validation, dict):
        findings.append(_finding("error", question, "model_plan.validation_plan", "must be an object"))
        validation = {}
    for key in ("metrics", "split_or_scenarios", "failure_conditions"):
        if not _nonempty(validation.get(key)):
            findings.append(_finding("error", question, f"model_plan.validation_plan.{key}", "required"))
    baseline = validation.get("baseline_candidate_id")
    if baseline not in candidate_ids:
        findings.append(_finding("error", question, "model_plan.validation_plan.baseline_candidate_id", "must reference a valid baseline candidate"))
    elif not any(item.get("id") == baseline and item.get("role") == "baseline" for item in candidates if isinstance(item, dict)):
        findings.append(_finding("error", question, "model_plan.validation_plan.baseline_candidate_id", "referenced candidate must have role=baseline"))

    figure_plan = contract.get("figure_plan", {})
    if not isinstance(figure_plan, dict):
        findings.append(_finding("error", question, "figure_plan", "must be an object"))
        figure_plan = {}
    no_figure_reason = _nonempty(figure_plan.get("no_figure_reason"))
    if not no_figure_reason:
        for key in ("evidence_questions", "candidate_chart_types", "preliminary_recommendation"):
            if not _nonempty(figure_plan.get(key)):
                findings.append(_finding("error", question, f"figure_plan.{key}", "required before execution unless no figure is justified"))

    invalidation = contract.get("invalidation", {})
    if not isinstance(invalidation, dict) or invalidation.get("status") != "current":
        findings.append(_finding("error", question, "invalidation.status", "contract is invalidated or malformed"))

    if phase in {"execute", "final"} and not _approval_ok(contract, "pre_execution"):
        findings.append(_finding("error", question, "approvals.pre_execution", "team approval must include actor, timestamp, and matching contract digest"))

    if phase == "final":
        observed = data_contract.get("observed_accesses", [])
        declared = {
            str(_resolve(workspace, str(item.get("path")))): item
            for item in datasets
            if isinstance(item, dict) and _nonempty(item.get("path"))
        }
        if datasets and not _nonempty(observed):
            findings.append(_finding("error", question, "data_contract.observed_accesses", "required after execution"))
        if isinstance(observed, list):
            forbidden = {
                str(_resolve(workspace, str(item)))
                for item in dependencies.get("forbidden_inputs", [])
            }
            for index, access in enumerate(observed):
                field = f"data_contract.observed_accesses[{index}]"
                if not isinstance(access, dict):
                    findings.append(_finding("error", question, field, "must be an object"))
                    continue
                for key in ("path", "sha256", "sheet_or_table", "fields", "row_scope", "filters", "preprocessing", "exclusions"):
                    if key not in access or (key not in {"filters", "preprocessing", "exclusions"} and not _nonempty(access[key])):
                        findings.append(_finding("error", question, f"{field}.{key}", "required"))
                if not _nonempty(access.get("path")):
                    continue
                path = str(_resolve(workspace, str(access["path"])))
                if path in forbidden:
                    findings.append(_finding("error", question, "dependencies.forbidden_inputs", f"forbidden input observed: {path}"))
                approved = declared.get(path)
                if approved is None:
                    findings.append(_finding("error", question, field, f"undeclared input: {path}"))
                    continue
                if str(access.get("sha256") or "").lower() != str(approved.get("sha256") or "").lower():
                    findings.append(_finding("error", question, f"{field}.sha256", "does not match approved dataset hash"))
                if access.get("sheet_or_table") != approved.get("sheet_or_table"):
                    findings.append(_finding("error", question, f"{field}.sheet_or_table", "does not match approved table/sheet"))
                declared_fields = {
                    str(item.get("name"))
                    for item in approved.get("fields", [])
                    if isinstance(item, dict) and _nonempty(item.get("name"))
                }
                observed_fields = access.get("fields", [])
                if not isinstance(observed_fields, list) or not observed_fields:
                    findings.append(_finding("error", question, f"{field}.fields", "must list fields actually read"))
                else:
                    undeclared_fields = sorted(set(map(str, observed_fields)) - declared_fields)
                    for name in undeclared_fields:
                        findings.append(_finding("error", question, f"{field}.fields", f"undeclared field: {name}"))
                for key in ("row_scope", "filters", "preprocessing", "exclusions"):
                    if access.get(key) != approved.get(key):
                        findings.append(_finding("error", question, f"{field}.{key}", "does not match approved data contract"))
        else:
            findings.append(_finding("error", question, "data_contract.observed_accesses", "must be a list"))

        execution = contract.get("execution", {})
        chosen = execution.get("chosen_model_id") if isinstance(execution, dict) else None
        if chosen not in candidate_ids:
            findings.append(_finding("error", question, "execution.chosen_model_id", "must reference an evaluated candidate"))
        if not isinstance(execution, dict) or execution.get("validation_status") != "passed":
            findings.append(_finding("error", question, "execution.validation_status", "must be passed"))
        for key in ("code_paths", "result_ids"):
            if not isinstance(execution, dict) or not _nonempty(execution.get(key)):
                findings.append(_finding("error", question, f"execution.{key}", "required"))
        declared_upstream = {
            str(item.get("result_id"))
            for item in upstream
            if isinstance(item, dict) and _nonempty(item.get("result_id"))
        }
        observed_upstream = execution.get("observed_upstream_result_ids", []) if isinstance(execution, dict) else []
        if not isinstance(observed_upstream, list):
            findings.append(_finding("error", question, "execution.observed_upstream_result_ids", "must be a list"))
        else:
            undeclared_upstream = sorted(set(map(str, observed_upstream)) - declared_upstream)
            for result_id in undeclared_upstream:
                findings.append(_finding("error", question, "execution.observed_upstream_result_ids", f"undeclared upstream result: {result_id}"))
            if declared_upstream and not observed_upstream:
                findings.append(_finding("error", question, "execution.observed_upstream_result_ids", "declared upstream dependency was not recorded at runtime"))
        if not _approval_ok(contract, "final_model"):
            findings.append(_finding("error", question, "approvals.final_model", "team approval must include actor, timestamp, and matching contract digest"))
        if not _approval_ok(contract, "final_figures"):
            findings.append(_finding("error", question, "approvals.final_figures", "team approval must include actor, timestamp, and matching contract digest"))
        if not no_figure_reason:
            for key in ("final_chart_types", "rationale", "result_ids"):
                if not _nonempty(figure_plan.get(key)):
                    findings.append(_finding("error", question, f"figure_plan.{key}", "required for final figures"))
        if contract.get("status") != "completed":
            findings.append(_finding("error", question, "status", "must be completed at final audit"))

    return findings, contract


def _dependency_findings(contracts: dict[str, dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    graph: dict[str, set[str]] = {question: set() for question in contracts}
    for question, contract in contracts.items():
        upstream = contract.get("dependencies", {}).get("upstream_results", [])
        if not isinstance(upstream, list):
            continue
        for item in upstream:
            if not isinstance(item, dict):
                continue
            parent = str(item.get("question_id") or "")
            if parent not in contracts:
                findings.append(_finding("error", question, "dependencies.upstream_results", f"unknown upstream question: {parent}"))
            else:
                graph[question].add(parent)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            findings.append(_finding("error", node, "dependencies", "dependency cycle detected"))
            return
        if node in visited:
            return
        visiting.add(node)
        for parent in graph[node]:
            visit(parent)
        visiting.remove(node)
        visited.add(node)

    for question in graph:
        visit(question)
    return findings


def audit(workspace: Path, phase: str, question: str | None = None) -> list[Finding]:
    questions_dir = workspace / "state" / "questions"
    paths = sorted(questions_dir.glob("Q*/question_contract.json"))
    if question:
        paths = [path for path in paths if path.parent.name == question]
    if not paths:
        return [_finding("error", question or "ALL", "contracts", f"no question contracts found under {questions_dir}")]

    findings: list[Finding] = []
    contracts: dict[str, dict[str, Any]] = {}
    for path in paths:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(_finding("error", path.parent.name, "json", str(exc)))
            continue
        contract_findings, contract = _audit_contract(workspace, value, phase, path)
        findings.extend(contract_findings)
        if contract is not None:
            question_id = str(contract.get("question_id") or path.parent.name)
            if question_id in contracts:
                findings.append(_finding("error", question_id, "question_id", "duplicate question contract"))
            contracts[question_id] = contract

    if not question:
        findings.extend(_dependency_findings(contracts))
        decision_path = workspace / "state" / "decision_log.json"
        if decision_path.is_file():
            try:
                state = json.loads(decision_path.read_text(encoding="utf-8"))
                expected = state.get("stages", {}).get("5", {}).get("qi_count")
                if isinstance(expected, int) and not isinstance(expected, bool) and expected != len(contracts):
                    findings.append(_finding("error", "ALL", "qi_count", f"decision log expects {expected}, found {len(contracts)} contracts"))
            except (OSError, json.JSONDecodeError) as exc:
                findings.append(_finding("error", "ALL", "decision_log", str(exc)))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--phase", choices=("plan", "execute", "final"), default="plan")
    parser.add_argument("--question", type=str)
    parser.add_argument(
        "--digest-for",
        choices=("pre_execution", "final_model", "final_figures"),
        help="print the digest that binds one approval; requires --question",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    if args.digest_for:
        if not args.question:
            parser.error("--digest-for requires --question")
        path = workspace / "state" / "questions" / args.question / "question_contract.json"
        try:
            contract = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(str(exc))
        if not isinstance(contract, dict):
            parser.error("question contract root must be an object")
        print(contract_digest(contract, args.digest_for))
        return 0
    findings = audit(workspace, args.phase, args.question)
    if args.as_json:
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    elif findings:
        for item in findings:
            print(f"[{item.severity.upper()}] {item.question} {item.field}: {item.message}")
    else:
        print(f"Question-contract audit passed: phase={args.phase}")
    return 1 if any(item.severity == "error" for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
