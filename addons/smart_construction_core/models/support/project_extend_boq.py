# -*- coding: utf-8 -*-
import re

from odoo import _, fields, models
from odoo.exceptions import UserError


class Project(models.Model):
    _inherit = "project.project"

    def action_rebuild_boq_hierarchy(self):
        """重建工程量清单的层级：专业 -> 分部 -> 清单项（幂等）。"""
        Boq = self.env["project.boq.line"].sudo()
        uom_fallback = self._default_uom()

        for project in self:
            # 清理旧的结构节点
            old_groups = Boq.search(
                [
                    ("project_id", "=", project.id),
                    ("line_type", "in", ["group", "major", "division"]),
                ]
            )
            if old_groups:
                old_groups.unlink()

            # item 行归零 parent
            item_lines = Boq.search(
                [("project_id", "=", project.id), ("line_type", "=", "item")]
            )
            item_lines.write({"parent_id": False})

            cache_major = {}
            cache_division = {}
            major_seq = 1
            division_seq = 1

            for line in item_lines.sorted(
                key=lambda l: (
                    l.section_type or "",
                    (l.major_name or "").strip(),
                    (l.division_name or "").strip(),
                    l.code or "",
                    l.id,
                )
            ):
                section = line.section_type or "building"
                major_name = (line.major_name or _("未分类专业")).strip()
                division_name = (line.division_name or "").strip()

                # Level 1: 专业
                key_major = (project.id, section, major_name)
                major_node = cache_major.get(key_major)
                if not major_node:
                    major_node = Boq.create(
                        {
                            "project_id": project.id,
                            "code": f"MAJ-{major_seq:03d}",
                            "name": major_name,
                            "section_type": section,
                            "boq_category": line.boq_category,
                            "line_type": "major",
                            "uom_id": uom_fallback.id,
                            "quantity": 0.0,
                            "price": 0.0,
                            "amount": 0.0,
                        }
                    )
                    major_seq += 1
                    cache_major[key_major] = major_node

                parent = major_node

                # Level 2: 分部
                if division_name:
                    key_division = (project.id, section, major_name, division_name)
                    div_node = cache_division.get(key_division)
                    if not div_node:
                        code, div_clean_name = self._split_division_name(division_name)
                        if not code:
                            code = f"DIV-{division_seq:03d}"
                        div_node = Boq.create(
                            {
                                "project_id": project.id,
                                "parent_id": major_node.id,
                                "code": code,
                                "name": div_clean_name,
                                "section_type": section,
                                "boq_category": line.boq_category,
                                "line_type": "division",
                                "uom_id": uom_fallback.id,
                                "quantity": 0.0,
                                "price": 0.0,
                                "amount": 0.0,
                                "division_name": division_name,
                            }
                        )
                        division_seq += 1
                        cache_division[key_division] = div_node
                    parent = div_node

                # Level 3: 清单项
                line.parent_id = parent.id

    def action_validate_boq(self):
        """导入后简单体检：标记缺关键信息或数值异常的清单行。"""
        self.ensure_one()
        Boq = self.env["project.boq.line"].sudo()
        lines = Boq.search(
            [("project_id", "=", self.id), ("line_type", "=", "item")]
        )
        if not lines:
            return True

        warnings = []
        for line in lines:
            msg_list = []
            if not line.major_name:
                msg_list.append(_("缺少专业名称"))
            if not line.division_name:
                msg_list.append(_("缺少分部名称"))
            if not line.uom_id:
                msg_list.append(_("缺少计量单位"))
            if line.quantity is not None and line.quantity <= 0:
                msg_list.append(_("工程量<=0"))
            if line.price is not None and line.price < 0:
                msg_list.append(_("单价为负数"))

            if msg_list:
                line.write(
                    {
                        "has_warning": True,
                        "warning_message": "；".join(msg_list),
                    }
                )
                warnings.append(
                    "%s: %s" % (line.name or line.code or line.id, "；".join(msg_list))
                )
            else:
                line.write({"has_warning": False, "warning_message": False})

        if warnings:
            raise UserError(
                _("检测到 %s 条异常清单行，请在列表中按“有警告”筛选查看。\n\n%s")
                % (len(warnings), "\n".join(warnings[:30]))
            )
        return True

    @staticmethod
    def _split_division_name(text):
        """从 '0402 人行道改造工程' 拆分编码+名称。"""
        raw = text or ""
        m = re.match(r"^(\d{3,})\s*(.*)$", raw)
        if not m:
            return "", raw.strip()
        code = m.group(1)
        name = m.group(2).strip() or raw.strip()
        return code, name

    def _default_uom(self):
        """获取通用计量单位，避免 group 节点必填单位报错。"""
        uom = self.env.ref("uom.product_uom_unit", raise_if_not_found=False)
        if not uom:
            uom = self.env["uom.uom"].search([], limit=1)
        return uom
