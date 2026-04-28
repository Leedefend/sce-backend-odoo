# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyDepartment(models.Model):
    _name = "sc.legacy.department"
    _description = "Legacy Organization Department Fact"
    _order = "legacy_department_id"

    legacy_department_id = fields.Char(required=True, index=True)
    name = fields.Char(required=True, index=True)
    parent_legacy_department_id = fields.Char(index=True)
    parent_id = fields.Many2one("sc.legacy.department", index=True, ondelete="set null")
    depth = fields.Char()
    state = fields.Char(index=True)
    identity_path = fields.Char()
    legacy_project_id = fields.Char(index=True)
    is_company = fields.Char()
    is_child_company = fields.Char()
    charge_leader_legacy_user_id = fields.Char(index=True)
    charge_leader_name = fields.Char()
    source_table = fields.Char(default="BASE_ORGANIZATION_DEPARTMENT", required=True)
    note = fields.Text()
    active = fields.Boolean(default=True, index=True)


class ScLegacyUserProfile(models.Model):
    _name = "sc.legacy.user.profile"
    _description = "Legacy User Profile Fact"
    _order = "legacy_user_id"

    legacy_user_id = fields.Char(required=True, index=True)
    user_id = fields.Many2one("res.users", index=True, ondelete="set null")
    generated_login = fields.Char(index=True)
    source_login = fields.Char(index=True)
    display_name = fields.Char(index=True)
    phone = fields.Char()
    email = fields.Char()
    employee_no = fields.Char(index=True)
    person_state = fields.Char(index=True)
    deleted_flag = fields.Char(index=True)
    locked_flag = fields.Char(index=True)
    is_admin_flag = fields.Char(index=True)
    sex = fields.Char()
    account_type = fields.Char(index=True)
    user_type = fields.Char(index=True)
    legacy_department_id = fields.Char(index=True)
    department_id = fields.Many2one("sc.legacy.department", index=True, ondelete="set null")
    department_name = fields.Char()
    tr_user_id = fields.Char(index=True)
    tr_user_state = fields.Char(index=True)
    tr_user_operator = fields.Char(index=True)
    tr_user_job_number = fields.Char(index=True)
    source_table = fields.Char(default="BASE_SYSTEM_USER", required=True)
    source_evidence = fields.Text()
    active = fields.Boolean(default=True, index=True)


class ScLegacyUserRole(models.Model):
    _name = "sc.legacy.user.role"
    _description = "Legacy User Role Assignment Fact"
    _order = "legacy_assignment_id"

    legacy_assignment_id = fields.Char(required=True, index=True)
    legacy_user_id = fields.Char(required=True, index=True)
    user_id = fields.Many2one("res.users", index=True, ondelete="set null")
    legacy_role_id = fields.Char(required=True, index=True)
    role_name = fields.Char(index=True)
    role_source = fields.Char(required=True, index=True)
    company_legacy_id = fields.Char(index=True)
    projected_group_ids = fields.Many2many(
        "res.groups",
        "sc_legacy_user_role_res_groups_rel",
        "legacy_role_id",
        "group_id",
        string="Projected Capability Groups",
        readonly=True,
    )
    projection_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("projected", "Projected"),
            ("unmapped", "Unmapped"),
        ],
        default="pending",
        index=True,
        readonly=True,
    )
    projection_note = fields.Char(readonly=True)
    source_table = fields.Char(required=True, index=True)
    note = fields.Text()
    active = fields.Boolean(default=True, index=True)


class ScLegacyUserProjectScope(models.Model):
    _name = "sc.legacy.user.project.scope"
    _description = "Legacy User Project Scope Fact"
    _order = "created_time desc, legacy_scope_key"

    legacy_scope_key = fields.Char(required=True, index=True)
    source_table = fields.Char(required=True, index=True)
    legacy_assignment_id = fields.Char(required=True, index=True)
    relation_name = fields.Char(index=True)
    legacy_user_id = fields.Char(required=True, index=True)
    user_id = fields.Many2one("res.users", index=True, ondelete="set null")
    company_legacy_id = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    resolved_project_ref = fields.Char(index=True, readonly=True)
    project_access_applied = fields.Boolean(default=False, index=True, readonly=True)
    project_access_note = fields.Char(readonly=True)
    project_access_applied_at = fields.Datetime(readonly=True)
    scope_state = fields.Char(required=True, index=True)
    created_by_legacy_user_id = fields.Char(index=True)
    created_by_name = fields.Char(index=True)
    created_time = fields.Datetime(index=True)
    removed_by_legacy_user_id = fields.Char(index=True)
    removed_by_name = fields.Char(index=True)
    removed_time = fields.Datetime(index=True)
    note = fields.Text()
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_scope_key_unique", "unique(legacy_scope_key)", "Legacy user project scope key must be unique."),
    ]
