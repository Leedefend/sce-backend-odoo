# -*- coding: utf-8 -*-
from __future__ import annotations

try:
    from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first
except Exception:  # pragma: no cover - keeps standalone imports usable outside Odoo.
    call_extension_hook_first = None


class MenuDeliveryConvergenceService:
    SOURCE_KIND = "menu_delivery_convergence_projection"
    SOURCE_AUTHORITIES = ("odoo_menu_projection", "menu_delivery_token_policy")
    NO_BUSINESS_FACT_AUTHORITY = True
    TOKEN_POLICY_SOURCE_KIND = "menu_delivery_token_policy"

    DEMO_TOKENS = (
        "演示",
        "demo",
        "试点",
    )
    ALWAYS_HIDDEN_TECHNICAL_TOKENS = (
        "设置/技术",
        "窗口动作",
        "菜单项",
        "iap",
    )
    BUSINESS_CONFIG_TOKENS = (
        "业务配置",
        "业务管理员配置中心",
        "表单字段配置",
        "字段策略台账",
        "新增表单字段",
        "表单字段",
        "字段配置",
        "数据字典",
        "基础设置",
        "业务字典",
    )
    SYSTEM_CONFIG_TOKENS = (
        "系统配置",
        "系统管理",
        "基础资料",
        "场景与能力",
        "能力目录",
        "场景编排",
        "工作流",
        "订阅实例",
        "交付包注册表",
        "订阅套餐",
        "交付包安装记录",
        "授权快照",
        "用量统计",
        "运营任务",
        "能力分组",
        "场景版本",
        "scene governance",
        "governance actions",
        "governance logs",
        "company channels",
    )
    TECHNICAL_TOKENS = ALWAYS_HIDDEN_TECHNICAL_TOKENS + BUSINESS_CONFIG_TOKENS + SYSTEM_CONFIG_TOKENS
    GOVERNANCE_TOKENS = SYSTEM_CONFIG_TOKENS
    NON_FORMAL_ENTRY_TOKENS = (
        "角色首页",
        "生命周期驾驶舱",
        "能力矩阵",
    )
    USER_ALLOWED_PATH_TOKENS = (
        "我的工作",
        "首页",
        "我的待办",
        "我的审批",
    )
    ADMIN_ALLOWED_PATH_TOKENS = USER_ALLOWED_PATH_TOKENS + (
        "我的工作",
        "系统管理",
    )
    HIDE_EXACT_LABELS = set()
    RENAME_LABELS = {}

    def __init__(self, env=None, token_policy: dict | None = None):
        self.env = env
        self._token_policy = self._resolve_token_policy(token_policy)
        self.demo_tokens = self._policy_tokens("demo_tokens", self.DEMO_TOKENS)
        self.always_hidden_technical_tokens = self._policy_tokens(
            "always_hidden_technical_tokens",
            self.ALWAYS_HIDDEN_TECHNICAL_TOKENS,
        )
        self.business_config_tokens = self._policy_tokens("business_config_tokens", self.BUSINESS_CONFIG_TOKENS)
        self.system_config_tokens = self._policy_tokens("system_config_tokens", self.SYSTEM_CONFIG_TOKENS)
        self.non_formal_entry_tokens = self._policy_tokens("non_formal_entry_tokens", self.NON_FORMAL_ENTRY_TOKENS)
        self.user_allowed_path_tokens = self._policy_tokens("user_allowed_path_tokens", self.USER_ALLOWED_PATH_TOKENS)
        self.admin_allowed_path_tokens = self._policy_tokens("admin_allowed_path_tokens", self.ADMIN_ALLOWED_PATH_TOKENS)
        self.hide_exact_labels = set(self._policy_tokens("hide_exact_labels", self.HIDE_EXACT_LABELS))
        self.rename_labels = self._policy_mapping("rename_labels", self.RENAME_LABELS)

    def _resolve_token_policy(self, override: dict | None = None) -> dict:
        if isinstance(override, dict):
            return dict(override)
        if self.env is None or not callable(call_extension_hook_first):
            return {}
        payload = call_extension_hook_first(self.env, "smart_core_menu_delivery_token_policy", self.env)
        return dict(payload) if isinstance(payload, dict) else {}

    def _policy_tokens(self, key: str, defaults) -> tuple:
        values = [item for item in defaults if str(item or "").strip()]
        extra = self._token_policy.get(key)
        if isinstance(extra, (list, tuple, set)):
            values.extend(item for item in extra if str(item or "").strip())
        seen = set()
        out = []
        for item in values:
            text = str(item or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            out.append(text)
        return tuple(out)

    def _policy_mapping(self, key: str, defaults) -> dict:
        out = dict(defaults or {})
        extra = self._token_policy.get(key)
        if isinstance(extra, dict):
            out.update({str(k or "").strip(): str(v or "").strip() for k, v in extra.items() if str(k or "").strip() and str(v or "").strip()})
        return out

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "token_policy": cls.TOKEN_POLICY_SOURCE_KIND,
        }

    @classmethod
    def token_policy_source_authority_contract(cls) -> dict:
        return {
            "kind": cls.TOKEN_POLICY_SOURCE_KIND,
            "authorities": [
                "USER_ALLOWED_PATH_TOKENS",
                "ADMIN_ALLOWED_PATH_TOKENS",
                "BUSINESS_CONFIG_TOKENS",
                "SYSTEM_CONFIG_TOKENS",
                "extension_hook:smart_core_menu_delivery_token_policy",
            ],
            "projection_only": True,
            "no_business_fact_authority": True,
            "extension_policy": True,
        }

    def apply(
        self,
        nav_fact: dict,
        nav_explained: dict,
        *,
        is_admin: bool,
        is_business_config_admin: bool = False,
    ) -> tuple[dict, dict, dict]:
        report = {
            "profile": "delivery_admin" if is_admin else "delivery_user",
            "source_authority": self.source_authority_contract(),
            "token_policy_source_authority": self.token_policy_source_authority_contract(),
            "is_business_config_admin": bool(is_business_config_admin),
            "hidden": [],
            "kept": [],
            "renamed": [],
            "summary": {
                "hidden_total": 0,
                "kept_total": 0,
                "renamed_total": 0,
            },
        }
        explained_tree = nav_explained.get("tree") if isinstance(nav_explained.get("tree"), list) else []
        explained_flat = nav_explained.get("flat") if isinstance(nav_explained.get("flat"), list) else []

        visible_menu_ids: set[int] = set()

        filtered_tree = []
        for node in explained_tree:
            if not isinstance(node, dict):
                continue
            filtered = self._filter_explained_node(
                node,
                path=[],
                is_admin=is_admin,
                is_business_config_admin=is_business_config_admin,
                visible_menu_ids=visible_menu_ids,
                report=report,
            )
            if filtered:
                filtered_tree.append(filtered)

        filtered_flat = []
        for node in explained_flat:
            if not isinstance(node, dict):
                continue
            menu_id = node.get("menu_id")
            if isinstance(menu_id, int) and menu_id in visible_menu_ids:
                copied = dict(node)
                self._apply_rename(copied, report=report)
                copied["delivery_bucket"] = report["profile"]
                filtered_flat.append(copied)

        nav_explained_out = {
            "tree": filtered_tree,
            "flat": filtered_flat,
        }
        nav_fact_out = self._filter_nav_fact(nav_fact, visible_menu_ids, report["profile"])

        report["summary"]["hidden_total"] = len(report["hidden"])
        report["summary"]["kept_total"] = len(report["kept"])
        report["summary"]["renamed_total"] = len(report["renamed"])
        report["summary"]["leaf_count_after"] = len(visible_menu_ids)
        return nav_fact_out, nav_explained_out, report

    def _filter_explained_node(
        self,
        node: dict,
        *,
        path: list[str],
        is_admin: bool,
        is_business_config_admin: bool,
        visible_menu_ids: set[int],
        report: dict,
    ):
        copied = dict(node)
        raw_name = str(copied.get("name") or "").strip()
        current_path = [*path, raw_name] if raw_name else list(path)
        children = copied.get("children") if isinstance(copied.get("children"), list) else []

        filtered_children = []
        for child in children:
            if not isinstance(child, dict):
                continue
            next_node = self._filter_explained_node(
                child,
                path=current_path,
                is_admin=is_admin,
                is_business_config_admin=is_business_config_admin,
                visible_menu_ids=visible_menu_ids,
                report=report,
            )
            if next_node:
                filtered_children.append(next_node)

        has_children = bool(filtered_children)
        if has_children:
            copied["children"] = filtered_children
            copied["delivery_bucket"] = report["profile"]
            return copied

        category = self._classify_leaf(
            raw_name,
            current_path,
            is_admin=is_admin,
            is_business_config_admin=is_business_config_admin,
        )
        menu_id = copied.get("menu_id")
        row = {
            "menu_id": menu_id,
            "name": raw_name,
            "path": "/".join([token for token in current_path if token]),
            "category": category,
        }
        if category.startswith("hidden_"):
            report["hidden"].append(row)
            return None

        self._apply_rename(copied, report=report)
        if isinstance(menu_id, int) and menu_id > 0:
            visible_menu_ids.add(menu_id)
        copied["delivery_bucket"] = category
        report["kept"].append({**row, "category": category, "name": str(copied.get("name") or raw_name)})
        return copied

    def _apply_rename(self, node: dict, *, report: dict) -> None:
        label = str(node.get("name") or "").strip()
        target = self.rename_labels.get(label)
        if not target:
            return
        node["name"] = target
        report["renamed"].append({"from": label, "to": target, "menu_id": node.get("menu_id")})

    def _classify_leaf(
        self,
        label: str,
        path: list[str],
        *,
        is_admin: bool,
        is_business_config_admin: bool = False,
    ) -> str:
        normalized_label = str(label or "").strip().lower()
        full_path = "/".join(str(part or "").strip() for part in path if str(part or "").strip())
        normalized_path = full_path.lower()
        allow_tokens = self.admin_allowed_path_tokens if is_admin else self.user_allowed_path_tokens

        if label in self.hide_exact_labels:
            return "hidden_demo"
        if self._contains_any(normalized_label, normalized_path, self.non_formal_entry_tokens):
            return "hidden_governance"
        if self._contains_any(normalized_label, normalized_path, self.demo_tokens):
            return "hidden_demo"
        if self._contains_any(normalized_label, normalized_path, self.always_hidden_technical_tokens):
            return "hidden_technical"
        if self._contains_any(normalized_label, normalized_path, self.business_config_tokens):
            if is_admin or is_business_config_admin:
                return "delivery_business_config"
            return "hidden_business_config"
        if self._contains_any(normalized_label, normalized_path, self.system_config_tokens):
            if is_admin:
                return "delivery_system_config"
            return "hidden_governance"
        if not self._contains_any(normalized_label, normalized_path, allow_tokens):
            return "hidden_technical"
        return "delivery_admin" if is_admin else "delivery_user"

    def _contains_any(self, normalized_label: str, normalized_path: str, tokens) -> bool:
        for token in tokens:
            token_norm = str(token or "").strip().lower()
            if not token_norm:
                continue
            if token_norm in normalized_label or token_norm in normalized_path:
                return True
        return False

    def _filter_nav_fact(self, nav_fact: dict, visible_menu_ids: set[int], profile: str) -> dict:
        fact_tree = nav_fact.get("tree") if isinstance(nav_fact.get("tree"), list) else []
        fact_flat = nav_fact.get("flat") if isinstance(nav_fact.get("flat"), list) else []

        filtered_tree = []
        for node in fact_tree:
            if not isinstance(node, dict):
                continue
            filtered = self._filter_fact_node(node, visible_menu_ids, profile)
            if filtered:
                filtered_tree.append(filtered)

        filtered_flat = []
        for node in fact_flat:
            if not isinstance(node, dict):
                continue
            menu_id = node.get("menu_id")
            if isinstance(menu_id, int) and menu_id in visible_menu_ids:
                copied = dict(node)
                copied["delivery_bucket"] = profile
                if str(copied.get("name") or "").strip() in self.rename_labels:
                    copied["name"] = self.rename_labels[str(copied.get("name") or "").strip()]
                filtered_flat.append(copied)
        return {
            "tree": filtered_tree,
            "flat": filtered_flat,
        }

    def _filter_fact_node(self, node: dict, visible_menu_ids: set[int], profile: str):
        copied = dict(node)
        children = copied.get("children") if isinstance(copied.get("children"), list) else []
        filtered_children = []
        for child in children:
            if not isinstance(child, dict):
                continue
            filtered = self._filter_fact_node(child, visible_menu_ids, profile)
            if filtered:
                filtered_children.append(filtered)

        menu_id = copied.get("menu_id")
        is_leaf = not filtered_children
        keep = bool(filtered_children)
        if is_leaf and isinstance(menu_id, int) and menu_id in visible_menu_ids:
            keep = True
        if not keep:
            return None

        if str(copied.get("name") or "").strip() in self.rename_labels:
            copied["name"] = self.rename_labels[str(copied.get("name") or "").strip()]
        copied["children"] = filtered_children
        copied["delivery_bucket"] = profile
        copied["has_children"] = bool(filtered_children)
        return copied
