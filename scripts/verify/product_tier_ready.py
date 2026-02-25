#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY_JSON = ROOT / "docs" / "product" / "product_tier_policy_v1.json"
LICENSE_CORE = ROOT / "addons" / "smart_license_core" / "core_extension.py"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "product_tier_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "product_tier_report.json"


def _load_policy() -> dict:
    if not POLICY_JSON.is_file():
        return {}
    try:
        payload = json.loads(POLICY_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _collect_capability_keys() -> list[str]:
    path = ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py"
    if not path.is_file():
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception:
        return []
    keys: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "list_capabilities_for_user":
            continue
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Dict):
                k = None
                v = None
                for kk, vv in zip(stmt.keys, stmt.values):
                    try:
                        key = ast.literal_eval(kk)
                    except Exception:
                        continue
                    if key == "key":
                        try:
                            val = ast.literal_eval(vv)
                        except Exception:
                            val = None
                        if isinstance(val, str):
                            k = val.strip()
                if k:
                    keys.append(k)
    return sorted(set(keys))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    policy = _load_policy()
    if not policy:
        errors.append("missing product tier policy")
    if not LICENSE_CORE.is_file():
        errors.append("missing smart_license_core/core_extension.py")

    levels = policy.get("levels") if isinstance(policy.get("levels"), list) else []
    if levels != ["community", "pro", "enterprise"]:
        errors.append("tier levels must be [community, pro, enterprise]")

    rules = policy.get("gating_rules") if isinstance(policy.get("gating_rules"), list) else []
    if not rules:
        errors.append("tier gating rules empty")
    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict):
            errors.append(f"invalid tier rule at #{idx + 1}")
            continue
        if not str(rule.get("prefix") or "").strip():
            errors.append(f"tier rule missing prefix at #{idx + 1}")
        if str(rule.get("min_level") or "").strip() not in {"community", "pro", "enterprise"}:
            errors.append(f"tier rule invalid min_level at #{idx + 1}")

    cap_keys = _collect_capability_keys()
    if not cap_keys:
        warnings.append("capability registry keys unavailable for tier coverage analysis")

    tier_rank = {"community": 1, "pro": 2, "enterprise": 3}
    rule_pairs = [
        (str(r.get("prefix") or "").strip(), str(r.get("min_level") or "").strip())
        for r in rules
        if isinstance(r, dict)
    ]

    def allowed(level: str) -> int:
        allow = 0
        for key in cap_keys:
            need = "community"
            for prefix, min_level in rule_pairs:
                if prefix and key.startswith(prefix):
                    need = min_level
                    break
            if tier_rank.get(level, 1) >= tier_rank.get(need, 1):
                allow += 1
        return allow

    community_count = allowed("community")
    pro_count = allowed("pro")
    enterprise_count = allowed("enterprise")
    if cap_keys and not (community_count <= pro_count <= enterprise_count):
        errors.append("tier monotonicity violated (community <= pro <= enterprise)")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "rule_count": len(rule_pairs),
            "capability_count": len(cap_keys),
            "community_allow_count": community_count,
            "pro_allow_count": pro_count,
            "enterprise_allow_count": enterprise_count,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Product Tier Report",
        "",
        f"- rule_count: {len(rule_pairs)}",
        f"- capability_count: {len(cap_keys)}",
        f"- community_allow_count: {community_count}",
        f"- pro_allow_count: {pro_count}",
        f"- enterprise_allow_count: {enterprise_count}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Errors",
        "",
    ]
    if errors:
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for item in warnings:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[product_tier_ready] FAIL")
        return 2
    print("[product_tier_ready] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
