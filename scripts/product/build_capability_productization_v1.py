#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CAP_REGISTRY_FILE = ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py"
SCENE_CATALOG_FILE = ROOT / "docs" / "contract" / "exports" / "scene_catalog.json"
PRODUCT_DIR = ROOT / "docs" / "product"
TEMPLATE_DIR = PRODUCT_DIR / "templates"


GROUP_META = {
    "project_management": ("项目管理", "briefcase", 10),
    "contract_management": ("合同管理", "file-text", 20),
    "cost_management": ("成本管理", "calculator", 30),
    "finance_management": ("财务结算", "wallet", 40),
    "analytics": ("驾驶舱与分析", "chart", 50),
    "governance": ("风险与审批", "shield", 60),
    "material_management": ("数据字典与配置", "boxes", 70),
    "others": ("工作台与入口", "grid", 80),
}

DOMAIN_BY_GROUP = {
    "project_management": "project",
    "contract_management": "contract",
    "cost_management": "cost",
    "finance_management": "payment",
    "analytics": "dashboard",
    "governance": "workflow",
    "material_management": "dictionary",
    "others": "workspace",
}

MODEL_BY_DOMAIN = {
    "project": "project.project",
    "contract": "sc.contract",
    "cost": "sc.cost.ledger",
    "payment": "sc.payment.request",
    "dashboard": "sc.dashboard.metric",
    "workflow": "sc.workflow.ticket",
    "dictionary": "sc.dictionary.item",
    "workspace": "smart_core.workspace",
}

ROLE_ALIAS = {
    "pm": "project_manager",
    "finance": "finance_manager",
    "executive": "construction_manager",
    "owner": "owner_manager",
}


@dataclass
class CapabilityDef:
    key: str
    label: str
    hint: str
    group_key: str
    scene_key: str
    required_roles: list[str]
    status: str
    required_groups: list[str]
    intent: str


def _literal(node: ast.AST) -> Any:
    return ast.literal_eval(node)


def _extract_capabilities() -> list[CapabilityDef]:
    tree = ast.parse(CAP_REGISTRY_FILE.read_text(encoding="utf-8"))
    capabilities: list[CapabilityDef] = []
    target_list_node: ast.List | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "_CAPABILITIES" for t in node.targets):
                if isinstance(node.value, ast.List):
                    target_list_node = node.value
                break
        if isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "_CAPABILITIES":
                if isinstance(node.value, ast.List):
                    target_list_node = node.value
                break

    if not target_list_node:
        return capabilities

    for item in target_list_node.elts:
            if not isinstance(item, ast.Call):
                continue
            if not isinstance(item.func, ast.Name) or item.func.id != "_cap":
                continue
            if len(item.args) < 5:
                continue
            key = str(_literal(item.args[0]))
            label = str(_literal(item.args[1]))
            hint = str(_literal(item.args[2]))
            group_key = str(_literal(item.args[3]))
            scene_key = str(_literal(item.args[4]))
            required_roles: list[str] = []
            required_groups: list[str] = []
            status = "ga"
            intent = "ui.contract"
            for kw in item.keywords:
                if kw.arg == "required_roles":
                    required_roles = [str(x) for x in _literal(kw.value)]
                elif kw.arg == "required_groups":
                    required_groups = [str(x) for x in _literal(kw.value)]
                elif kw.arg == "status":
                    status = str(_literal(kw.value))
            capabilities.append(
                CapabilityDef(
                    key=key,
                    label=label,
                    hint=hint,
                    group_key=group_key,
                    scene_key=scene_key,
                    required_roles=required_roles,
                    status=status,
                    required_groups=required_groups,
                    intent=intent,
                )
            )
    return capabilities


def _load_scene_catalog() -> dict[str, Any]:
    raw = json.loads(SCENE_CATALOG_FILE.read_text(encoding="utf-8"))
    scenes = raw.get("scenes")
    if not isinstance(scenes, list):
        scenes = []
    return {"meta": raw, "scenes": scenes}


def _status_to_product(status: str) -> str:
    normalized = str(status or "").strip().lower()
    if normalized == "ga":
        return "ready"
    if normalized in {"beta", "alpha"}:
        return "partial"
    return "planned"


def _surface_support(group_key: str) -> list[str]:
    if group_key in {"analytics", "governance"}:
        return ["governed", "hud"]
    return ["governed", "native", "hud"]


def _role_scope(roles: list[str]) -> list[str]:
    if not roles:
        return ["通用"]
    out = set()
    for role in roles:
        if role == "owner":
            out.add("业主")
        elif role in {"pm", "finance", "executive"}:
            out.add("施工")
        else:
            out.add("通用")
    if "施工" in out and "业主" in out:
        out.add("通用")
    return sorted(out)


def _scene_type(layout_kind: str) -> str:
    kind = str(layout_kind or "").strip().lower()
    return {
        "workspace": "workspace",
        "list": "list",
        "ledger": "monitor",
        "record": "detail",
    }.get(kind, "dashboard")


def _business_goal(scene_key: str) -> str:
    key = scene_key.lower()
    if key.startswith("projects."):
        return "项目全周期经营与执行管理"
    if key.startswith("finance."):
        return "资金、支付与结算闭环"
    if key.startswith("cost."):
        return "成本与预算执行控制"
    if key.startswith("contract."):
        return "合同执行与结算协同"
    if key.startswith("portal."):
        return "运营治理与工作台入口"
    return "业务场景操作入口"


