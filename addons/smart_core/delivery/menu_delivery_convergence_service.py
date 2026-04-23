# -*- coding: utf-8 -*-
from __future__ import annotations


class MenuDeliveryConvergenceService:
    DEMO_TOKENS = (
        "演示",
        "demo",
        "试点",
    )
    TECHNICAL_TOKENS = (
        "设置/技术",
        "窗口动作",
        "菜单项",
        "iap",
        "业务管理员配置中心",
        "项目管理（后台）",
        "数据字典",
        "定额库",
        "工作流",
        "数据分析",
        "业务字典",
        "基础资料",
    )
    GOVERNANCE_TOKENS = (
        "场景与能力",
        "能力目录",
        "场景编排",
        "订阅实例",
        "交付包注册表",
        "订阅套餐",
        "交付包安装记录",
        "授权快照",
        "用量统计",
        "运营任务",
        "能力分组",
        "场景版本",
    )
    NON_FORMAL_ENTRY_TOKENS = (
        "工作台",
        "生命周期驾驶舱",
        "能力矩阵",
    )
    USER_ALLOWED_PATH_TOKENS = (
        "智能施工 2.0",
        "项目管理",
        "合同管理",
        "成本管理",
        "物资管理",
        "看板中心",
        "财务账款",
        "结算中心",
        "执行结构",
        "项目立项",
        "项目台账",
        "项目驾驶舱",
        "我的工作",
        "工程资料",
    )
    ADMIN_ALLOWED_PATH_TOKENS = (
        "智能施工 2.0",
        "我的工作",
        "项目管理",
        "执行与生产",
        "成本与资金",
        "合同管理",
        "成本管理",
        "物资管理",
        "看板中心",
        "财务账款",
        "结算中心",
        "执行结构",
        "项目立项",
        "项目台账",
        "项目驾驶舱",
        "工程资料",
        "系统管理",
    )
    HIDE_EXACT_LABELS = {
        "快速创建项目",
        "项目列表（演示）",
        "项目驾驶舱（演示）",
    }
    RENAME_LABELS = {
        "项目台账（试点）": "项目台账",
    }

    def apply(self, nav_fact: dict, nav_explained: dict, *, is_admin: bool) -> tuple[dict, dict, dict]:
        report = {
            "profile": "delivery_admin" if is_admin else "delivery_user",
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

    def _filter_explained_node(self, node: dict, *, path: list[str], is_admin: bool, visible_menu_ids: set[int], report: dict):
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

        category = self._classify_leaf(raw_name, current_path, is_admin=is_admin)
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
        target = self.RENAME_LABELS.get(label)
        if not target:
            return
        node["name"] = target
        report["renamed"].append({"from": label, "to": target, "menu_id": node.get("menu_id")})

    def _classify_leaf(self, label: str, path: list[str], *, is_admin: bool) -> str:
        normalized_label = str(label or "").strip().lower()
        full_path = "/".join(str(part or "").strip() for part in path if str(part or "").strip())
        normalized_path = full_path.lower()
        allow_tokens = self.ADMIN_ALLOWED_PATH_TOKENS if is_admin else self.USER_ALLOWED_PATH_TOKENS

        if label in self.HIDE_EXACT_LABELS:
            return "hidden_demo"
        if self._contains_any(normalized_label, normalized_path, self.NON_FORMAL_ENTRY_TOKENS):
            return "hidden_governance"
        if self._contains_any(normalized_label, normalized_path, self.DEMO_TOKENS):
            return "hidden_demo"
        if self._contains_any(normalized_label, normalized_path, self.TECHNICAL_TOKENS):
            return "hidden_technical"
        if self._contains_any(normalized_label, normalized_path, self.GOVERNANCE_TOKENS):
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
                if str(copied.get("name") or "").strip() in self.RENAME_LABELS:
                    copied["name"] = self.RENAME_LABELS[str(copied.get("name") or "").strip()]
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

        if str(copied.get("name") or "").strip() in self.RENAME_LABELS:
            copied["name"] = self.RENAME_LABELS[str(copied.get("name") or "").strip()]
        copied["children"] = filtered_children
        copied["delivery_bucket"] = profile
        copied["has_children"] = bool(filtered_children)
        return copied
