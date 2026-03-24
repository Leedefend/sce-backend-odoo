#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "product_scene_contract_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "product_scene_contract_guard.md"
CONTRACT_VERSION = "scene_contract_standard_v1"
EXPECTED_DELIVERY = {
    "projects.intake": {"product_key": "fr1", "capability": "delivery.fr1.project_intake"},
    "project.management": {"product_key": "fr2", "capability": "delivery.fr2.project_flow"},
    "cost": {"product_key": "fr3", "capability": "delivery.fr3.cost_tracking"},
    "payment": {"product_key": "fr4", "capability": "delivery.fr4.payment_tracking"},
    "settlement": {"product_key": "fr5", "capability": "delivery.fr5.settlement_summary"},
    "my_work.workspace": {"product_key": "my_work", "capability": "delivery.my_work.workspace"},
}
EXPECTED_RUNTIME = {
    "project.dashboard.enter": {"scene_key": "project.dashboard", "product_key": "fr2", "capability": "delivery.fr2.project_flow"},
    "project.plan_bootstrap.enter": {"scene_key": "project.plan_bootstrap", "product_key": "fr2", "capability": "delivery.fr2.project_flow"},
    "project.execution.enter": {"scene_key": "project.execution", "product_key": "fr2", "capability": "delivery.fr2.project_flow"},
    "cost.tracking.enter": {"scene_key": "cost.tracking", "product_key": "fr3", "capability": "delivery.fr3.cost_tracking"},
    "payment.enter": {"scene_key": "payment", "product_key": "fr4", "capability": "delivery.fr4.payment_tracking"},
    "settlement.enter": {"scene_key": "settlement", "product_key": "fr5", "capability": "delivery.fr5.settlement_summary"},
}


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _post(intent_url: str, token: str | None, intent: str, params: dict | None = None, *, db_name: str = ""):
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    if db_name:
        headers["X-Odoo-DB"] = db_name
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    return status, payload if isinstance(payload, dict) else {}


def _assert_ok(status: int, payload: dict, label: str) -> None:
    if status >= 400 or payload.get("ok") is not True:
        raise RuntimeError(f"{label} failed: status={status} payload={payload}")


