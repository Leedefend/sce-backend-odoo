# -*- coding: utf-8 -*-
from __future__ import annotations
import json
import re
from odoo.addons.smart_core.core.source_authority import build_source_authority_contract
from odoo.addons.smart_core.core.delivery_menu_defaults import (
    build_delivery_menu_child,
    build_delivery_menu_group,
    build_delivery_menu_root,
    synthetic_menu_id,
)
from odoo.addons.smart_core.delivery.menu_delivery_convergence_service import MenuDeliveryConvergenceService
from odoo.addons.smart_core.delivery.native_config_menu_projection import native_config_delivery_groups
from odoo.addons.smart_core.utils.backend_contract_boundaries import MENU_CONFIG_POLICY_MODEL
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first

_PREVIEW_GROUP_ANCHOR_SKIPPED_LABELS = {"系统菜单", "业务菜单"}
_CUSTOMER_ACCEPTANCE_GROUP_LABELS: set[str] = set()


def register_preview_group_anchor_skipped_label(label: str) -> None:
    text = str(label or "").strip()
    if text:
        _PREVIEW_GROUP_ANCHOR_SKIPPED_LABELS.add(text)


def register_customer_acceptance_group_label(label: str) -> None:
    text = str(label or "").strip()
    if text:
        _CUSTOMER_ACCEPTANCE_GROUP_LABELS.add(text)


