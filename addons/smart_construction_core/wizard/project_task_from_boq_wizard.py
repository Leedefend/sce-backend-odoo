# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class ProjectTaskFromBoqWizard(models.TransientModel):
    _name = "project.task.from.boq.wizard"
    _description = "从工程量清单生成施工任务"

    project_id = fields.Many2one("project.project", string="项目", required=True)
    group_mode = fields.Selection(
        [
            ("code6", "按清单编码前6位分组（推荐）"),
            ("section", "按工程类别分组"),
            ("code_prefix", "自定义编码前缀分组"),
            ("cost_item", "按成本项分组"),
        ],
        string="任务分组方式",
        default="code6",
        required=True,
    )
    code_prefix_len = fields.Integer(
        "编码前缀长度", default=6,
        help="仅在“自定义编码前缀分组”时生效。",
    )
    overwrite = fields.Boolean(
        "覆盖已有BOQ任务",
        default=False,
        help="勾选后，如已存在同分组键的 BOQ 任务，将被更新数量/金额；否则跳过已有任务。"
    )

    def action_generate_tasks(self):
        self.ensure_one()
        project = self.project_id
        boq_lines = self.env["project.boq.line"].search([("project_id", "=", project.id)])
        if not boq_lines:
            raise UserError("当前项目没有工程量清单数据，无法生成任务。")

        Task = self.env["project.task"]

        groups = {}
        for line in boq_lines:
            section = line.section_type or "other"
            key, label = self._compute_group_key(line, section)
            work_id = False
            if self.group_mode in ("code6", "code_prefix", "section"):
                work_id = self._get_or_create_work_node(project, line, section, key)
            data = groups.setdefault(
                key,
                {
                    "section": section,
                    "label": label,
                    "qty": 0.0,
                    "amount": 0.0,
                    "items": self.env["project.boq.line"],
                    "work_id": work_id,
                },
            )
            data["qty"] += line.quantity or 0.0
            data["amount"] += line.amount or 0.0
            data["items"] |= line
            if not data["work_id"] and line.work_id:
                data["work_id"] = line.work_id.id

        created = 0
        updated = 0
        for key, data in groups.items():
            # 查找已有 BOQ 生成的任务
            existing = Task.search(
                [
                    ("project_id", "=", project.id),
                    ("boq_generated", "=", True),
                    ("boq_group_key", "=", key),
                ],
                limit=1,
            )
            name_parts = [data["label"] or "BOQ聚合任务"]
            task_vals = {
                "project_id": project.id,
                "name": " - ".join(name_parts),
                "boq_generated": True,
                "boq_group_key": key,
                "boq_section_type": data["section"],
                "boq_quantity_total": data["qty"],
                "boq_amount_total": data["amount"],
                "boq_line_ids": [(6, 0, [l.id for l in data["items"]])],
                "work_id": data.get("work_id"),
            }

            if existing:
                if self.overwrite:
                    existing.write(task_vals)
                    existing.boq_line_ids.write({"task_id": False})
                    data["items"].write(
                        {
                            "task_id": existing.id,
                            "work_id": data.get("work_id"),
                        }
                    )
                    updated += 1
                else:
                    continue
            else:
                task = Task.create(task_vals)
                data["items"].write(
                    {
                        "task_id": task.id,
                        "work_id": data.get("work_id"),
                    }
                )
                created += 1

        if created == 0 and updated == 0:
            raise UserError("未创建任何任务，可能已存在同分组任务或清单数据为空。")

        return {
            "type": "ir.actions.act_window",
            "res_model": "project.task",
            "view_mode": "tree,form",
            "domain": [("project_id", "=", project.id), ("boq_generated", "=", True)],
            "context": {"default_project_id": project.id},
        }

    @staticmethod
    def _section_labels():
        return {
            "building": "建筑",
            "installation": "安装/机电",
            "decoration": "装饰",
            "landscape": "景观",
            "other": "其他",
        }

    def _compute_group_key(self, line, section):
        """Return grouping key and human label based on selected mode."""
        code = (line.code or "").strip()
        if self.group_mode == "code6":
            prefix = code[:6] or "无编码"
            label = f"[{prefix}] BOQ聚合任务"
            return prefix, label
        if self.group_mode == "section":
            label = f"{dict(self._section_labels()).get(section, section)} BOQ聚合任务"
            return section or "other", label
        if self.group_mode == "cost_item" and line.cost_item_id:
            key = f"cost:{line.cost_item_id.id}"
            label = f"{line.cost_item_id.display_name} BOQ聚合任务"
            return key, label
        if self.group_mode == "code_prefix":
            prefix_len = self.code_prefix_len or 0
            prefix = code[:prefix_len] if prefix_len > 0 else ""
            label = f"[{prefix or '无编码'}] BOQ聚合任务"
            return prefix or "nocode", label
        # fallback
        label = f"{dict(self._section_labels()).get(section, section)} BOQ聚合任务"
        return section or "other", label

    def _get_or_create_work_node(self, project, line, section, key):
        """根据分组规则匹配/创建工程结构节点."""
        Work = self.env["construction.work.breakdown"]
        code = (line.code or "").strip()
        level = "sub_section"
        name = line.name or key

        if self.group_mode == "section":
            level = "sub_division"
            code = section or "other"
            name = dict(self._section_labels()).get(section, section) or "工程结构"
        elif self.group_mode in ("code6", "code_prefix"):
            prefix_len = 6 if self.group_mode == "code6" else (self.code_prefix_len or 0)
            code = code[:prefix_len] if prefix_len else (code or "nocode")
            name = f"[{code or '无编码'}] {line.name or '分项工程'}"

        domain = [
            ("project_id", "=", project.id),
            ("code", "=", code),
            ("level_type", "=", level),
        ]
        work = Work.search(domain, limit=1)
        if not work:
            work = Work.create(
                {
                    "project_id": project.id,
                    "code": code,
                    "name": name,
                    "level_type": level,
                }
            )
        return work.id
