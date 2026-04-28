# -*- coding: utf-8 -*-
from odoo import models


class HrDepartment(models.Model):
    _inherit = "hr.department"
    _description = "组织架构"

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