def _target_role(scene_key: str) -> list[str]:
    key = scene_key.lower()
    if key.startswith("finance."):
        return ["finance_manager", "construction_manager"]
    if key.startswith("projects."):
        return ["project_manager", "construction_manager"]
    if key.startswith("cost."):
        return ["project_manager", "finance_manager"]
    if key.startswith("contract."):
        return ["project_manager", "finance_manager"]
    if key.startswith("portal."):
        return ["construction_manager", "project_manager", "finance_manager"]
    return ["construction_manager"]


def _entry_type(scene_key: str) -> str:
    if scene_key in {"portal.dashboard", "projects.dashboard", "my_work.workspace"}:
        return "home"
    if scene_key.startswith("projects.") or scene_key.startswith("finance."):
        return "menu"
    return "shortcut"


def _capability_keys_by_group(capabilities: list[CapabilityDef]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for cap in capabilities:
        grouped[cap.group_key].append(cap.key)
    return {key: sorted(values) for key, values in grouped.items()}


def _fallback_scene_capabilities(scene_key: str, grouped: dict[str, list[str]]) -> list[str]:
    key = str(scene_key or "").strip().lower()
    if not key:
        return []
    if key in {"contracts.monitor", "contract.center"}:
        return grouped.get("contract_management", [])
    if key in {"risk.center", "risk.monitor"}:
        return sorted(
            set(
                [
                    *grouped.get("governance", []),
                    *[x for x in grouped.get("project_management", []) if ".risk." in x or x.endswith(".risk.list")],
                ]
            )
        )
    if key in {"my_work.workspace", "portal.dashboard"}:
        return sorted(set([*grouped.get("others", []), *grouped.get("governance", [])]))
    if key == "task.center":
        return [x for x in grouped.get("project_management", []) if ".task." in x]
    if key == "data.dictionary":
        return grouped.get("material_management", [])
    if key.startswith("projects."):
        return sorted(set([*grouped.get("project_management", []), *grouped.get("analytics", [])]))
    if key.startswith("finance.") or key.startswith("payments."):
        return sorted(set([*grouped.get("finance_management", []), *grouped.get("contract_management", [])]))
    if key.startswith("cost."):
        return grouped.get("cost_management", [])
    if key.startswith("contract."):
        return grouped.get("contract_management", [])
    return []


def _capability_catalog(capabilities: list[CapabilityDef]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for cap in capabilities:
        domain = DOMAIN_BY_GROUP.get(cap.group_key, "project")
        items.append(
            {
                "capability_key": cap.key,
                "name": cap.label,
                "domain": domain,
                "description": cap.hint,
                "source_model": MODEL_BY_DOMAIN.get(domain, "project.project"),
                "main_action": {"intent": cap.intent},
                "main_menu": {"group_key": cap.group_key},
                "main_scene": cap.scene_key,
                "status": _status_to_product(cap.status),
                "surface_support": _surface_support(cap.group_key),
                "role_scope": _role_scope(cap.required_roles),
                "required_roles": [ROLE_ALIAS.get(r, r) for r in cap.required_roles],
                "required_groups": cap.required_groups,
            }
        )
    return {
        "version": "v1",
        "generated_on": date.today().isoformat(),
        "capability_count": len(items),
        "capabilities": sorted(items, key=lambda x: x["capability_key"]),
    }


def _capability_grouping(capabilities: list[CapabilityDef]) -> dict[str, Any]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for cap in capabilities:
        grouped[cap.group_key].append(cap.key)
    groups: list[dict[str, Any]] = []
    for key, (label, icon, sequence) in GROUP_META.items():
        groups.append(
            {
                "group_key": key,
                "group_name": label,
                "group_icon": icon,
                "sequence": sequence,
                "description": f"{label}能力集合",
                "capability_count": len(grouped.get(key, [])),
                "capability_keys": sorted(grouped.get(key, [])),
            }
        )
    return {"version": "v1", "groups": groups}


def _scene_catalog_v2(
    scene_rows: list[dict[str, Any]],
    capabilities: list[CapabilityDef],
) -> dict[str, Any]:
    grouped = _capability_keys_by_group(capabilities)
    cap_by_scene: dict[str, list[str]] = defaultdict(list)
    for cap in capabilities:
        cap_by_scene[cap.scene_key].append(cap.key)
    out_rows: list[dict[str, Any]] = []
    for row in scene_rows:
        scene_key = str(row.get("scene_key") or "").strip()
        if not scene_key:
            continue
        layout = row.get("layout") if isinstance(row.get("layout"), dict) else {}
        renderability = row.get("renderability") if isinstance(row.get("renderability"), dict) else {}
        primary_caps = sorted(cap_by_scene.get(scene_key, []))
        if not primary_caps:
            primary_caps = _fallback_scene_capabilities(scene_key, grouped)
        out_rows.append(
            {
                "scene_key": scene_key,
                "scene_name": str(row.get("name") or scene_key),
                "scene_type": _scene_type(layout.get("kind")),
                "target_role": _target_role(scene_key),
                "business_goal": _business_goal(scene_key),
                "primary_capabilities": primary_caps,
                "entry_type": _entry_type(scene_key),
                "status": "ready"
                if bool(renderability.get("is_renderable")) and bool(renderability.get("is_interaction_ready"))
                else "partial",
                "is_product_scene": _is_product_scene(scene_key),
            }
        )
    existing = {item["scene_key"] for item in out_rows}
    # Productized aliases ensure core business scenes stay stable even when runtime scene keys drift.
    alias_rows = [
        ("projects.execution", "项目执行", "workspace", "projects.ledger"),
        ("projects.detail", "项目详情", "detail", "projects.intake"),
        ("contracts.monitor", "合同监控", "monitor", "contract.center"),
        ("cost.control", "成本控制", "monitor", "cost.project_cost_ledger"),
        ("payments.approval", "支付审批", "workspace", "finance.payment_requests"),
        ("risk.center", "风险中心", "monitor", "risk.monitor"),
        ("my_work.workspace", "我的工作台", "workspace", "portal.dashboard"),
    ]
    for alias_key, alias_name, scene_type, source_scene in alias_rows:
        if alias_key in existing:
            continue
        alias_caps = sorted(cap_by_scene.get(source_scene, []))
        if not alias_caps:
            alias_caps = _fallback_scene_capabilities(alias_key, grouped)
        out_rows.append(
            {
                "scene_key": alias_key,
                "scene_name": alias_name,
                "scene_type": scene_type,
                "target_role": _target_role(source_scene),
                "business_goal": _business_goal(source_scene),
                "primary_capabilities": alias_caps,
                "entry_type": "menu" if alias_key != "my_work.workspace" else "my_work",
                "status": "ready" if alias_caps else "partial",
                "alias_of": source_scene,
                "is_product_scene": True,
            }
        )
    return {
        "version": "v2",
        "generated_on": date.today().isoformat(),
        "scene_count": len(out_rows),
        "scenes": sorted(out_rows, key=lambda x: x["scene_key"]),
    }


def _capability_scene_mapping(
    catalog: dict[str, Any],
    scene_catalog_v2: dict[str, Any],
) -> dict[str, Any]:
    caps = catalog.get("capabilities") if isinstance(catalog.get("capabilities"), list) else []
    scenes = scene_catalog_v2.get("scenes") if isinstance(scene_catalog_v2.get("scenes"), list) else []
    scene_to_caps: dict[str, list[dict[str, str]]] = defaultdict(list)
    cap_to_scenes: dict[str, list[dict[str, str]]] = defaultdict(list)
    scene_primary_map = {
        str(row.get("scene_key") or ""): [str(x) for x in (row.get("primary_capabilities") or []) if str(x)]
        for row in scenes
        if isinstance(row, dict)
    }
    for cap in caps:
        cap_key = str(cap.get("capability_key") or "")
        scene_key = str(cap.get("main_scene") or "")
        if not cap_key or not scene_key:
            continue
        item = {"capability_key": cap_key, "role": "primary"}
        scene_to_caps[scene_key].append(item)
        cap_to_scenes[cap_key].append({"scene_key": scene_key, "role": "primary"})

    # Add productized/fallback scene mapping from scene catalog definitions.
    known_cap_keys = {str(cap.get("capability_key") or "") for cap in caps}
    for scene_key, cap_keys in scene_primary_map.items():
        for cap_key in cap_keys:
            if cap_key not in known_cap_keys:
                continue
            if cap_key not in {item["capability_key"] for item in scene_to_caps.get(scene_key, [])}:
                scene_to_caps[scene_key].append({"capability_key": cap_key, "role": "supporting"})
            if scene_key not in {item["scene_key"] for item in cap_to_scenes.get(cap_key, [])}:
                cap_to_scenes[cap_key].append({"scene_key": scene_key, "role": "supporting"})

    known_scene_keys = {str(row.get("scene_key") or "") for row in scenes}
    orphan_caps = sorted([k for k, v in cap_to_scenes.items() if not v])
    void_scenes = sorted([k for k in known_scene_keys if k and not scene_to_caps.get(k)])
    product_scene_keys = sorted([k for k in known_scene_keys if _is_product_scene(k)])
    product_void_scenes = sorted([k for k in product_scene_keys if k not in scene_to_caps])

    mapping_rate_all = round((len(known_scene_keys) - len(void_scenes)) / len(known_scene_keys), 4) if known_scene_keys else 0.0
    mapping_rate_product = (
        round((len(product_scene_keys) - len(product_void_scenes)) / len(product_scene_keys), 4)
        if product_scene_keys
        else 0.0
    )

    return {
        "version": "v1",
        "generated_on": date.today().isoformat(),
        "scene_to_capabilities": [
            {"scene_key": key, "capabilities": sorted(vals, key=lambda x: x["capability_key"])}
            for key, vals in sorted(scene_to_caps.items(), key=lambda x: x[0])
        ],
        "capability_to_scenes": [
            {"capability_key": key, "scenes": sorted(vals, key=lambda x: x["scene_key"])}
            for key, vals in sorted(cap_to_scenes.items(), key=lambda x: x[0])
        ],
        "orphan_capabilities": orphan_caps,
        "void_scenes": void_scenes,
        "product_scene_to_capabilities": [
            {"scene_key": key, "capabilities": sorted(scene_to_caps.get(key, []), key=lambda x: x["capability_key"])}
            for key in product_scene_keys
            if scene_to_caps.get(key)
        ],
        "product_void_scenes": product_void_scenes,
        "quality_summary": {
            "scene_total": len(known_scene_keys),
            "scene_mapped": len(known_scene_keys) - len(void_scenes),
            "mapping_rate_all": mapping_rate_all,
            "product_scene_total": len(product_scene_keys),
            "product_scene_mapped": len(product_scene_keys) - len(product_void_scenes),
            "mapping_rate_product": mapping_rate_product,
            "orphan_capability_count": len(orphan_caps),
        },
    }


def _role_scene_matrix(scene_catalog_v2: dict[str, Any]) -> dict[str, Any]:
    roles = [
        "construction_manager",
        "project_manager",
        "owner_manager",
        "finance_manager",
        "risk_manager",
        "regulator_viewer",
    ]
    defaults = {
        "construction_manager": "projects.dashboard",
        "project_manager": "projects.execution",
        "owner_manager": "projects.dashboard",
        "finance_manager": "payments.approval",
        "risk_manager": "risk.center",
        "regulator_viewer": "risk.center",
    }
    high_freq = {
        "construction_manager": ["projects.dashboard", "contracts.monitor", "cost.control"],
        "project_manager": ["projects.execution", "projects.detail", "my_work.workspace"],
        "owner_manager": ["projects.dashboard", "contracts.monitor", "payments.approval"],
        "finance_manager": ["payments.approval", "cost.control", "contracts.monitor"],
        "risk_manager": ["risk.center", "my_work.workspace", "projects.detail"],
        "regulator_viewer": ["risk.center", "projects.dashboard"],
    }
    disabled = {
        "construction_manager": [],
        "project_manager": [],
        "owner_manager": ["governance.runtime.audit"],
        "finance_manager": [],
        "risk_manager": ["finance.settlement_orders"],
        "regulator_viewer": ["finance.payment_requests", "cost.project_budget"],
    }
    role_rows = []
    for role in roles:
        role_rows.append(
            {
                "role_key": role,
                "home_scene": defaults.get(role, "projects.dashboard"),
                "high_frequency_scenes": high_freq.get(role, []),
                "disabled_scenes": disabled.get(role, []),
                "default_capability_groups": _default_groups_for_role(role),
            }
        )
    scene_keys = {str(row.get("scene_key") or "") for row in scene_catalog_v2.get("scenes", [])}
    for row in role_rows:
        row["home_scene_ready"] = row["home_scene"] in scene_keys
    return {"version": "v1", "roles": role_rows}


def _default_groups_for_role(role_key: str) -> list[str]:
    mapping = {
        "construction_manager": ["project_management", "contract_management", "cost_management", "analytics"],
        "project_manager": ["project_management", "cost_management", "contract_management", "others"],
        "owner_manager": ["project_management", "contract_management", "finance_management", "analytics"],
        "finance_manager": ["finance_management", "contract_management", "cost_management", "analytics"],
        "risk_manager": ["governance", "analytics", "project_management"],
        "regulator_viewer": ["governance", "analytics"],
    }
    return mapping.get(role_key, ["project_management"])


def _capability_maturity(catalog: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
    map_by_cap = {
        str(item.get("capability_key") or ""): item.get("scenes") or []
        for item in (mapping.get("capability_to_scenes") or [])
        if isinstance(item, dict)
    }
    rows = []
    for cap in catalog.get("capabilities", []):
        key = str(cap.get("capability_key") or "")
        status = str(cap.get("status") or "planned")
        scenes = map_by_cap.get(key, [])
        has_scene = bool(scenes)
        if status == "ready" and has_scene:
            maturity = "productized"
        elif status in {"ready", "partial"} and has_scene:
            maturity = "ready"
        elif status in {"ready", "partial"}:
            maturity = "partial"
        else:
            maturity = "planned"
        rows.append(
            {
                "capability_key": key,
                "name": cap.get("name"),
                "status": status,
                "scene_bound": has_scene,
                "maturity": maturity,
            }
        )
    return {"version": "v1", "rows": rows}


def _capability_gap_backlog(
    catalog: dict[str, Any],
    scene_catalog_v2: dict[str, Any],
    mapping: dict[str, Any],
    maturity: dict[str, Any],
) -> dict[str, Any]:
    scene_keys = {
        str(item.get("scene_key") or "")
        for item in scene_catalog_v2.get("scenes", [])
        if isinstance(item, dict) and _is_product_scene(str(item.get("scene_key") or ""))
    }
    cap_to_scene = {
        str(item.get("capability_key") or ""): item.get("scenes") or []
        for item in mapping.get("capability_to_scenes", [])
        if isinstance(item, dict)
    }
    issues: list[dict[str, Any]] = []
    for cap in catalog.get("capabilities", []):
        key = str(cap.get("capability_key") or "")
        scenes = cap_to_scene.get(key, [])
        if not scenes:
            issues.append(
                {
                    "priority": "P0",
                    "type": "有能力无场景",
                    "item_key": key,
                    "description": "能力存在但未绑定任何 scene，无法进入产品入口。",
                }
            )
    for scene_key in mapping.get("void_scenes", []):
        if not _is_product_scene(str(scene_key or "")):
            continue
        issues.append(
            {
                "priority": "P1",
                "type": "有场景无能力",
                "item_key": scene_key,
                "description": "scene 可访问但未映射 capability，产品语义不完整。",
            }
        )
    for row in maturity.get("rows", []):
        if str(row.get("maturity")) in {"planned", "partial"}:
            issues.append(
                {
                    "priority": "P2",
                    "type": "能力成熟度不足",
                    "item_key": str(row.get("capability_key") or ""),
                    "description": "能力已存在但尚未达到 productized 标准。",
                }
            )
    issues.sort(key=lambda x: ("P0", "P1", "P2").index(x["priority"]))
    return {"version": "v1", "generated_on": date.today().isoformat(), "issues": issues}


def _is_product_scene(scene_key: str) -> bool:
    key = str(scene_key or "").strip().lower()
    if not key:
        return False
    if "__pkg" in key:
        return False
    if key.startswith("default"):
        return False
    return True


def _product_scene_catalog(scene_catalog_v2: dict[str, Any]) -> dict[str, Any]:
    rows = scene_catalog_v2.get("scenes") if isinstance(scene_catalog_v2.get("scenes"), list) else []
    product_rows = [row for row in rows if isinstance(row, dict) and _is_product_scene(str(row.get("scene_key") or ""))]
    return {
        "version": "v1",
        "generated_on": scene_catalog_v2.get("generated_on"),
        "scene_count": len(product_rows),
        "scenes": sorted(product_rows, key=lambda x: str(x.get("scene_key") or "")),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _md_capability_catalog(payload: dict[str, Any]) -> str:
    rows = payload.get("capabilities", [])
    lines = [
        "# Capability Catalog v1",
        "",
        f"- generated_on: {payload.get('generated_on')}",
        f"- capability_count: {payload.get('capability_count')}",
        "",
        "| capability_key | name | domain | source_model | main_scene | status | role_scope |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['capability_key']} | {row['name']} | {row['domain']} | {row['source_model']} | {row['main_scene']} | {row['status']} | {','.join(row['role_scope'])} |"
        )
    return "\n".join(lines)


def _md_capability_grouping(payload: dict[str, Any]) -> str:
    lines = [
        "# Capability Grouping v1",
        "",
        "| group_key | group_name | icon | sequence | capability_count |",
        "|---|---|---|---:|---:|",
    ]
    for row in payload.get("groups", []):
        lines.append(
            f"| {row['group_key']} | {row['group_name']} | {row['group_icon']} | {row['sequence']} | {row['capability_count']} |"
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 菜单、首页、工作台入口按以上 group_key 组织。",
            "- 每个 capability 必须归属一个 group_key，禁止无组能力。",
        ]
    )
    return "\n".join(lines)


def _md_scene_catalog(payload: dict[str, Any]) -> str:
    lines = [
        "# Scene Catalog v2",
        "",
        f"- generated_on: {payload.get('generated_on')}",
        f"- scene_count: {payload.get('scene_count')}",
        "",
        "| scene_key | scene_name | scene_type | target_role | business_goal | primary_capabilities | entry_type | status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in payload.get("scenes", []):
        lines.append(
            f"| {row['scene_key']} | {row['scene_name']} | {row['scene_type']} | {','.join(row['target_role'])} | {row['business_goal']} | {','.join(row['primary_capabilities']) or '-'} | {row['entry_type']} | {row['status']} |"
        )
    return "\n".join(lines)


def _md_capability_scene_mapping(payload: dict[str, Any]) -> str:
    summary = payload.get("quality_summary") if isinstance(payload.get("quality_summary"), dict) else {}
    lines = [
        "# Capability Scene Mapping v1",
        "",
        f"- generated_on: {payload.get('generated_on')}",
        f"- orphan_capabilities: {len(payload.get('orphan_capabilities', []))}",
        f"- void_scenes: {len(payload.get('void_scenes', []))}",
        f"- product_void_scenes: {len(payload.get('product_void_scenes', []))}",
        f"- mapping_rate_all: {summary.get('mapping_rate_all', 0)}",
        f"- mapping_rate_product: {summary.get('mapping_rate_product', 0)}",
        "",
        "## Scene -> Capabilities",
        "",
        "| scene_key | capabilities(primary) |",
        "|---|---|",
    ]
    for row in payload.get("scene_to_capabilities", []):
        caps = ",".join(item["capability_key"] for item in row.get("capabilities", []))
        lines.append(f"| {row['scene_key']} | {caps or '-'} |")
    lines.extend(
        [
            "",
            "## Gaps",
            "",
            f"- orphan_capabilities: {', '.join(payload.get('orphan_capabilities', [])) or 'none'}",
            f"- void_scenes: {', '.join(payload.get('void_scenes', [])[:20]) or 'none'}",
            f"- product_void_scenes: {', '.join(payload.get('product_void_scenes', [])[:20]) or 'none'}",
        ]
    )
    return "\n".join(lines)


def _md_role_scene_matrix(payload: dict[str, Any]) -> str:
    lines = [
        "# Role Scene Matrix v1",
        "",
        "| role_key | home_scene | high_frequency_scenes | disabled_scenes | default_capability_groups |",
        "|---|---|---|---|---|",
    ]
    for row in payload.get("roles", []):
        lines.append(
            f"| {row['role_key']} | {row['home_scene']} | {','.join(row['high_frequency_scenes']) or '-'} | {','.join(row['disabled_scenes']) or '-'} | {','.join(row['default_capability_groups'])} |"
        )
    return "\n".join(lines)


def _md_capability_maturity(payload: dict[str, Any]) -> str:
    lines = [
        "# Capability Maturity Matrix v1",
        "",
        "| capability_key | status | scene_bound | maturity |",
        "|---|---|---|---|",
    ]
    for row in payload.get("rows", []):
        lines.append(
            f"| {row['capability_key']} | {row['status']} | {str(bool(row['scene_bound'])).lower()} | {row['maturity']} |"
        )
    lines.extend(
        [
            "",
            "## 成熟度标准",
            "",
            "- planned: 仅定义，未形成可用入口",
            "- partial: 部分可用，映射或入口不完整",
            "- ready: 可用且已绑定场景",
            "- productized: 可用 + 场景绑定 + 产品入口稳定",
        ]
    )
    return "\n".join(lines)


def _md_capability_gap_backlog(payload: dict[str, Any]) -> str:
    lines = [
        "# Capability Gap Backlog v1",
        "",
        f"- generated_on: {payload.get('generated_on')}",
        "",
        "| priority | type | item_key | description |",
        "|---|---|---|---|",
    ]
    for row in payload.get("issues", []):
        lines.append(f"| {row['priority']} | {row['type']} | {row['item_key']} | {row['description']} |")
    return "\n".join(lines)


def _md_entry_registry_quality(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    issues = payload.get("issues") if isinstance(payload.get("issues"), dict) else {}
    lines = [
        "# Entry Registry Quality Report v1",
        "",
        f"- generated_on: {payload.get('generated_on')}",
        f"- status: {payload.get('status')}",
        "",
        "## Summary",
        "",
        f"- product_scene_total: {summary.get('product_scene_total', 0)}",
        f"- scene_entry_total: {summary.get('scene_entry_total', 0)}",
        f"- scene_entry_coverage: {summary.get('scene_entry_coverage', 0)}",
        f"- capability_total: {summary.get('capability_total', 0)}",
        f"- capability_entry_total: {summary.get('capability_entry_total', 0)}",
        f"- capability_entry_coverage: {summary.get('capability_entry_coverage', 0)}",
        f"- role_count: {summary.get('role_count', 0)}",
        "",
        "## Issues",
        "",
        f"- scene_entry_missing: {', '.join(issues.get('scene_entry_missing', [])[:20]) or 'none'}",
        f"- capability_entry_missing: {', '.join(issues.get('capability_entry_missing', [])[:20]) or 'none'}",
    ]
    role_missing = issues.get("role_home_missing", [])
    if role_missing:
        role_lines = ", ".join(f"{item.get('role_key')}:{item.get('home_scene')}" for item in role_missing[:10])
        lines.append(f"- role_home_missing: {role_lines}")
    else:
        lines.append("- role_home_missing: none")
    return "\n".join(lines)


def _construction_template_md(role_scene_matrix: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Construction Enterprise Template v1",
            "",
            "## 默认角色集合",
            "",
            "- construction_manager",
            "- project_manager",
            "- finance_manager",
            "- risk_manager",
            "",
            "## 默认 Scene 集合",
            "",
            "- projects.dashboard",
            "- projects.execution",
            "- projects.detail",
            "- contracts.monitor",
            "- cost.control",
            "- payments.approval",
            "- risk.center",
            "- my_work.workspace",
            "",
            "## 默认 Capability Groups",
            "",
            "- project_management",
            "- contract_management",
            "- cost_management",
            "- finance_management",
            "- analytics",
            "- governance",
            "",
            "## 首页入口布局",
            "",
            "- 我的工作",
            "- 核心场景入口",
            "- 关键风险",
            "- 经营驾驶舱",
            "- 能力快捷入口",
            "",
            "## 角色入口策略",
            "",
            "以下策略来自 role_scene_matrix_v1：",
            "",
            *[
                f"- {row['role_key']}: home={row['home_scene']}, 高频={','.join(row['high_frequency_scenes']) or '-'}"
                for row in role_scene_matrix.get("roles", [])
                if row.get("role_key") in {"construction_manager", "project_manager", "finance_manager", "risk_manager"}
            ],
        ]
    )


def _owner_template_md() -> str:
    return "\n".join(
        [
            "# Owner Management Template Draft v1",
            "",
            "## 目标能力分组",
            "",
            "- 项目监督（project oversight）",
            "- 合同执行监控（contract execution）",
            "- 投资控制（investment control）",
            "- 支付审核（payment approval）",
            "- 风险预警（risk early warning）",
            "",
            "## 目标首页 Scene",
            "",
            "- owner.dashboard",
            "- contracts.monitor",
            "- payments.approval",
            "- risk.center",
            "",
            "## 角色矩阵（草案）",
            "",
            "- owner_manager: 首页=owner.dashboard, 高频=contracts.monitor,payments.approval",
            "- owner_finance: 首页=payments.approval, 高频=cost.control,contracts.monitor",
            "- owner_exec: 首页=owner.dashboard, 高频=risk.center,projects.dashboard",
            "",
            "## 迁移原则",
            "",
            "- 不改底层五层架构",
            "- 通过 capability + scene 重编排实现业主管理模式",
            "- 前端入口按 governed surface 消费，不绕过 contract",
        ]
    )


def _construction_template_json(role_scene_matrix: dict[str, Any]) -> dict[str, Any]:
    role_rows = role_scene_matrix.get("roles") if isinstance(role_scene_matrix.get("roles"), list) else []
    return {
        "template_key": "construction_enterprise",
        "version": "v1",
        "default_roles": ["construction_manager", "project_manager", "finance_manager", "risk_manager"],
        "default_scenes": [
            "projects.dashboard",
            "projects.execution",
            "projects.detail",
            "contracts.monitor",
            "cost.control",
            "payments.approval",
            "risk.center",
            "my_work.workspace",
        ],
        "default_capability_groups": [
            "project_management",
            "contract_management",
            "cost_management",
            "finance_management",
            "analytics",
            "governance",
        ],
        "home_layout_sections": [
            "my_work",
            "core_scenes",
            "key_risks",
            "business_dashboard",
            "capability_shortcuts",
        ],
        "role_entry_policy": [
            {
                "role_key": row.get("role_key"),
                "home_scene": row.get("home_scene"),
                "high_frequency_scenes": row.get("high_frequency_scenes") or [],
                "disabled_scenes": row.get("disabled_scenes") or [],
            }
            for row in role_rows
            if row.get("role_key") in {"construction_manager", "project_manager", "finance_manager", "risk_manager"}
        ],
    }


def _owner_template_json() -> dict[str, Any]:
    return {
        "template_key": "owner_management_draft",
        "version": "v1-draft",
        "capability_groups": [
            "project_oversight",
            "contract_execution_monitoring",
            "investment_control",
            "payment_approval",
            "risk_early_warning",
        ],
        "home_scenes": [
            "owner.dashboard",
            "contracts.monitor",
            "payments.approval",
            "risk.center",
        ],
        "role_matrix": [
            {"role_key": "owner_manager", "home_scene": "owner.dashboard", "high_frequency_scenes": ["contracts.monitor", "payments.approval"]},
            {"role_key": "owner_finance", "home_scene": "payments.approval", "high_frequency_scenes": ["cost.control", "contracts.monitor"]},
            {"role_key": "owner_exec", "home_scene": "owner.dashboard", "high_frequency_scenes": ["risk.center", "projects.dashboard"]},
        ],
        "migration_principles": [
            "reuse_five_layer_architecture",
            "reorchestrate_by_capability_and_scene",
            "consume_governed_surface_only",
        ],
    }


def _scene_entry_registry(
    scene_catalog_product: dict[str, Any],
    mapping: dict[str, Any],
) -> dict[str, Any]:
    scenes = scene_catalog_product.get("scenes") if isinstance(scene_catalog_product.get("scenes"), list) else []
    scene_caps_map = {
        str(row.get("scene_key") or ""): [str(item.get("capability_key") or "") for item in (row.get("capabilities") or [])]
        for row in (mapping.get("product_scene_to_capabilities") or [])
        if isinstance(row, dict)
    }
    entries: list[dict[str, Any]] = []
    for scene in scenes:
        scene_key = str(scene.get("scene_key") or "").strip()
        if not scene_key:
            continue
        caps = [x for x in scene_caps_map.get(scene_key, []) if x]
        entries.append(
            {
                "entry_key": f"scene::{scene_key}",
                "entry_source": "scene",
                "scene_key": scene_key,
                "scene_name": str(scene.get("scene_name") or scene_key),
                "entry_type": str(scene.get("entry_type") or "menu"),
                "target_role": scene.get("target_role") or [],
                "required_capabilities": caps,
                "status": str(scene.get("status") or "ready"),
            }
        )
    return {
        "version": "v1",
        "generated_on": date.today().isoformat(),
        "entry_count": len(entries),
        "entries": sorted(entries, key=lambda x: x["entry_key"]),
    }


def _capability_entry_registry(
    capability_catalog: dict[str, Any],
    mapping: dict[str, Any],
) -> dict[str, Any]:
    cap_to_scenes = {
        str(row.get("capability_key") or ""): [str(item.get("scene_key") or "") for item in (row.get("scenes") or [])]
        for row in (mapping.get("capability_to_scenes") or [])
        if isinstance(row, dict)
    }
    entries: list[dict[str, Any]] = []
    for cap in capability_catalog.get("capabilities", []):
        cap_key = str(cap.get("capability_key") or "").strip()
        if not cap_key:
            continue
        scene_keys = [x for x in cap_to_scenes.get(cap_key, []) if x and _is_product_scene(x)]
        primary_scene = str(cap.get("main_scene") or "").strip()
        if primary_scene and _is_product_scene(primary_scene) and primary_scene not in scene_keys:
            scene_keys = [primary_scene, *scene_keys]
        entries.append(
            {
                "entry_key": f"capability::{cap_key}",
                "entry_source": "capability",
                "capability_key": cap_key,
                "name": str(cap.get("name") or cap_key),
                "domain": str(cap.get("domain") or ""),
                "group_key": str((cap.get("main_menu") or {}).get("group_key") or ""),
                "scene_keys": sorted(set(scene_keys)),
                "role_scope": cap.get("role_scope") or [],
                "status": str(cap.get("status") or "ready"),
            }
        )
    return {
        "version": "v1",
        "generated_on": date.today().isoformat(),
        "entry_count": len(entries),
        "entries": sorted(entries, key=lambda x: x["entry_key"]),
    }


def _entry_registry_quality_report(
    scene_catalog_product: dict[str, Any],
    capability_catalog: dict[str, Any],
    scene_entry_registry: dict[str, Any],
    capability_entry_registry: dict[str, Any],
    role_scene_matrix: dict[str, Any],
) -> dict[str, Any]:
    product_scenes = scene_catalog_product.get("scenes") if isinstance(scene_catalog_product.get("scenes"), list) else []
    capabilities = capability_catalog.get("capabilities") if isinstance(capability_catalog.get("capabilities"), list) else []
    scene_entries = scene_entry_registry.get("entries") if isinstance(scene_entry_registry.get("entries"), list) else []
    capability_entries = capability_entry_registry.get("entries") if isinstance(capability_entry_registry.get("entries"), list) else []
    role_rows = role_scene_matrix.get("roles") if isinstance(role_scene_matrix.get("roles"), list) else []

    product_scene_keys = {str((row or {}).get("scene_key") or "").strip() for row in product_scenes if str((row or {}).get("scene_key") or "").strip()}
    capability_keys = {str((row or {}).get("capability_key") or "").strip() for row in capabilities if str((row or {}).get("capability_key") or "").strip()}
    scene_entry_keys = {str((row or {}).get("scene_key") or "").strip() for row in scene_entries if str((row or {}).get("scene_key") or "").strip()}
    capability_entry_keys = {str((row or {}).get("capability_key") or "").strip() for row in capability_entries if str((row or {}).get("capability_key") or "").strip()}

    scene_coverage = round(len(scene_entry_keys & product_scene_keys) / len(product_scene_keys), 4) if product_scene_keys else 0.0
    capability_coverage = round(len(capability_entry_keys & capability_keys) / len(capability_keys), 4) if capability_keys else 0.0

    scene_entry_missing = sorted(product_scene_keys - scene_entry_keys)
    capability_entry_missing = sorted(capability_keys - capability_entry_keys)

    role_home_missing = []
    for role in role_rows:
        role_key = str((role or {}).get("role_key") or "").strip()
        home_scene = str((role or {}).get("home_scene") or "").strip()
        if role_key and home_scene and home_scene not in product_scene_keys:
            role_home_missing.append({"role_key": role_key, "home_scene": home_scene})

    status = "pass"
    if scene_entry_missing or capability_entry_missing or role_home_missing:
        status = "warn"
    if scene_coverage < 0.95 or capability_coverage < 0.95:
        status = "fail"

    return {
        "version": "v1",
        "generated_on": date.today().isoformat(),
        "status": status,
        "summary": {
            "product_scene_total": len(product_scene_keys),
            "scene_entry_total": len(scene_entries),
            "scene_entry_coverage": scene_coverage,
            "capability_total": len(capability_keys),
            "capability_entry_total": len(capability_entries),
            "capability_entry_coverage": capability_coverage,
            "role_count": len(role_rows),
        },
        "issues": {
            "scene_entry_missing": scene_entry_missing,
            "capability_entry_missing": capability_entry_missing,
            "role_home_missing": role_home_missing,
        },
    }


def main() -> int:
    PRODUCT_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

    capabilities = _extract_capabilities()
    scene_raw = _load_scene_catalog()
    scene_rows = scene_raw["scenes"]

    capability_catalog = _capability_catalog(capabilities)
    capability_grouping = _capability_grouping(capabilities)
    scene_catalog_v2 = _scene_catalog_v2(scene_rows, capabilities)
    scene_catalog_product_v1 = _product_scene_catalog(scene_catalog_v2)
    capability_scene_mapping = _capability_scene_mapping(capability_catalog, scene_catalog_v2)
    scene_entry_registry_v1 = _scene_entry_registry(scene_catalog_product_v1, capability_scene_mapping)
    capability_entry_registry_v1 = _capability_entry_registry(capability_catalog, capability_scene_mapping)
    role_scene_matrix = _role_scene_matrix(scene_catalog_v2)
    entry_registry_quality_v1 = _entry_registry_quality_report(
        scene_catalog_product_v1,
        capability_catalog,
        scene_entry_registry_v1,
        capability_entry_registry_v1,
        role_scene_matrix,
    )
    capability_maturity = _capability_maturity(capability_catalog, capability_scene_mapping)
    capability_gap_backlog = _capability_gap_backlog(
        capability_catalog, scene_catalog_v2, capability_scene_mapping, capability_maturity
    )

    _write_json(PRODUCT_DIR / "capability_catalog_v1.json", capability_catalog)
    _write_markdown(PRODUCT_DIR / "capability_catalog_v1.md", _md_capability_catalog(capability_catalog))

    _write_markdown(PRODUCT_DIR / "capability_grouping_v1.md", _md_capability_grouping(capability_grouping))

    _write_json(PRODUCT_DIR / "scene_catalog_v2.json", scene_catalog_v2)
    _write_markdown(PRODUCT_DIR / "scene_catalog_v2.md", _md_scene_catalog(scene_catalog_v2))
    _write_json(PRODUCT_DIR / "scene_catalog_product_v1.json", scene_catalog_product_v1)
    _write_json(PRODUCT_DIR / "scene_entry_registry_v1.json", scene_entry_registry_v1)

    _write_json(PRODUCT_DIR / "capability_scene_mapping_v1.json", capability_scene_mapping)
    _write_markdown(PRODUCT_DIR / "capability_scene_mapping_v1.md", _md_capability_scene_mapping(capability_scene_mapping))
    _write_json(PRODUCT_DIR / "capability_entry_registry_v1.json", capability_entry_registry_v1)
    _write_json(PRODUCT_DIR / "entry_registry_quality_report_v1.json", entry_registry_quality_v1)
    _write_markdown(PRODUCT_DIR / "entry_registry_quality_report_v1.md", _md_entry_registry_quality(entry_registry_quality_v1))

    _write_markdown(PRODUCT_DIR / "role_scene_matrix_v1.md", _md_role_scene_matrix(role_scene_matrix))
    _write_json(PRODUCT_DIR / "role_scene_matrix_v1.json", role_scene_matrix)

    _write_markdown(PRODUCT_DIR / "capability_maturity_matrix_v1.md", _md_capability_maturity(capability_maturity))
    _write_markdown(PRODUCT_DIR / "capability_gap_backlog_v1.md", _md_capability_gap_backlog(capability_gap_backlog))

    _write_markdown(
        TEMPLATE_DIR / "construction_enterprise_template_v1.md",
        _construction_template_md(role_scene_matrix),
    )
    _write_json(
        TEMPLATE_DIR / "construction_enterprise_template_v1.json",
        _construction_template_json(role_scene_matrix),
    )
    _write_markdown(
        TEMPLATE_DIR / "owner_management_template_draft_v1.md",
        _owner_template_md(),
    )
    _write_json(
        TEMPLATE_DIR / "owner_management_template_draft_v1.json",
        _owner_template_json(),
    )

    print("[capability_productization] generated files:")
    print("- docs/product/capability_catalog_v1.md")
    print("- docs/product/capability_catalog_v1.json")
    print("- docs/product/capability_grouping_v1.md")
    print("- docs/product/scene_catalog_v2.md")
    print("- docs/product/scene_catalog_v2.json")
    print("- docs/product/scene_catalog_product_v1.json")
    print("- docs/product/scene_entry_registry_v1.json")
    print("- docs/product/capability_scene_mapping_v1.md")
    print("- docs/product/capability_scene_mapping_v1.json")
    print("- docs/product/capability_entry_registry_v1.json")
    print("- docs/product/entry_registry_quality_report_v1.json")
    print("- docs/product/entry_registry_quality_report_v1.md")
    print("- docs/product/role_scene_matrix_v1.md")
    print("- docs/product/role_scene_matrix_v1.json")
    print("- docs/product/capability_maturity_matrix_v1.md")
    print("- docs/product/capability_gap_backlog_v1.md")
    print("- docs/product/templates/construction_enterprise_template_v1.md")
    print("- docs/product/templates/construction_enterprise_template_v1.json")
    print("- docs/product/templates/owner_management_template_draft_v1.md")
    print("- docs/product/templates/owner_management_template_draft_v1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
