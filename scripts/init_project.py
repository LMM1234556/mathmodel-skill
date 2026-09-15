#!/usr/bin/env python3
"""Initialize a Huawei Cup modeling workspace after the target year is confirmed."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parent.parent
DECISION_TEMPLATE = SKILL_ROOT / "templates" / "shared" / "decision_log.json"
RULES_TEMPLATE = SKILL_ROOT / "templates" / "shared" / "rules_snapshot.json"
COMPETITIONS = ("huawei",)
WORKSPACE_DIRS = ("state", "results", "figures", "paper_workspace")


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"模板根节点必须是 object: {path}")
    return value


def _validate_inputs(competition: str, year: int) -> None:
    if competition not in COMPETITIONS:
        raise ValueError(f"不支持的 competition: {competition!r}")
    if not isinstance(year, int) or isinstance(year, bool) or not 2000 <= year <= 2200:
        raise ValueError("year 必须是 2000–2200 之间的四位整数")


def initialize_project(
    workspace: Path,
    competition: str,
    year: int,
    started_at: str | None = None,
) -> tuple[Path, Path]:
    """Create the canonical state files without overwriting an existing project."""

    _validate_inputs(competition, year)
    workspace = workspace.resolve()
    decision_path = workspace / "state" / "decision_log.json"
    rules_path = workspace / "state" / "rules_snapshot.json"
    existing = [path for path in (decision_path, rules_path) if path.exists()]
    if existing:
        names = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            f"检测到已有状态，未覆盖: {names}。请读取并恢复该项目；不要重新初始化。"
        )

    timestamp = started_at or datetime.now().astimezone().isoformat(timespec="seconds")
    decision = _load_object(DECISION_TEMPLATE)
    rules = _load_object(RULES_TEMPLATE)

    decision["competition"] = competition
    decision["started_at"] = timestamp
    decision["problem_meta"]["year"] = year
    decision["compliance"]["ruleset"]["competition_year"] = year
    decision["events"]["log"].append(
        {
            "type": "project_initialized",
            "ts": timestamp,
            "competition": competition,
            "competition_year": year,
        }
    )
    rules["competition"] = competition
    rules["competition_year"] = year

    payloads = {
        decision_path: json.dumps(decision, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        rules_path: json.dumps(rules, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
    }
    for directory in WORKSPACE_DIRS:
        (workspace / directory).mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    try:
        for path, payload in payloads.items():
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
            created.append(path)
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return decision_path, rules_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument(
        "--competition",
        choices=COMPETITIONS,
        required=True,
        help="Current release supports only huawei; the explicit value is persisted for auditability.",
    )
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    try:
        decision_path, rules_path = initialize_project(
            args.workspace, args.competition, args.year
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] 初始化失败: {exc}")
        return 1

    result = {
        "competition": args.competition,
        "competition_year": args.year,
        "decision_log": str(decision_path),
        "rules_snapshot": str(rules_path),
        "next_gate": "verify_current_rules",
    }
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"[OK] 已初始化 {args.competition} {args.year} 项目")
        print(f"decision log: {decision_path}")
        print(f"rules snapshot: {rules_path}")
        print("next gate: 核验当届官方规则")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
