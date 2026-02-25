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
VERIFY_DIR = ROOT / "scripts" / "verify"
EXPORT_JSON = ROOT / "docs" / "contract" / "exports" / "intent_catalog_enriched.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "intent_capability_matrix.md"
TEST_DIRS = [
    ROOT / "addons" / "smart_core" / "tests",
    ROOT / "addons" / "smart_construction_core" / "tests",
    ROOT / "scripts" / "verify",
]

WRITE_HINT_PATTERN = re.compile(
    r"(create|write|unlink|delete|batch|execute|upload|cancel|approve|reject|submit|done|import|rollback|pin|set)",
    re.IGNORECASE,
)
ORM_CALL_PATTERN = re.compile(
    r"\.(search|browse|read|create|write|unlink|search_count|check_access_rights|check_access_rule)\(",
    re.IGNORECASE,
)
SUDO_PATTERN = re.compile(r"\.sudo\(")


@dataclass
class HandlerIntent:
    intent_type: str
    file_path: Path
    class_name: str
    required_groups: list[str]
    etag_enabled: bool
    non_idempotent_allowed: bool
    source: str
    is_write_operation: bool
    acl_mode: str
    layer: str
    orm_used: bool
    may_trigger_sudo: bool
    has_test_file: bool
    has_smoke_make_target: bool
    smoke_make_targets: list[str]


def _literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _find_handlers(path: Path) -> list[HandlerIntent]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    out: list[HandlerIntent] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        intent_type = ""
        required_groups: list[str] = []
        etag_enabled = False
        non_idempotent_allowed = False
        acl_mode = ""
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign):
                continue
            for target in stmt.targets:
                if not isinstance(target, ast.Name):
                    continue
                name = target.id
                value = _literal(stmt.value)
                if name == "INTENT_TYPE" and isinstance(value, str):
                    intent_type = value.strip()
                elif name == "REQUIRED_GROUPS" and isinstance(value, list):
                    required_groups = [str(x).strip() for x in value if str(x).strip()]
                elif name == "ETAG_ENABLED":
                    etag_enabled = bool(value)
                elif name == "NON_IDEMPOTENT_ALLOWED":
                    non_idempotent_allowed = bool(str(value or "").strip())
                elif name == "ACL_MODE" and isinstance(value, str):
                    acl_mode = value.strip()
        if not intent_type:
            continue
        is_write = bool(WRITE_HINT_PATTERN.search(intent_type)) or non_idempotent_allowed
        layer = _layer_for_intent(intent_type)
        out.append(
            HandlerIntent(
                intent_type=intent_type,
                file_path=path,
                class_name=node.name,
                required_groups=required_groups,
                etag_enabled=etag_enabled,
                non_idempotent_allowed=non_idempotent_allowed,
                source=str(path.relative_to(ROOT)),
                is_write_operation=is_write,
                acl_mode=acl_mode,
                layer=layer,
                orm_used=bool(ORM_CALL_PATTERN.search(text)),
                may_trigger_sudo=bool(SUDO_PATTERN.search(text)),
                has_test_file=False,
                has_smoke_make_target=False,
                smoke_make_targets=[],
            )
        )
    return out


def _layer_for_intent(intent_type: str) -> str:
    low = str(intent_type or "").strip().lower()
    if (
        low in {"system.init", "ui.contract", "api.data", "execute_button", "permission.check"}
        or low.startswith("file.")
        or low.startswith("api.data.")
    ):
        return "core"
    if low.startswith("scene.governance.") or low.startswith("scene.package."):
        return "governance"
    return "domain"


def _collect_make_targets() -> dict[str, str]:
    if not MAKEFILE.exists():
        return {}
    targets: dict[str, str] = {}
    current = ""
    lines: list[str] = []
    for raw in MAKEFILE.read_text(encoding="utf-8").splitlines():
        if raw and not raw.startswith("\t") and ":" in raw and not raw.lstrip().startswith("#"):
            if current:
                targets[current] = "\n".join(lines)
            current = raw.split(":", 1)[0].strip()
            lines = []
            continue
        if current and raw.startswith("\t"):
            lines.append(raw.strip())
    if current:
        targets[current] = "\n".join(lines)
    return targets


def _script_files() -> list[Path]:
    if not VERIFY_DIR.is_dir():
        return []
    return [p for p in VERIFY_DIR.glob("*") if p.is_file() and p.suffix in {".py", ".js", ".sh"}]


def _test_files_with_content() -> list[tuple[Path, str]]:
    out: list[tuple[Path, str]] = []
    for test_dir in TEST_DIRS:
        if not test_dir.is_dir():
            continue
        for path in test_dir.rglob("*.py"):
            try:
                out.append((path, path.read_text(encoding="utf-8")))
            except Exception:
                continue
    return out


