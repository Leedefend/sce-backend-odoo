#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "product_delivery_productization_readiness.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "product_delivery_productization_readiness.md"


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _load_json(path: Path) -> dict:
    text = _read(path)
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _manifest(path: Path) -> dict:
    text = _read(path)
    if not text:
        return {}
    try:
        module = ast.parse(text, filename=str(path), mode="exec")
    except Exception:
        return {}
    for node in module.body:
        if not isinstance(node, ast.Expr):
            continue
        try:
            value = ast.literal_eval(node.value)
        except Exception:
            continue
        if isinstance(value, dict) and value.get("name"):
            return value
    return {}


def _has_all(text: str, tokens: list[str]) -> bool:
    lowered = text.lower()
    return all(token.lower() in lowered for token in tokens)


def _row(item_id: str, title: str, area: str, severity: str, ok: bool, evidence: str, next_step: str) -> dict:
    return {
        "id": item_id,
        "title": title,
        "area": area,
        "severity": severity,
        "ok": bool(ok),
        "evidence": evidence,
        "next_step": next_step,
    }


def collect_checks() -> list[dict]:
    audit_doc = ROOT / "docs" / "product" / "product_delivery_productization_audit_v1.md"
    feature_index = ROOT / "docs" / "product" / "feature_index.zh.md"
    capability_matrix = ROOT / "docs" / "product" / "product_capability_matrix_v2.md"
    tier_policy = ROOT / "docs" / "product" / "product_tier_policy_v1.json"
    delivery_playbook = ROOT / "docs" / "product" / "delivery_playbook_v1.md"
    standard_package = ROOT / "docs" / "product" / "delivery" / "v1" / "standard_delivery_package_v1.md"
    scoreboard = ROOT / "docs" / "product" / "delivery" / "v1" / "delivery_readiness_scoreboard_v1.md"
    role_docs = [
        ROOT / "docs" / "product" / "delivery" / "v1" / "user_journey_pm.md",
        ROOT / "docs" / "product" / "delivery" / "v1" / "user_journey_finance.md",
        ROOT / "docs" / "product" / "delivery" / "v1" / "user_journey_exec.md",
        ROOT / "docs" / "product" / "delivery" / "v1" / "user_journey_purchase.md",
        ROOT / "docs" / "product" / "delivery" / "v1" / "roles_v1.md",
    ]
    construction_bundle_manifest = ROOT / "addons" / "smart_construction_bundle" / "__manifest__.py"
    license_manifest = ROOT / "addons" / "smart_license_core" / "__manifest__.py"
    prod_runbook = ROOT / "docs" / "ops" / "production_deployment_runbook_v1.md"
    product_gap_report = ROOT / "docs" / "ops" / "audit" / "product_delivery_gap_report.md"
    package_manifest = ROOT / "docs" / "ops" / "audit" / "product_delivery_package_manifest.md"

    checks: list[dict] = []

    audit_text = _read(audit_doc)
    checks.append(
        _row(
            "productization_audit_doc",
            "产品化审计文档",
            "governance",
            "P0",
            audit_doc.is_file() and _has_all(audit_text, ["产品包", "版本", "角色", "开通", "验收", "支持"]),
            str(audit_doc.relative_to(ROOT)),
            "沉淀产品包、版本、角色、开通、验收、支持六线审计。",
        )
    )

    cap_text = _read(capability_matrix)
    checks.append(
        _row(
            "capability_matrix_substantial",
            "产品能力矩阵足够完整",
            "catalog",
            "P0",
            capability_matrix.is_file() and "capability_count: 63" in cap_text and "product_capability_count: 20" in cap_text,
            str(capability_matrix.relative_to(ROOT)),
            "持续把能力矩阵作为产品能力目录的数据源。",
        )
    )

    feature_text = _read(feature_index)
    feature_rows = [
        line
        for line in feature_text.splitlines()
        if line.startswith("|") and "`" in line and "产品能力" not in line and "---" not in line
    ]
    checks.append(
        _row(
            "feature_index_customer_catalog",
            "客户可读功能索引",
            "catalog",
            "P0",
            len(feature_rows) >= 12 and _has_all(feature_text, ["目标角色", "版本", "验收方式"]),
            str(feature_index.relative_to(ROOT)),
            "把轻量模块索引升级为客户可读产品能力目录。",
        )
    )

    policy = _load_json(tier_policy)
    levels = policy.get("levels") if isinstance(policy.get("levels"), list) else []
    rules = policy.get("gating_rules") if isinstance(policy.get("gating_rules"), list) else []
    checks.append(
        _row(
            "tier_policy_defined",
            "版本套餐策略存在",
            "commercialization",
            "P0",
            {"community", "pro", "enterprise"}.issubset(set(str(x) for x in levels)) and bool(rules),
            str(tier_policy.relative_to(ROOT)),
            "补齐每个套餐的客户价值、限制和升级路径。",
        )
    )

    construction_bundle = _manifest(construction_bundle_manifest)
    bundle_data = construction_bundle.get("data") if isinstance(construction_bundle.get("data"), list) else []
    checks.append(
        _row(
            "construction_bundle_real_package",
            "施工行业产品包不是空壳",
            "bundle",
            "P0",
            bool(bundle_data),
            str(construction_bundle_manifest.relative_to(ROOT)),
            "把菜单、角色、策略、默认入口、验收资产放入 bundle 交付边界。",
        )
    )

    license_core = _manifest(license_manifest)
    license_data = license_core.get("data") if isinstance(license_core.get("data"), list) else []
    checks.append(
        _row(
            "license_core_customer_visible",
            "授权能力客户可见",
            "commercialization",
            "P1",
            bool(license_data),
            str(license_manifest.relative_to(ROOT)),
            "把授权状态、能力不可用原因和升级说明纳入产品界面或交付契约。",
        )
    )

    playbook_text = _read(delivery_playbook)
    checks.append(
        _row(
            "onboarding_playbook_customer_ready",
            "开通交付手册客户可执行",
            "onboarding",
            "P0",
            _has_all(playbook_text, ["company", "role", "acceptance"]) and _has_all(playbook_text, ["rollback", "evidence"]),
            str(delivery_playbook.relative_to(ROOT)),
            "从安装命令手册升级为企业开通、角色配置、验收、回滚的交付旅程。",
        )
    )

    checks.append(
        _row(
            "customer_acceptance_package",
            "客户验收证据包存在",
            "acceptance",
            "P0",
            standard_package.is_file() and scoreboard.is_file(),
            f"{standard_package.relative_to(ROOT)}; {scoreboard.relative_to(ROOT)}",
            "补齐截图、角色路径、数据口径、已知限制和客户签收清单。",
        )
    )

    role_doc_count = len([path for path in role_docs if path.is_file()])
    checks.append(
        _row(
            "role_journey_coverage",
            "核心角色旅程覆盖",
            "journey",
            "P1",
            role_doc_count >= 5,
            f"role_doc_count={role_doc_count}",
            "把角色旅程变成浏览器可验证的黄金路径。",
        )
    )

    prod_text = _read(prod_runbook)
    checks.append(
        _row(
            "ops_support_runbook",
            "生产运维与支持路径清楚",
            "support",
            "P1",
            prod_runbook.is_file() and _has_all(prod_text, ["rollback", "evidence", "verification"]),
            str(prod_runbook.relative_to(ROOT)),
            "补系统内健康检查、诊断包导出、发布历史和配置审计入口。",
        )
    )

    checks.append(
        _row(
            "engineering_delivery_reports",
            "工程交付报告链存在",
            "governance",
            "P1",
            product_gap_report.is_file() and package_manifest.is_file(),
            f"{product_gap_report.relative_to(ROOT)}; {package_manifest.relative_to(ROOT)}",
            "保持工程报告，但不要把 gap_count=0 等同于产品成熟。",
        )
    )

    return checks


