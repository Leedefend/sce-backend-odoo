from .view_dispatcher import ViewDispatcher

class UniversalViewSemanticParser:
    def __init__(self, env, model, view_type="form", view_id=None, context=None):
        self.env = env
        self.model = model
        self.view_type = view_type
        self.view_id = view_id
        self.context = context or {}

    def parse(self):
        # 1. 调用视图解析调度器
        dispatcher = ViewDispatcher(self.env, self.model, self.view_type, self.view_id, self.context)
        raw_layout = dispatcher.parse()

        # 2. 模型权限
        model_permissions = self._parse_model_permissions()

        # 3. 字段定义 + 权限
        fields = self._parse_fields_with_permissions(raw_layout)

        # 4. 字段标签补全
        self._merge_field_labels(raw_layout, fields)

        # 5. 权限应用（字段/按钮）
        self._apply_permissions_to_layout(raw_layout, fields)

        # 6. 菜单、动作解析
        menus = self._parse_menus()
        actions = self._parse_actions()

        # 7. 动态覆盖
        final_layout = self._apply_dynamic_overrides(raw_layout)

        return {
            "model": self.model,
            "view_type": self.view_type,
            "view_id": self.view_id,
            "permissions": model_permissions,
            "layout": final_layout,
            "fields": fields,
            "menus": menus,
            "actions": actions
        }

    # ---------------- 模型权限 ----------------
    def _parse_model_permissions(self):
        model = self.env[self.model]
        return {
            "read": model.check_access_rights("read", raise_exception=False),
            "write": model.check_access_rights("write", raise_exception=False),
            "create": model.check_access_rights("create", raise_exception=False),
            "unlink": model.check_access_rights("unlink", raise_exception=False),
        }

    # ---------------- 字段权限 ----------------
    def _parse_fields_with_permissions(self, layout):
        all_fields = self.env[self.model].fields_get()
        used_fields = set()
        self._extract_field_names(layout, used_fields)

        processed = {}
        for name in used_fields:
            if name in all_fields:
                processed[name] = self._apply_field_permissions(all_fields[name])
        return processed

    def _apply_field_permissions(self, field_def):
        groups_str = field_def.get("groups")
        group_xml_ids = self._normalize_groups(groups_str)

        group_ok = any(
            self.env.ref(xml_id, raise_if_not_found=False) in self.env.user.groups_id
            for xml_id in group_xml_ids
        ) if group_xml_ids else True

        return {
            **field_def,
            "visible": group_ok,
            "editable": group_ok
        }

    # ---------------- 字段标签补全 ----------------
    def _merge_field_labels(self, layout, fields):
        def merge(node):
            if isinstance(node, dict):
                if "name" in node and node["name"] in fields:
                    field_def = fields[node["name"]]
                    if not node.get("string"):
                        node["string"] = field_def.get("string")
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        merge(v)
            elif isinstance(node, list):
                for item in node:
                    merge(item)
        merge(layout)

    # ---------------- 权限应用 ----------------
    def _apply_permissions_to_layout(self, layout, fields):
        def apply(node):
            if isinstance(node, dict):
                # 补全默认 visible/editable
                if "visible" not in node:
                    node["visible"] = True
                if "editable" not in node:
                    node["editable"] = True

                # 字段权限
                if "name" in node and node["name"] in fields:
                    f = fields[node["name"]]
                    node["visible"] = f["visible"]
                    node["editable"] = f["editable"]

                # 按钮 groups 权限
                if "groups" in node:
                    node["visible"] = self._check_groups_permission(node.get("groups")) and not (node.get("invisible") is True)

                # 动态属性解析
                for key in ["invisible", "readonly", "required"]:
                    if key in node:
                        node[key] = self._parse_condition(node[key])

                # 递归子节点
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        apply(v)

            elif isinstance(node, list):
                for item in node:
                    apply(item)
        apply(layout)

    def _check_groups_permission(self, groups):
        group_xml_ids = self._normalize_groups(groups)
        if not group_xml_ids:
            return True
        return any(
            self.env.ref(xml_id, raise_if_not_found=False) in self.env.user.groups_id
            for xml_id in group_xml_ids
        )

    # ---------------- 菜单解析 ----------------
    def _parse_menus(self):
        menus = []
        all_menus = self.env["ir.ui.menu"].search([("parent_id", "=", False)], order="sequence")
        for menu in all_menus:
            if not menu.groups_id or menu.groups_id & self.env.user.groups_id:
                menus.append(self._build_menu_node(menu))
        return menus

    def _build_menu_node(self, menu):
        return {
            "id": menu.id,
            "name": menu.name,
            "sequence": menu.sequence,
            "action_id": menu.action.id if menu.action else None,
            "children": [
                self._build_menu_node(child)
                for child in menu.child_id
                if not child.groups_id or child.groups_id & self.env.user.groups_id
            ]
        }

    # ---------------- 动作解析 ----------------
    def _parse_actions(self):
        actions = []
        all_actions = self.env["ir.actions.act_window"].search([])
        for act in all_actions:
            actions.append({
                "id": act.id,
                "name": act.name,
                "res_model": act.res_model,
                "view_modes": act.view_mode.split(","),
                "domain": act.domain,
                "context": act.context
            })
        return actions

    # ---------------- 工具方法 ----------------
    def _extract_field_names(self, node, result):
        if isinstance(node, dict):
            if "name" in node:
                result.add(node["name"])
            for v in node.values():
                self._extract_field_names(v, result)
        elif isinstance(node, list):
            for item in node:
                self._extract_field_names(item, result)

    def _normalize_groups(self, groups):
        if not groups:
            return []
        if isinstance(groups, str):
            return [g.strip() for g in groups.split(",") if g.strip()]
        if isinstance(groups, list):
            return [g.strip() for g in groups if isinstance(g, str) and g.strip()]
        return []

    def _parse_condition(self, expr):
        if expr in ("1", "true", "True"):
            return True
        if expr in ("0", "false", "False", None):
            return False
        return expr   # 表达式保留 
    
    # ---------- 动态合并逻辑 ----------
    def _apply_dynamic_overrides(self, layout):
        """
        合并 ui.dynamic.config 的动态配置
        """
        if 'ui.dynamic.config' not in self.env:
            return layout
        overrides = self.env['ui.dynamic.config'].search([
            ('model', '=', self.model),
            ('view_id', '=', self.view_id or False)
        ])
        override_map = {o.path: o.override_data for o in overrides}

        def merge(node):
            if isinstance(node, dict):
                path = node.get('meta', {}).get('path')
                if path and path in override_map:
                    # 合并覆盖
                    node.update(override_map[path])
                    node['meta']['source'] = 'dynamic'
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        merge(v)
            elif isinstance(node, list):
                for item in node:
                    merge(item)

        merge(layout)
        return layout
    
