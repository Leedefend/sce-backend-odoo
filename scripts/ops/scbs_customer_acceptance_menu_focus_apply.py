#!/usr/bin/env python3
"""Focus customer-facing menus on data acceptance entries.

Run with:
    DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/ops/scbs_customer_acceptance_menu_focus_apply.py

This script only writes runtime menu projection policies. It does not delete
menus, actions, or business data.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from odoo.tools.safe_eval import safe_eval


MODULE = "smart_construction_core"
OUTPUT_JSON_NAME = "scbs_customer_acceptance_menu_focus_apply_result_v1.json"

SC_ROOT_XMLID = "smart_construction_core.menu_sc_root"
OLD_ACCEPTANCE_ROOT_XMLID = "smart_construction_core.menu_scbs55_user_acceptance_root"
DIRECT_ACCEPTANCE_ROOT_XMLID = "smart_construction_core.menu_sc_user_acceptance_root"
DIRECT_ACCEPTANCE_SYSTEM_ROOT_XMLID = "smart_construction_core.menu_scbsly_direct_project_acceptance_root"
PROJECT_LEDGER_XMLID = "smart_construction_core.menu_sc_project_project"
ACCEPTANCE_PROJECT_LEDGER_XMLID_NAME = "menu_sc_acceptance_project_ledger"

ROOT_LABEL = "数据验收"
OLD_ACCEPTANCE_LABEL = "旧业务数据核对"
DIRECT_ACCEPTANCE_LABEL = "直营项目数据核对"
DIRECT_SYSTEM_LABEL = "直营项目单据核对"
PROJECT_LEDGER_LABEL = "项目台账（公司/项目/经营方式）"
OLD_ACCEPTANCE_SHADOW_RENAMES = {
    "施工合同": "施工合同（旧业务）",
    "施工合同（旧业务）": "施工合同（旧业务）",
}
OLD_ACCEPTANCE_SHADOW_RENAME_XMLIDS = {
    "smart_construction_core.menu_scbs55_user_acceptance_030_施工合同": "施工合同（旧业务）",
}


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_acceptance_menu_focus/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_acceptance_menu_focus/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ref(xmlid: str):
    return env.ref(xmlid, raise_if_not_found=False)  # noqa: F821


def xmlid_for(record) -> str:
    xid = env["ir.model.data"].sudo().search(  # noqa: F821
        [("model", "=", record._name), ("res_id", "=", int(record.id))],
        limit=1,
    )
    return f"{xid.module}.{xid.name}" if xid else ""


def ensure_xmlid(record, name: str) -> None:
    existing = env["ir.model.data"].sudo().search(  # noqa: F821
        [("module", "=", MODULE), ("name", "=", name), ("model", "=", record._name)],
        limit=1,
    )
    if existing:
        if int(existing.res_id or 0) != int(record.id):
            existing.write({"res_id": int(record.id)})
        return
    env["ir.model.data"].sudo().create(  # noqa: F821
        {
            "module": MODULE,
            "name": name,
            "model": record._name,
            "res_id": int(record.id),
            "noupdate": True,
        }
    )


def ensure_menu(*, xmlid_name: str, name: str, parent, sequence: int, action=None):
    menu = ref(f"{MODULE}.{xmlid_name}")
    values = {
        "name": name,
        "parent_id": parent.id if parent else False,
        "sequence": sequence,
        "active": True,
    }
    if action:
        values["action"] = f"{action._name},{action.id}"
    if menu:
        menu.sudo().write(values)
    else:
        menu = env["ir.ui.menu"].sudo().create(values)  # noqa: F821
        ensure_xmlid(menu, xmlid_name)
    return menu


def menu_policy_payload(menu, *, group_label: str, visible_menu_path: str | None = None) -> dict:
    action = menu.action
    action_id = int(action.id) if action else 0
    model_name = str(getattr(action, "res_model", "") or "") if action else ""
    menu_xmlid = xmlid_for(menu)
    return {
        "menu_xmlid": menu_xmlid,
        "menu_key": menu_xmlid,
        "page_key": menu_xmlid,
        "menu_id": int(menu.id),
        "action_id": action_id,
        "route": f"/a/{action_id}?menu_id={int(menu.id)}" if action_id else "",
        "label": str(menu.name or ""),
        "model": model_name,
        "res_model": model_name,
        "enabled": True,
        "release_state": "released",
        "access_level": "public",
        "sequence": int(menu.sequence or 0),
        "visible_menu_path": visible_menu_path or str(menu.complete_name or menu.name or ""),
        "policy_note": "Customer data acceptance focused product navigation entry.",
        "policy_group_label": group_label,
        "record_count": action_record_count(action),
    }


def action_domain(action) -> list:
    text = str(getattr(action, "domain", "") or "").strip()
    if not text:
        return []
    try:
        value = safe_eval(text, {"context": {}, "uid": env.uid, "active_id": False, "active_ids": []})  # noqa: F821
        return value if isinstance(value, list) else []
    except Exception:
        return []


def action_record_count(action) -> int:
    model_name = str(getattr(action, "res_model", "") or "").strip() if action else ""
    if not model_name or model_name not in env:  # noqa: F821
        return 0
    try:
        return int(env[model_name].sudo().with_context(active_test=False).search_count(action_domain(action)))  # noqa: F821
    except Exception:
        return 0


def action_leaf_menus(root_menu):
    Menu = env["ir.ui.menu"].sudo().with_context(active_test=False)  # noqa: F821
    ids = collect_self_and_active_descendant_ids(root_menu)
    return [
        menu
        for menu in Menu.browse(sorted(ids)).exists()
        if bool(menu.action) and bool(menu.active)
    ]


def build_product_menu_groups(old_root, direct_root, project_menu) -> list[dict]:
    old_menus = [project_menu] + [
        menu
        for menu in action_leaf_menus(old_root)
        if int(menu.id) != int(project_menu.id)
        and action_record_count(menu.action) > 0
    ]
    direct_menus = [menu for menu in action_leaf_menus(direct_root) if action_record_count(menu.action) > 0]
    return [
        {
            "group_key": "construction.acceptance.old_business_data",
            "group_label": OLD_ACCEPTANCE_LABEL,
            "category": "customer_acceptance_old_business_data",
            "menus": sorted(
                [
                    menu_policy_payload(
                        menu,
                        group_label=OLD_ACCEPTANCE_LABEL,
                        visible_menu_path=f"数据验收 / {OLD_ACCEPTANCE_LABEL} / {menu.name}",
                    )
                    for menu in old_menus
                ],
                key=lambda item: (int(item.get("sequence") or 0), str(item.get("label") or "")),
            ),
        },
        {
            "group_key": "construction.acceptance.direct_project_data",
            "group_label": DIRECT_ACCEPTANCE_LABEL,
            "category": "customer_acceptance_direct_project_data",
            "menus": sorted(
                [
                    menu_policy_payload(
                        menu,
                        group_label=DIRECT_ACCEPTANCE_LABEL,
                        visible_menu_path=(
                            "数据验收 / "
                            f"{DIRECT_ACCEPTANCE_LABEL} / "
                            f"{menu.parent_id.name or DIRECT_SYSTEM_LABEL} / {menu.name}"
                        ),
                    )
                    for menu in direct_menus
                ],
                key=lambda item: (str(item.get("visible_menu_path") or ""), int(item.get("sequence") or 0)),
            ),
        },
    ]


def rename_old_acceptance_shadow_menus(old_root) -> list[dict[str, object]]:
    if not old_root:
        return []
    Menu = env["ir.ui.menu"].sudo().with_context(active_test=False)  # noqa: F821
    ids = collect_self_and_active_descendant_ids(old_root)
    changes: list[dict[str, object]] = []
    for menu in Menu.browse(sorted(ids)).exists():
        current_name = str(menu.name or "")
        target_name = OLD_ACCEPTANCE_SHADOW_RENAMES.get(current_name)
        if not target_name:
            continue
        menu.write({"name": target_name})
        changes.append(
            {
                "menu_id": int(menu.id),
                "menu_xmlid": xmlid_for(menu),
                "old_name": current_name,
                "new_name": target_name,
            }
        )
    return changes


def force_old_acceptance_shadow_custom_labels() -> tuple[list[dict[str, object]], dict[int, str]]:
    changes: list[dict[str, object]] = []
    labels: dict[int, str] = {}
    for menu_xmlid, target_name in OLD_ACCEPTANCE_SHADOW_RENAME_XMLIDS.items():
        menu = ref(menu_xmlid)
        if not menu:
            changes.append(
                {
                    "menu_id": 0,
                    "menu_xmlid": menu_xmlid,
                    "old_name": "",
                    "new_name": target_name,
                    "status": "missing_menu_xmlid",
                }
            )
            continue
        old_name = str(menu.name or "")
        if old_name != target_name:
            menu.sudo().write({"name": target_name})
        labels[int(menu.id)] = target_name
        changes.append(
            {
                "menu_id": int(menu.id),
                "menu_xmlid": menu_xmlid,
                "old_name": old_name,
                "new_name": target_name,
                "status": "updated" if old_name != target_name else "already_aligned",
            }
        )
    return changes, labels


def sync_product_policies(menu_groups: list[dict]) -> dict[str, object]:
    ProductPolicy = env["sc.product.policy"].sudo()  # noqa: F821
    product_keys = ("construction.standard", "construction.preview")
    results = {}
    for product_key in product_keys:
        rec = ProductPolicy.search([("product_key", "=", product_key)], limit=1)
        if not rec:
            results[product_key] = {"status": "SKIP", "reason": "missing_product_policy"}
            continue
        rec.write(
            {
                "menu_groups": menu_groups,
                "note": "Customer data acceptance focused navigation active.",
            }
        )
        results[product_key] = {
            "status": "PASS",
            "policy_id": int(rec.id),
            "group_count": len(menu_groups),
            "menu_count": sum(len(group.get("menus") or []) for group in menu_groups),
        }
    return results


def collect_self_and_active_descendant_ids(menu) -> set[int]:
    if not menu:
        return set()
    env.cr.execute(  # noqa: F821
        """
        WITH RECURSIVE descendants AS (
            SELECT id, active
              FROM ir_ui_menu
             WHERE id = %s
            UNION ALL
            SELECT child.id, child.active
              FROM ir_ui_menu child
              JOIN descendants parent ON child.parent_id = parent.id
        )
        SELECT id FROM descendants WHERE active
        """,
        [int(menu.id)],
    )
    return {int(row[0]) for row in env.cr.fetchall()}  # noqa: F821


def active_menu_rows() -> list[tuple[int, int, str]]:
    env.cr.execute(  # noqa: F821
        """
        SELECT id, COALESCE(sequence, 0)
          FROM ir_ui_menu
         WHERE active
         ORDER BY id
        """
    )
    Menu = env["ir.ui.menu"].sudo().with_context(active_test=False)  # noqa: F821
    return [
        (int(menu.id), sequence, str(menu.complete_name or menu.name or ""))
        for menu_id, sequence in ((int(row[0]), int(row[1] or 0)) for row in env.cr.fetchall())  # noqa: F821
        for menu in Menu.browse(menu_id).exists()
    ]


def upsert_policy(
    *,
    menu,
    visible: bool,
    sequence: int | None = None,
    custom_label: str | None = None,
    target_parent=None,
    note: str,
) -> str:
    Policy = env["ui.menu.config.policy"].sudo().with_context(active_test=False)  # noqa: F821
    policies = Policy.search([("company_id", "=", env.company.id), ("menu_id", "=", int(menu.id))])  # noqa: F821
    values = {
        "active": True,
        "company_id": env.company.id,  # noqa: F821
        "menu_id": int(menu.id),
        "visible": bool(visible),
        "custom_label": custom_label or False,
        "target_parent_menu_id": int(target_parent.id) if target_parent else False,
        "sequence_override": int(sequence if sequence is not None else (menu.sequence or 0)),
        "note": note,
        "role_group_ids": [(5, 0, 0)],
    }
    if policies:
        policies.write(values)
        return "updated"
    Policy.create(values)
    return "created"


ensure_allowed_db()
artifact_dir = artifact_root()

sc_root = ref(SC_ROOT_XMLID)
old_acceptance_root = ref(OLD_ACCEPTANCE_ROOT_XMLID)
direct_acceptance_root = ref(DIRECT_ACCEPTANCE_ROOT_XMLID)
direct_acceptance_system_root = ref(DIRECT_ACCEPTANCE_SYSTEM_ROOT_XMLID)
project_ledger = ref(PROJECT_LEDGER_XMLID)

missing = [
    xmlid
    for xmlid, record in (
        (SC_ROOT_XMLID, sc_root),
        (OLD_ACCEPTANCE_ROOT_XMLID, old_acceptance_root),
        (DIRECT_ACCEPTANCE_ROOT_XMLID, direct_acceptance_root),
        (DIRECT_ACCEPTANCE_SYSTEM_ROOT_XMLID, direct_acceptance_system_root),
        (PROJECT_LEDGER_XMLID, project_ledger),
    )
    if not record
]
if missing:
    raise RuntimeError({"missing_required_menus": missing})

acceptance_project_ledger = ensure_menu(
    xmlid_name=ACCEPTANCE_PROJECT_LEDGER_XMLID_NAME,
    name=PROJECT_LEDGER_LABEL,
    parent=old_acceptance_root,
    sequence=5,
    action=project_ledger.action,
)
shadow_renames = rename_old_acceptance_shadow_menus(old_acceptance_root)
shadow_forced_labels, shadow_custom_labels = force_old_acceptance_shadow_custom_labels()
shadow_custom_labels.update(
    {
        int(item["menu_id"]): str(item["new_name"])
        for item in shadow_renames
        if int(item.get("menu_id") or 0)
    }
)

allowed_ids = set()
allowed_ids.add(int(sc_root.id))
allowed_ids.update(collect_self_and_active_descendant_ids(old_acceptance_root))
allowed_ids.update(collect_self_and_active_descendant_ids(direct_acceptance_root))
allowed_ids.add(int(acceptance_project_ledger.id))

visible_results = []
hidden_results = []

visible_specs = {
    int(sc_root.id): {"label": ROOT_LABEL, "sequence": 1, "target": None},
    int(old_acceptance_root.id): {"label": OLD_ACCEPTANCE_LABEL, "sequence": 1, "target": None},
    int(direct_acceptance_root.id): {"label": DIRECT_ACCEPTANCE_LABEL, "sequence": 2, "target": None},
    int(direct_acceptance_system_root.id): {"label": DIRECT_SYSTEM_LABEL, "sequence": 1, "target": None},
    int(acceptance_project_ledger.id): {
        "label": PROJECT_LEDGER_LABEL,
        "sequence": 5,
        "target": None,
    },
}

Menu = env["ir.ui.menu"].sudo()  # noqa: F821
for menu in Menu.browse(sorted(allowed_ids)).exists():
    spec = visible_specs.get(int(menu.id), {})
    custom_label = shadow_custom_labels.get(int(menu.id)) or spec.get("label")
    action = upsert_policy(
        menu=menu,
        visible=True,
        sequence=spec.get("sequence"),
        custom_label=custom_label,
        target_parent=spec.get("target"),
        note="Customer data acceptance focused view: retained as an explicit verification entry.",
    )
    visible_results.append(
        {
            "menu_id": int(menu.id),
            "menu_xmlid": xmlid_for(menu),
            "path": str(menu.complete_name or menu.name or ""),
            "policy_action": action,
            "custom_label": custom_label or "",
        }
    )

for menu_id, sequence, path in active_menu_rows():
    if menu_id in allowed_ids:
        continue
    menu = Menu.browse(menu_id).exists()
    if not menu:
        continue
    action = upsert_policy(
        menu=menu,
        visible=False,
        sequence=sequence,
        note="Hidden during customer data acceptance so users only see verification entries.",
    )
    hidden_results.append(
        {
            "menu_id": menu_id,
            "menu_xmlid": xmlid_for(menu),
            "path": path,
            "policy_action": action,
        }
    )

product_menu_groups = build_product_menu_groups(
    old_acceptance_root,
    direct_acceptance_root,
    acceptance_project_ledger,
)
product_policy_results = sync_product_policies(product_menu_groups)

result = {
    "status": "PASS",
    "db": env.cr.dbname,  # noqa: F821
    "company_id": int(env.company.id),  # noqa: F821
    "allowed_count": len(visible_results),
    "hidden_count": len(hidden_results),
    "allowed_roots": {
        "root": SC_ROOT_XMLID,
        "old_acceptance": OLD_ACCEPTANCE_ROOT_XMLID,
        "direct_acceptance": DIRECT_ACCEPTANCE_ROOT_XMLID,
        "direct_acceptance_system": DIRECT_ACCEPTANCE_SYSTEM_ROOT_XMLID,
        "project_ledger": PROJECT_LEDGER_XMLID,
        "acceptance_project_ledger": f"{MODULE}.{ACCEPTANCE_PROJECT_LEDGER_XMLID_NAME}",
    },
    "visible_results": visible_results,
    "hidden_results_sample": hidden_results[:80],
    "shadow_renames": shadow_renames,
    "shadow_forced_labels": shadow_forced_labels,
    "product_policy_results": product_policy_results,
}
write_json(artifact_dir / OUTPUT_JSON_NAME, result)
env.cr.commit()  # noqa: F821
print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
