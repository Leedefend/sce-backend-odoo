# -*- coding: utf-8 -*-
"""Audit whether formal business models carry migrated real business data.

Run with:
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec < scripts/verify/formal_business_data_carrying_matrix_probe.py
"""

from collections import Counter, defaultdict
import json

from odoo.tools.safe_eval import safe_eval


SOURCE_FIELDS = ("source_origin", "legacy_source_model", "legacy_source_table", "legacy_record_id")
LEGACY_PREFIX = "sc.legacy."


KNOWN_INDIRECT_CARRYING_RULES = {
    "sc.legacy.workflow.audit": [
        {
            "target_model": "sc.history.todo",
            "domain": [],
            "carrying_type": "formal_runtime_surface",
            "note": "历史流程审计投影为历史待办，再进入工作台事项。",
        },
        {
            "target_model": "sc.workbench.item",
            "domain": [("source_model", "=", "sc.history.todo")],
            "carrying_type": "formal_runtime_surface",
            "note": "工作台我的待办/我的审批消费历史待办投影。",
        },
    ],
    "sc.legacy.account.transaction.line": [
        {
            "target_model": "sc.account.income.expense.summary",
            "domain": [],
            "carrying_type": "analysis_projection",
            "note": "账户收支统计表汇总账户流水；资金台账只承载现金办理口径，不要求一比一承载全部账户流水。",
        },
        {
            "target_model": "sc.treasury.ledger",
            "domain": [],
            "carrying_type": "analysis_projection",
            "note": "可确认现金收支进入资金台账，作为账户流水的一部分运行面。",
        },
    ],
    "sc.legacy.deduction.adjustment.line": [
        {
            "target_model": "sc.settlement.adjustment",
            "domain": [("legacy_line_id", "!=", False)],
            "carrying_type": "formal_runtime_surface",
            "note": "历史扣款/调整行进入结算调整；缺正式项目锚点的历史事实补建历史未归档项目锚点。",
        },
    ],
    "sc.legacy.fund.daily.snapshot.fact": [
        {
            "target_model": "sc.fund.daily.summary",
            "domain": [],
            "carrying_type": "readonly_projection",
            "note": "资金日报历史快照进入只读日报汇总。",
        },
        {
            "target_model": "sc.dashboard.cockpit.fact",
            "domain": [("fact_type", "=", "fund_cockpit")],
            "carrying_type": "analysis_projection",
            "note": "资金驾驶舱消费资金日报汇总投影。",
        },
    ],
    "sc.legacy.invoice.surcharge.fact": [
        {
            "target_model": "sc.ar.ap.project.summary",
            "domain": [],
            "carrying_type": "analysis_projection",
            "note": "进入项目/供应商账款分析口径。",
        },
    ],
    "sc.legacy.tax.deduction.fact": [
        {
            "target_model": "sc.ar.ap.project.summary",
            "domain": [],
            "carrying_type": "analysis_projection",
            "note": "进入项目/供应商账款分析口径。",
        },
    ],
    "sc.legacy.self.funding.fact": [
        {
            "target_model": "sc.ar.ap.project.summary",
            "domain": [],
            "carrying_type": "analysis_projection",
            "note": "进入项目/供应商账款分析口径。",
        },
    ],
    "sc.legacy.project.fund.balance.fact": [
        {
            "target_model": "sc.ar.ap.project.summary",
            "domain": [],
            "carrying_type": "analysis_projection",
            "note": "进入项目资金余额分析口径。",
        },
    ],
    "sc.legacy.supplier.contract.pricing.fact": [
        {
            "target_model": "construction.contract",
            "domain": [("type", "=", "in")],
            "carrying_type": "formal_runtime_surface",
            "note": "历史供应商合同计价事实进入支出合同；缺项目/供应商锚点的历史事实补建历史未归档锚点。",
        },
        {
            "target_model": "sc.ar.ap.project.summary",
            "domain": [],
            "carrying_type": "analysis_projection",
            "note": "进入项目/供应商账款分析口径。",
        },
    ],
    "sc.legacy.material.detail": [
        {
            "target_model": "sc.material.catalog",
            "domain": [("legacy_material_detail_id", "!=", False)],
            "carrying_type": "master_data_projection",
            "note": "历史材料明细全量投影为正式材料档案；产品模板只作为可交易物料提升目标，不承担全量历史承载。",
        },
    ],
    "sc.legacy.material.category": [
        {
            "target_model": "product.category",
            "domain": [("legacy_material_category_id", "!=", False)],
            "carrying_type": "master_data_projection",
            "note": "历史材料分类投影为产品分类，供材料档案/采购/库存正式分类字段消费。",
        },
    ],
    "sc.legacy.user.project.scope": [
        {
            "target_model": "project.project",
            "domain": [("legacy_project_id", "!=", False)],
            "carrying_type": "support_access_projection",
            "note": "历史项目范围通过项目主数据、用户映射和运行项目访问应用承载。",
        },
    ],
    "sc.legacy.department": [
        {
            "target_model": "hr.department",
            "domain": [],
            "carrying_type": "support_access_projection",
            "min_records": 10,
            "note": "历史组织部门已物化为 hr.department，供内部单位/部门字段承载。",
        },
    ],
    "sc.legacy.user.profile": [
        {
            "target_model": "res.users",
            "domain": [("login", "like", "legacy_%")],
            "carrying_type": "support_access_projection",
            "note": "历史用户资料投影为运行用户。",
        },
    ],
    "sc.legacy.user.role": [
        {
            "target_model": "res.users",
            "domain": [("login", "like", "legacy_%")],
            "carrying_type": "support_access_projection",
            "note": "历史角色通过运行用户/能力组承载。",
        },
    ],
    "sc.legacy.file.index": [
        {
            "target_model": "ir.attachment",
            "domain": [],
            "carrying_type": "legacy_evidence_custody",
            "note": "部分历史文件已进入附件保管；是否进入项目资料需业务目标决策。",
        },
    ],
    "sc.legacy.task.evidence": [
        {
            "target_model": "ir.attachment",
            "domain": [],
            "carrying_type": "legacy_evidence_custody",
            "note": "部分任务证据已进入附件保管；是否进入施工资料/项目资料需业务目标决策。",
        },
    ],
    "sc.legacy.report.inventory": [
        {
            "target_model": "sc.legacy.report.inventory",
            "domain": [],
            "carrying_type": "legacy_reference_retained",
            "note": "历史报表清单作为参考目录保留，不等同正式业务办理模型。",
        },
    ],
}

