# -*- coding: utf-8 -*-
"""Build the complete construction product capability scope from policy and native menus.

Run with:
    odoo shell -d <db> -c <conf> < scripts/verify/full_product_capability_scope_audit.py
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


try:
    ROOT = Path(__file__).resolve().parents[2]
except NameError:  # Odoo shell executes stdin without __file__.
    ROOT = Path("/mnt")
ARTIFACT_PATH = Path(os.getenv("FULL_PRODUCT_CAPABILITY_SCOPE_JSON", str(ROOT / "artifacts" / "product" / "full_product_capability_scope_v1.json")))
REPORT_PATH = Path(os.getenv("FULL_PRODUCT_CAPABILITY_SCOPE_MD", str(ROOT / "docs" / "product" / "full_product_capability_scope_v1.md")))
PRODUCT_KEY = "construction.standard"
PRODUCT_ROOT_XMLID = "smart_construction_core.menu_sc_root"
PRODUCT_ROOT_LABEL = "智慧施工管理平台"

FORMAL_CENTER_ORDER = [
    "基础资料",
    "项目中心",
    "合同中心",
    "施工管理",
    "物资与分包",
    "财务中心",
    "人事行政",
    "资料证照",
    "税务中心",
]

HANDLING_NAME_TOKENS = (
    "办理",
    "申请",
    "登记",
    "记录",
    "审批",
    "结算",
    "签证",
    "计划",
    "汇报",
    "订单",
    "使用",
    "存档",
    "借阅",
    "报名",
    "支付",
    "退回",
    "收入",
    "付款",
    "支出",
    "方单",
    "台班",
    "报价",
    "询价",
    "入库",
    "出库",
    "采购",
    "工资",
    "报销",
    "奖金",
    "补助",
    "社保",
    "请假",
    "休假",
    "印章",
    "上报",
)
NON_HANDLING_PATH_TOKENS = (
    "统计分析",
    "智慧大屏",
    "首页",
    "配置中心",
    "系统配置",
    "用户核对菜单",
    "用户验收",
)
NON_HANDLING_NAME_TOKENS = (
    "台账",
    "报表",
    "统计",
    "分析",
    "汇总",
    "总览",
    "明细",
    "驾驶舱",
    "大屏",
    "待办",
    "我的审批",
    "名册",
    "字典",
    "配置",
)
NON_HANDLING_MODEL_TOKENS = (
    ".summary",
    ".ledger",
    ".fact",
    ".cockpit",
    ".analysis",
)
DOMAIN_GROUP_LABELS = (
    "费用与保证金",
    "合同管理",
    "结算管理",
    "分包管理",
    "劳务管理",
    "机械管理",
    "材料管理",
    "收款管理",
    "付款管理",
    "借还款",
    "账户资金",
    "自筹资金",
    "油卡管理",
    "发票税务",
)
HISTORY_TOKENS = (
    "用户核对菜单",
    "用户验收",
    "直营项目系统菜单",
    "acceptance",
    "legacy",
)
NATIVE_MENU_ALIASES_COVERED_BY_RELEASE = {
    "smart_construction_core.menu_sc_invoice_input_report_user": "smart_construction_core.menu_sc_invoice_input",
}
PRODUCT_POLICY_DOMAIN_OVERRIDES = {
    # These entries are finance cash handling capabilities even when an
    # environment still carries an older intermediate "费用" path segment.
    "smart_construction_core.menu_sc_payment_deposit_return": "费用与保证金",
    "smart_construction_core.menu_sc_payment_deposit_return_refund_formal": "费用与保证金",
    "smart_construction_core.menu_sc_reimbursement_request": "费用与保证金",
    "smart_construction_core.menu_sc_project_expense_claim": "费用与保证金",
}


def _text(value) -> str:
    return str(value or "").strip()


def _escape(value) -> str:
    return _text(value).replace("|", "\\|")


def _write_text_with_fallback(path: Path, content: str, *, fallback_name: str) -> Path:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
    except (OSError, PermissionError):
        fallback = Path("/tmp/sce-product-artifacts") / fallback_name
        fallback.parent.mkdir(parents=True, exist_ok=True)
        fallback.write_text(content, encoding="utf-8")
        return fallback


def _xmlid(record) -> str:
    if not record:
        return ""
    try:
        return record.get_external_id().get(record.id, "") or ""
    except Exception:
        row = env["ir.model.data"].sudo().search([("model", "=", record._name), ("res_id", "=", record.id)], limit=1)  # noqa: F821
        return row.complete_name if row else ""


def _menu_path(menu) -> str:
    names = []
    current = menu
    while current:
        names.append(_text(current.name))
        current = current.parent_id
    return " / ".join(reversed([name for name in names if name]))


def _path_parts(path: str) -> list[str]:
    return [part.strip() for part in _text(path).replace("/", " / ").split(" / ") if part.strip()]


def _center_from_path(path: str) -> str:
    parts = _path_parts(path)
    if parts and parts[0] == PRODUCT_ROOT_LABEL and len(parts) > 1:
        return parts[1]
    return ""


def _domain_from_path(path: str, center: str) -> str:
    parts = _path_parts(path)
    if center in parts:
        index = parts.index(center)
        if index + 1 < len(parts) - 1:
            return parts[index + 1]
    return ""


def _policy_handling_rows(policy) -> list[dict]:
    rows = []
    for group in policy.menu_groups or []:
        if not isinstance(group, dict):
            continue
        center = _text(group.get("group_label") or group.get("label"))
        for menu in group.get("menus") or []:
            if not isinstance(menu, dict) or _text(menu.get("entry_intent")) != "handling":
                continue
            path = _text(menu.get("visible_menu_path"))
            menu_xmlid = _text(menu.get("menu_xmlid") or menu.get("page_key") or menu.get("menu_key"))
            rows.append(
                {
                    "source": "product_policy",
                    "status": "released_formal_handling" if menu.get("enabled", True) and _text(menu.get("release_state") or "released") == "released" else "modeled_policy_not_released",
                    "center": center or _center_from_path(path),
                    "domain": PRODUCT_POLICY_DOMAIN_OVERRIDES.get(menu_xmlid) or _domain_from_path(path, center),
                    "label": _text(menu.get("label") or menu.get("page_label")),
                    "path": path,
                    "model": _text(menu.get("integration_model") or menu.get("fact_model") or menu.get("res_model")),
                    "target": _text(menu.get("integration_target")),
                    "business_category_code": _text(menu.get("default_business_category_code")),
                    "menu_xmlid": menu_xmlid,
                    "release_state": _text(menu.get("release_state")) or "released",
                    "enabled": bool(menu.get("enabled", True)),
                }
            )
    return rows


def _native_menu_rows() -> list[dict]:
    root = env.ref(PRODUCT_ROOT_XMLID, raise_if_not_found=False)  # noqa: F821
    if not root:
        return []
    Menu = env["ir.ui.menu"].sudo().with_context(active_test=False)  # noqa: F821
    IMD = env["ir.model.data"].sudo()  # noqa: F821
    rows = []
    for menu in Menu.search([]):
        current = menu
        in_root = False
        while current:
            if int(current.id) == int(root.id):
                in_root = True
                break
            current = current.parent_id
        if not in_root:
            continue
        action = menu.action
        model = _text(getattr(action, "res_model", "") if action else "")
        if not model:
            continue
        imd = IMD.search([("model", "=", "ir.ui.menu"), ("res_id", "=", menu.id), ("module", "=", "smart_construction_core")], limit=1)
        if not imd:
            continue
        path = _menu_path(menu)
        rows.append(
            {
                "source": "native_menu",
                "status": "",
                "center": _center_from_path(path),
                "domain": _domain_from_path(path, _center_from_path(path)),
                "label": _text(menu.name),
                "path": path,
                "model": model,
                "target": _text(getattr(action, "name", "") if action else ""),
                "business_category_code": "",
                "menu_xmlid": imd.complete_name,
                "release_state": "native_active" if menu.active else "native_inactive",
                "enabled": bool(menu.active),
            }
        )
    return rows


def _is_history(row: dict) -> bool:
    text = " ".join([_text(row.get("path")), _text(row.get("menu_xmlid")), _text(row.get("model"))]).lower()
    return any(token.lower() in text for token in HISTORY_TOKENS) or _text(row.get("model")).startswith("sc.legacy.")


def _is_non_handling(row: dict) -> bool:
    path = _text(row.get("path"))
    label = _text(row.get("label"))
    center = _text(row.get("center"))
    domain = _text(row.get("domain"))
    model = _text(row.get("model")).lower()
    if label and label in {center, domain}:
        return True
    if label in DOMAIN_GROUP_LABELS:
        return True
    if any(token in path for token in NON_HANDLING_PATH_TOKENS):
        return True
    if any(token in label for token in NON_HANDLING_NAME_TOKENS):
        return True
    return any(token in model for token in NON_HANDLING_MODEL_TOKENS)


def _looks_handling(row: dict) -> bool:
    text = " ".join([_text(row.get("label")), _text(row.get("path")), _text(row.get("target"))])
    return any(token in text for token in HANDLING_NAME_TOKENS)


def _classify_native_gap(row: dict, released_xmlids: set[str]) -> str:
    xmlid = _text(row.get("menu_xmlid"))
    if xmlid in released_xmlids:
        return "covered_by_released_formal_handling"
    if _text(NATIVE_MENU_ALIASES_COVERED_BY_RELEASE.get(xmlid)) in released_xmlids:
        return "covered_by_released_formal_handling"
    if _is_history(row):
        return "history_acceptance_or_source"
    if _is_non_handling(row):
        return "query_analysis_config_or_container"
    if _looks_handling(row):
        return "modeled_native_handling_not_in_release"
    return "needs_capability_review"


def _sort_key(row: dict):
    center = _text(row.get("center"))
    return (
        FORMAL_CENTER_ORDER.index(center) if center in FORMAL_CENTER_ORDER else 99,
        _text(row.get("domain")),
        _text(row.get("label")),
        _text(row.get("menu_xmlid")),
    )


def _group(rows: list[dict], status: str) -> dict[str, list[dict]]:
    grouped = defaultdict(list)
    for row in rows:
        if row.get("status") == status:
            grouped[_text(row.get("center")) or "未归类"].append(row)
    return {key: sorted(value, key=_sort_key) for key, value in sorted(grouped.items())}


def _render_rows(lines: list[str], rows: list[dict], *, include_status: bool = False) -> None:
    if not rows:
        lines.append("无。")
        return
    header = "| 中心 | 业务域 | 能力入口 | 模型 | 状态 | XMLID |" if include_status else "| 中心 | 业务域 | 能力入口 | 模型 | XMLID |"
    sep = "| --- | --- | --- | --- | --- | --- |" if include_status else "| --- | --- | --- | --- | --- |"
    lines.extend([header, sep])
    for row in sorted(rows, key=_sort_key):
        cells = [
            _escape(row.get("center")),
            _escape(row.get("domain")),
            _escape(row.get("label")),
            "`%s`" % _escape(row.get("model")),
        ]
        if include_status:
            cells.append(_escape(row.get("release_state")))
        cells.append("`%s`" % _escape(row.get("menu_xmlid")))
        lines.append("| " + " | ".join(cells) + " |")


def main() -> int:
    policy = env["sc.product.policy"].sudo().with_context(active_test=False).search([("product_key", "=", PRODUCT_KEY)], limit=1)  # noqa: F821
    if not policy:
        raise AssertionError("missing product policy: %s" % PRODUCT_KEY)
    policy_rows = _policy_handling_rows(policy)
    released_xmlids = {_text(row.get("menu_xmlid")) for row in policy_rows if row.get("status") == "released_formal_handling"}
    native_rows = _native_menu_rows()
    for row in native_rows:
        row["status"] = _classify_native_gap(row, released_xmlids)
    all_rows = policy_rows + native_rows
    not_in_release = [row for row in native_rows if row.get("status") == "modeled_native_handling_not_in_release"]
    review = [row for row in native_rows if row.get("status") == "needs_capability_review"]
    history = [row for row in native_rows if row.get("status") == "history_acceptance_or_source"]
    non_handling = [row for row in native_rows if row.get("status") == "query_analysis_config_or_container"]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product_key": PRODUCT_KEY,
        "summary": {
            "released_formal_handling_count": len([row for row in policy_rows if row.get("status") == "released_formal_handling"]),
            "policy_modeled_not_released_count": len([row for row in policy_rows if row.get("status") == "modeled_policy_not_released"]),
            "native_modeled_not_in_release_count": len(not_in_release),
            "history_acceptance_or_source_count": len(history),
            "query_analysis_config_or_container_count": len(non_handling),
            "needs_capability_review_count": len(review),
        },
        "rows": all_rows,
    }
    artifact_path = _write_text_with_fallback(
        ARTIFACT_PATH,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        fallback_name="full_product_capability_scope_v1.json",
    )

    released = [row for row in policy_rows if row.get("status") == "released_formal_handling"]
    lines = [
        "# 完整产品办理能力口径 V1",
        "",
        "本报告不只按当前发布导航计数，而是同时读取产品策略与 Odoo 原生菜单动作，区分已发布正式办理能力、已建模但未纳入发布面的办理能力、历史验收/来源入口，以及查询分析配置入口。",
        "",
        "## 口径",
        "",
        "- 已发布正式办理能力：产品策略中 `entry_intent=handling` 且已发布、启用的入口。",
        "- 已建模未发布办理能力：原生产品菜单下存在动作和业务模型，名称/路径呈现办理语义，但未进入当前产品策略发布面。",
        "- 历史验收/来源入口：用户核对、用户验收、legacy/source fact 类入口，不直接等同正式产品办理能力。",
        "- 查询分析配置入口：台账、报表、统计、大屏、配置、字典、治理等非办理入口。",
        "",
        "## 摘要",
        "",
        f"- 已发布正式办理能力：`{payload['summary']['released_formal_handling_count']}`",
        f"- 产品策略中已建模但未发布：`{payload['summary']['policy_modeled_not_released_count']}`",
        f"- 原生菜单中已建模但未纳入发布面的办理能力：`{payload['summary']['native_modeled_not_in_release_count']}`",
        f"- 历史验收/来源入口：`{payload['summary']['history_acceptance_or_source_count']}`",
        f"- 查询分析配置入口：`{payload['summary']['query_analysis_config_or_container_count']}`",
        f"- 待人工复核入口：`{payload['summary']['needs_capability_review_count']}`",
        "",
        "## 已发布正式办理能力",
        "",
    ]
    _render_rows(lines, released)
    lines.extend(["", "## 已建模但未纳入发布面的办理能力", ""])
    _render_rows(lines, not_in_release, include_status=True)
    lines.extend(["", "## 待人工复核入口", ""])
    _render_rows(lines, review, include_status=True)
    lines.extend(["", "## 历史验收/来源入口边界", ""])
    lines.append("这些入口用于历史数据承载、核对或来源追溯；只有吸收到正式模型和正式产品菜单后，才算正式办理能力。")
    lines.append("")
    _render_rows(lines, history[:120], include_status=True)
    if len(history) > 120:
        lines.append("")
        lines.append("- 其余历史入口详见 JSON artifact。")
    report_path = _write_text_with_fallback(
        REPORT_PATH,
        "\n".join(lines) + "\n",
        fallback_name="full_product_capability_scope_v1.md",
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "artifact": str(artifact_path),
                "report": str(report_path),
                **payload["summary"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
