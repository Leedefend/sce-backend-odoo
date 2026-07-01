# -*- coding: utf-8 -*-
"""Fail when runtime UI contracts contain test placeholder markers.

Run with Odoo shell, for example:
  ENV=dev DB_NAME=sc_demo make verify.runtime_contract.test_placeholder.guard
"""

import json
import os


def _env():
    return globals()["env"]


def _text(value):
    return str(value or "").strip()


def _snippet(value):
    text = json.dumps(value if isinstance(value, dict) else {}, ensure_ascii=False, sort_keys=True)
    index = text.find("CODEX_")
    if index < 0:
        return text[:240]
    start = max(0, index - 80)
    end = min(len(text), index + 180)
    return text[start:end]


def main():
    env_obj = _env()
    Contract = env_obj["ui.business.config.contract"].sudo()
    domain = [
        ("active", "=", True),
        "|",
        ("name", "ilike", "codex_view_orch_surface_"),
        ("contract_json", "ilike", "CODEX_"),
    ]
    rows = Contract.search(domain, order="model, action_id, view_type, id")
    violations = []
    for rec in rows:
        violations.append(
            {
                "id": int(rec.id or 0),
                "name": _text(rec.name),
                "model": _text(rec.model),
                "view_type": _text(rec.view_type),
                "action_id": int(rec.action_id.id or 0),
                "status": _text(rec.status),
                "snippet": _snippet(rec.contract_json or {}),
            }
        )

    report = {
        "database": env_obj.cr.dbname,
        "violation_count": len(violations),
        "violations": violations[:50],
    }
    path = os.getenv(
        "RUNTIME_CONTRACT_TEST_PLACEHOLDER_GUARD_PATH",
        "/tmp/runtime_contract_test_placeholder_guard.json",
    ).strip()
    if path:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)

    if violations:
        raise AssertionError(
            "runtime UI contracts contain test placeholders: %s"
            % json.dumps(report, ensure_ascii=False)
        )

    print("[runtime_contract_test_placeholder_guard] PASS %s" % json.dumps(report, ensure_ascii=False))


main()