def _extract_token(login_payload: dict) -> str:
    data = login_payload.get("data") if isinstance(login_payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if token:
        return token
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    return str(session.get("token") or "").strip()


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _as_list(value):
    return value if isinstance(value, list) else []


def _text(value) -> str:
    return str(value or "").strip()


def _validate_standard_contract(contract: dict, *, scene_key: str, product_key: str, capability: str, label: str) -> dict:
    if not isinstance(contract, dict):
        raise RuntimeError(f"{label}: scene_contract_standard_v1 missing")
    if _text(contract.get("contract_version")) != CONTRACT_VERSION:
        raise RuntimeError(f"{label}: contract_version drift")
    identity = _as_dict(contract.get("identity"))
    target = _as_dict(contract.get("target"))
    state = _as_dict(contract.get("state"))
    page = _as_dict(contract.get("page"))
    actions = _as_dict(contract.get("actions"))
    governance = _as_dict(contract.get("governance"))
    if _text(identity.get("scene_key")) != scene_key:
        raise RuntimeError(f"{label}: identity.scene_key drift")
    if _text(identity.get("product_key")) != product_key:
        raise RuntimeError(f"{label}: identity.product_key drift")
    if _text(identity.get("capability")) != capability:
        raise RuntimeError(f"{label}: identity.capability drift")
    if _text(governance.get("contract_version")) != CONTRACT_VERSION:
        raise RuntimeError(f"{label}: governance.contract_version drift")
    if governance.get("policy_match") is not True:
        raise RuntimeError(f"{label}: governance.policy_match must be true")
    if governance.get("released") is not True:
        raise RuntimeError(f"{label}: governance.released must be true")
    route = _text(target.get("route"))
    if not route:
        raise RuntimeError(f"{label}: target.route missing")
    if "/workbench" in route:
        raise RuntimeError(f"{label}: target.route fallback drift")
    if not isinstance(page.get("zones"), list):
        raise RuntimeError(f"{label}: page.zones must be list")
    if not isinstance(page.get("blocks"), list):
        raise RuntimeError(f"{label}: page.blocks must be list")
    if not _text(state.get("status")):
        raise RuntimeError(f"{label}: state.status missing")
    next_action = _as_dict(actions.get("next_action"))
    return {
        "scene_key": scene_key,
        "product_key": product_key,
        "capability": capability,
        "route": route,
        "status": _text(state.get("status")),
        "block_count": len(_as_list(page.get("blocks"))),
        "zone_count": len(_as_list(page.get("zones"))),
        "next_action_intent": _text(next_action.get("intent")),
        "diagnostics_ref": _text(governance.get("diagnostics_ref")),
    }


def main() -> int:
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "demo_pm").strip()
    password = str(os.getenv("E2E_PASSWORD") or "demo").strip()
    intent_url = f"{base_url}/api/v1/intent"
    if db_name:
        intent_url = f"{intent_url}?db={db_name}"

    report: dict = {"status": "PASS", "db_name": db_name, "login": login, "delivery": {}, "runtime": {}, "page_contract": {}}
    try:
        status, login_resp = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, db_name=db_name)
        _assert_ok(status, login_resp, "login")
        token = _extract_token(login_resp)
        if not token:
            raise RuntimeError("login token missing")

        status, init_resp = _post(
            intent_url,
            token,
            "system.init",
            {"scene": "web", "with_preload": False, "root_xmlid": "smart_construction_core.menu_sc_root"},
            db_name=db_name,
        )
        _assert_ok(status, init_resp, "system.init")
        init_data = _as_dict(init_resp.get("data"))
        delivery = _as_dict(init_data.get("delivery_engine_v1"))
        scenes = _as_list(delivery.get("scenes"))
        index = {_text(row.get("scene_key")): row for row in scenes if isinstance(row, dict)}
        if sorted(index.keys()) != sorted(EXPECTED_DELIVERY.keys()):
            raise RuntimeError(f"delivery scene keys drift: {sorted(index.keys())}")
        for scene_key, expected in EXPECTED_DELIVERY.items():
            row = _as_dict(index.get(scene_key))
            report["delivery"][scene_key] = _validate_standard_contract(
                _as_dict(row.get("scene_contract_standard_v1")),
                scene_key=scene_key,
                product_key=expected["product_key"],
                capability=expected["capability"],
                label=f"delivery:{scene_key}",
            )

        status, initiation_resp = _post(
            intent_url,
            token,
            "project.initiation.enter",
            {
                "name": f"SCENE-CONTRACT-{uuid4().hex[:8]}",
                "description": "scene contract guard",
                "date_start": "2026-03-24",
            },
            db_name=db_name,
        )
        _assert_ok(status, initiation_resp, "project.initiation.enter")
        project_id = int(_as_dict(_as_dict(initiation_resp.get("data")).get("record")).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project.initiation.enter missing record.id")

        for intent, expected in EXPECTED_RUNTIME.items():
            status, resp = _post(intent_url, token, intent, {"project_id": project_id}, db_name=db_name)
            _assert_ok(status, resp, intent)
            data = _as_dict(resp.get("data"))
            contract = _as_dict(data.get("scene_contract_standard_v1"))
            validated = _validate_standard_contract(
                contract,
                scene_key=expected["scene_key"],
                product_key=expected["product_key"],
                capability=expected["capability"],
                label=intent,
            )
            blocks = _as_list(data.get("blocks"))
            if len(_as_list(_as_dict(contract.get("page")).get("blocks"))) != len(blocks):
                raise RuntimeError(f"{intent}: standardized block count drift")
            suggested_action = _as_dict(data.get("suggested_action"))
            next_action = _as_dict(_as_dict(contract.get("actions")).get("next_action"))
            if _text(suggested_action.get("intent")) != _text(next_action.get("intent")):
                raise RuntimeError(f"{intent}: next_action.intent drift")
            report["runtime"][intent] = validated

        status, page_resp = _post(intent_url, token, "page.contract", {"page_key": "my_work"}, db_name=db_name)
        _assert_ok(status, page_resp, "page.contract(my_work)")
        page_contract = _as_dict(_as_dict(page_resp.get("data")).get("page_contract"))
        report["page_contract"]["my_work"] = _validate_standard_contract(
            _as_dict(page_contract.get("scene_contract_standard_v1")),
            scene_key="my_work.workspace",
            product_key="my_work",
            capability="delivery.my_work.workspace",
            label="page.contract:my_work",
        )
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = str(exc)
        _write_json(OUT_JSON, report)
        _write(
            OUT_MD,
            "# Product Scene Contract Guard\n\n"
            f"- status: `FAIL`\n"
            f"- db_name: `{db_name}`\n"
            f"- login: `{login}`\n"
            f"- error: `{str(exc)}`\n",
        )
        print("[product_scene_contract_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    _write(
        OUT_MD,
        "# Product Scene Contract Guard\n\n"
        f"- status: `PASS`\n"
        f"- db_name: `{db_name}`\n"
        f"- login: `{login}`\n"
        f"- delivery_scene_count: `{len(report['delivery'])}`\n"
        f"- runtime_scene_count: `{len(report['runtime'])}`\n"
        f"- page_contract_checks: `{', '.join(report['page_contract'].keys())}`\n",
    )
    print("[product_scene_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
