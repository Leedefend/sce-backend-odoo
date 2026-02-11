#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import json
import re


@dataclass
class IntentRow:
    intent: str
    module: str
    cls: str
    aliases: list[str]
    has_idempotency_window: bool
    test_literal_refs: int
    test_refs: int


HANDLER_DIRS = [
    Path("addons/smart_core/handlers"),
    Path("addons/smart_construction_core/handlers"),
]

TEST_DIRS = [
    Path("addons/smart_core/tests"),
    Path("addons/smart_construction_core/tests"),
]


def _literal_list(node: ast.AST) -> list[str]:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    out: list[str] = []
    for elt in node.elts:
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
            out.append(elt.value.strip())
    return [s for s in out if s]


def _class_assign_map(node: ast.ClassDef) -> dict[str, ast.AST]:
    out: dict[str, ast.AST] = {}
    for item in node.body:
        if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
            out[item.targets[0].id] = item.value
    return out


def collect_intents(repo_root: Path) -> list[IntentRow]:
    rows: list[IntentRow] = []
    for rel_dir in HANDLER_DIRS:
        abs_dir = repo_root / rel_dir
        if not abs_dir.exists():
            continue
        for py_file in sorted(abs_dir.glob("*.py")):
            src = py_file.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=str(py_file))
            module = str(py_file.relative_to(repo_root))
            for node in tree.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                assigns = _class_assign_map(node)
                intent_node = assigns.get("INTENT_TYPE")
                if not (isinstance(intent_node, ast.Constant) and isinstance(intent_node.value, str)):
                    continue
                intent = intent_node.value.strip()
                if not intent:
                    continue
                aliases = _literal_list(assigns.get("ALIASES", ast.List(elts=[])))
                has_idempotency_window = "IDEMPOTENCY_WINDOW_SECONDS" in assigns
                rows.append(
                    IntentRow(
                        intent=intent,
                        module=module,
                        cls=node.name,
                        aliases=aliases,
                        has_idempotency_window=has_idempotency_window,
                        test_literal_refs=0,
                        test_refs=0,
                    )
                )
    return rows


def count_test_refs(repo_root: Path, intents: list[IntentRow]) -> None:
    test_files: list[Path] = []
    for rel_dir in TEST_DIRS:
        abs_dir = repo_root / rel_dir
        if abs_dir.exists():
            test_files.extend(sorted(abs_dir.rglob("test_*.py")))
    blobs: list[tuple[Path, str]] = []
    for tf in test_files:
        try:
            blobs.append((tf, tf.read_text(encoding="utf-8")))
        except Exception:
            continue
    combined = "\n".join(text for _, text in blobs)
    for row in intents:
        row.test_literal_refs = len(re.findall(re.escape(row.intent), combined))

        module_stem = Path(row.module).stem
        signals = [row.intent, row.cls, module_stem, *row.aliases]
        seen_files: set[str] = set()
        for path, text in blobs:
            for signal in signals:
                signal_text = str(signal or "").strip()
                if not signal_text:
                    continue
                if re.search(re.escape(signal_text), text):
                    seen_files.add(str(path))
                    break
        row.test_refs = len(seen_files)


def render_markdown(rows: list[IntentRow]) -> str:
    lines = [
        "# Intent Surface Report",
        "",
        "| intent | module | class | aliases | idempotency_window | test_literal_refs | test_refs |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for row in sorted(rows, key=lambda r: (r.intent, r.module, r.cls)):
            aliases = ", ".join(row.aliases) if row.aliases else "-"
            lines.append(
                f"| `{row.intent}` | `{row.module}` | `{row.cls}` | {aliases} | "
                f"{'yes' if row.has_idempotency_window else 'no'} | {row.test_literal_refs} | {row.test_refs} |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate intent surface report.")
    parser.add_argument(
        "--output-md",
        default="docs/ops/audit/intent_surface_report.md",
        help="Markdown output path",
    )
    parser.add_argument(
        "--output-json",
        default="artifacts/intent_surface_report.json",
        help="JSON output path",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    rows = collect_intents(repo_root)
    count_test_refs(repo_root, rows)

    out_md = repo_root / args.output_md
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(rows), encoding="utf-8")

    out_json = repo_root / args.output_json
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps(
            [
                {
                    "intent": r.intent,
                    "module": r.module,
                    "class": r.cls,
                    "aliases": r.aliases,
                    "has_idempotency_window": r.has_idempotency_window,
                    "test_literal_refs": r.test_literal_refs,
                    "test_refs": r.test_refs,
                }
                for r in sorted(rows, key=lambda x: (x.intent, x.module, x.cls))
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(str(out_md))
    print(str(out_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