NON_BLOCKING_CARRYING_TYPES = {
    "formal_runtime_surface",
    "analysis_projection",
    "readonly_projection",
    "legacy_reference_retained",
    "legacy_evidence_custody",
    "master_data_projection",
    "support_access_projection",
}


def _serialize_domain(domain):
    return [list(item) if isinstance(item, tuple) else item for item in (domain or [])]


def _safe_count(model_name, domain=None):
    if not model_name or model_name not in env:
        return None
    fields = env[model_name]._fields
    for item in domain or []:
        if isinstance(item, (tuple, list)) and item and item[0] not in fields:
            return {"missing_field": item[0]}
    try:
        return int(env[model_name].sudo().with_context(active_test=False).search_count(domain or []))
    except Exception as exc:
        return {"error": "%s: %s" % (type(exc).__name__, str(exc)[:220])}


def _stored(model, field_name):
    field = model._fields.get(field_name)
    return bool(field and getattr(field, "store", True))


def _read_group_count(model_name, field_name, domain=None, limit=80):
    if model_name not in env:
        return []
    model = env[model_name].sudo()
    if field_name not in model._fields or not _stored(model, field_name):
        return []
    try:
        rows = model.read_group(domain or [], [field_name], [field_name], limit=limit)
    except Exception as exc:
        return [{"error": "%s: %s" % (type(exc).__name__, str(exc)[:180])}]
    result = []
    for row in rows:
        raw_value = row.get(field_name)
        if isinstance(raw_value, (list, tuple)):
            value = raw_value[-1] if raw_value else False
        else:
            value = raw_value
        if value:
            result.append({"value": value, "count": row.get("%s_count" % field_name, row.get("__count", 0))})
    return sorted(result, key=lambda item: (-int(item.get("count") or 0), str(item.get("value") or "")))


def _has_legacy_signal(model_name):
    if model_name not in env:
        return False
    fields = env[model_name]._fields
    return any(field in fields for field in SOURCE_FIELDS) or any(
        name.startswith("legacy_") or "_legacy_" in name for name in fields
    )


def _legacy_count_for_target(model_name):
    fields = env[model_name]._fields
    if "source_origin" in fields:
        return _safe_count(model_name, [("source_origin", "=", "legacy")])
    if "legacy_source_model" in fields:
        return _safe_count(model_name, [("legacy_source_model", "!=", False)])
    return None


def _safe_action_domain(menu):
    if not menu or not menu.action or menu.action._name != "ir.actions.act_window":
        return []
    raw = getattr(menu.action, "domain", None)
    if raw in (None, False, ""):
        return []
    try:
        parsed = safe_eval(raw) if isinstance(raw, str) else raw
    except Exception:
        return []
    if isinstance(parsed, tuple):
        parsed = list(parsed)
    return parsed if isinstance(parsed, list) else []


