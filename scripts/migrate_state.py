#!/usr/bin/env python3
"""Migrate a mathmodel decision log to the current template without data loss."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = SKILL_ROOT / "templates" / "shared" / "decision_log.json"
CURRENT_SCHEMA = "3.3"
SUPPORTED_INPUTS = {"3.1", "3.2", CURRENT_SCHEMA}


def _merge_template(template: object, existing: object) -> object:
    """Preserve existing values while adding missing template keys recursively."""

    if isinstance(template, dict) and isinstance(existing, dict):
        merged = {
            key: _merge_template(value, existing[key])
            if key in existing else value
            for key, value in template.items()
        }
        for key, value in existing.items():
            if key not in merged:
                merged[key] = value
        return merged
    return existing


def _atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False,
        prefix=f".{path.name}.", suffix=".tmp"
    ) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def migrate(path: Path) -> Path | None:
    existing = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(existing, dict):
        raise ValueError("decision_log 根节点必须是 object")
    schema = existing.get("_schema_version")
    if schema not in SUPPORTED_INPUTS:
        raise ValueError(
            f"不支持从 schema {schema!r} 迁移；仅支持 {sorted(SUPPORTED_INPUTS)}"
        )
    if schema == CURRENT_SCHEMA:
        return None

    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    merged = _merge_template(template, existing)
    assert isinstance(merged, dict)
    merged["_schema_version"] = CURRENT_SCHEMA

    backup = path.with_name(f"{path.stem}.v{schema.replace('.', '')}.backup{path.suffix}")
    if backup.exists():
        raise FileExistsError(f"备份已存在，未覆盖: {backup}")
    shutil.copy2(path, backup)
    try:
        _atomic_write(path, merged)
    except Exception:
        shutil.copy2(backup, path)
        raise
    return backup


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "decision_log", nargs="?", default="state/decision_log.json",
        help="Path to decision_log.json (default: state/decision_log.json)",
    )
    args = parser.parse_args()
    path = Path(args.decision_log).resolve()
    if not path.is_file():
        parser.error(f"文件不存在: {path}")
    try:
        backup = migrate(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"迁移失败: {exc}")
        return 1
    if backup is None:
        print(f"无需迁移，已经是 schema {CURRENT_SCHEMA}: {path}")
    else:
        print(f"迁移完成: {path}")
        print(f"原文件备份: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
