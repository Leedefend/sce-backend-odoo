#!/usr/bin/env python3
"""Restore released formal contract menus plus accepted-data verification menus.

Deprecated for production product navigation. Use
``scripts/ops/formal_product_menu_policy_restore.py`` or
``make policy.restore.formal_product_menu`` for the formal product menu release
policy. This script is retained for migration/acceptance investigations only.

Run with:
    PROJECT=sc-backend-odoo-dev DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/ops/contract_product_acceptance_policy_restore.py
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from odoo import SUPERUSER_ID, api
from odoo.modules.registry import Registry
from odoo.tools.safe_eval import safe_eval


PRODUCT_KEYS = ("construction.standard", "construction.preview")

FORMAL_CONTRACT_MENU_XMLIDS = (
    "smart_construction_core.menu_sc_contract_income",
    "smart_construction_core.menu_sc_project_income_contract",
    "smart_construction_core.menu_sc_income_contract_execution",
    "smart_construction_core.menu_sc_contract_event",
    "smart_construction_core.menu_sc_general_contract",
    "smart_construction_core.menu_sc_contract_expense",
    "smart_construction_core.menu_sc_expense_contract_execution",
)

FORMAL_SETTLEMENT_MENU_XMLIDS = (
    "smart_construction_core.menu_sc_settlement_order",
    "smart_construction_core.menu_sc_settlement_adjustment",
    "smart_construction_core.menu_sc_income_contract_settlement",
    "smart_construction_core.menu_sc_expense_contract_settlement",
    "smart_construction_core.menu_sc_material_settlement",
    "smart_construction_core.menu_sc_labor_settlement",
    "smart_construction_core.menu_sc_equipment_settlement",
    "smart_construction_core.menu_sc_material_rental_settlement",
    "smart_construction_core.menu_sc_subcontract_settlement",
)

OLD_ACCEPTANCE_ROOT_XMLID = "smart_construction_core.menu_scbs55_user_acceptance_root"
DIRECT_ACCEPTANCE_ROOT_XMLID = "smart_construction_core.menu_sc_user_acceptance_root"

OUTPUT_JSON_NAME = "contract_product_acceptance_policy_restore_v1.json"


def _artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path(f"/tmp/contract_product_acceptance_policy/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/contract_product_acceptance_policy/{env.cr.dbname}")  # noqa: F821


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _ref(xmlid: str):
    return env.ref(xmlid, raise_if_not_found=False)  # noqa: F821


def _xmlid_for(record) -> str:
    if not record:
        return ""
    external_id = record.get_external_id().get(record.id, "")
    if external_id:
        return external_id
    row = env["ir.model.data"].sudo().search([("model", "=", record._name), ("res_id", "=", int(record.id))], limit=1)  # noqa: F821
    return f"{row.module}.{row.name}" if row else ""


def _action_domain(action) -> list:
    text = str(getattr(action, "domain", "") or "").strip()
    if not text:
        return []
    try:
        value = safe_eval(text, {"context": {}, "uid": env.uid, "active_id": False, "active_ids": []})  # noqa: F821
        return value if isinstance(value, list) else []
    except Exception:
        return []


def _action_record_count(action) -> int:
    model_name = str(getattr(action, "res_model", "") or "").strip() if action else ""
    if not model_name or model_name not in env:  # noqa: F821
        return 0
    try:
        return int(env[model_name].sudo().with_context(active_test=False).search_count(_action_domain(action)))  # noqa: F821
    except Exception:
        return 0


def _collect_active_descendant_ids(root_menu) -> set[int]:
    if not root_menu:
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
        [int(root_menu.id)],
    )
    return {int(row[0]) for row in env.cr.fetchall()}  # noqa: F821


def _action_leaf_menus(root_menu) -> list:
    ids = _collect_active_descendant_ids(root_menu)
    Menu = env["ir.ui.menu"].sudo().with_context(active_test=False)  # noqa: F821
    return [menu for menu in Menu.browse(sorted(ids)).exists() if menu.active and menu.action]


def _menu_payload(menu, *, group_label: str, release_domain: str, note: str, visible_menu_path: str | None = None) -> dict:
    action = menu.action
    action_id = int(action.id) if action else 0
    model_name = str(getattr(action, "res_model", "") or "") if action else ""
    menu_xmlid = _xmlid_for(menu)
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
        "release_domain": release_domain,
        "sequence": int(menu.sequence or 0),
        "visible_menu_path": visible_menu_path or str(menu.complete_name or menu.name or ""),
        "policy_note": note,
        "policy_group_label": group_label,
        "record_count": _action_record_count(action),
    }


def _formal_group(group_key: str, group_label: str, release_domain: str, xmlids: tuple[str, ...]) -> dict:
    menus = []
    missing = []
    for xmlid in xmlids:
        menu = _ref(xmlid)
        if not menu:
            missing.append(xmlid)
            continue
        menus.append(
            _menu_payload(
                menu,
                group_label=group_label,
                release_domain=release_domain,
                note="Formal product menu retained after accepted-data projection.",
            )
        )
    if missing:
        raise RuntimeError({"missing_formal_menu_xmlids": missing})
    return {
        "group_key": group_key,
        "group_label": group_label,
        "category": release_domain,
        "menus": menus,
    }


def _acceptance_group(root_xmlid: str, *, group_key: str, group_label: str, release_domain: str) -> dict:
    root = _ref(root_xmlid)
    if not root:
        raise RuntimeError({"missing_acceptance_root_xmlid": root_xmlid})
    menus = []
    for menu in _action_leaf_menus(root):
        if _action_record_count(menu.action) <= 0:
            continue
        path = str(menu.complete_name or menu.name or "")
        menus.append(
            _menu_payload(
                menu,
                group_label=group_label,
                release_domain=release_domain,
                note="Accepted source data remains visible for user verification.",
                visible_menu_path=path.replace("用户验收 / 直营项目系统菜单", f"数据验收 / {group_label}"),
            )
        )
    menus.sort(key=lambda row: (str(row.get("visible_menu_path") or ""), int(row.get("sequence") or 0), str(row.get("label") or "")))
    return {
        "group_key": group_key,
        "group_label": group_label,
        "category": release_domain,
        "menus": menus,
    }


def _policy_release_pages(groups: list[dict]) -> list[dict]:
    pages = []
    for group in groups:
        if not isinstance(group, dict):
            continue
        for menu in group.get("menus") if isinstance(group.get("menus"), list) else []:
            if not isinstance(menu, dict):
                continue
            pages.append(
                {
                    "page_key": str(menu.get("page_key") or menu.get("menu_xmlid") or ""),
                    "menu_key": str(menu.get("menu_key") or menu.get("menu_xmlid") or ""),
                    "menu_xmlid": str(menu.get("menu_xmlid") or ""),
                    "label": str(menu.get("label") or ""),
                    "route": str(menu.get("route") or ""),
                    "menu_id": int(menu.get("menu_id") or 0),
                    "action_id": int(menu.get("action_id") or 0),
                    "res_model": str(menu.get("res_model") or menu.get("model") or ""),
                    "enabled": True,
                    "release_state": "released",
                    "access_level": "public",
                    "visible_menu_path": str(menu.get("visible_menu_path") or ""),
                }
            )
    return pages


def _merge_pages(existing_pages: list, required_pages: list[dict]) -> tuple[list[dict], int]:
    merged = [dict(page) for page in existing_pages if isinstance(page, dict)]
    index = {}
    for pos, page in enumerate(merged):
        for key in ("menu_xmlid", "page_key", "menu_key"):
            value = str(page.get(key) or "").strip()
            if value:
                index.setdefault(value, pos)
        menu_id = int(page.get("menu_id") or 0)
        if menu_id:
            index.setdefault(f"menu_id:{menu_id}", pos)
    added = 0
    for page in required_pages:
        keys = [str(page.get(key) or "").strip() for key in ("menu_xmlid", "page_key", "menu_key")]
        menu_id = int(page.get("menu_id") or 0)
        if menu_id:
            keys.append(f"menu_id:{menu_id}")
        hit = next((index[key] for key in keys if key and key in index), None)
        if hit is None:
            hit = len(merged)
            merged.append({})
            added += 1
        merged[hit].update({key: value for key, value in page.items() if value not in ("", 0, None)})
        merged[hit]["enabled"] = True
        merged[hit]["release_state"] = "released"
        merged[hit]["access_level"] = "public"
        for key in keys:
            if key:
                index.setdefault(key, hit)
    return merged, added


def _sync_platform_release_gate(product_key: str, pages: list[dict]) -> dict:
    platform_db = str(env["ir.config_parameter"].sudo().get_param("smart_core.platform_release_db", "") or "").strip() or "sc_platform_core"  # noqa: F821
    current_db = str(env.cr.dbname)  # noqa: F821

    def update_in(read_env):
        Snapshot = read_env["sc.edition.release.snapshot"].sudo()
        snapshot = Snapshot.search(
            [("product_key", "=", product_key), ("state", "=", "released"), ("is_active", "=", True), ("active", "=", True)],
            order="released_at desc, activated_at desc, id desc",
            limit=1,
        )
        if not snapshot:
            return {"status": "SKIP", "reason": "active_release_snapshot_not_found", "platform_db": platform_db}
        meta = dict(snapshot.meta_json if isinstance(snapshot.meta_json, dict) else {})
        draft = dict(meta.get("release_draft") if isinstance(meta.get("release_draft"), dict) else {})
        merged_pages, added = _merge_pages(draft.get("pages") if isinstance(draft.get("pages"), list) else [], pages)
        draft["pages"] = merged_pages
        draft["page_count"] = sum(1 for page in merged_pages if isinstance(page, dict) and page.get("enabled", True) and str(page.get("release_state") or "released") in {"released", "preview"})
        draft["total_page_count"] = len(merged_pages)
        draft["fingerprint"] = hashlib.sha256(json.dumps(merged_pages, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        meta["release_draft"] = draft
        snapshot.write({"meta_json": meta})
        return {"status": "PASS", "platform_db": platform_db, "snapshot_id": int(snapshot.id), "added_page_count": added, "release_draft_page_count": int(draft["page_count"])}

    if platform_db == current_db:
        return update_in(env)  # noqa: F821
    try:
        registry = Registry(platform_db)
        with registry.cursor() as cr:
            read_env = api.Environment(cr, SUPERUSER_ID, dict(env.context or {}))  # noqa: F821
            result = update_in(read_env)
            cr.commit()
            return result
    except Exception as exc:
        return {"status": "SKIP", "reason": "platform_release_db_unavailable", "platform_db": platform_db, "error": str(exc)}


def _main() -> None:
    groups = [
        _formal_group("construction.formal.contract", "合同中心", "formal_contract_domain", FORMAL_CONTRACT_MENU_XMLIDS),
        _formal_group("construction.formal.settlement", "结算中心", "formal_settlement_domain", FORMAL_SETTLEMENT_MENU_XMLIDS),
        _acceptance_group(
            OLD_ACCEPTANCE_ROOT_XMLID,
            group_key="construction.acceptance.old_business_data",
            group_label="旧业务数据核对",
            release_domain="customer_acceptance_old_business_data",
        ),
        _acceptance_group(
            DIRECT_ACCEPTANCE_ROOT_XMLID,
            group_key="construction.acceptance.direct_project_data",
            group_label="直营项目数据核对",
            release_domain="customer_acceptance_direct_project_data",
        ),
    ]
    pages = _policy_release_pages(groups)
    Policy = env["sc.product.policy"].sudo()  # noqa: F821
    policy_results = {}
    platform_results = {}
    for product_key in PRODUCT_KEYS:
        policy = Policy.search([("product_key", "=", product_key)], limit=1)
        if not policy:
            policy_results[product_key] = {"status": "SKIP", "reason": "missing_product_policy"}
            continue
        policy.write(
            {
                "menu_groups": groups,
                "note": "Formal contract/settlement menus released; accepted legacy and direct-project data verification menus retained.",
            }
        )
        policy_results[product_key] = {
            "status": "PASS",
            "policy_id": int(policy.id),
            "group_count": len(groups),
            "menu_count": sum(len(group.get("menus") or []) for group in groups),
        }
        platform_results[product_key] = _sync_platform_release_gate(product_key, pages)
    result = {
        "status": "PASS" if all(row.get("status") == "PASS" for row in policy_results.values()) else "FAIL",
        "db": env.cr.dbname,  # noqa: F821
        "policy_results": policy_results,
        "platform_release_gate_results": platform_results,
        "groups": [(group["group_label"], len(group.get("menus") or [])) for group in groups],
    }
    _write_json(_artifact_root() / OUTPUT_JSON_NAME, result)
    env.cr.commit()  # noqa: F821
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


_main()
