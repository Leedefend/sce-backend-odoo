# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import UserError


class HrDepartment(models.Model):
    _name = "hr.department"
    _inherit = ["hr.department", "sc.delete.guard.mixin"]
    _description = "组织架构"
    _sc_delete_guard_blocker_models = (
        "hr.department",
        "hr.employee",
        "hr.job",
        "sc.contract.event",
        "sc.document.admin.document",
        "sc.hr.payroll.document",
        "sc.office.admin.document",
        "sc.plan",
        "sc.plan.line",
        "sc.subcontract.request",
    )
    _sc_delete_guard_include_models = _sc_delete_guard_blocker_models

    def _setup_complete(self):
        super()._setup_complete()
        labels = {
            "name": "部门名称",
            "active": "有效",
            "company_id": "公司",
            "manager_id": "负责人",
            "parent_id": "上级部门",
            "child_ids": "下级部门",
            "message_follower_ids": "关注人",
            "message_ids": "沟通记录",
        }
        for field_name, label in labels.items():
            if field_name in self._fields:
                self._fields[field_name].string = label

    def unlink(self):
        active_departments = self.filtered("active")
        if active_departments:
            raise UserError("请先停用部门后再删除。")
        self._sc_raise_delete_blockers(action_label="删除部门")
        return super().unlink()
