# ✅ 文件路径建议：services/semantic/view/kanban_parser.py

from .base import BaseViewParser
from .base import parse_safe_context
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from ...permission import PermissionService


class KanbanViewParser(BaseViewParser):


    def parse(self):
        view_info = self.get_view_info('kanban')
        arch = view_info['arch']  # ✅ 已在 base.py 中转换为 etree.Element
        env = self._get_environment()
        perm = PermissionService(env)

        result = {
            "view_type": "kanban",
            "layout": {
                "tag": "kanban",
                "groups": [],
                "cards": [],
                "color_field": None,
                "actions": [],
                "menu": {},
                "raw_fields": [],
                "group_by": None,
                "group_field": {},
                "on_create": None,
                "quick_create_view": None,
            },
            "field_defs": perm.filter_fields(view_info.get("model"), arch)
        }

        # ✅ 视图根节点就是 <kanban>，无需再查找
        kanban_node = arch if arch.tag == 'kanban' else arch.find('kanban')
        if kanban_node is None:
            raise UserError("视图结构无效：找不到 <kanban> 根节点")

        # ✅ 提取基本属性
        result["layout"]["on_create"] = kanban_node.get("on_create")
        result["layout"]["quick_create_view"] = kanban_node.get("quick_create_view")

        # ✅ 分组字段
        group_by = kanban_node.get("default_group_by") or kanban_node.get("group_by")
        if group_by:
            result["layout"]["group_by"] = group_by

        # ✅ 提取卡片字段（t-name="kanban-box"）
        for template in arch.xpath(".//t[@t-name='kanban-box']"):
            for field_node in template.xpath(".//field"):
                field_info = {
                    "name": field_node.attrib.get("name"),
                    "widget": field_node.attrib.get("widget"),
                    "options": parse_safe_context(field_node.attrib.get("options", "{}")),
                    "nolabel": field_node.attrib.get("nolabel"),
                    "force_save": field_node.attrib.get("force_save"),
                    "on_change": field_node.attrib.get("on_change"),
                    "domain": field_node.attrib.get("domain"),
                    "t_if": field_node.attrib.get("t-if"),
                }
                result["layout"]["cards"].append(field_info)

        # ✅ 提取分组定义
        group_field_name = result["layout"]["group_by"] or "stage_id"
        fields_def = view_info.get("fields", {})
        if group_field_name in fields_def:
            group_def = fields_def[group_field_name]
            result["layout"]["group_field"] = {
                "name": group_field_name,
                "type": group_def.get("type"),
                "string": group_def.get("string"),
            }

            # ✅ 提取分组数据（通过 read_group）
            domain = perm.apply_rules(view_info["model"])
            groups = env[view_info["model"]].read_group(domain, [group_field_name], [group_field_name], limit=100)
            result["layout"]["groups"] = [
                {
                    "value": g[group_field_name][0] if isinstance(g[group_field_name], (list, tuple)) else g[group_field_name],
                    "count": g.get(group_field_name + "_count", 0)
                }
                for g in groups
            ]

        # ✅ 提取颜色字段
        color_field = kanban_node.xpath(".//field[@name='color']")
        if color_field:
            result["layout"]["color_field"] = "color"

        # ✅ 动作按钮
        for action_node in arch.xpath(".//a[@name]"):
            result["layout"]["actions"].append({
                "name": action_node.get("name"),
                "type": action_node.get("type"),
                "context": parse_safe_context(action_node.get("t-attf-context", "{}"))
            })

        # ✅ 自定义菜单（t-name="kanban-menu"）
        menu_template = arch.xpath(".//t[@t-name='kanban-menu']")
        if menu_template:
            menu_items = []
            for item in menu_template[0].xpath(".//a[@name]"):
                menu_items.append({
                    "name": item.get("name"),
                    "type": item.get("type"),
                    "context": parse_safe_context(item.get("t-attf-context", "{}"))
                })
            result["layout"]["menu"] = {"items": menu_items}

        # ✅ 记录所有字段名
        result["layout"]["raw_fields"] = list(self.extract_fields(arch))

        return result
