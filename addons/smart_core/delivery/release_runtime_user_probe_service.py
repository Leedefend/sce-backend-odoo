# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

try:
    from odoo import SUPERUSER_ID, api
    from odoo.modules.registry import Registry
except Exception:  # pragma: no cover - lightweight unit-test stubs may not load Odoo.
    SUPERUSER_ID = 1
    api = None
    Registry = None

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract

from .delivery_engine import DeliveryEngine
from .product_identity import resolve_product_identity


def _text(value: Any) -> str:
    return str(value or "").strip()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_int(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except Exception:
        return 0
    return parsed if parsed > 0 else 0


class ReleaseRuntimeUserProbeService:
    SOURCE_KIND = "release_runtime_user_probe_projection"
    SOURCE_AUTHORITIES = (
        "platform_release_snapshot_projection",
        "delivery_engine_projection",
        "business_runtime_user_registry",
    )
    NO_BUSINESS_FACT_AUTHORITY = True

    def __init__(self, env):
        self.env = env

    @classmethod
    def source_authority_contract(cls) -> dict[str, Any]:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            runtime_carrier="release_operator_surface.runtime_user_probe",
        )

    def _config_param(self, key: str, default: str = "") -> str:
        try:
            return _text(self.env["ir.config_parameter"].sudo().get_param(key, default))
        except Exception:
            return _text(default)

    def _source_db_name(self) -> str:
        return self._config_param("smart_core.release_operator.catalog_source_db", "") or "sc_demo"

    def _platform_db_name(self) -> str:
        return self._config_param("smart_core.platform_release_db", "") or "sc_platform_core"

    def _probe_login(self, explicit_login: str = "") -> str:
        return _text(explicit_login) or self._config_param("smart_core.release_operator.runtime_probe_login", "") or "wutao"

    def _with_db_env(self, db_name: str, callback):
        if api is None or Registry is None:
            raise RuntimeError("ODOO_REGISTRY_UNAVAILABLE")
        current_db = _text(getattr(getattr(self.env, "cr", None), "dbname", ""))
        if db_name and db_name == current_db:
            return callback(self.env)
        registry = Registry(db_name)
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, dict(getattr(self.env, "context", {}) or {}))
            return callback(env)

    def _active_snapshot(self, *, product_key: str) -> dict[str, Any]:
        platform_db = self._platform_db_name()

        def _read(platform_env):
            snapshot = platform_env["sc.edition.release.snapshot"].sudo().search(
                [
                    ("product_key", "=", product_key),
                    ("state", "=", "released"),
                    ("is_active", "=", True),
                    ("active", "=", True),
                ],
                order="released_at desc, activated_at desc, id desc",
                limit=1,
            )
            return snapshot.to_runtime_dict() if snapshot else {}

        return self._with_db_env(platform_db, _read)

    def _active_release_pages(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        meta = _dict(snapshot.get("meta_json"))
        release_draft = _dict(meta.get("release_draft"))
        pages = [
            row
            for row in _list(release_draft.get("pages"))
            if isinstance(row, dict)
            and bool(row.get("enabled", True))
            and (_text(row.get("release_state")) or "released") in {"released", "preview"}
        ]
        return [dict(row) for row in pages]

    def _allowed_values_from_pages(self, pages: list[dict[str, Any]]) -> set[str]:
        values: set[str] = set()
        for page in pages:
            for key in ("page_key", "menu_key", "menu_xmlid", "route", "scene_key", "res_model"):
                token = _text(page.get(key))
                if token:
                    values.add(token)
            menu_id = _to_int(page.get("menu_id"))
            action_id = _to_int(page.get("action_id"))
            if menu_id:
                values.add(f"system.menu_{menu_id}")
            if action_id:
                values.add(f"/a/{action_id}")
        return values

    def _iter_leaves(self, nodes: list[dict[str, Any]], path: list[str] | None = None):
        current_path = list(path or [])
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            label = _text(node.get("label") or node.get("title"))
            next_path = current_path + ([label] if label else [])
            children = node.get("children") if isinstance(node.get("children"), list) else []
            if children:
                yield from self._iter_leaves(children, next_path)
                continue
            yield node, next_path

    def _leaf_values(self, node: dict[str, Any]) -> set[str]:
        meta = _dict(node.get("meta"))
        entry_target = _dict(meta.get("entry_target"))
        refs = _dict(entry_target.get("compatibility_refs"))
        values = {
            _text(node.get("key")),
            _text(node.get("route")),
            _text(node.get("scene_key")),
            _text(node.get("menu_xmlid")),
            _text(node.get("model")),
            _text(meta.get("route")),
            _text(meta.get("scene_key")),
            _text(meta.get("menu_key")),
            _text(meta.get("menu_xmlid")),
            _text(meta.get("model")),
            _text(entry_target.get("route")),
            _text(entry_target.get("scene_key")),
            _text(refs.get("model")),
        }
        menu_id = node.get("menu_id") or meta.get("menu_id") or refs.get("menu_id")
        action_id = meta.get("action_id") or refs.get("action_id")
        if menu_id:
            values.add(f"system.menu_{menu_id}")
        if action_id:
            values.add(f"/a/{action_id}")
        return {item for item in values if item}

    def _leaf_summary(self, node: dict[str, Any], path: list[str]) -> dict[str, Any]:
        meta = _dict(node.get("meta"))
        entry_target = _dict(meta.get("entry_target"))
        refs = _dict(entry_target.get("compatibility_refs"))
        return {
            "key": _text(node.get("key")),
            "label": _text(node.get("label") or node.get("title")),
            "path": " / ".join([item for item in path if item]),
            "route": _text(meta.get("route") or node.get("route") or entry_target.get("route")),
            "scene_key": _text(meta.get("scene_key") or node.get("scene_key") or entry_target.get("scene_key")),
            "menu_id": _to_int(meta.get("menu_id") or node.get("menu_id") or refs.get("menu_id")),
            "menu_key": _text(meta.get("menu_key")),
            "menu_xmlid": _text(meta.get("menu_xmlid") or node.get("menu_xmlid")),
            "action_id": _to_int(meta.get("action_id") or refs.get("action_id")),
            "res_model": _text(meta.get("model") or node.get("model") or refs.get("model")),
            "entry_target_type": _text(entry_target.get("type")),
        }

    def _filter_leaves(self, nav: list[dict[str, Any]], allowed_values: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        kept: list[dict[str, Any]] = []
        removed: list[dict[str, Any]] = []
        for node, path in self._iter_leaves(nav):
            summary = self._leaf_summary(node, path)
            summary["matched"] = sorted(self._leaf_values(node) & allowed_values)
            if summary["matched"]:
                kept.append(summary)
            else:
                removed.append(summary)
        return kept, removed

    def _source_target_failures(self, source_env, kept: list[dict[str, Any]]) -> list[dict[str, Any]]:
        failures: list[dict[str, Any]] = []
        delivered_scene_keys = {_text(row.get("scene_key")) for row in kept if _text(row.get("scene_key"))}
        for row in kept:
            route = _text(row.get("route"))
            entry_target_type = _text(row.get("entry_target_type"))
            menu_id = _to_int(row.get("menu_id"))
            action_id = _to_int(row.get("action_id"))
            res_model = _text(row.get("res_model"))
            scene_key = _text(row.get("scene_key"))
            if route.startswith("/a/") or action_id or menu_id:
                if scene_key:
                    failures.append({**row, "reason_code": "ACTION_LEAF_HAS_SCENE_KEY"})
                if not action_id:
                    failures.append({**row, "reason_code": "ACTION_ID_MISSING"})
                if not menu_id:
                    failures.append({**row, "reason_code": "MENU_ID_MISSING"})
                if not res_model:
                    failures.append({**row, "reason_code": "RES_MODEL_MISSING"})
                if menu_id:
                    menu = source_env["ir.ui.menu"].sudo().browse(menu_id)
                    if not menu.exists():
                        failures.append({**row, "reason_code": "SOURCE_MENU_NOT_FOUND"})
                if action_id:
                    action = source_env["ir.actions.actions"].sudo().browse(action_id)
                    if not action.exists():
                        failures.append({**row, "reason_code": "SOURCE_ACTION_NOT_FOUND"})
                if res_model and res_model not in getattr(source_env.registry, "models", {}):
                    failures.append({**row, "reason_code": "SOURCE_MODEL_NOT_FOUND"})
            if entry_target_type == "scene" or route.startswith("/s/"):
                if not scene_key:
                    failures.append({**row, "reason_code": "SCENE_KEY_MISSING"})
                elif scene_key not in delivered_scene_keys and route.strip("/") != f"s/{scene_key}".strip("/"):
                    failures.append({**row, "reason_code": "SCENE_ROUTE_MISMATCH"})
        return failures

    def _run_on_source_env(self, source_env, *, product_key: str, login: str, snapshot: dict[str, Any], allowed_values: set[str]) -> dict[str, Any]:
        user = source_env["res.users"].sudo().search([("login", "=", login), ("active", "=", True)], limit=1)
        if not user:
            return {
                "status": "fail",
                "reason_code": "RUNTIME_USER_NOT_FOUND",
                "failure_count": 1,
                "failures": [{"reason_code": "RUNTIME_USER_NOT_FOUND", "login": login}],
            }
        identity = resolve_product_identity(product_key=product_key)
        user_env = api.Environment(source_env.cr, int(user.id), dict(getattr(source_env, "context", {}) or {}))
        delivery = DeliveryEngine(user_env).build(
            data={"role_surface": {"role_code": ""}},
            product_key=identity.get("product_key") or product_key,
            edition_key=identity.get("edition_key"),
            base_product_key=identity.get("base_product_key"),
            native_nav=[],
        )
        nav = _list(delivery.get("nav"))
        kept, removed = self._filter_leaves(nav, allowed_values)
        failures = self._source_target_failures(source_env, kept)
        status = "fail" if failures else ("warn" if removed else "pass")
        company = getattr(user, "company_id", None)
        return {
            "status": status,
            "reason_code": "OK" if status == "pass" else ("RUNTIME_TARGET_FAILURES" if failures else "RUNTIME_RELEASE_GATE_REMOVED_LEAVES"),
            "source_db": _text(getattr(getattr(source_env, "cr", None), "dbname", "")),
            "login": login,
            "user_id": int(user.id or 0),
            "company_id": int(company.id or 0) if company else 0,
            "company_name": _text(getattr(company, "name", "")) if company else "",
            "product_key": product_key,
            "snapshot_id": int(snapshot.get("id") or 0),
            "snapshot_version": _text(snapshot.get("version")),
            "allowed_page_count": len(allowed_values),
            "delivered_leaf_count": len(kept) + len(removed),
            "kept_leaf_count": len(kept),
            "removed_leaf_count": len(removed),
            "failure_count": len(failures),
            "failures": failures[:20],
            "kept_sample": kept[:10],
            "removed_sample": removed[:10],
            "delivery_meta": deepcopy(_dict(delivery.get("meta"))),
        }

    def probe(self, *, product_key: str, login: str = "") -> dict[str, Any]:
        product_key = _text(product_key)
        login = self._probe_login(login)
        source_db = self._source_db_name()
        platform_db = self._platform_db_name()
        base = {
            "contract_version": "release_runtime_user_probe_v1",
            "source_authority": self.source_authority_contract(),
            "product_key": product_key,
            "login": login,
            "source_db": source_db,
            "platform_db": platform_db,
        }
        if not product_key:
            return {**base, "status": "fail", "reason_code": "PRODUCT_KEY_REQUIRED", "failure_count": 1, "failures": []}
        try:
            snapshot = self._active_snapshot(product_key=product_key)
            if not snapshot:
                return {
                    **base,
                    "status": "warn",
                    "reason_code": "ACTIVE_RELEASE_SNAPSHOT_NOT_FOUND",
                    "failure_count": 0,
                    "failures": [],
                }
            pages = self._active_release_pages(snapshot)
            allowed_values = self._allowed_values_from_pages(pages)
            if not allowed_values:
                return {
                    **base,
                    "status": "fail",
                    "reason_code": "ACTIVE_RELEASE_HAS_NO_ALLOWED_PAGES",
                    "snapshot_id": int(snapshot.get("id") or 0),
                    "snapshot_version": _text(snapshot.get("version")),
                    "failure_count": 1,
                    "failures": [{"reason_code": "ACTIVE_RELEASE_HAS_NO_ALLOWED_PAGES"}],
                }
            result = self._with_db_env(
                source_db,
                lambda source_env: self._run_on_source_env(
                    source_env,
                    product_key=product_key,
                    login=login,
                    snapshot=snapshot,
                    allowed_values=allowed_values,
                ),
            )
            return {**base, **result}
        except Exception as exc:
            return {
                **base,
                "status": "warn",
                "reason_code": "RUNTIME_PROBE_UNAVAILABLE",
                "failure_count": 0,
                "failures": [],
                "error": _text(exc),
            }