def _target_tree():
    seed_model = "sc.business.menu.taxonomy.seed"
    if seed_model not in env:
        return {}
    return env[seed_model].sudo().target_tree()


def _child_by_name(parent, name):
    return env["ir.ui.menu"].sudo().with_context(
        active_test=False,
        lang="zh_CN",
        **{"ir.ui.menu.full_list": True},
    ).search(
        [("parent_id", "=", parent.id), ("name", "=", name), ("active", "=", True)],
        limit=1,
    )


def _target_leaf_menus():
    root = env.ref("smart_construction_core.menu_sc_root", raise_if_not_found=False)
    if not root:
        return []
    root = root.sudo().with_context(active_test=False, lang="zh_CN")
    leaves = []
    for top_name, top_children in _target_tree().items():
        top = _child_by_name(root, top_name)
        for child_name, child_value in top_children.items():
            child = _child_by_name(top, child_name) if top else env["ir.ui.menu"].sudo()
            if isinstance(child_value, dict) and "model" not in child_value:
                for leaf_name in child_value:
                    leaf = _child_by_name(child, leaf_name) if child else env["ir.ui.menu"].sudo()
                    leaves.append(("%s/%s/%s" % (top_name, child_name, leaf_name), leaf))
            else:
                leaves.append(("%s/%s" % (top_name, child_name), child))
    return leaves


def _menu_model_index():
    by_model = defaultdict(list)
    for path, menu in _target_leaf_menus():
        if not menu or not menu.action or menu.action._name != "ir.actions.act_window":
            continue
        model_name = getattr(menu.action, "res_model", None)
        if not model_name:
            continue
        by_model[model_name].append(
            {
                "path": path,
                "menu_id": menu.id,
                "action_id": menu.action.id,
                "action_domain": _safe_action_domain(menu),
            }
        )
    return by_model


def _runtime_menu_model_index():
    root = env.ref("smart_construction_core.menu_sc_root", raise_if_not_found=False)
    if not root:
        return {}
    menu_model = env["ir.ui.menu"].sudo().with_context(
        active_test=False,
        lang="zh_CN",
        **{"ir.ui.menu.full_list": True},
    )
    by_model = defaultdict(list)

    def walk(parent, prefix):
        children = menu_model.search(
            [("parent_id", "=", parent.id), ("active", "=", True)],
            order="sequence,id",
        )
        for child in children:
            path = "%s/%s" % (prefix, child.name) if prefix else child.name
            if child.action and child.action._name == "ir.actions.act_window":
                model_name = getattr(child.action, "res_model", None)
                if model_name:
                    by_model[model_name].append(
                        {
                            "path": path,
                            "menu_id": child.id,
                            "action_id": child.action.id,
                            "action_domain": _safe_action_domain(child),
                        }
                    )
            walk(child, path)

    walk(root.sudo(), "")
    return by_model


def _legacy_sources():
    rows = []
    for ir_model in env["ir.model"].sudo().search([("model", "=like", LEGACY_PREFIX + "%")], order="model"):
        model_name = ir_model.model
        if model_name not in env:
            continue
        count = _safe_count(model_name)
        if count:
            rows.append({"model": model_name, "name": ir_model.name, "record_count": count})
    return rows


def _formal_targets(menu_index):
    rows = []
    for ir_model in env["ir.model"].sudo().search([], order="model"):
        model_name = ir_model.model
        if not model_name or model_name.startswith(LEGACY_PREFIX) or model_name not in env:
            continue
        if not _has_legacy_signal(model_name) and model_name not in menu_index:
            continue
        fields = env[model_name]._fields
        legacy_by_source_model = _read_group_count(model_name, "legacy_source_model")
        legacy_by_source_table = _read_group_count(model_name, "legacy_source_table")
        source_origin_distribution = _read_group_count(model_name, "source_origin")
        rows.append(
            {
                "model": model_name,
                "name": ir_model.name,
                "total_records": _safe_count(model_name),
                "legacy_records": _legacy_count_for_target(model_name),
                "has_legacy_signal": _has_legacy_signal(model_name),
                "source_fields": [field for field in SOURCE_FIELDS if field in fields],
                "legacy_by_source_model": legacy_by_source_model,
                "legacy_by_source_table": legacy_by_source_table,
                "source_origin_distribution": source_origin_distribution,
                "menu_paths": menu_index.get(model_name, []),
            }
        )
    return rows


