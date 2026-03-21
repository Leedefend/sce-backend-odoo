#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_FILE = ROOT / "addons/smart_core/utils/contract_governance.py"

REPORT_JSON = ROOT / "artifacts/backend/contract_governance_determinism_report.json"
REPORT_MD = ROOT / "docs/ops/audit/contract_governance_determinism_report.md"
ITERATIONS = 20


def _load_apply_contract_governance():
    spec = importlib.util.spec_from_file_location("contract_governance_guard_module", GOVERNANCE_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {GOVERNANCE_FILE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, "apply_contract_governance", None)
    if not callable(fn):
        raise RuntimeError("apply_contract_governance not found in contract_governance.py")
    return fn


def _stable_hash(payload: dict) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sample_payload() -> dict:
    return {
        "head": {
            "model": "project.project",
            "view_type": "form",
            "permissions": {"read": True, "write": True, "create": True},
        },
        "permissions": {
            "effective": {"rights": {"read": True, "write": True, "create": True}},
        },
        "fields": {
            "name": {"required": True, "readonly": False, "string": "名称", "type": "char"},
            "manager_id": {"required": False, "readonly": False, "string": "项目经理", "type": "many2one"},
            "budget_total": {"required": False, "readonly": False, "string": "预算", "type": "monetary"},
            "lifecycle_state": {
                "required": False,
                "readonly": False,
                "string": "项目状态",
                "type": "selection",
                "selection": [
                    ["draft", "草稿"],
                    ["in_progress", "在建"],
                    ["done", "竣工"],
                ],
            },
        },
        "views": {
            "form": {
                "layout": [
                    {"type": "field", "name": "name"},
                    {"type": "field", "name": "manager_id"},
                    {"type": "field", "name": "budget_total"},
                ]
            }
        },
        "buttons": [
            {
                "key": "submit",
                "label": "提交立项",
                "requiredCapabilities": ["project.lifecycle.transition"],
                "required_capabilities": ["project.lifecycle.transition"],
                "groupsXmlids": ["smart_core.group_smart_core_data_operator"],
                "required_roles": ["pm"],
                "level": "header",
            },
            {
                "key": "action_view_tasks",
                "label": "查看任务",
                "level": "smart",
            },
        ],
        "validator": {
            "record_rules": {
                "sql_checks": [
                    {
                        "name": "project_date_greater",
                        "message": "start must be before end",
                        "definition": "check(date >= date_start)",
                    }
                ]
            }
        },
        "scenes": [
            {
                "key": "projects.list",
                "name": "项目列表",
                "target": {"route": "/projects", "actionId": 1001, "menuId": 2010},
                "access": {"allowed": True, "requiredCapabilities": ["project.read"]},
            }
        ],
        "capabilities": [
            {
                "key": "project.read",
                "name": "项目查看",
                "status": "ga",
                "defaultPayload": {"route": "/projects", "action_xmlid": "should_strip"},
            }
        ],
    }


def _run_mode(mode: str) -> tuple[bool, list[str], str]:
    apply_contract_governance = _load_apply_contract_governance()
    hashes: list[str] = []
    for _ in range(ITERATIONS):
        payload = copy.deepcopy(_sample_payload())
        governed = apply_contract_governance(payload, mode)
        hashes.append(_stable_hash(governed))
    first = hashes[0] if hashes else ""
    stable = all(item == first for item in hashes)
    return stable, hashes, first


def main() -> int:
    user_ok, user_hashes, user_first = _run_mode("user")
    hud_ok, hud_hashes, hud_first = _run_mode("hud")
    ok = user_ok and hud_ok

    report = {
        "ok": ok,
        "iterations": ITERATIONS,
        "modes": {
            "user": {
                "stable": user_ok,
                "first_hash": user_first,
                "unique_hashes": sorted(set(user_hashes)),
                "unique_count": len(set(user_hashes)),
            },
            "hud": {
                "stable": hud_ok,
                "first_hash": hud_first,
                "unique_hashes": sorted(set(hud_hashes)),
                "unique_count": len(set(hud_hashes)),
            },
        },
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Contract Governance Determinism Report",
                "",
                f"- ok: `{ok}`",
                f"- iterations: `{ITERATIONS}`",
                f"- user.stable: `{user_ok}`",
                f"- user.unique_count: `{len(set(user_hashes))}`",
                f"- hud.stable: `{hud_ok}`",
                f"- hud.unique_count: `{len(set(hud_hashes))}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if not ok:
        print("[contract_governance_determinism_guard] FAIL")
        return 1
    print("[contract_governance_determinism_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
