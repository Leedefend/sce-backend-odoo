#!/usr/bin/env python3
"""Guard side-effect intent governance policy (idempotency or explicit waiver)."""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDLER_DIRS = [
    ROOT / "addons/smart_core/handlers",
    ROOT / "addons/smart_construction_core/handlers",
]
POLICY_PATH = ROOT / "scripts/verify/baselines/side_effect_intents_policy.json"
PLACEHOLDER_RE = re.compile(r"^(todo|tbd|n/?a|none|-)$", re.IGNORECASE)


@dataclass
class IntentClassMeta:
    intent: str
    module: str
    class_name: str
    has_idem_window: bool
    waiver_reason: str


def _class_assign_map(node: ast.ClassDef) -> dict[str, ast.AST]:
    out: dict[str, ast.AST] = {}
    for item in node.body:
        if isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
            out[item.targets[0].id] = item.value
    return out


def _const_str(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.strip()
    return ""


def _collect_intents() -> dict[str, IntentClassMeta]:
    table: dict[str, IntentClassMeta] = {}
    for handler_dir in HANDLER_DIRS:
        if not handler_dir.exists():
            continue
        for py_file in sorted(handler_dir.glob("*.py")):
            src = py_file.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=str(py_file))
            module = py_file.relative_to(ROOT).as_posix()
            for node in tree.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                assigns = _class_assign_map(node)
                intent = _const_str(assigns.get("INTENT_TYPE"))
                if not intent:
                    continue
                meta = IntentClassMeta(
                    intent=intent,
                    module=module,
                    class_name=node.name,
                    has_idem_window=("IDEMPOTENCY_WINDOW_SECONDS" in assigns),
                    waiver_reason=_const_str(assigns.get("NON_IDEMPOTENT_ALLOWED")),
                )
                table[intent] = meta
    return table


def _load_policy() -> list[dict[str, str]]:
    if not POLICY_PATH.exists():
        raise FileNotFoundError(POLICY_PATH.as_posix())
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    rows = payload.get("intents") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("policy format invalid: intents must be list")
    out: list[dict[str, str]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        intent = str(item.get("intent") or "").strip()
        req = str(item.get("requirement") or "").strip()
        if intent and req:
            out.append({"intent": intent, "requirement": req})
    return out


def _valid_waiver(reason: str) -> bool:
    text = str(reason or "").strip()
    if len(text) < 8:
        return False
    if PLACEHOLDER_RE.match(text):
        return False
    return True


def main() -> int:
    try:
        policy = _load_policy()
    except (FileNotFoundError, ValueError) as exc:
        print("[FAIL] side-effect intent policy guard")
        print(f"- {exc}")
        return 1

    intents = _collect_intents()
    errors: list[str] = []

    for item in policy:
        intent = item["intent"]
        requirement = item["requirement"]
        meta = intents.get(intent)
        if not meta:
            errors.append(f"policy intent not found in handlers: {intent}")
            continue

        if requirement == "idempotency_window":
            if not meta.has_idem_window:
                errors.append(f"{intent}: missing IDEMPOTENCY_WINDOW_SECONDS ({meta.module}:{meta.class_name})")
        elif requirement == "explicit_waiver":
            if not _valid_waiver(meta.waiver_reason):
                errors.append(
                    f"{intent}: missing/invalid NON_IDEMPOTENT_ALLOWED ({meta.module}:{meta.class_name})"
                )
        else:
            errors.append(f"{intent}: unsupported requirement '{requirement}'")

    if errors:
        print("[FAIL] side-effect intent policy guard")
        for err in errors:
            print(f"- {err}")
        return 1

    print("[OK] side-effect intent policy guard")
    print(f"- policy_items: {len(policy)}")
    print(f"- intents_scanned: {len(intents)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
