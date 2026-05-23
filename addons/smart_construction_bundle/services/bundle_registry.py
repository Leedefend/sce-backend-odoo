# -*- coding: utf-8 -*-
from __future__ import annotations


def list_bundle_scenes() -> list[dict]:
    return [
        {"code": "projects.intake", "name": "项目立项与台账", "tier": "standard"},
        {"code": "projects.dashboard", "name": "项目驾驶舱", "tier": "standard"},
        {"code": "finance.payment_requests", "name": "付款申请与审批", "tier": "pro"},
        {"code": "finance.payment_ledger", "name": "资金与结算台账", "tier": "pro"},
        {"code": "portal.dashboard", "name": "经营指标与领导看板", "tier": "pro"},
    ]


def list_bundle_capabilities() -> list[dict]:
    return [
        {"key": "product.project.delivery", "label": "项目交付", "tier": "standard"},
        {"key": "product.execution.collaboration", "label": "执行协同", "tier": "standard"},
        {"key": "product.finance.payment", "label": "付款申请", "tier": "pro"},
        {"key": "product.finance.ledger", "label": "资金台账", "tier": "pro"},
        {"key": "product.analytics.executive", "label": "经营看板", "tier": "pro"},
        {"key": "product.governance.runtime", "label": "发布与能力治理", "tier": "enterprise"},
    ]


def recommended_roles() -> list[str]:
    return ["pm", "finance", "purchase_manager", "executive", "admin"]


def default_dashboard() -> str:
    return "projects.dashboard"


def product_profile() -> dict:
    return {
        "product_key": "construction.standard",
        "bundle_key": "smart_construction_bundle",
        "label": "施工企业管理标准产品包",
        "tiers": ["standard", "pro", "enterprise"],
        "customer_capability_catalog": "docs/product/feature_index.zh.md",
        "acceptance_assets": [
            "docs/product/delivery/v1/standard_delivery_package_v1.md",
            "docs/product/delivery/v1/delivery_readiness_scoreboard_v1.md",
            "docs/product/product_delivery_productization_audit_v1.md",
        ],
    }
