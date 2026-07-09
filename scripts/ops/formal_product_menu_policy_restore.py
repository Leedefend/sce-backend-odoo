# -*- coding: utf-8 -*-
"""Restore product menu policies from the locked formal business baseline.

This script intentionally excludes legacy/user-acceptance menus from the
product release policy. Those menus are migration/acceptance surfaces, not the
daily product navigation contract.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from odoo import SUPERUSER_ID, api
from odoo.modules.registry import Registry


BASELINE_FILE = "formal_business_product_menu_policy_v1.json"
PRODUCT_KEYS = ("construction.standard", "construction.preview")
OUTPUT_JSON_NAME = "formal_product_menu_policy_restore_v1.json"
ACTIVATED_MENU_XMLIDS: list[str] = []
CONFIG_CENTER_GROUP_LABEL = "配置中心"
CONFIG_CENTER_LOWCODING_LABEL = "低代码系统配置"
LEGACY_CONFIG_GROUP_LABELS = {"基础设置", "系统设置", "业务配置"}
CONFIG_CENTER_LOWCODING_MENU_XMLIDS = {
    "smart_construction_core.menu_sc_business_config_workbench",
    "smart_construction_core.menu_ui_menu_config_policy_business_config",
    "smart_construction_core.menu_ui_form_field_policy_business_config",
    "smart_construction_core.menu_ui_form_custom_field_wizard_business_config",
}
FORMAL_MASTER_DATA_MENU_CONFIG = (
    {
        "xmlid": "smart_construction_core.menu_sc_master_data_center",
        "custom_label": "基础资料",
        "sequence_override": 10,
        "target_parent_xmlid": "",
        "note": "正式产品菜单分组：基础资料。",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_customer_partner",
        "custom_label": "客户",
        "sequence_override": 1,
        "target_parent_xmlid": "smart_construction_core.menu_sc_master_data_center",
        "note": "正式产品菜单：客户主数据。",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_supplier_partner",
        "custom_label": "供应商",
        "sequence_override": 2,
        "target_parent_xmlid": "smart_construction_core.menu_sc_master_data_center",
        "note": "正式产品菜单：供应商主数据。",
    },
)


def _text(value) -> str:
    return str(value or "").strip()


def _baseline_path() -> Path:
    candidates = [
        Path.cwd() / "scripts" / "verify" / "baselines" / BASELINE_FILE,
        Path("/mnt/scripts/verify/baselines") / BASELINE_FILE,
        Path("/home/lidefend/workspace/sce-backend-odoo/scripts/verify/baselines") / BASELINE_FILE,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("missing formal product menu baseline: %s" % BASELINE_FILE)


def _artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path("/mnt/artifacts/migration"), Path("/tmp")])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path("/tmp")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_baseline_products() -> dict[str, dict]:
    payload = json.loads(_baseline_path().read_text(encoding="utf-8"))
    products = payload.get("products") if isinstance(payload, dict) else payload
    if not isinstance(products, list):
        raise RuntimeError("baseline products must be a list")
    out = {}
    for product in products:
        if not isinstance(product, dict):
            continue
        product_key = _text(product.get("product_key"))
        if product_key in PRODUCT_KEYS:
            out[product_key] = product
    missing = [key for key in PRODUCT_KEYS if key not in out]
    if missing:
        raise RuntimeError("baseline missing products: %s" % missing)
    return out


def _external_action_xmlid(action) -> str:
    if not action:
        return ""
    return action.get_external_id().get(action.id, "") or ""


def _hydrate_menu_row(menu: dict) -> dict:
    row = dict(menu or {})
    menu_xmlid = _text(row.get("menu_xmlid") or row.get("page_key") or row.get("menu_key"))
    if not menu_xmlid:
        raise RuntimeError("formal product menu missing menu_xmlid: %s" % row)
    menu_record = env.ref(menu_xmlid, raise_if_not_found=False)  # noqa: F821
    if not menu_record:
        raise RuntimeError("formal product menu xmlid does not resolve: %s" % menu_xmlid)
    if hasattr(menu_record, "active") and not bool(menu_record.active):
        menu_record.sudo().write({"active": True})
        ACTIVATED_MENU_XMLIDS.append(menu_xmlid)
    action = menu_record.action
    if not action:
        raise RuntimeError("formal product menu has no action: %s" % menu_xmlid)
    action_id = int(action.id or 0)
    model_name = _text(getattr(action, "res_model", "")) or _text(row.get("res_model") or row.get("model"))
    view_modes = [_text(item) for item in _text(getattr(action, "view_mode", "")).split(",") if _text(item)]
    route = "/a/%s?menu_id=%s" % (action_id, int(menu_record.id))
    row.update(
        {
            "menu_xmlid": menu_xmlid,
            "menu_key": menu_xmlid,
            "page_key": menu_xmlid,
            "menu_id": int(menu_record.id),
            "action_id": action_id,
            "action_xmlid": _text(row.get("action_xmlid")) or _external_action_xmlid(action),
            "route": route,
            "model": model_name,
            "res_model": model_name,
            "view_modes": view_modes or (row.get("view_modes") if isinstance(row.get("view_modes"), list) else []),
            "enabled": bool(row.get("enabled", True)),
            "release_state": _text(row.get("release_state")) or "released",
            "access_level": _text(row.get("access_level")) or "public",
            "visible_menu_path": _text(row.get("visible_menu_path")) or _text(menu_record.complete_name or menu_record.name),
        }
    )
    row.pop("id", None)
    return row


def _canonical_group_label(label: str) -> str:
    label = _text(label)
    if label in LEGACY_CONFIG_GROUP_LABELS:
        return CONFIG_CENTER_GROUP_LABEL
    return label


def _normalize_menu_for_group(menu: dict, *, canonical_label: str, legacy_label: str) -> dict:
    row = dict(menu or {})
    menu_xmlid = _text(row.get("menu_xmlid") or row.get("page_key") or row.get("menu_key"))
    if canonical_label:
        row["product_key"] = canonical_label
    if legacy_label and canonical_label and legacy_label != canonical_label:
        for key in ("visible_menu_path", "menu_complete_name"):
            value = _text(row.get(key))
            if value:
                row[key] = value.replace(" / %s /" % legacy_label, " / %s /" % canonical_label).replace(
                    "/%s/" % legacy_label,
                    "/%s/" % canonical_label,
                )
    if canonical_label == CONFIG_CENTER_GROUP_LABEL and menu_xmlid in CONFIG_CENTER_LOWCODING_MENU_XMLIDS:
        label = _text(row.get("label") or row.get("page_label") or row.get("name"))
        if label:
            row["visible_menu_path"] = "智慧施工管理平台 / %s / %s / %s" % (
                CONFIG_CENTER_GROUP_LABEL,
                CONFIG_CENTER_LOWCODING_LABEL,
                label,
            )
        row["product_domain"] = "lowcode_system_config"
        row["product_domain_label"] = CONFIG_CENTER_LOWCODING_LABEL
        row["entry_intent"] = "config"
        row["entry_intent_label"] = "配置"
        row["policy_note"] = "config_center_lowcode_system_config_grouped"
    return row


def _hydrate_group(group: dict) -> dict:
    row = dict(group or {})
    legacy_label = _text(row.get("group_label") or row.get("label") or row.get("title"))
    canonical_label = _canonical_group_label(legacy_label)
    row["group_label"] = canonical_label
    row["group_key"] = "construction.%s" % canonical_label if canonical_label else _text(row.get("group_key"))
    row["label"] = canonical_label or _text(row.get("label"))
    row["title"] = canonical_label or _text(row.get("title"))
    menus = []
    for menu in row.get("menus") or []:
        if not isinstance(menu, dict):
            continue
        menus.append(
            _normalize_menu_for_group(
                _hydrate_menu_row(menu),
                canonical_label=canonical_label,
                legacy_label=legacy_label,
            )
        )
    row["menus"] = menus
    return row


def _hydrate_capability(row: dict) -> dict:
    payload = dict(row or {})
    legacy_group_label = _text(payload.get("group_label"))
    canonical_group_label = _canonical_group_label(legacy_group_label)
    if canonical_group_label:
        payload["group_label"] = canonical_group_label
        payload["group_key"] = "construction.%s" % canonical_group_label
        payload["product_key"] = canonical_group_label
    menu_xmlid = _text(payload.get("menu_xmlid") or payload.get("target_page_key"))
    if menu_xmlid:
        menu_record = env.ref(menu_xmlid, raise_if_not_found=False)  # noqa: F821
        action = menu_record.action if menu_record else None
        if menu_record and action:
            payload["menu_xmlid"] = menu_xmlid
            payload["target_page_key"] = menu_xmlid
            payload["action_id"] = int(action.id or 0)
            payload["res_model"] = _text(getattr(action, "res_model", "")) or _text(payload.get("res_model"))
        if canonical_group_label == CONFIG_CENTER_GROUP_LABEL and menu_xmlid in CONFIG_CENTER_LOWCODING_MENU_XMLIDS:
            label = _text(payload.get("label") or payload.get("name"))
            if label:
                payload["visible_menu_path"] = "智慧施工管理平台 / %s / %s / %s" % (
                    CONFIG_CENTER_GROUP_LABEL,
                    CONFIG_CENTER_LOWCODING_LABEL,
                    label,
                )
            payload["product_domain"] = "lowcode_system_config"
    payload.pop("id", None)
    return payload


def _merge_menu_groups(groups: list[dict]) -> list[dict]:
    out = []
    by_label = {}
    for group in groups:
        label = _text(group.get("group_label") or group.get("label"))
        existing = by_label.get(label)
        if existing is not None:
            existing["menus"] = [*(existing.get("menus") or []), *(group.get("menus") or [])]
            continue
        by_label[label] = group
        out.append(group)
    return out


def _hydrate_product(product: dict) -> dict:
    payload = dict(product or {})
    payload.pop("id", None)
    payload["menu_groups"] = _merge_menu_groups(
        [_hydrate_group(group) for group in payload.get("menu_groups") or [] if isinstance(group, dict)]
    )
    payload["capabilities"] = [
        _hydrate_capability(row)
        for row in payload.get("capabilities") or []
        if isinstance(row, dict)
    ]
    payload.setdefault("policy_source_authority", {
        "kind": "formal_product_menu_policy_baseline",
        "authorities": ["scripts/verify/baselines/formal_business_product_menu_policy_v1.json"],
        "projection_only": True,
        "no_business_fact_authority": True,
    })
    payload["note"] = "Restored from locked formal product menu baseline; user-acceptance menus are excluded."
    return payload


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
                    "page_key": _text(menu.get("page_key") or menu.get("menu_xmlid")),
                    "menu_key": _text(menu.get("menu_key") or menu.get("menu_xmlid")),
                    "menu_xmlid": _text(menu.get("menu_xmlid")),
                    "label": _text(menu.get("label") or menu.get("name")),
                    "route": _text(menu.get("route")),
                    "menu_id": int(menu.get("menu_id") or 0),
                    "action_id": int(menu.get("action_id") or 0),
                    "res_model": _text(menu.get("res_model") or menu.get("model")),
                    "enabled": True,
                    "release_state": "released",
                    "access_level": "public",
                    "visible_menu_path": _text(menu.get("visible_menu_path")),
                }
            )
    return pages


def _write_snapshot(read_env, product_key: str, pages: list[dict], *, platform_db: str) -> dict:
    Snapshot = read_env["sc.edition.release.snapshot"].sudo()
    snapshot = Snapshot.search(
        [
            ("product_key", "=", product_key),
            ("state", "=", "released"),
            ("is_active", "=", True),
            ("active", "=", True),
        ],
        order="released_at desc, activated_at desc, id desc",
        limit=1,
    )
    if not snapshot:
        return {"status": "SKIP", "reason": "active_release_snapshot_not_found", "platform_db": platform_db}
    meta = dict(snapshot.meta_json if isinstance(snapshot.meta_json, dict) else {})
    draft = dict(meta.get("release_draft") if isinstance(meta.get("release_draft"), dict) else {})
    draft["pages"] = pages
    draft["page_count"] = len(pages)
    draft["total_page_count"] = len(pages)
    draft["fingerprint"] = hashlib.sha256(
        json.dumps(pages, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    meta["release_draft"] = draft
    snapshot.write({"meta_json": meta})
    return {
        "status": "PASS",
        "platform_db": platform_db,
        "snapshot_id": int(snapshot.id),
        "release_draft_page_count": len(pages),
    }


def _sync_platform_release_gate(product_key: str, pages: list[dict]) -> dict:
    platform_db = _text(env["ir.config_parameter"].sudo().get_param("smart_core.platform_release_db", "")) or "sc_platform_core"  # noqa: F821
    current_db = _text(env.cr.dbname)  # noqa: F821
    if platform_db == current_db:
        return _write_snapshot(env, product_key, pages, platform_db=platform_db)  # noqa: F821
    try:
        registry = Registry(platform_db)
        with registry.cursor() as cr:
            read_env = api.Environment(cr, SUPERUSER_ID, dict(env.context or {}))  # noqa: F821
            result = _write_snapshot(read_env, product_key, pages, platform_db=platform_db)
            cr.commit()
            return result
    except Exception as exc:
        return {"status": "FAIL", "reason": "platform_release_db_unavailable", "platform_db": platform_db, "error": str(exc)}


def _ensure_formal_master_data_menu_config() -> dict:
    Policy = env["ui.menu.config.policy"].sudo()  # noqa: F821
    company = env.ref("base.main_company", raise_if_not_found=False) or env.company  # noqa: F821
    rows = []
    for spec in FORMAL_MASTER_DATA_MENU_CONFIG:
        menu = env.ref(spec["xmlid"], raise_if_not_found=False)  # noqa: F821
        if not menu:
            raise RuntimeError("formal menu config xmlid does not resolve: %s" % spec["xmlid"])
        target_parent = (
            env.ref(spec["target_parent_xmlid"], raise_if_not_found=False)  # noqa: F821
            if spec.get("target_parent_xmlid")
            else False
        )
        values = {
            "company_id": int(company.id),
            "menu_id": int(menu.id),
            "target_parent_menu_id": int(target_parent.id) if target_parent else False,
            "custom_label": spec["custom_label"],
            "sequence_override": int(spec["sequence_override"]),
            "visible": True,
            "active": True,
            "note": spec["note"],
        }
        policy = Policy.search([("company_id", "=", company.id), ("menu_id", "=", menu.id)], limit=1)
        status = "UPDATED" if policy else "CREATED"
        if policy:
            policy.write(values)
        else:
            policy = Policy.create(values)
        rows.append(
            {
                "status": status,
                "policy_id": int(policy.id),
                "menu_xmlid": spec["xmlid"],
                "menu_id": int(menu.id),
                "target_parent_menu_id": int(target_parent.id) if target_parent else 0,
                "custom_label": spec["custom_label"],
                "sequence_override": int(spec["sequence_override"]),
            }
        )
    return {"status": "PASS", "rows": rows}


def main() -> None:
    baseline = _load_baseline_products()
    Policy = env["sc.product.policy"].sudo()  # noqa: F821
    policy_results = {}
    snapshot_results = {}
    group_counts = {}
    menu_config_result = _ensure_formal_master_data_menu_config()
    for product_key in PRODUCT_KEYS:
        product = _hydrate_product(baseline[product_key])
        policy = Policy.search([("product_key", "=", product_key)], limit=1)
        if not policy:
            policy_results[product_key] = {"status": "SKIP", "reason": "missing_product_policy"}
            continue
        values = {
            "base_product_key": _text(product.get("base_product_key")) or "construction",
            "edition_key": _text(product.get("edition_key")) or product_key.split(".", 1)[1],
            "label": _text(product.get("label")) or product_key,
            "version": _text(product.get("version")) or "v1",
            "state": _text(product.get("state")) or "stable",
            "access_level": _text(product.get("access_level")) or "public",
            "allowed_role_codes": product.get("allowed_role_codes") if isinstance(product.get("allowed_role_codes"), list) else [],
            "menu_groups": product["menu_groups"],
            "scenes": product.get("scenes") if isinstance(product.get("scenes"), list) else [],
            "capabilities": product.get("capabilities") if isinstance(product.get("capabilities"), list) else [],
            "scene_version_bindings": product.get("scene_version_bindings") if isinstance(product.get("scene_version_bindings"), dict) else {},
            "note": product["note"],
            "active": True,
        }
        policy.write(values)
        pages = _policy_release_pages(product["menu_groups"])
        snapshot_results[product_key] = _sync_platform_release_gate(product_key, pages)
        group_counts[product_key] = {
            _text(group.get("group_label")): len(group.get("menus") or [])
            for group in product["menu_groups"]
        }
        policy_results[product_key] = {
            "status": "PASS",
            "policy_id": int(policy.id),
            "group_count": len(product["menu_groups"]),
            "menu_count": len(pages),
            "capability_count": len(values["capabilities"]),
        }
    ok = all(row.get("status") == "PASS" for row in policy_results.values()) and all(
        row.get("status") == "PASS" for row in snapshot_results.values()
    )
    result = {
        "status": "PASS" if ok else "FAIL",
        "db": env.cr.dbname,  # noqa: F821
        "baseline": BASELINE_FILE,
        "policy_results": policy_results,
        "snapshot_results": snapshot_results,
        "group_counts": group_counts,
        "menu_config_result": menu_config_result,
        "activated_menu_xmlids": sorted(set(ACTIVATED_MENU_XMLIDS)),
    }
    _write_json(_artifact_root() / OUTPUT_JSON_NAME, result)
    if not ok:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        raise SystemExit(1)
    env.cr.commit()  # noqa: F821
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


main()
