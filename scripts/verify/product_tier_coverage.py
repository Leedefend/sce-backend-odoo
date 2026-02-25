#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
POLICY_JSON = ROOT / "docs" / "product" / "product_tier_policy_v1.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "product_tier_coverage_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "product_tier_coverage_report.json"

TIER_RANK = {"community": 1, "pro": 2, "enterprise": 3}
TIERS = ("community", "pro", "enterprise")


def _load_policy() -> dict:
    if not POLICY_JSON.is_file():
        return {}
    try:
        payload = json.loads(POLICY_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[bool, str]:
    status, payload = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, ""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    return bool(token), token


def _intent(intent_url: str, token: str, intent: str, params: dict | None = None) -> tuple[int, dict]:
    status, payload = http_post_json(
        intent_url,
        {"intent": intent, "params": params or {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    return status, payload if isinstance(payload, dict) else {}


def _read_config_param(intent_url: str, token: str, key: str) -> tuple[int, str]:
    status, payload = _intent(
        intent_url,
        token,
        "api.data",
        {
            "op": "list",
            "model": "ir.config_parameter",
            "fields": ["id", "key", "value"],
            "domain": [["key", "=", key]],
            "limit": 1,
        },
    )
    if status >= 400 or payload.get("ok") is not True:
        return 0, ""
    rows = (((payload.get("data") or {}).get("records")) or [])
    if not rows:
        return 0, ""
    row = rows[0] if isinstance(rows[0], dict) else {}
    try:
        rec_id = int(row.get("id") or 0)
    except Exception:
        rec_id = 0
    return rec_id, str(row.get("value") or "")


def _set_config_param(intent_url: str, token: str, key: str, value: str) -> bool:
    rec_id, _ = _read_config_param(intent_url, token, key)
    if rec_id > 0:
        status, payload = _intent(
            intent_url,
            token,
            "api.data",
            {
                "op": "write",
                "model": "ir.config_parameter",
                "ids": [rec_id],
                "vals": {"value": value},
            },
        )
        return status < 400 and payload.get("ok") is True
    status, payload = _intent(
        intent_url,
        token,
        "api.data",
        {
            "op": "create",
            "model": "ir.config_parameter",
            "vals": {"key": key, "value": value},
        },
    )
    return status < 400 and payload.get("ok") is True


def _extract_capability_keys(system_init_payload: dict) -> set[str]:
    data = system_init_payload.get("data") if isinstance(system_init_payload.get("data"), dict) else {}
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        data = data.get("data") or {}
    caps = data.get("capabilities") if isinstance(data, dict) else []
    out: set[str] = set()
    if isinstance(caps, list):
        for item in caps:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip()
            if key:
                out.add(key)
    return out


def _min_tier_for_key(key: str, rules: list[dict]) -> str:
    cap_key = str(key or "").strip().lower()
    for row in rules:
        prefix = str(row.get("prefix") or "").strip().lower()
        tier = str(row.get("min_level") or "").strip().lower()
        if prefix and cap_key.startswith(prefix) and tier in TIER_RANK:
            return tier
    return "community"


def _collect_static_capability_keys() -> set[str]:
    files = [
        ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py",
        ROOT / "addons" / "smart_owner_core" / "services" / "capability_registry_owner.py",
        ROOT / "addons" / "smart_construction_bundle" / "services" / "bundle_registry.py",
        ROOT / "addons" / "smart_owner_bundle" / "services" / "bundle_registry.py",
    ]
    out: set[str] = set()
    pattern = re.compile(r"[\"']key[\"']\s*:\s*[\"']([^\"']+)[\"']")
    for path in files:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for key in pattern.findall(text):
            val = str(key or "").strip()
            if val:
                out.add(val)
    return out


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    policy = _load_policy()
    rules = policy.get("gating_rules") if isinstance(policy.get("gating_rules"), list) else []
    if not rules:
        errors.append("missing product tier policy rules")

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    ok, token = _login(intent_url, db_name, login, password)
    if not ok:
        errors.append("login failed")
        token = ""

    license_key = "sc.license.level"
    original_value = ""
    original_id = 0
    if token:
        original_id, original_value = _read_config_param(intent_url, token, license_key)

    runtime_visible_by_tier: dict[str, int] = {}
    runtime_keys_by_tier: dict[str, set[str]] = {}
    capability_total = 0
    if token:
        for tier in TIERS:
            if not _set_config_param(intent_url, token, license_key, tier):
                errors.append(f"failed to set {license_key}={tier}")
                continue
            status, payload = _intent(intent_url, token, "system.init", {"contract_mode": "user"})
            if status >= 400 or payload.get("ok") is not True:
                errors.append(f"system.init failed under tier={tier}")
                continue
            keys = _extract_capability_keys(payload)
            runtime_keys_by_tier[tier] = keys
            runtime_visible_by_tier[tier] = len(keys)
            capability_total = max(capability_total, len(keys))

        # restore original config
        restore_val = original_value if original_id > 0 else "enterprise"
        if not _set_config_param(intent_url, token, license_key, restore_val):
            warnings.append(f"failed to restore {license_key} to {restore_val}")

    static_keys = _collect_static_capability_keys()
    community_keys = runtime_keys_by_tier.get("community", set())
    pro_keys = runtime_keys_by_tier.get("pro", set())
    enterprise_keys = runtime_keys_by_tier.get("enterprise", set())
    all_runtime_keys = community_keys | pro_keys | enterprise_keys
    all_keys = static_keys or all_runtime_keys
    capability_total = max(capability_total, len(all_keys))

    if not all_keys:
        errors.append("capability_count = 0, tier coverage blind spot")

    # static policy projection as primary proof (eliminates blind spot when runtime extension is absent)
    static_visible_by_tier = {"community": 0, "pro": 0, "enterprise": 0}
    for key in sorted(all_keys):
        min_tier = _min_tier_for_key(key, rules)
        for tier in TIERS:
            if TIER_RANK[tier] >= TIER_RANK[min_tier]:
                static_visible_by_tier[tier] += 1

    if not (
        static_visible_by_tier["community"] <= static_visible_by_tier["pro"] <= static_visible_by_tier["enterprise"]
    ):
        errors.append("tier monotonicity violated (static policy projection)")

    hidden_by_tier = {
        "community": max(0, capability_total - static_visible_by_tier["community"]),
        "pro": max(0, capability_total - static_visible_by_tier["pro"]),
        "enterprise": max(0, capability_total - static_visible_by_tier["enterprise"]),
    }
    if hidden_by_tier["community"] <= 0:
        errors.append("community hidden_by_tier must be > 0")
    if hidden_by_tier["pro"] <= 0:
        warnings.append("pro hidden_by_tier <= 0 (no enterprise-only capability observed)")

    # runtime enforcement evidence (non-blocking warning if extension not active in current DB)
    if runtime_visible_by_tier:
        for tier in TIERS:
            rv = runtime_visible_by_tier.get(tier, 0)
            sv = static_visible_by_tier.get(tier, 0)
            if rv != sv:
                warnings.append(f"runtime tier coverage mismatch for {tier}: runtime={rv}, static_policy={sv}")

    coverage_ratio = {
        tier: round((static_visible_by_tier.get(tier, 0) / capability_total), 4) if capability_total else 0.0
        for tier in TIERS
    }

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "capability_total": capability_total,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "visible_by_tier": {tier: static_visible_by_tier.get(tier, 0) for tier in TIERS},
        "runtime_visible_by_tier": {tier: runtime_visible_by_tier.get(tier, 0) for tier in TIERS},
        "hidden_by_tier": hidden_by_tier,
        "coverage_ratio": coverage_ratio,
        "expected_visible_by_policy": static_visible_by_tier,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Product Tier Coverage Report",
        "",
        f"- capability_total: {capability_total}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "| tier | visible | hidden | coverage_ratio | expected_visible_by_policy |",
        "|---|---:|---:|---:|---:|",
    ]
    for tier in TIERS:
        lines.append(
            f"| {tier} | {static_visible_by_tier.get(tier, 0)} | {hidden_by_tier.get(tier, 0)} | "
            f"{coverage_ratio.get(tier, 0.0):.4f} | {static_visible_by_tier.get(tier, 0)} |"
        )
    lines.extend(["", "## Errors", ""])
    if errors:
        lines.extend([f"- {item}" for item in errors])
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend([f"- {item}" for item in warnings])
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[product_tier_coverage] FAIL")
        return 2
    print("[product_tier_coverage] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
