# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyDepartment(models.Model):
    _name = "sc.legacy.department"
    _description = "历史组织部门事实"
    _order = "legacy_department_id"

    legacy_department_id = fields.Char(string="原部门编号", required=True, index=True)
    name = fields.Char(string="部门名称", required=True, index=True)
    parent_legacy_department_id = fields.Char(string="原上级部门编号", index=True)
    parent_id = fields.Many2one("sc.legacy.department", string="原上级部门", index=True, ondelete="set null")
    depth = fields.Char(string="层级")
    state = fields.Char(string="状态", index=True)
    identity_path = fields.Char(string="原始路径")
    legacy_project_id = fields.Char(string="原项目编号", index=True)
    is_company = fields.Char(string="公司标记")
    is_child_company = fields.Char(string="子公司标记")
    charge_leader_legacy_user_id = fields.Char(string="负责人原用户编号", index=True)
    charge_leader_name = fields.Char(string="负责人")
    source_table = fields.Char(string="来源表", default="BASE_ORGANIZATION_DEPARTMENT", required=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(default=True, index=True)


class ScLegacyUserProfile(models.Model):
    _name = "sc.legacy.user.profile"
    _description = "历史用户档案事实"
    _order = "legacy_user_id"

    legacy_user_id = fields.Char(string="原用户编号", required=True, index=True)
    user_id = fields.Many2one("res.users", string="新系统用户", index=True, ondelete="set null")
    generated_login = fields.Char(string="生成登录名", index=True)
    source_login = fields.Char(string="原登录名", index=True)
    display_name = fields.Char(string="姓名", index=True)
    phone = fields.Char(string="手机号")
    legacy_created_at = fields.Datetime(string="建立时间", index=True)
    department_scope_summary = fields.Text(string="所属部门")
    department_scope_count = fields.Integer(string="所属部门数", default=0)
    account_state_label = fields.Char(string="状态", index=True)
    login_count = fields.Integer(string="登录次数", default=0)
    last_login_at = fields.Datetime(string="最近登录时间", index=True)
    email = fields.Char(string="邮箱")
    employee_no = fields.Char(string="员工编号", index=True)
    credential_type = fields.Char(string="证件类型")
    credential_no = fields.Char(string="证件号码", index=True)
    residence_address = fields.Char(string="居住地址")
    archive_no = fields.Char(string="档案编号", index=True)
    birth_date = fields.Date(string="出生日期")
    political_status = fields.Char(string="政治面貌")
    nation = fields.Char(string="民族")
    native_place = fields.Char(string="籍贯")
    graduation_school = fields.Char(string="毕业院校")
    graduation_date = fields.Date(string="毕业时间")
    major = fields.Char(string="所学专业")
    education = fields.Char(string="学历")
    professional_title = fields.Char(string="职称")
    professional_qualification = fields.Char(string="职业资格")
    person_state = fields.Char(string="人员状态", index=True)
    deleted_flag = fields.Char(string="删除标记", index=True)
    locked_flag = fields.Char(string="锁定标记", index=True)
    is_admin_flag = fields.Char(string="管理员标记", index=True)
    sex = fields.Char(string="性别")
    account_type = fields.Char(string="账号类型", index=True)
    user_type = fields.Char(string="用户类型", index=True)
    personnel_type = fields.Char(string="人员类型", index=True)
    legacy_department_id = fields.Char(string="原部门编号", index=True)
    department_id = fields.Many2one("sc.legacy.department", string="原部门", index=True, ondelete="set null")
    department_name = fields.Char(string="部门")
    work_unit = fields.Char(string="单位")
    project_name = fields.Char(string="项目")
    role_summary = fields.Char(string="角色")
    role_count = fields.Integer(string="角色数", default=0)
    company_email = fields.Char(string="公司邮箱")
    emergency_contact = fields.Char(string="紧急联系人")
    emergency_phone = fields.Char(string="紧急联系电话")
    emergency_relation = fields.Char(string="紧急联系人关系")
    bank_name = fields.Char(string="开户行")
    bank_account = fields.Char(string="银行卡号")
    onboarding_date = fields.Date(string="入职日期")
    post_salary = fields.Char(string="岗位工资")
    construction_site = fields.Char(string="施工地")
    age = fields.Char(string="年龄")
    tr_user_id = fields.Char(string="TR用户编号", index=True)
    tr_user_state = fields.Char(string="TR用户状态", index=True)
    tr_user_operator = fields.Char(string="TR操作员", index=True)
    tr_user_job_number = fields.Char(string="TR工号", index=True)
    source_table = fields.Char(string="来源表", default="BASE_SYSTEM_USER", required=True)
    source_evidence = fields.Text(string="来源依据")
    active = fields.Boolean(default=True, index=True)


class ScLegacyUserRole(models.Model):
    _name = "sc.legacy.user.role"
    _description = "历史用户角色分配事实"
    _order = "legacy_assignment_id"

    legacy_assignment_id = fields.Char(string="原分配编号", required=True, index=True)
    legacy_user_id = fields.Char(string="原用户编号", required=True, index=True)
    user_id = fields.Many2one("res.users", string="新系统用户", index=True, ondelete="set null")
    legacy_role_id = fields.Char(string="原角色编号", required=True, index=True)
    role_name = fields.Char(string="角色名称", index=True)
    role_source = fields.Char(string="角色来源", required=True, index=True)
    company_legacy_id = fields.Char(string="原公司编号", index=True)
    projected_group_ids = fields.Many2many(
        "res.groups",
        "sc_legacy_user_role_res_groups_rel",
        "legacy_role_id",
        "group_id",
        string="投影能力组",
        readonly=True,
    )
    projection_state = fields.Selection(
        [
            ("pending", "Pending"),
            ("projected", "Projected"),
            ("unmapped", "Unmapped"),
        ],
        default="pending",
        string="投影状态",
        index=True,
        readonly=True,
    )
    projection_note = fields.Char(string="投影说明", readonly=True)
    source_table = fields.Char(string="来源表", required=True, index=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(default=True, index=True)


class ScLegacyUserProjectScope(models.Model):
    _name = "sc.legacy.user.project.scope"
    _description = "历史用户项目范围事实"
    _order = "created_time desc, legacy_scope_key"

    legacy_scope_key = fields.Char(string="原授权范围键", required=True, index=True)
    source_table = fields.Char(string="来源表", required=True, index=True)
    legacy_assignment_id = fields.Char(string="原分配编号", required=True, index=True)
    relation_name = fields.Char(string="关系名称", index=True)
    legacy_user_id = fields.Char(string="原用户编号", required=True, index=True)
    user_id = fields.Many2one("res.users", string="新系统用户", index=True, ondelete="set null")
    company_legacy_id = fields.Char(string="原公司编号", index=True)
    project_legacy_id = fields.Char(string="原项目编号", index=True)
    project_id = fields.Many2one("project.project", string="新系统项目", index=True, ondelete="set null")
    resolved_project_ref = fields.Char(string="项目匹配依据", index=True, readonly=True)
    project_access_applied = fields.Boolean(string="已应用项目访问", default=False, index=True, readonly=True)
    project_access_note = fields.Char(string="项目访问说明", readonly=True)
    project_access_applied_at = fields.Datetime(string="项目访问应用时间", readonly=True)
    scope_state = fields.Char(string="授权状态", required=True, index=True)
    created_by_legacy_user_id = fields.Char(string="创建人原用户编号", index=True)
    created_by_name = fields.Char(string="创建人", index=True)
    created_time = fields.Datetime(string="创建时间", index=True)
    removed_by_legacy_user_id = fields.Char(string="移除人原用户编号", index=True)
    removed_by_name = fields.Char(string="移除人", index=True)
    removed_time = fields.Datetime(string="移除时间", index=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_scope_key_unique", "unique(legacy_scope_key)", "历史用户项目范围键必须唯一。"),
    ]