class MenuService:
    SOURCE_KIND = "delivery_menu_projection"
    SOURCE_AUTHORITIES = ("odoo_menu_fact_projection", "menu_delivery_convergence_projection", "delivery_product_policy_projection")
    NO_BUSINESS_FACT_AUTHORITY = True
    NATIVE_PREVIEW_GROUP_KEY = "native_preview"
    NATIVE_PREVIEW_GROUP_LABEL = "系统菜单"
    BUSINESS_INTENT_BUCKETS = (
        ("handling", "办理入口", 10, {"handling"}),
        ("ledger_query", "台账查询", 20, {"query", "master_data"}),
        ("analysis", "分析报表", 30, {"analysis"}),
        ("source_fact", "来源明细", 40, {"source_fact"}),
        ("config", "配置管理", 50, {"config"}),
    )
    BUSINESS_GROUP_DISPLAY_ORDER = {
        "基础资料": 5,
        "人事行政": 70,
        "资料证照": 80,
        "配置中心": 990,
        "配置": 990,
        "系统配置": 990,
    }

    def __init__(self, env=None):
        self.env = env
        self._business_group_display_order = self._resolve_business_group_display_order()

    def _resolve_business_group_display_order(self) -> dict:
        order = dict(self.BUSINESS_GROUP_DISPLAY_ORDER)
        if self.env is None:
            return order
        hook_payload = call_extension_hook_first(self.env, "smart_core_business_nav_group_display_order", self.env)
        if isinstance(hook_payload, dict):
            for label, sequence in hook_payload.items():
                label = str(label or "").strip()
                if not label:
                    continue
                try:
                    order[label] = int(sequence)
                except Exception:
                    continue
        return order

    @classmethod
    def source_authority_contract(cls) -> dict:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            runtime_carrier="delivery_engine_v1.nav",
        )

    def _is_admin_role(self, role_code: str) -> bool:
        normalized = str(role_code or "").strip().lower()
        return normalized in {"admin", "platform_admin", "system_admin", "administrator"}

    def _is_business_config_role(self, role_code: str) -> bool:
        normalized = str(role_code or "").strip().lower()
        return normalized in {"executive", "business_config_admin", "business_admin", "implementation_admin"}

    def _converged_menu(
        self,
        *,
        menu: dict,
        group_label: str,
        role_code: str,
        is_admin: bool = False,
        is_business_config_admin: bool = False,
    ):
        row = dict(menu or {})
        label = str(row.get("label") or "").strip()
        if not label:
            return None
        if row.get("native_preview"):
            row["delivery_bucket"] = "native_preview"
            row["source_authority"] = self.source_authority_contract()
            return row
        if str(row.get("scene_source") or "").strip() == "native_business_config_menu_projection":
            row["delivery_bucket"] = "delivery_business_config"
            row["source_authority"] = self.source_authority_contract()
            return row
        service = MenuDeliveryConvergenceService(self.env)
        category = service._classify_leaf(
            label,
            [group_label, label],
            is_admin=bool(is_admin) or self._is_admin_role(role_code),
            is_business_config_admin=bool(is_business_config_admin) or self._is_business_config_role(role_code),
        )
        if category.startswith("hidden_"):
            return None
        renamed = service.rename_labels.get(label)
        if renamed:
            row["label"] = renamed
        row["delivery_bucket"] = category
        row["source_authority"] = self.source_authority_contract()
        return row

    def _node_has_target(self, node: dict) -> bool:
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        return bool(
            node.get("route")
            or node.get("scene_key")
            or node.get("action_id")
            or node.get("model")
            or meta.get("route")
            or meta.get("scene_key")
            or meta.get("action_id")
            or meta.get("model")
        )

    def _iter_leaf_nodes(self, nodes, ancestors=None):
        parent_chain = list(ancestors or [])
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            children = node.get("children") if isinstance(node.get("children"), list) else []
            if children:
                yield from self._iter_leaf_nodes(children, parent_chain + [node])
                continue
            yield parent_chain, node

    def _resolve_preview_group_anchor(self, ancestors: list[dict]) -> tuple[str, str, int]:
        skipped_labels = _PREVIEW_GROUP_ANCHOR_SKIPPED_LABELS
        for ancestor in ancestors or []:
            if not isinstance(ancestor, dict):
                continue
            key = str(ancestor.get("key") or "").strip()
            if key.startswith("root:"):
                continue
            label = str(ancestor.get("label") or ancestor.get("title") or ancestor.get("name") or "").strip()
            if label in skipped_labels:
                continue
            menu_id = ancestor.get("menu_id")
            if (isinstance(menu_id, int) and menu_id > 0) and label:
                return f"menu_{menu_id}", label, int(menu_id)
        for ancestor in ancestors or []:
            if not isinstance(ancestor, dict):
                continue
            label = str(ancestor.get("label") or ancestor.get("title") or ancestor.get("name") or "").strip()
            if label in skipped_labels:
                continue
            if label:
                key = str(ancestor.get("key") or "").strip().replace(":", "_") or "ungrouped"
                return key, label, 0
        return "ungrouped", "业务菜单", 0

    def _menu_dedupe_key(self, row: dict) -> str:
        menu_id = row.get("menu_id")
        if isinstance(menu_id, int) and menu_id > 0:
            return f"menu_id:{menu_id}"
        scene_key = str(row.get("scene_key") or "").strip()
        if scene_key:
            return f"scene:{scene_key}"
        route = str(row.get("route") or "").strip()
        if route:
            return f"route:{route}"
        menu_xmlid = str(row.get("menu_xmlid") or "").strip()
        if menu_xmlid:
            return f"xmlid:{menu_xmlid}"
        return f"label:{str(row.get('label') or '').strip()}"

    def _positive_int(self, value) -> int:
        try:
            number = int(value or 0)
        except Exception:
            return 0
        return number if number > 0 else 0

    def _node_sequence(self, node: dict) -> int:
        sequence = self._positive_int(node.get("sequence"))
        if sequence:
            return sequence
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        sequence = self._positive_int(meta.get("sequence"))
        if sequence:
            return sequence
        child_sequences = [
            self._node_sequence(child)
            for child in (node.get("children") if isinstance(node.get("children"), list) else [])
            if isinstance(child, dict) and self._node_sequence(child) > 0
        ]
        return min(child_sequences) if child_sequences else 0

    def _sort_delivery_nodes(self, nodes: list[dict], *, top_level: bool = False) -> list[dict]:
        decorated = []
        for index, node in enumerate(nodes or []):
            if not isinstance(node, dict):
                continue
            next_node = dict(node)
            children = next_node.get("children") if isinstance(next_node.get("children"), list) else []
            if children:
                next_node["children"] = self._sort_delivery_nodes(children, top_level=False)
            decorated.append((index, next_node))

        def sort_key(item):
            index, node = item
            label = str(node.get("label") or node.get("title") or "").strip()
            if top_level:
                group_rank = self._business_group_display_order.get(label, 500)
                return (group_rank, self._node_sequence(node) or 9999, index)
            return (self._node_sequence(node) or 9999, index)

        return [node for _index, node in sorted(decorated, key=sort_key)]

    def _policy_has_menu_surface(self, policy: dict) -> bool:
        for group in policy.get("menu_groups") or []:
            if not isinstance(group, dict):
                continue
            for menu in group.get("menus") or []:
                if isinstance(menu, dict) and str(menu.get("label") or "").strip():
                    return True
        return False

    def _policy_is_customer_acceptance_focus(self, policy: dict) -> bool:
        for group in policy.get("menu_groups") or []:
            if not isinstance(group, dict):
                continue
            group_key = str(group.get("group_key") or "").strip()
            category = str(group.get("category") or "").strip()
            if group_key.startswith("catalog.acceptance.") or category.startswith("customer_acceptance_"):
                return True
        return False

    def _release_menu_enabled(self, menu: dict) -> bool:
        if not isinstance(menu, dict):
            return False
        if menu.get("enabled") is False:
            return False
        release_state = str(menu.get("release_state") or "released").strip().lower() or "released"
        return release_state in {"released", "preview", "stable", "public"}

    def _native_authorized_menu_index(self, native_nav: list[dict]) -> dict[str, set]:
        index = {"ids": set(), "xmlids": set(), "scenes": set(), "routes": set()}
        def visit(nodes):
            for node in nodes or []:
                if not isinstance(node, dict):
                    continue
                yield node
                children = node.get("children") if isinstance(node.get("children"), list) else []
                yield from visit(children)

        # Policy entries may legitimately target a visible parent action/menu,
        # not only a leaf.  Index every user-visible native node so the policy
        # intersection does not discard valid entries before parent-chain
        # reconstruction.  The native tree is already built under the real
        # request user, so this remains an authorization check rather than a
        # sudo-derived catalog lookup.
        for leaf in visit(native_nav or []):
            if not isinstance(leaf, dict):
                continue
            meta = leaf.get("meta") if isinstance(leaf.get("meta"), dict) else {}
            menu_id = leaf.get("menu_id") or meta.get("menu_id")
            try:
                menu_id_int = int(menu_id or 0)
            except Exception:
                menu_id_int = 0
            if menu_id_int > 0:
                index["ids"].add(menu_id_int)
            menu_xmlid = str(meta.get("menu_xmlid") or leaf.get("menu_xmlid") or "").strip()
            if menu_xmlid:
                index["xmlids"].add(menu_xmlid)
            scene_key = str(leaf.get("scene_key") or meta.get("scene_key") or "").strip()
            if scene_key:
                index["scenes"].add(scene_key)
            route = str(leaf.get("route") or meta.get("route") or "").strip()
            if route:
                index["routes"].add(route)
        return index

    def _policy_menu_user_authorized(
        self,
        menu: dict,
        native_index: dict[str, set],
        *,
        is_admin: bool = False,
        is_business_config_admin: bool = False,
    ) -> bool:
        if is_admin or is_business_config_admin:
            return True
        menu_xmlid = str(menu.get("menu_xmlid") or "").strip()
        if menu_xmlid and menu_xmlid in native_index.get("xmlids", set()):
            return True
        menu_id = menu.get("menu_id")
        try:
            menu_id_int = int(menu_id or 0)
        except Exception:
            menu_id_int = 0
        if menu_id_int > 0 and menu_id_int in native_index.get("ids", set()):
            return True
        scene_key = str(menu.get("scene_key") or "").strip()
        if scene_key and scene_key in native_index.get("scenes", set()):
            return True
        route = str(menu.get("route") or "").strip()
        if route and route in native_index.get("routes", set()):
            return True
        return False

    def _flatten_policy_menus(self, policy: dict) -> list[dict]:
        out = []
        index = 0
        productization_keys = (
            "product_domain",
            "product_domain_label",
            "entry_intent",
            "entry_intent_label",
            "fact_model",
            "disposition_policy",
            "integration_target",
            "default_business_category_code",
            "allowed_business_category_codes",
            "required_relationships",
            "locked_data_policy",
            "productization_source",
            "business_entry_contract_version",
            "entry_target_policy",
            "integration_action_id",
            "integration_action_xmlid",
            "integration_view_modes",
            "integration_entry_target",
            "integration_model",
            "record_scope_policy",
            "project_scope_policy",
        )
        for group in policy.get("menu_groups") or []:
            if not isinstance(group, dict):
                continue
            for menu in group.get("menus") or []:
                if not isinstance(menu, dict):
                    continue
                if not self._release_menu_enabled(menu):
                    continue
                index += 1
                scene_key = str(menu.get("scene_key") or "").strip()
                menu_id = menu.get("menu_id")
                route = str(menu.get("route") or "").strip()
                action_id = menu.get("action_id")
                menu_xmlid = str(menu.get("menu_xmlid") or "").strip()
                if route.startswith("/a/") and scene_key == menu_xmlid:
                    scene_key = ""
                raw_anchor = scene_key or (str(menu_id) if isinstance(menu_id, int) and menu_id > 0 else str(menu.get("menu_key") or "").strip() or str(index))
                sanitized_anchor = raw_anchor.replace(":", "_").replace("/", "_").replace(".", "_")
                model = str(menu.get("model") or menu.get("res_model") or "").strip()
                if not action_id and not model and not scene_key and not route:
                    continue
                row = {
                    "menu_key": f"system.policy.{sanitized_anchor}",
                    "label": str(menu.get("label") or "").strip(),
                    "menu_id": menu_id,
                    "route": route,
                    "scene_key": scene_key,
                    "product_key": str(menu.get("product_key") or "").strip(),
                    "capability_key": str(menu.get("capability_key") or "").strip(),
                    "menu_xmlid": menu_xmlid,
                    "action_id": action_id,
                    "action_xmlid": str(menu.get("action_xmlid") or "").strip(),
                    "model": model,
                    "view_modes": menu.get("view_modes") if isinstance(menu.get("view_modes"), list) else [],
                    "sequence": self._positive_int(menu.get("sequence")),
                    "scene_source": "delivery_policy",
                    "policy_group_key": str(group.get("group_key") or "").strip(),
                    "policy_group_label": str(group.get("group_label") or "").strip(),
                    "visible_menu_path": str(menu.get("visible_menu_path") or "").strip(),
                    "entry_target": menu.get("entry_target") if isinstance(menu.get("entry_target"), dict) else {},
                }
                for key in productization_keys:
                    value = menu.get(key)
                    if value not in (None, "", []):
                        row[key] = value
                out.append(row)
        return [row for row in out if row.get("menu_key") and row.get("label")]

    def _policy_menu_path_parts(self, menu: dict) -> list[str]:
        path = str(menu.get("visible_menu_path") or "").strip()
        if not path:
            return []
        return [part.strip() for part in re.split(r"\s+/\s+", path) if part.strip()]

    def _acceptance_menu_group_parts(self, menu: dict, group_label: str) -> list[str]:
        parts = self._policy_menu_path_parts(menu)
        for index, part in enumerate(parts):
            if part == group_label:
                return [item for item in parts[index + 1 : -1] if item and item != group_label]
        return []

    def _append_policy_path_child(
        self,
        *,
        nodes: list[dict],
        parent_key: str,
        group_label: str,
        menu: dict,
        child: dict,
        group_config_menu_ids_by_label: dict[str, int] | None = None,
    ) -> None:
        group_parts = self._acceptance_menu_group_parts(menu, group_label)
        if not group_parts:
            nodes.append(child)
            return
        self._append_acceptance_child(
            nodes=nodes,
            parent_key=parent_key,
            group_parts=group_parts,
            child=child,
            group_config_menu_ids_by_label=group_config_menu_ids_by_label,
        )

    def _acceptance_group_key(self, parent_key: str, label: str, index: int) -> str:
        safe = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", str(label or "").strip()).strip("_")
        return f"{parent_key}.{safe or index}"

    def _append_acceptance_child(
        self,
        *,
        nodes: list[dict],
        parent_key: str,
        group_parts: list[str],
        child: dict,
        group_config_menu_ids_by_label: dict[str, int] | None = None,
    ) -> None:
        if not group_parts:
            nodes.append(child)
            return
        label = group_parts[0]
        group = next((row for row in nodes if row.get("label") == label and str(row.get("key") or "").startswith("group:")), None)
        if not group:
            group = build_delivery_menu_group(
                self._acceptance_group_key(parent_key, label, len(nodes) + 1),
                label,
                [],
                config_menu_id=int((group_config_menu_ids_by_label or {}).get(label) or 0),
            )
            meta = dict(group.get("meta") if isinstance(group.get("meta"), dict) else {})
            meta["explicit_menu_path_group"] = True
            group["meta"] = meta
            nodes.append(group)
        next_parent_key = str((group.get("meta") or {}).get("group_key") or parent_key)
        self._append_acceptance_child(
            nodes=group.setdefault("children", []),
            parent_key=next_parent_key,
            group_parts=group_parts[1:],
            child=child,
            group_config_menu_ids_by_label=group_config_menu_ids_by_label,
        )

    def _business_entry_intent(self, node: dict) -> str:
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        return str(meta.get("entry_intent") or "").strip()

    def _business_intent_bucket(self, node: dict) -> tuple[str, str, int, set] | None:
        intent = self._business_entry_intent(node)
        if intent:
            for bucket in self.BUSINESS_INTENT_BUCKETS:
                if intent in bucket[3]:
                    return bucket
        for child in (node.get("children") if isinstance(node.get("children"), list) else []):
            if not isinstance(child, dict):
                continue
            bucket = self._business_intent_bucket(child)
            if bucket:
                return bucket
        return None

    def _has_business_entry_intent(self, node: dict) -> bool:
        if self._business_entry_intent(node):
            return True
        return any(
            self._has_business_entry_intent(child)
            for child in (node.get("children") if isinstance(node.get("children"), list) else [])
            if isinstance(child, dict)
        )

    def _intent_labeled_node(self, node: dict) -> dict:
        if not isinstance(node, dict):
            return node
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        intent = str(meta.get("entry_intent") or "").strip()
        if not intent:
            return node
        label = str(node.get("label") or node.get("title") or "").strip()
        if not label:
            return node
        next_label = label
        if intent in {"query", "master_data"}:
            if not any(token in label for token in ("台账", "查询", "名册", "资料", "客户", "供应商")):
                next_label = f"{label}查询"
        elif intent == "analysis":
            if not any(token in label for token in ("报表", "分析", "总览", "余额", "明细")):
                next_label = f"{label}报表"
        elif intent == "source_fact":
            if not any(token in label for token in ("明细", "来源", "表", "记录")):
                next_label = f"{label}明细"
        elif intent == "config":
            if not any(token in label for token in ("配置", "设置", "字典")):
                next_label = f"{label}配置"
        if next_label == label:
            return node
        next_node = dict(node)
        next_node["label"] = next_label
        next_node["title"] = next_label
        next_meta = dict(meta)
        next_meta["original_label"] = label
        next_meta["intent_label_applied"] = True
        next_node["meta"] = next_meta
        return next_node

    def _merge_by_category_key(self, node: dict) -> str:
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        if str(meta.get("disposition_policy") or "").strip() != "merge_by_category":
            return ""
        target = str(meta.get("integration_target") or "").strip()
        model = str(meta.get("integration_model") or meta.get("fact_model") or meta.get("model") or "").strip()
        if not target or not model:
            return ""
        return f"{model}::{target}"

    def _merge_by_category_label(self, node: dict) -> str:
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        target = str(meta.get("integration_target") or "").strip()
        if not target:
            return "分类办理"
        label = re.sub(r"^[A-Za-z0-9_.]+[/\s]*", "", target).strip()
        return label or target

    def _merged_integration_meta(self, items: list[dict]) -> dict:
        action_ids = set()
        first_meta = {}
        for item in items:
            meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
            try:
                action_id = int(meta.get("integration_action_id") or 0)
            except Exception:
                action_id = 0
            if action_id > 0:
                action_ids.add(action_id)
                if not first_meta:
                    first_meta = meta
        if len(action_ids) != 1 or not first_meta:
            return {}
        view_modes = first_meta.get("integration_view_modes")
        entry_target = first_meta.get("integration_entry_target")
        return {
            "action_id": next(iter(action_ids)),
            "action_xmlid": str(first_meta.get("integration_action_xmlid") or "").strip(),
            "model": str(first_meta.get("integration_model") or first_meta.get("fact_model") or first_meta.get("model") or "").strip(),
            "view_modes": view_modes if isinstance(view_modes, list) else [],
            "entry_target": entry_target if isinstance(entry_target, dict) else {},
        }

    def _merged_record_scope_policy(self, items: list[dict]) -> str:
        policies = {
            str(
                (item.get("meta") or {}).get("record_scope_policy")
                or (item.get("meta") or {}).get("project_scope_policy")
                or ""
            ).strip().lower()
            for item in items or []
            if isinstance(item, dict) and isinstance(item.get("meta"), dict)
        }
        policies.discard("")
        if "current_project" in policies:
            policies.discard("current_project")
            policies.add("current_record")
        if not policies:
            return ""
        if policies == {"current_record"}:
            return "current_record"
        if "current_record" in policies:
            return "current_record"
        if "global" in policies:
            return "global"
        if "exempt" in policies:
            return "exempt"
        return ""

    def _merged_project_scope_policy(self, items: list[dict]) -> str:
        policy = self._merged_record_scope_policy(items)
        if policy == "current_record":
            return "current_project"
        return policy

    def _business_category_codes(self, items: list[dict]) -> list[str]:
        codes = []
        seen = set()
        for item in items or []:
            if not isinstance(item, dict):
                continue
            meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
            raw_allowed = meta.get("allowed_business_category_codes")
            candidates = raw_allowed if isinstance(raw_allowed, list) and raw_allowed else [meta.get("default_business_category_code")]
            for candidate in candidates:
                code = str(candidate or "").strip()
                if code and code not in seen:
                    seen.add(code)
                    codes.append(code)
        return codes

    def _business_category_options(self, items: list[dict]) -> list[dict]:
        codes = self._business_category_codes(items)
        category_by_code = self._business_category_default_index(codes)
        options = []
        seen = set()
        item_by_code = {}
        for item in items or []:
            if not isinstance(item, dict):
                continue
            meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
            default_code = str(meta.get("default_business_category_code") or "").strip()
            raw_allowed = meta.get("allowed_business_category_codes")
            candidates = raw_allowed if isinstance(raw_allowed, list) and raw_allowed else [default_code]
            for candidate in candidates:
                code = str(candidate or "").strip()
                if code and code not in item_by_code:
                    item_by_code[code] = item
        for code in codes:
            if not code or code in seen:
                continue
            seen.add(code)
            category = category_by_code.get(code, {})
            default_values = category.get("default_values") if isinstance(category.get("default_values"), dict) else {}
            category_id = category.get("id")
            item = item_by_code.get(code, {})
            meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
            label = str(
                category.get("name")
                or meta.get("default_business_category_label")
                or meta.get("current_business_category_label")
                or item.get("label")
                or item.get("title")
                or ""
            ).strip()
            options.append(
                {
                    "code": code,
                    "label": label,
                    "category_id": category_id,
                    "default_values": default_values,
                    "menu_id": item.get("menu_id") or item.get("id"),
                    "menu_xmlid": str(meta.get("menu_xmlid") or "").strip(),
                    "integration_target": str(meta.get("integration_target") or "").strip(),
                }
            )
        return options

    def _business_category_default_index(self, codes: list[str]) -> dict[str, dict]:
        if not codes or self.env is None or "sc.business.category" not in self.env:
            return {}
        categories = self.env["sc.business.category"].sudo().search([("code", "in", codes)])
        index = {}
        for category in categories:
            defaults = {}
            raw_defaults = str(category.default_values_json or "").strip()
            if raw_defaults:
                try:
                    parsed = json.loads(raw_defaults)
                    if isinstance(parsed, dict):
                        defaults = parsed
                except Exception:
                    defaults = {}
            index[str(category.code or "").strip()] = {
                "id": category.id,
                "name": category.name,
                "default_values": defaults,
            }
        return index

    def _group_merge_by_category_nodes(self, nodes: list[dict], parent_key: str = "") -> list[dict]:
        grouped = {}
        passthrough = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            key = self._merge_by_category_key(node)
            if not key:
                passthrough.append(node)
                continue
            grouped.setdefault(key, []).append(node)
        synthetic_groups = []
        for key, items in grouped.items():
            first = items[0]
            meta = first.get("meta") if isinstance(first.get("meta"), dict) else {}
            integration_meta = self._merged_integration_meta(items)
            if not integration_meta:
                synthetic_groups.extend(items)
                continue
            label = self._merge_by_category_label(first)
            node_key = f"{parent_key}.merge_by_category:{key}" if parent_key else f"merge_by_category:{key}"
            sequence_candidates = [
                self._node_sequence(item)
                for item in items
                if self._node_sequence(item) > 0
            ]
            sequence = min(sequence_candidates) if sequence_candidates else 0
            record_scope_policy = self._merged_record_scope_policy(items)
            group_meta = {
                "business_entry_group": True,
                "synthetic": True,
                "configurable": False,
                "node_kind": "navigation_group",
                "merge_by_category_group": len(items) > 1,
                "single_category_integrated_entry": len(items) <= 1,
                "allowed_business_category_codes": self._business_category_codes(items),
                "business_category_options": self._business_category_options(items),
                "product_domain": meta.get("product_domain"),
                "product_domain_label": meta.get("product_domain_label"),
                "integration_target": meta.get("integration_target"),
                "fact_model": meta.get("fact_model") or meta.get("model"),
                "integration_model": meta.get("integration_model"),
                "entry_intent": meta.get("entry_intent"),
                "entry_intent_label": meta.get("entry_intent_label"),
                "disposition_policy": meta.get("disposition_policy"),
                "business_entry_contract_version": meta.get("business_entry_contract_version"),
                "entry_target_policy": "merge_to_list_form_by_business_category",
                "record_scope_policy": record_scope_policy,
                "project_scope_policy": "current_project" if record_scope_policy == "current_record" else record_scope_policy,
                "source": "delivery_engine_v1",
                "source_authority": self.source_authority_contract(),
            }
            for field in ("action_id", "action_xmlid", "model", "view_modes", "entry_target"):
                value = integration_meta.get(field)
                if value not in (None, "", []):
                    group_meta[field] = value
            route = ""
            entry_target = group_meta.get("entry_target") if isinstance(group_meta.get("entry_target"), dict) else {}
            if entry_target:
                route = str(entry_target.get("route") or "").strip()
                if route:
                    group_meta["route"] = route
            node = {
                "key": node_key,
                "label": label,
                "title": label,
                "menu_id": synthetic_menu_id(node_key, base=870_000_000, span=10_000_000),
                "children": [],
                "meta": group_meta,
                "configurable": False,
            }
            for field in ("action_id", "action_xmlid", "model", "view_modes", "entry_target", "route"):
                value = group_meta.get(field)
                if value not in (None, "", []):
                    node[field] = value
            if sequence > 0:
                node["sequence"] = sequence
                group_meta["sequence"] = sequence
            synthetic_groups.append(node)
        return passthrough + synthetic_groups

    def _group_children_by_business_intent(self, nodes: list[dict], parent_key: str = "") -> list[dict]:
        next_nodes = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            children = node.get("children") if isinstance(node.get("children"), list) else []
            if children:
                node = dict(node)
                child_key = str(node.get("key") or node.get("menu_id") or node.get("id") or parent_key).strip()
                node["children"] = self._group_children_by_business_intent(children, parent_key=child_key)
            next_nodes.append(node)
        bucketed = {}
        passthrough = []
        for node in next_nodes:
            meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
            if meta.get("explicit_menu_path_group"):
                passthrough.append(node)
                continue
            bucket = self._business_intent_bucket(node)
            if not bucket:
                passthrough.append(node)
                continue
            bucketed.setdefault(bucket[0], []).append(node)
        productized_count = sum(len(items) for items in bucketed.values())
        if productized_count < 1:
            return next_nodes
        flattened = []
        for bucket_key, label, sequence, _intents in self.BUSINESS_INTENT_BUCKETS:
            items = bucketed.get(bucket_key) or []
            if not items:
                continue
            intent_parent_key = parent_key or "root"
            children = (
                self._group_merge_by_category_nodes(items, parent_key=f"{intent_parent_key}.intent.{bucket_key}")
                if bucket_key == "handling"
                else items
            )
            for child in self._sort_delivery_nodes(children):
                next_child = self._intent_labeled_node(child)
                next_child = dict(next_child)
                next_child.setdefault("sequence", int(next_child.get("sequence") or sequence))
                meta = dict(next_child.get("meta") if isinstance(next_child.get("meta"), dict) else {})
                meta.setdefault("intent_group", bucket_key)
                meta.setdefault("business_entry_group", True)
                meta.setdefault("source_authority", self.source_authority_contract())
                next_child["meta"] = meta
                flattened.append(next_child)
        passthrough_items = [
            item
            for item in passthrough
            if (
                (isinstance(item.get("meta"), dict) and item["meta"].get("explicit_menu_path_group"))
                or not self._has_business_entry_intent(item)
            )
        ]
        return self._sort_delivery_nodes(passthrough_items) + flattened

    def _native_preview_menus(self, *, native_nav: list[dict], policy: dict) -> list[dict]:
        preview_menus_by_group = {}
        group_order = []
        emitted_menu_ids = set()
        scene_route_map = {}
        for scene in policy.get("scenes") or []:
            if not isinstance(scene, dict):
                continue
            scene_key = str(scene.get("scene_key") or "").strip()
            route = str(scene.get("route") or "").strip()
            if scene_key and route:
                scene_route_map[scene_key] = route
        for ancestors, leaf in self._iter_leaf_nodes(native_nav):
            meta = leaf.get("meta") if isinstance(leaf.get("meta"), dict) else {}
            menu_id = leaf.get("menu_id") or meta.get("menu_id")
            scene_key = str(leaf.get("scene_key") or ((leaf.get("meta") or {}).get("scene_key")) or "").strip()
            label = str(leaf.get("label") or leaf.get("title") or scene_key).strip()
            if not label or not menu_id:
                continue
            try:
                normalized_menu_id = int(menu_id)
            except Exception:
                continue
            if normalized_menu_id <= 0 or normalized_menu_id in emitted_menu_ids:
                continue
            emitted_menu_ids.add(normalized_menu_id)
            anchor_key, anchor_label, anchor_menu_id = self._resolve_preview_group_anchor(ancestors)
            group_key = f"system.{anchor_key}"
            if group_key not in preview_menus_by_group:
                preview_menus_by_group[group_key] = {
                    "group_key": group_key,
                    "group_label": anchor_label,
                    "config_menu_id": anchor_menu_id,
                    "native_preview": True,
                    "menus": [],
                }
                group_order.append(group_key)
            preview_menus_by_group[group_key]["menus"].append(
                {
                    "menu_key": f"system.menu_{normalized_menu_id}",
                    "label": label,
                    "menu_id": normalized_menu_id,
                    "route": str(meta.get("route") or leaf.get("route") or scene_route_map.get(scene_key) or ""),
                    "scene_key": scene_key,
                    "product_key": "",
                    "capability_key": "",
                    "menu_xmlid": str((meta.get("menu_xmlid")) or ""),
                    "scene_source": str((meta.get("scene_source")) or "native_preview"),
                    "native_preview": True,
                    "action_id": meta.get("action_id") or leaf.get("action_id"),
                    "action_xmlid": str(meta.get("action_xmlid") or leaf.get("action_xmlid") or ""),
                    "model": str(meta.get("model") or leaf.get("model") or ""),
                    "sequence": self._positive_int(leaf.get("sequence") or meta.get("sequence")),
                    "entry_target": meta.get("entry_target") if isinstance(meta.get("entry_target"), dict) else {},
                    "view_modes": (
                        meta.get("view_modes")
                        if isinstance(meta.get("view_modes"), list)
                        else (leaf.get("view_modes") if isinstance(leaf.get("view_modes"), list) else [])
                    ),
                }
            )
        return [preview_menus_by_group[group_key] for group_key in group_order]

    def _native_group_config_menu_ids_by_label(self, native_nav: list[dict]) -> dict[str, int]:
        groups: dict[str, int] = {}

        def visit(nodes: list[dict]):
            for node in nodes if isinstance(nodes, list) else []:
                if not isinstance(node, dict):
                    continue
                meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
                label = str(node.get("label") or node.get("title") or node.get("name") or "").strip()
                try:
                    menu_id = int((node.get("menu_id") or meta.get("menu_id") or 0))
                except Exception:
                    menu_id = 0
                children = node.get("children") if isinstance(node.get("children"), list) else []
                has_action = bool(
                    node.get("action_id")
                    or node.get("action")
                    or node.get("model")
                    or meta.get("action_id")
                    or meta.get("model")
                )
                if label and menu_id > 0 and children and not has_action:
                    groups.setdefault(label, menu_id)
                if children:
                    visit(children)

        visit(native_nav or [])
        if self.env is None:
            return groups
        try:
            Menu = self.env["ir.ui.menu"].sudo()
        except Exception:
            return groups

        root_id = 0
        root_xmlid = str(call_extension_hook_first(self.env, "smart_core_business_root_menu_xmlid", self.env) or "").strip()
        if not root_xmlid:
            try:
                root_xmlid = str(
                    self.env["ir.config_parameter"].sudo().get_param("smart_core.business_root_menu_xmlid", "") or ""
                ).strip()
            except Exception:
                root_xmlid = ""
        if root_xmlid and hasattr(self.env, "ref"):
            try:
                root = self.env.ref(root_xmlid, raise_if_not_found=False)
            except TypeError:
                try:
                    root = self.env.ref(root_xmlid)
                except Exception:
                    root = None
            except Exception:
                root = None
            if root and getattr(root, "_name", "") == "ir.ui.menu":
                try:
                    root_id = int(root.id or 0)
                except Exception:
                    root_id = 0
        if not root_id:
            return groups
        try:
            menus = Menu.search([("parent_id", "=", root_id)])
        except Exception:
            return groups
        for menu in menus or []:
            label = str(getattr(menu, "name", "") or "").strip()
            try:
                menu_id = int(getattr(menu, "id", 0) or 0)
            except Exception:
                menu_id = 0
            if label and menu_id:
                groups[label] = menu_id
        return groups

    def _native_runtime_config_menus(
        self,
        *,
        native_nav: list[dict],
        policy: dict,
        role_code: str,
        is_admin: bool,
        is_business_config_admin: bool,
    ) -> list[dict]:
        groups = self._native_preview_menus(native_nav=native_nav, policy=policy)
        out = []
        service = MenuDeliveryConvergenceService(self.env)
        for group in groups:
            if not isinstance(group, dict):
                continue
            group_label = str(group.get("group_label") or "").strip() or "系统菜单"
            menus = []
            for menu in group.get("menus") or []:
                if not isinstance(menu, dict):
                    continue
                label = str(menu.get("label") or "").strip()
                model = str(menu.get("model") or "").strip()
                category = service._classify_leaf(
                    label,
                    [group_label, label],
                    is_admin=bool(is_admin) or self._is_admin_role(role_code),
                    is_business_config_admin=bool(is_business_config_admin) or self._is_business_config_role(role_code),
                )
                if (
                    category == "delivery_business_config"
                    or (model in {MENU_CONFIG_POLICY_MODEL} and (is_admin or is_business_config_admin))
                ):
                    menus.append(menu)
            if menus:
                next_group = dict(group)
                next_group["menus"] = menus
                out.append(next_group)
        return out

    def build_nav(self, *, policy: dict, role_surface: dict | None = None, native_nav: list[dict] | None = None) -> list[dict]:
        import logging
        logging.getLogger(__name__).warning(
            "NAV_IDENTITY uid=%s company=%s allowed=%s policy_key=%s",
            getattr(getattr(self.env, "user", None), "id", None),
            getattr(getattr(self.env, "company", None), "id", None),
            getattr(getattr(self.env, "context", {}), "get", lambda *_: None)("allowed_company_ids"),
            policy.get("product_key") if isinstance(policy, dict) else None,
        )
        role_code = str((role_surface or {}).get("role_code") or "").strip().lower()
        is_admin = bool((role_surface or {}).get("is_platform_admin"))
        is_business_config_admin = bool((role_surface or {}).get("is_business_config_admin")) or self._is_business_config_role(role_code)
        policy_has_menu_surface = self._policy_has_menu_surface(policy)
        customer_acceptance_focus = self._policy_is_customer_acceptance_focus(policy)
        native_index = self._native_authorized_menu_index(native_nav or [])
        native_group_config_ids_by_label = self._native_group_config_menu_ids_by_label(native_nav or [])
        authorized_policy_rows = [
            menu
            for menu in self._flatten_policy_menus(policy)
            if self._policy_menu_user_authorized(
                menu,
                native_index,
                is_admin=is_admin,
                is_business_config_admin=is_business_config_admin,
            )
        ]
        policy_authorized_ids = set()
        policy_authorized_scenes = set()
        policy_authorized_routes = set()
        policy_authorized_xmlids = set()
        for menu in authorized_policy_rows:
            menu_id = menu.get("menu_id")
            scene_key = str(menu.get("scene_key") or "").strip()
            route = str(menu.get("route") or "").strip()
            menu_xmlid = str(menu.get("menu_xmlid") or "").strip()
            if isinstance(menu_id, int) and menu_id > 0:
                policy_authorized_ids.add(menu_id)
            if scene_key:
                policy_authorized_scenes.add(scene_key)
            if route:
                policy_authorized_routes.add(route)
            if menu_xmlid:
                policy_authorized_xmlids.add(menu_xmlid)
        grouped_native = (
            []
            if customer_acceptance_focus and not is_admin
            else self._native_runtime_config_menus(
                    native_nav=native_nav or [],
                    policy=policy,
                    role_code=role_code,
                    is_admin=is_admin,
                    is_business_config_admin=is_business_config_admin,
                )
            if policy_has_menu_surface
            else self._native_preview_menus(native_nav=native_nav or [], policy=policy)
        )
        if self.env is not None and (is_admin or is_business_config_admin):
            grouped_native = native_config_delivery_groups(self.env) + list(grouped_native or [])
        groups_by_key = {}
        group_order = []
        scene_group_map = {}
        dedupe_ids = set()
        dedupe_scenes = set()
        dedupe_routes = set()
        dedupe_xmlids = set()

        if policy_has_menu_surface:
            for group in policy.get("menu_groups") or []:
                if not isinstance(group, dict):
                    continue
                group_label = str(group.get("group_label") or group.get("label") or group.get("title") or "").strip()
                if not group_label:
                    continue
                group_key = str(group.get("group_key") or group.get("key") or "").strip()
                if not group_key:
                    safe_label = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", group_label).strip("_")
                    group_key = f"catalog.{safe_label or 'product_group'}"
                if group_key in groups_by_key:
                    continue
                groups_by_key[group_key] = {
                    "group_key": group_key,
                    "group_label": group_label,
                    "config_menu_id": int(native_group_config_ids_by_label.get(group_label) or 0),
                    "native_preview": False,
                    "menus": [],
                }
                group_order.append(group_key)

        for group in grouped_native:
            if not isinstance(group, dict):
                continue
            group_key = str(group.get("group_key") or "").strip() or "system.ungrouped"
            group_label = str(group.get("group_label") or "").strip() or "系统菜单"
            if group_key not in groups_by_key:
                groups_by_key[group_key] = {
                    "group_key": group_key,
                    "group_label": group_label,
                    "config_menu_id": int(group.get("config_menu_id") or native_group_config_ids_by_label.get(group_label) or 0),
                    "native_preview": bool(group.get("native_preview")),
                    "menus": [],
                }
                group_order.append(group_key)
            elif group.get("native_preview"):
                groups_by_key[group_key]["native_preview"] = True
            if int(group.get("config_menu_id") or 0):
                groups_by_key[group_key]["config_menu_id"] = int(group.get("config_menu_id") or 0)
            elif native_group_config_ids_by_label.get(group_label):
                groups_by_key[group_key].setdefault("config_menu_id", int(native_group_config_ids_by_label[group_label]))
            for menu in group.get("menus") or []:
                if not isinstance(menu, dict):
                    continue
                menu_id = menu.get("menu_id")
                scene_key = str(menu.get("scene_key") or "").strip()
                route = str(menu.get("route") or "").strip()
                menu_xmlid = str(menu.get("menu_xmlid") or "").strip()
                if policy_has_menu_surface and (
                    (isinstance(menu_id, int) and menu_id > 0 and menu_id in policy_authorized_ids)
                    or (scene_key and scene_key in policy_authorized_scenes)
                    or (route and route in policy_authorized_routes)
                    or (menu_xmlid and menu_xmlid in policy_authorized_xmlids)
                ):
                    continue
                converged_menu = self._converged_menu(
                    menu=menu,
                    group_label=group_label,
                    role_code=role_code,
                    is_admin=is_admin,
                    is_business_config_admin=is_business_config_admin,
                )
                if not converged_menu:
                    continue
                if (
                    (isinstance(menu_id, int) and menu_id > 0 and menu_id in dedupe_ids)
                    or (scene_key and scene_key in dedupe_scenes)
                    or (route and route in dedupe_routes)
                    or (menu_xmlid and menu_xmlid in dedupe_xmlids)
                ):
                    continue
                if isinstance(menu_id, int) and menu_id > 0:
                    dedupe_ids.add(menu_id)
                if scene_key:
                    dedupe_scenes.add(scene_key)
                if route:
                    dedupe_routes.add(route)
                if menu_xmlid:
                    dedupe_xmlids.add(menu_xmlid)
                groups_by_key[group_key]["menus"].append(converged_menu)
                if scene_key and scene_key not in scene_group_map:
                    scene_group_map[scene_key] = group_key

        if not group_order:
            fallback_key = "system.ungrouped"
            groups_by_key[fallback_key] = {
                "group_key": fallback_key,
                "group_label": "系统菜单",
                "menus": [],
            }
            group_order.append(fallback_key)

        convergence_service = MenuDeliveryConvergenceService(self.env)
        for menu in authorized_policy_rows:
            converged_menu = dict(menu)
            policy_group_key = str(menu.get("policy_group_key") or "").strip()
            policy_group_label = str(menu.get("policy_group_label") or "").strip()
            preserve_policy_label = (
                policy_group_key.startswith("catalog.acceptance.")
                or policy_group_label in _CUSTOMER_ACCEPTANCE_GROUP_LABELS
            )
            renamed = None if preserve_policy_label else convergence_service.rename_labels.get(str(converged_menu.get("label") or "").strip())
            if renamed:
                converged_menu["label"] = renamed
            converged_menu["delivery_bucket"] = "released_product_policy"
            converged_menu["source_authority"] = self.source_authority_contract()
            menu_id = menu.get("menu_id")
            scene_key = str(menu.get("scene_key") or "").strip()
            route = str(menu.get("route") or "").strip()
            menu_xmlid = str(menu.get("menu_xmlid") or "").strip()
            if (isinstance(menu_id, int) and menu_id > 0 and menu_id in dedupe_ids) or (scene_key and scene_key in dedupe_scenes) or (route and route in dedupe_routes) or (menu_xmlid and menu_xmlid in dedupe_xmlids):
                continue
            if isinstance(menu_id, int) and menu_id > 0:
                dedupe_ids.add(menu_id)
            if scene_key:
                dedupe_scenes.add(scene_key)
            if route:
                dedupe_routes.add(route)
            if menu_xmlid:
                dedupe_xmlids.add(menu_xmlid)
            target_group_key = policy_group_key or scene_group_map.get(scene_key) or group_order[0]
            if target_group_key not in groups_by_key:
                groups_by_key[target_group_key] = {
                    "group_key": target_group_key,
                    "group_label": str(menu.get("policy_group_label") or "").strip() or "产品发布面",
                    "config_menu_id": int(menu.get("policy_group_menu_id") or 0),
                    "menus": [],
                }
                group_order.append(target_group_key)
            groups_by_key[target_group_key]["menus"].append(converged_menu)

        label_to_group_key = {}
        for group_key in group_order:
            row = groups_by_key.get(group_key) or {}
            group_label = str(row.get("group_label") or "").strip()
            if not group_label:
                continue
            current_key = label_to_group_key.get(group_label)
            if not current_key or (
                not str(current_key).startswith("catalog.")
                and str(group_key).startswith("catalog.")
            ):
                label_to_group_key[group_label] = group_key

        merged_groups_by_key = {}
        merged_group_order = []
        for group_key in group_order:
            row = groups_by_key.get(group_key) or {}
            group_label = str(row.get("group_label") or "").strip()
            canonical_key = label_to_group_key.get(group_label) or group_key
            canonical_row = groups_by_key.get(canonical_key) or row
            if canonical_key not in merged_groups_by_key:
                merged_groups_by_key[canonical_key] = {
                    "group_key": canonical_key,
                    "group_label": str(canonical_row.get("group_label") or group_label or "系统菜单"),
                    "config_menu_id": int(canonical_row.get("config_menu_id") or 0),
                    "native_preview": bool(canonical_row.get("native_preview")),
                    "menus": [],
                }
                merged_group_order.append(canonical_key)
            if row.get("native_preview"):
                merged_groups_by_key[canonical_key]["native_preview"] = True
            if int(row.get("config_menu_id") or 0):
                merged_groups_by_key[canonical_key]["config_menu_id"] = int(row.get("config_menu_id") or 0)
            merged_groups_by_key[canonical_key]["menus"].extend(row.get("menus") if isinstance(row.get("menus"), list) else [])

        groups_by_key = merged_groups_by_key
        group_order = merged_group_order

        group_nodes = []
        for group_key in group_order:
            row = groups_by_key.get(group_key) or {}
            group_label = str(row.get("group_label") or "系统菜单")
            if not int(row.get("config_menu_id") or 0) and native_group_config_ids_by_label.get(group_label):
                row["config_menu_id"] = int(native_group_config_ids_by_label[group_label])
            menus = row.get("menus") if isinstance(row.get("menus"), list) else []
            if group_label in _CUSTOMER_ACCEPTANCE_GROUP_LABELS:
                children = []
                for menu in menus:
                    child = build_delivery_menu_child(menu)
                    if not child:
                        continue
                    self._append_acceptance_child(
                        nodes=children,
                        parent_key=str(row.get("group_key") or group_key),
                        group_parts=self._acceptance_menu_group_parts(menu, group_label),
                        child=child,
                        group_config_menu_ids_by_label=native_group_config_ids_by_label,
                    )
            else:
                children = []
                for menu in menus:
                    child = build_delivery_menu_child(menu)
                    if not child:
                        continue
                    self._append_policy_path_child(
                        nodes=children,
                        parent_key=str(row.get("group_key") or group_key),
                        group_label=group_label,
                        menu=menu,
                        child=child,
                        group_config_menu_ids_by_label=native_group_config_ids_by_label,
                    )
                children = self._group_children_by_business_intent(
                    children,
                    parent_key=str(row.get("group_key") or group_key),
                )
            if not children:
                continue
            group_node = build_delivery_menu_group(
                str(row.get("group_key") or group_key),
                group_label,
                children,
                config_menu_id=int(row.get("config_menu_id") or 0),
            )
            if row.get("native_preview"):
                group_meta = dict(group_node.get("meta") if isinstance(group_node.get("meta"), dict) else {})
                group_meta["native_preview"] = True
                group_meta["runtime_authority"] = "native_preview_only"
                group_node["meta"] = group_meta
            group_nodes.append(group_node)

        group_nodes = self._sort_delivery_nodes(group_nodes, top_level=True)
        root = build_delivery_menu_root(group_nodes, role_code)
        root["key"] = "root:system_menu"
        root["label"] = "系统菜单"
        root["title"] = "系统菜单"
        root["meta"] = {
            "source": "delivery_engine_v1",
            "role_code": role_code,
            "strategy": "unified_system_menu",
            "source_authority": self.source_authority_contract(),
        }
        logging.getLogger(__name__).warning("NAV_RESULT uid=%s roots=%s leaves=%s", getattr(getattr(self.env, "user", None), "id", None), len(group_nodes), self._count_leaf_nodes([root]))
        return [root]

    def _count_leaf_nodes(self, nodes: list[dict] | None) -> int:
        count = 0
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            children = node.get("children") if isinstance(node.get("children"), list) else []
            if children:
                count += self._count_leaf_nodes(children)
            else:
                count += 1
        return count

    def describe_nav(self, nav: list[dict] | None) -> dict:
        root = (nav or [None])[0] if isinstance(nav, list) and nav else {}
        groups = root.get("children") if isinstance(root, dict) and isinstance(root.get("children"), list) else []
        stable_groups = []
        native_preview_groups = []
        for group in groups:
            if not isinstance(group, dict):
                continue
            meta = group.get("meta") if isinstance(group.get("meta"), dict) else {}
            group_key = str(meta.get("group_key") or "").strip()
            if meta.get("native_preview") or group_key == self.NATIVE_PREVIEW_GROUP_KEY:
                native_preview_groups.append(group)
            else:
                stable_groups.append(group)
        return {
            "source_authority": self.source_authority_contract(),
            "group_count": len(groups),
            "stable_group_count": len(stable_groups),
            "native_preview_group_count": len(native_preview_groups),
            "stable_leaf_count": sum(self._count_leaf_nodes(group.get("children") or []) for group in stable_groups),
            "native_preview_leaf_count": sum(self._count_leaf_nodes(group.get("children") or []) for group in native_preview_groups),
            "native_preview_group_key": self.NATIVE_PREVIEW_GROUP_KEY if native_preview_groups else "",
            "group_keys": [
                str(((group.get("meta") or {}).get("group_key")) or "").strip()
                for group in groups
                if isinstance(group, dict)
            ],
        }