def write_reports(checks: list[dict], strict: bool) -> dict:
    failed = [row for row in checks if not row["ok"]]
    failed_p0 = [row for row in failed if row["severity"] == "P0"]
    score = round(100.0 * (len(checks) - len(failed)) / max(len(checks), 1), 1)
    decision = "ready" if not failed else ("needs_productization_p0" if failed_p0 else "needs_productization_p1")
    payload = {
        "ok": not failed if strict else True,
        "decision": decision,
        "strict": strict,
        "summary": {
            "check_count": len(checks),
            "pass_count": len(checks) - len(failed),
            "gap_count": len(failed),
            "p0_gap_count": len(failed_p0),
            "score": score,
        },
        "checks": checks,
        "gaps": failed,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Product Delivery Productization Readiness",
        "",
        f"- decision: {decision}",
        f"- strict: {str(strict).lower()}",
        f"- score: {score}",
        f"- check_count: {payload['summary']['check_count']}",
        f"- pass_count: {payload['summary']['pass_count']}",
        f"- gap_count: {payload['summary']['gap_count']}",
        f"- p0_gap_count: {payload['summary']['p0_gap_count']}",
        "",
        "## Checks",
        "",
        "| id | severity | area | status | next_step |",
        "|---|---|---|---|---|",
    ]
    for row in checks:
        lines.append(
            f"| {row['id']} | {row['severity']} | {row['area']} | "
            f"{'PASS' if row['ok'] else 'GAP'} | {row['next_step']} |"
        )

    lines.extend(["", "## P0 Gaps", ""])
    if failed_p0:
        for row in failed_p0:
            lines.append(f"- {row['id']}: {row['title']} -> {row['next_step']}")
    else:
        lines.append("- none")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="fail when productization gaps exist")
    args = parser.parse_args()

    checks = collect_checks()
    payload = write_reports(checks, strict=bool(args.strict))

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    print(
        "[product_delivery_productization_readiness] "
        f"decision={payload['decision']} score={payload['summary']['score']} "
        f"gap_count={payload['summary']['gap_count']} p0_gap_count={payload['summary']['p0_gap_count']}"
    )
    return 2 if args.strict and payload["summary"]["gap_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