def _resolve_intent_tests(
    intent: HandlerIntent,
    make_targets: dict[str, str],
    verify_scripts: list[Path],
    test_files: list[tuple[Path, str]],
) -> None:
    intent_token = intent.intent_type
    intent_token_snake = intent_token.replace(".", "_")
    handler_stem = intent.file_path.stem

    test_hits = []
    for path, content in test_files:
        if intent_token in content or handler_stem in content:
            test_hits.append(path)
    intent.has_test_file = bool(test_hits)

    smoke_targets: list[str] = []
    verify_script_names = [p.name for p in verify_scripts]
    for target, body in make_targets.items():
        if not target.startswith("verify."):
            continue
        hay = f"{target}\n{body}"
        if intent_token in hay or intent_token_snake in hay or handler_stem in hay:
            smoke_targets.append(target)
            continue
        for script_name in verify_script_names:
            if script_name not in hay:
                continue
            if intent_token_snake in script_name or handler_stem in script_name:
                smoke_targets.append(target)
                break
    dedup = sorted(set(smoke_targets))
    intent.smoke_make_targets = dedup
    intent.has_smoke_make_target = bool(dedup)


def _render_markdown(rows: list[HandlerIntent]) -> str:
    missing_tests = [r for r in rows if not r.has_test_file]
    missing_smoke = [r for r in rows if not r.has_smoke_make_target]
    write_without_groups = [r for r in rows if r.is_write_operation and not r.required_groups]
    write_without_acl_hint = [
        r
        for r in rows
        if r.is_write_operation
        and "check_access_rights(" not in r.file_path.read_text(encoding="utf-8")
        and "check_access_rule(" not in r.file_path.read_text(encoding="utf-8")
    ]

    lines = [
        "# Intent Capability Matrix Audit",
        "",
        f"- intent_count: {len(rows)}",
        f"- missing_test_count: {len(missing_tests)}",
        f"- missing_smoke_target_count: {len(missing_smoke)}",
        f"- write_without_required_groups_count: {len(write_without_groups)}",
        f"- write_without_acl_hint_count: {len(write_without_acl_hint)}",
        "",
        "## Matrix",
        "",
        "| intent_type | layer | required_groups | acl_mode | etag_enabled | has_test | has_smoke_target | is_write | orm_used | may_sudo | source |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in sorted(rows, key=lambda x: x.intent_type):
        lines.append(
            "| {intent} | {layer} | {groups} | {acl_mode} | {etag} | {test} | {smoke} | {write} | {orm} | {sudo} | {src} |".format(
                intent=row.intent_type,
                layer=row.layer,
                groups=len(row.required_groups),
                acl_mode=row.acl_mode or "-",
                etag="Y" if row.etag_enabled else "N",
                test="Y" if row.has_test_file else "N",
                smoke="Y" if row.has_smoke_make_target else "N",
                write="Y" if row.is_write_operation else "N",
                orm="Y" if row.orm_used else "N",
                sudo="Y" if row.may_trigger_sudo else "N",
                src=row.source,
            )
        )

    def _append_section(title: str, values: list[HandlerIntent]) -> None:
        lines.extend(["", f"## {title}", ""])
        if not values:
            lines.append("- none")
            return
        for item in sorted(values, key=lambda x: x.intent_type):
            lines.append(f"- `{item.intent_type}` ({item.source})")

    _append_section("Missing Test Coverage", missing_tests)
    _append_section("Missing Smoke Make Targets", missing_smoke)
    _append_section("Write Intents Without REQUIRED_GROUPS", write_without_groups)
    _append_section("Write Intents Without ACL Guard Hints", write_without_acl_hint)
    return "\n".join(lines) + "\n"


def main() -> int:
    rows: list[HandlerIntent] = []
    for handler_dir in HANDLER_DIRS:
        if not handler_dir.is_dir():
            continue
        for path in sorted(handler_dir.glob("*.py")):
            rows.extend(_find_handlers(path))

    make_targets = _collect_make_targets()
    verify_scripts = _script_files()
    test_files = _test_files_with_content()
    for row in rows:
        _resolve_intent_tests(row, make_targets, verify_scripts, test_files)

    EXPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "intent_capability_matrix_report",
        "intent_count": len(rows),
        "intents": [
            {
                "intent_type": r.intent_type,
                "class_name": r.class_name,
                "required_groups": r.required_groups,
                "etag_enabled": r.etag_enabled,
                "has_test_file": r.has_test_file,
                "has_smoke_make_target": r.has_smoke_make_target,
                "smoke_make_targets": r.smoke_make_targets,
                "is_write_operation": r.is_write_operation,
                "is_write": r.is_write_operation,
                "acl_mode": r.acl_mode,
                "layer": r.layer,
                "orm_used": r.orm_used,
                "may_trigger_sudo": r.may_trigger_sudo,
                "source": r.source,
            }
            for r in sorted(rows, key=lambda x: x.intent_type)
        ],
    }
    EXPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(_render_markdown(rows), encoding="utf-8")

    print(str(EXPORT_JSON))
    print(str(REPORT_MD))
    print("[intent_capability_matrix_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
