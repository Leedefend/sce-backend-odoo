# -*- coding: utf-8 -*-
from __future__ import annotations


class MenuDeliveryConvergenceService:
    SOURCE_KIND = "menu_delivery_convergence_projection"
    SOURCE_AUTHORITIES = ("odoo_menu_projection", "legacy_construction_menu_token_policy")
    NO_BUSINESS_FACT_AUTHORITY = True
    LEGACY_TOKEN_POLICY_SOURCE_KIND = "legacy_construction_menu_token_policy"

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
        "项目管理（后台）",
    )
    BUSINESS_CONFIG_TOKENS = (
        "业务配置",
        "业务管理员配置中心",
        "数据字典",
        "定额库",
        "业务字典",
        "成本科目",
        "阶段资料要求",
        "项目阶段资料要求",
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
        "智能施工 2.0",
        "项目管理",
        "合同管理",
        "合同中心",
        "项目合同",
        "收入合同",
        "支出合同",
        "一般合同",
        "成本管理",
        "成本报表",
        "物资管理",
        "看板中心",
        "财务账款",
        "结算中心",
        "执行结构",
        "项目立项",
        "项目台账",
        "项目驾驶舱",
        "投标",
        "报名",
        "开标",
        "中标",
        "保证金",
        "自筹",
        "付款还",
        "资金借还",
        "借款",
        "还款",
        "费用中心",
        "费用",
        "报销",
        "收支",
        "统计表",
        "收入",
        "公司财务支出",
        "项目资金",
        "承包人",
        "项目款",
        "公司款",
        "发票税务",
        "发票",
        "开票",
        "税务",
        "付款",
        "支付",
        "往来单位付款",
        "扣款",
        "实缴",
        "资金账户",
        "账户间资金往来",
        "收款",
        "到款",
        "资金日报",
        "我的工作",
        "工程资料",
        "客户",
        "供应商",
        "人事行政",
        "请假",
        "休假",
        "印章",
        "资料证照",
        "证照",
        "借阅",
        "业务配置",
        "基础设置",
        "组织架构",
        "历史用户",
        "历史用户权限",
        "用户信息",
        "用户信息与权限",
        "历史角色",
        "项目授权范围",
        "系统配置",
    )
    ADMIN_ALLOWED_PATH_TOKENS = (
        "智能施工 2.0",
        "我的工作",
        "项目管理",
        "执行与生产",
        "成本与资金",
        "合同管理",
        "合同中心",
        "项目合同",
        "收入合同",
        "支出合同",
        "一般合同",
        "成本管理",
        "成本报表",
        "物资管理",
        "看板中心",
        "财务账款",
        "结算中心",
        "执行结构",
        "项目立项",
        "项目台账",
        "项目驾驶舱",
        "投标",
        "报名",
        "开标",
        "中标",
        "保证金",
        "自筹",
        "付款还",
        "资金借还",
        "借款",
        "还款",
        "费用中心",
        "费用",
        "报销",
        "收支",
        "统计表",
        "收入",
        "公司财务支出",
        "项目资金",
        "承包人",
        "项目款",
        "公司款",
        "发票税务",
        "发票",
        "开票",
        "税务",
        "付款",
        "支付",
        "往来单位付款",
        "扣款",
        "实缴",
        "资金账户",
        "账户间资金往来",
        "收款",
        "到款",
        "资金日报",
        "工程资料",
        "人事行政",
        "请假",
        "休假",
        "印章",
        "资料证照",
        "证照",
        "借阅",
        "基础设置",
        "组织架构",
        "历史用户",
        "历史用户权限",
        "用户信息",
        "用户信息与权限",
        "历史角色",
        "项目授权范围",
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

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "legacy_token_policy": cls.LEGACY_TOKEN_POLICY_SOURCE_KIND,
        }

    @classmethod
    def legacy_token_policy_source_authority_contract(cls) -> dict:
        return {
            "kind": cls.LEGACY_TOKEN_POLICY_SOURCE_KIND,
            "authorities": [
                "USER_ALLOWED_PATH_TOKENS",
                "ADMIN_ALLOWED_PATH_TOKENS",
                "BUSINESS_CONFIG_TOKENS",
                "SYSTEM_CONFIG_TOKENS",
            ],
            "projection_only": True,
            "no_business_fact_authority": True,
            "legacy_compatibility": True,
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
            "legacy_token_policy_source_authority": self.legacy_token_policy_source_authority_contract(),
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
        target = self.RENAME_LABELS.get(label)
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
        allow_tokens = self.ADMIN_ALLOWED_PATH_TOKENS if is_admin else self.USER_ALLOWED_PATH_TOKENS

        if label in self.HIDE_EXACT_LABELS:
            return "hidden_demo"
        if self._contains_any(normalized_label, normalized_path, self.NON_FORMAL_ENTRY_TOKENS):
            return "hidden_governance"
        if self._contains_any(normalized_label, normalized_path, self.DEMO_TOKENS):
            return "hidden_demo"
        if self._contains_any(normalized_label, normalized_path, self.ALWAYS_HIDDEN_TECHNICAL_TOKENS):
            return "hidden_technical"
        if self._contains_any(normalized_label, normalized_path, self.BUSINESS_CONFIG_TOKENS):
            if is_admin or is_business_config_admin:
                return "delivery_business_config"
            return "hidden_business_config"
        if self._contains_any(normalized_label, normalized_path, self.SYSTEM_CONFIG_TOKENS):
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
