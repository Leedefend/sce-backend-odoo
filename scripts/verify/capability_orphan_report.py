#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
CAPABILITY_REGISTRY = ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py"
SCENE_MATRIX_JSON = ROOT / "artifacts" / "backend" / "scene_capability_matrix_report.json"
ROLE_BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "capability_orphan_report.md"
ARTIFACT_JSON = ROOT / "artifacts" / "backend" / "capability_orphan_report.json"


def _safe_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_registry_caps() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not CAPABILITY_REGISTRY.is_file():
        return out
    tree = ast.parse(CAPABILITY_REGISTRY.read_text(encoding="utf-8"), filename=str(CAPABILITY_REGISTRY))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "_cap":
            continue
        if len(node.args) < 5:
            continue
        key_node = node.args[0]
        scene_node = node.args[4]
        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
            continue
        cap_key = key_node.value.strip()
        if not cap_key:
            continue
        intent = "ui.contract"
        for kw in node.keywords:
            if kw.arg == "intent" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                intent = kw.value.value.strip() or intent
        scene_key = ""
        if isinstance(scene_node, ast.Constant) and isinstance(scene_node.value, str):
            scene_key = scene_node.value.strip()
        out[cap_key] = {"intent": intent, "scene_key": scene_key}
    return out


def _scene_referenced_caps() -> set[str]:
    payload = _safe_json(SCENE_MATRIX_JSON)
    out: set[str] = set()
    for row in payload.get("matrix") or []:
        if not isinstance(row, dict):
            continue
        for field in ("declared_capabilities", "required_capabilities", "all_capabilities"):
            values = row.get(field)
            if not isinstance(values, list):
                continue
            for value in values:
                text = str(value or "").strip()
                if text:
                    out.add(text)
    return out


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    db_candidates = []
    for item in (db_name, "", "sc_demo", "sc_p3", "sc_p2", "sc_test"):
        val = str(item or "").strip()
        if val not in db_candidates:
            db_candidates.append(val)
    candidates = [
        (login, password),
        ("admin", os.getenv("ADMIN_PASSWD") or "admin"),
        ("sc_fx_pm", os.getenv("E2E_PROD_LIKE_PASSWORD") or "prod_like"),
        ("demo_pm", os.getenv("E2E_ROLE_MATRIX_DEFAULT_PASSWORD") or "demo"),
    ]
    for cand_db in db_candidates:
        for cand_login, cand_password in candidates:
            cand_login = str(cand_login or "").strip()
            cand_password = str(cand_password or "").strip()
            if not cand_login:
                continue
            status, body = http_post_json(
                intent_url,
                {"intent": "login", "params": {"db": cand_db, "login": cand_login, "password": cand_password}},
                headers={"X-Anonymous-Intent": "1"},
            )
            if status != 200 or not isinstance(body, dict) or body.get("ok") is not True:
                continue
            data = body.get("data") if isinstance(body.get("data"), dict) else {}
            token = str(data.get("token") or "").strip()
            if token:
                return token
    secret = str(os.getenv("SC_BOOTSTRAP_SECRET") or os.getenv("BOOTSTRAP_SECRET") or "").strip()
    if secret:
        bootstrap_login = str(os.getenv("SC_BOOTSTRAP_LOGIN") or os.getenv("BOOTSTRAP_LOGIN") or "svc_project_ro").strip()
        status, body = http_post_json(
            intent_url,
            {"intent": "session.bootstrap", "params": {"secret": secret, "login": bootstrap_login, "db": db_name}},
            headers={"X-Anonymous-Intent": "1"},
        )
        if status == 200 and isinstance(body, dict) and body.get("ok") is True:
            data = body.get("data") if isinstance(body.get("data"), dict) else {}
            token = str(data.get("token") or "").strip()
            if token:
                return token
    return ""


def _surface_caps_from_runtime() -> set[str]:
    fixtures = _safe_json(ROLE_BASELINE_JSON).get("fixtures") if isinstance(_safe_json(ROLE_BASELINE_JSON).get("fixtures"), list) else []
    if not fixtures:
        return set()

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    default_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or "prod_like").strip()
    surfaced: set[str] = set()
    for fx in fixtures:
        if not isinstance(fx, dict):
            continue
        login = str(fx.get("login") or "").strip()
        if not login:
            continue
        token = _login(intent_url, db_name, login, default_password)
        if not token:
            continue
        status, body = http_post_json(
            intent_url,
            {"intent": "system.init", "params": {"contract_mode": "hud"}},
            headers={"Authorization": f"Bearer {token}"},
        )
        if status != 200 or not isinstance(body, dict) or body.get("ok") is not True:
            continue
        data = body.get("data") if isinstance(body.get("data"), dict) else {}
        for cap in data.get("capabilities") or []:
            if not isinstance(cap, dict):
                continue
            key = str(cap.get("key") or "").strip()
            if key:
                surfaced.add(key)
    return surfaced


def main() -> int:
    registry_caps = _extract_registry_caps()
    registry_keys = set(registry_caps.keys())
    scene_refs = _scene_referenced_caps()
    for cap_key, meta in registry_caps.items():
        if str(meta.get("scene_key") or "").strip():
            scene_refs.add(cap_key)
    surfaced = _surface_caps_from_runtime()

    unreferenced_by_scene = sorted(registry_keys - scene_refs)
    without_intent_binding = sorted(
        [k for k, meta in registry_caps.items() if not str(meta.get("intent") or "").strip()]
    )
    not_surfaced = sorted(registry_keys - surfaced) if surfaced else sorted(registry_keys)

    report = {
        "ok": True,
        "summary": {
            "registry_capability_count": len(registry_keys),
            "scene_referenced_count": len(scene_refs),
            "runtime_surfaced_count": len(surfaced),
            "unreferenced_by_scene_count": len(unreferenced_by_scene),
            "without_intent_binding_count": len(without_intent_binding),
            "not_surfaced_count": len(not_surfaced),
        },
        "unreferenced_by_scene": unreferenced_by_scene,
        "without_intent_binding": without_intent_binding,
        "not_surfaced": not_surfaced,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Capability Orphan Report",
        "",
        f"- registry_capability_count: {report['summary']['registry_capability_count']}",
        f"- scene_referenced_count: {report['summary']['scene_referenced_count']}",
        f"- runtime_surfaced_count: {report['summary']['runtime_surfaced_count']}",
        f"- unreferenced_by_scene_count: {report['summary']['unreferenced_by_scene_count']}",
        f"- without_intent_binding_count: {report['summary']['without_intent_binding_count']}",
        f"- not_surfaced_count: {report['summary']['not_surfaced_count']}",
    ]

    def _append(title: str, values: list[str]) -> None:
        lines.extend(["", f"## {title}", ""])
        if not values:
            lines.append("- none")
            return
        for item in values:
            lines.append(f"- `{item}`")

    _append("Unreferenced By Scene", unreferenced_by_scene)
    _append("Without Intent Binding", without_intent_binding)
    _append("Not Surfaced In Runtime", not_surfaced)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(ARTIFACT_JSON))
    print(str(REPORT_MD))
    print("[capability_orphan_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