def _carrying_index(target_rows):
    by_source = defaultdict(list)
    for target in target_rows:
        for item in target.get("legacy_by_source_model") or []:
            source_model = item.get("value")
            if not source_model:
                continue
            by_source[source_model].append(
                {
                    "target_model": target["model"],
                    "target_legacy_rows": item.get("count"),
                    "target_total_records": target.get("total_records"),
                    "menu_paths": target.get("menu_paths", []),
                }
            )
    return by_source


def _indirect_carrying_targets(source_model):
    result = []
    for rule in KNOWN_INDIRECT_CARRYING_RULES.get(source_model, []):
        count = _safe_count(rule["target_model"], rule.get("domain") or [])
        if not count:
            continue
        min_records = int(rule.get("min_records") or 0)
        if isinstance(count, int) and min_records and count < min_records:
            continue
        result.append(
            {
                "target_model": rule["target_model"],
                "target_records": count,
                "target_domain": _serialize_domain(rule.get("domain") or []),
                "carrying_type": rule["carrying_type"],
                "note": rule.get("note") or "",
            }
        )
    return result


def _source_state(direct_targets, indirect_targets):
    if direct_targets:
        return "carried_by_formal_business_model"
    if not indirect_targets:
        return "needs_mapping_or_projection"
    carrying_types = {target.get("carrying_type") for target in indirect_targets}
    if "formal_runtime_surface" in carrying_types:
        return "carried_by_indirect_formal_runtime_surface"
    if any(str(carrying_type).endswith("_partial") for carrying_type in carrying_types):
        return "partial_projection_needs_business_decision"
    if carrying_types and carrying_types.issubset(NON_BLOCKING_CARRYING_TYPES):
        return "classified_nonblocking_projection_or_reference"
    return "needs_mapping_or_projection"


def main():
    menu_index = _menu_model_index()
    runtime_menu_index = _runtime_menu_model_index()
    merged_menu_index = defaultdict(list)
    for model_name, paths in menu_index.items():
        merged_menu_index[model_name].extend(paths)
    for model_name, paths in runtime_menu_index.items():
        known = {(item.get("menu_id"), item.get("action_id")) for item in merged_menu_index[model_name]}
        for item in paths:
            key = (item.get("menu_id"), item.get("action_id"))
            if key not in known:
                merged_menu_index[model_name].append(item)
    legacy_sources = _legacy_sources()
    formal_targets = _formal_targets(merged_menu_index)
    carried_by_source = _carrying_index(formal_targets)

    source_rows = []
    gap_rows = []
    for source in legacy_sources:
        source_model = source["model"]
        carrying_targets = carried_by_source.get(source_model, [])
        indirect_targets = _indirect_carrying_targets(source_model)
        state = _source_state(carrying_targets, indirect_targets)
        row = {
            "legacy_source_model": source_model,
            "legacy_source_name": source.get("name"),
            "source_records": source.get("record_count"),
            "state": state,
            "carrying_targets": carrying_targets,
            "indirect_carrying_targets": indirect_targets,
        }
        source_rows.append(row)
        if state in ("needs_mapping_or_projection", "partial_projection_needs_business_decision"):
            gap_rows.append(row)

    target_without_menu = [
        row
        for row in formal_targets
        if row.get("legacy_records") and not row.get("menu_paths") and row.get("has_legacy_signal")
    ]
    target_without_target_tree_menu = [
        row
        for row in formal_targets
        if row.get("legacy_records") and not menu_index.get(row["model"]) and row.get("has_legacy_signal")
    ]
    menu_models_with_no_data = [
        row
        for row in formal_targets
        if row.get("menu_paths") and not row.get("total_records")
    ]

    status_counts = Counter(row["state"] for row in source_rows)
    result = {
        "ok": True,
        "database": env.cr.dbname,
        "legacy_source_count": len(legacy_sources),
        "formal_target_count": len(formal_targets),
        "menu_model_count": len(menu_index),
        "runtime_menu_model_count": len(runtime_menu_index),
        "status_counts": dict(sorted(status_counts.items())),
        "gap_count": len(gap_rows),
        "gap_rows": gap_rows,
        "target_without_menu_count": len(target_without_menu),
        "target_without_menu": target_without_menu,
        "target_without_target_tree_menu_count": len(target_without_target_tree_menu),
        "target_without_target_tree_menu": target_without_target_tree_menu,
        "menu_models_with_no_data_count": len(menu_models_with_no_data),
        "menu_models_with_no_data": menu_models_with_no_data,
        "legacy_sources": source_rows,
        "formal_targets": formal_targets,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


main()
