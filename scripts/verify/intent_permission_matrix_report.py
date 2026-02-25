#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER_DIRS = [
    ROOT / "addons" / "smart_core" / "handlers",
    ROOT / "addons" / "smart_construction_core" / "handlers",
]
MAKEFILE = ROOT / "Makefile"
TEST_DIRS = [
    ROOT / "addons" / "smart_core" / "tests",
    ROOT / "addons" / "smart_construction_core" / "tests",
    ROOT / "scripts" / "verify",
]
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "intent_permission_matrix.md"
ARTIFACT_JSON = ROOT / "artifacts" / "backend" / "intent_permission_matrix.json"
WRITE_HINT_PATTERN = re.compile(
    r"(create|write|unlink|delete|batch|execute|upload|cancel|approve|reject|submit|done|import|rollback|pin|set)",
    re.IGNORECASE,
)


def _literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


@dataclass
class IntentRow:
    intent: str
    source: str
    is_write: bool
    required_groups: list[str]
    acl_mode: str
    smoke: bool = False
    has_test: bool = False


def _class_attr_literal(cls: ast.ClassDef, attr_name: str):
    for stmt in cls.body:
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if isinstance(target, ast.Name) and target.id == attr_name:
                return _literal(stmt.value)
    return None


def _resolve_attr(class_map: dict[str, ast.ClassDef], cls: ast.ClassDef, attr_name: str, visited: set[str] | None = None):
    visited = visited or set()
    if cls.name in visited:
        return None
    visited.add(cls.name)
    value = _class_attr_literal(cls, attr_name)
    if value is not None:
        return value
    for base in cls.bases:
        if isinstance(base, ast.Name):
            base_cls = class_map.get(base.id)
            if base_cls is not None:
                inherited = _resolve_attr(class_map, base_cls, attr_name, visited=visited)
                if inherited is not None:
                    return inherited
    return None


def _collect_rows() -> list[IntentRow]:
    rows: list[IntentRow] = []
    for handler_dir in HANDLER_DIRS:
        if not handler_dir.is_dir():
            continue
        for path in sorted(handler_dir.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
            class_map = {cls.name: cls for cls in classes}
            for cls in classes:
                intent = _resolve_attr(class_map, cls, "INTENT_TYPE")
                if not isinstance(intent, str) or not intent.strip():
                    continue
                required = _resolve_attr(class_map, cls, "REQUIRED_GROUPS") or []
                required_groups = [str(x).strip() for x in required if str(x).strip()]
                acl_mode = str(_resolve_attr(class_map, cls, "ACL_MODE") or "").strip()
                non_idempotent = bool(str(_resolve_attr(class_map, cls, "NON_IDEMPOTENT_ALLOWED") or "").strip())
                is_write = bool(WRITE_HINT_PATTERN.search(intent)) or non_idempotent
                rows.append(
                    IntentRow(
                        intent=intent.strip(),
                        source=str(path.relative_to(ROOT)),
                        is_write=is_write,
                        required_groups=required_groups,
                        acl_mode=acl_mode,
                    )
                )
    # de-dup by intent
    dedup: dict[str, IntentRow] = {}
    for row in rows:
        dedup[row.intent] = row
    return [dedup[k] for k in sorted(dedup.keys())]


def _collect_make_text() -> str:
    return MAKEFILE.read_text(encoding="utf-8") if MAKEFILE.is_file() else ""


def _collect_test_text() -> str:
    blobs = []
    for test_dir in TEST_DIRS:
        if not test_dir.is_dir():
            continue
        for path in test_dir.rglob("*.py"):
            try:
                blobs.append(path.read_text(encoding="utf-8"))
            except Exception:
                continue
    return "\n".join(blobs)


def _render(rows: list[IntentRow]) -> str:
    write_rows = [r for r in rows if r.is_write]
    lines = [
        "# Intent Permission Matrix",
        "",
        f"- intent_count: {len(rows)}",
        f"- write_intent_count: {len(write_rows)}",
        "",
        "| intent | is_write | required_groups | ACL_MODE | smoke | test | source |",
        "|---|---:|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {intent} | {is_write} | {groups} | {acl} | {smoke} | {test} | {src} |".format(
                intent=row.intent,
                is_write="Y" if row.is_write else "N",
                groups=", ".join(row.required_groups) if row.required_groups else "-",
                acl=row.acl_mode or "-",
                smoke="Y" if row.smoke else "N",
                test="Y" if row.has_test else "N",
                src=row.source,
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    rows = _collect_rows()
    make_text = _collect_make_text()
    test_text = _collect_test_text()
    for row in rows:
        token = row.intent.replace(".", "_")
        row.smoke = row.intent in make_text or token in make_text
        row.has_test = row.intent in test_text

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(_render(rows), encoding="utf-8")
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(
        json.dumps(
            {
                "summary": {
                    "intent_count": len(rows),
                    "write_intent_count": len([r for r in rows if r.is_write]),
                },
                "rows": [
                    {
                        "intent": r.intent,
                        "source": r.source,
                        "is_write": bool(r.is_write),
                        "required_groups": list(r.required_groups or []),
                        "acl_mode": str(r.acl_mode or ""),
                        "smoke": bool(r.smoke),
                        "has_test": bool(r.has_test),
                    }
                    for r in rows
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(str(REPORT_MD))
    print(str(ARTIFACT_JSON))
    print("[intent_permission_matrix_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
