#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard runtime scene set covers key business domains (project/task/contract/cost/risk)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_JSON = ROOT / "artifacts" / "scene_key_domain_coverage_guard.json"
ARTIFACT_MD = ROOT / "artifacts" / "scene_key_domain_coverage_guard.md"


def _login_token(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, login_resp, "login")
    data = login_resp.get("data") if isinstance(login_resp.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if not token:
        raise RuntimeError("login response missing token")
    return token


def _load_runtime_scenes(intent_url: str, db_name: str, token: str) -> list[dict]:
    status, resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "hud"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, "system.init hud")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data
    scenes = data.get("scenes")
    return scenes if isinstance(scenes, list) else []


def _contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def main() -> None:
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    intent_url = f"{base_url}/api/v1/intent"

    token = _login_token(intent_url, db_name, login, password)
    scenes = _load_runtime_scenes(intent_url, db_name, token)

    domain_tokens = {
        "project": ["project", "项目"],
        "task": ["task", "任务"],
        "contract": ["contract", "合同"],
        "cost": ["cost", "成本"],
        "risk": ["risk", "风险"],
    }

    hits: dict[str, list[str]] = {k: [] for k in domain_tokens}
    for row in scenes:
        if not isinstance(row, dict):
            continue
        scene_key = str(row.get("key") or row.get("code") or row.get("scene_key") or "").strip()
        scene_name = str(row.get("name") or row.get("label") or "").strip()
        route = ""
        target = row.get("target") if isinstance(row.get("target"), dict) else {}
        if isinstance(target, dict):
            route = str(target.get("route") or target.get("action_xmlid") or "").strip()
        haystack = f"{scene_key} {scene_name} {route}".lower()
        for domain, tokens in domain_tokens.items():
            normalized = [token.lower() for token in tokens]
            if _contains_any(haystack, normalized):
                if scene_key and scene_key not in hits[domain]:
                    hits[domain].append(scene_key)

    missing = [domain for domain, matched in hits.items() if not matched]
    ok = len(missing) == 0

    report = {
        "ok": ok,
        "summary": {
            "runtime_scene_count": len(scenes),
            "domain_count": len(domain_tokens),
            "covered_domain_count": len(domain_tokens) - len(missing),
            "missing_domain_count": len(missing),
            "probe_login": login,
        },
        "domains": {k: {"matched_scene_keys": v, "matched_count": len(v)} for k, v in hits.items()},
        "missing_domains": missing,
        "errors": [] if ok else [f"missing key domain scenes: {', '.join(missing)}"],
    }

    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Scene Key Domain Coverage Guard",
        "",
        f"- status: {'PASS' if ok else 'FAIL'}",
        f"- runtime_scene_count: {len(scenes)}",
        f"- covered_domain_count: {report['summary']['covered_domain_count']}/{report['summary']['domain_count']}",
        f"- missing_domain_count: {len(missing)}",
        f"- probe_login: {login}",
    ]
    if missing:
        lines.extend(["", "## Missing Domains", *[f"- {item}" for item in missing]])
    ARTIFACT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(ARTIFACT_JSON))
    print(str(ARTIFACT_MD))
    if not ok:
        raise RuntimeError("scene key domain coverage not satisfied")
    print("[scene_key_domain_coverage_guard] PASS")


if __name__ == "__main__":
    main()
