#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAP_REGISTRY = ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py"

REPORT_MD = ROOT / "docs" / "product" / "product_capability_matrix_v2.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "product_module_graph_v2.json"


PRODUCT_CAPS = {
    "project.initiation.enter": "product.project.initiation",
    "project.list.open": "product.project.delivery",
    "project.board.open": "product.project.delivery",
    "project.dashboard.open": "product.project.delivery",
    "project.lifecycle.open": "product.project.delivery",
    "project.task.list": "product.execution.collaboration",
    "project.task.board": "product.execution.collaboration",
    "project.document.open": "product.execution.collaboration",
    "project.structure.manage": "product.execution.collaboration",
    "project.risk.list": "product.risk.control",
    "project.weekly_report.open": "product.reporting.weekly",
    "project.lifecycle.transition": "product.project.delivery",
    "finance.payment_request.list": "product.finance.payment",
    "finance.payment_request.form": "product.finance.payment",
    "finance.approval.center": "product.finance.approval",
    "finance.ledger.payment": "product.finance.ledger",
    "finance.ledger.treasury": "product.finance.ledger",
    "finance.settlement.order": "product.finance.settlement",
    "finance.invoice.list": "product.finance.ledger",
    "finance.plan.funding": "product.finance.payment",
    "finance.metrics.operating": "product.finance.operating_metrics",
    "finance.exception.monitor": "product.risk.control",
    "cost.ledger.open": "product.cost.control",
    "cost.budget.manage": "product.cost.control",
    "cost.boq.manage": "product.cost.control",
    "cost.progress.report": "product.cost.control",
    "cost.profit.compare": "product.finance.operating_metrics",
    "contract.center.open": "product.contract.center",
    "contract.income.track": "product.contract.center",
    "contract.expense.track": "product.contract.center",
    "contract.settlement.audit": "product.finance.settlement",
    "analytics.dashboard.executive": "product.analytics.executive",
    "analytics.lifecycle.monitor": "product.analytics.executive",
    "analytics.exception.list": "product.analytics.executive",
    "analytics.project.focus": "product.analytics.executive",
    "governance.capability.matrix": "product.governance.runtime",
    "governance.scene.openability": "product.governance.runtime",
    "governance.runtime.audit": "product.governance.runtime",
    "material.catalog.open": "product.procurement.material",
    "material.procurement.list": "product.procurement.material",
    "workspace.today.focus": "product.workspace.navigation",
    "workspace.project.watch": "product.workspace.navigation",
}

PRODUCT_TO_MODULE = {
    "product.project.initiation": "module.project_lifecycle",
    "product.project.delivery": "module.project_lifecycle",
    "product.execution.collaboration": "module.execution_delivery",
    "product.finance.payment": "module.finance_settlement",
    "product.finance.approval": "module.finance_settlement",
    "product.finance.ledger": "module.finance_settlement",
    "product.finance.settlement": "module.finance_settlement",
    "product.finance.operating_metrics": "module.business_analytics",
    "product.cost.control": "module.execution_delivery",
    "product.reporting.weekly": "module.business_analytics",
    "product.risk.control": "module.risk_compliance",
    "product.contract.center": "module.contract_commercial",
    "product.analytics.executive": "module.business_analytics",
    "product.governance.runtime": "module.governance_platform",
    "product.procurement.material": "module.procurement_supply",
    "product.workspace.navigation": "module.governance_platform",
}


def _parse_capability_keys() -> list[str]:
    if not CAP_REGISTRY.is_file():
        return []
    tree = ast.parse(CAP_REGISTRY.read_text(encoding="utf-8"), filename=str(CAP_REGISTRY))
    keys = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
        if not isinstance(value, ast.List):
            continue
        for item in value.elts:
            if not isinstance(item, ast.Call):
                continue
            if not isinstance(item.func, ast.Name) or item.func.id != "_cap":
                continue
            if not item.args:
                continue
            try:
                key = ast.literal_eval(item.args[0])
            except Exception:
                key = ""
            key = str(key or "").strip()
            if key:
                keys.append(key)
    return sorted(set(keys))


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    cap_keys = _parse_capability_keys()
    if not cap_keys:
        errors.append("capability keys empty")

    rows = []
    unassigned = []
    for key in cap_keys:
        product = PRODUCT_CAPS.get(key, "")
        module = PRODUCT_TO_MODULE.get(product, "")
        if not product or not module:
            unassigned.append(key)
            continue
        rows.append({"capability_key": key, "product_capability": product, "industry_module": module})

    if unassigned:
        errors.append(f"unassigned_capability_count={len(unassigned)}")

    products = sorted({row["product_capability"] for row in rows})
    modules = sorted({row["industry_module"] for row in rows})
    if len(products) != 16:
        errors.append(f"product_capability_count_mismatch={len(products)} expected=16")
    if len(modules) != 8:
        errors.append(f"industry_module_count_mismatch={len(modules)} expected=8")
    report = {
        "ok": len(errors) == 0,
        "summary": {
            "capability_count": len(cap_keys),
            "mapped_capability_count": len(rows),
            "product_capability_count": len(products),
            "industry_module_count": len(modules),
            "unassigned_capability_count": len(unassigned),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "products": products,
        "industry_modules": modules,
        "rows": rows,
        "unassigned_capabilities": unassigned,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Product Capability Matrix v2",
        "",
        "- target: 42 capability -> 16 product capability -> 8 industry module",
        f"- capability_count: {len(cap_keys)}",
        f"- mapped_capability_count: {len(rows)}",
        f"- product_capability_count: {len(products)}",
        f"- industry_module_count: {len(modules)}",
        f"- unassigned_capability_count: {len(unassigned)}",
        f"- error_count: {len(errors)}",
        "",
        "## Product Capability List",
        "",
    ]
    for item in products:
        lines.append(f"- {item} ({PRODUCT_TO_MODULE.get(item, '-')})")
    lines.extend(["", "## Capability Mapping", ""])
    lines.append("| capability_key | product_capability | industry_module |")
    lines.append("|---|---|---|")
    for row in rows:
        lines.append(f"| {row['capability_key']} | {row['product_capability']} | {row['industry_module']} |")
    lines.extend(["", "## Unassigned", ""])
    if unassigned:
        for key in unassigned:
            lines.append(f"- {key}")
    else:
        lines.append("- none")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[product_capability_matrix_v2_report] FAIL")
        return 2
    print("[product_capability_matrix_v2_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
