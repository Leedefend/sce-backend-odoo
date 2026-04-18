# -*- coding: utf-8 -*-
from odoo import api, models


class ScSecurityPolicy(models.TransientModel):
    _name = "sc.security.policy"
    _description = "SC Security Policy"

    _CUSTOMER_COMPANY_NAME = "四川保盛建设集团有限公司"
    _CUSTOMER_DEPARTMENTS = (
        ("经营部", "functional"),
        ("工程部", "functional"),
        ("财务部", "functional"),
        ("行政部", "functional"),
        ("成控部", "functional"),
        ("项目部", "project"),
    )
    _CUSTOMER_USERS = (
        {"login": "wutao", "name": "吴涛", "phone": "13518193984", "active": True, "primary_department": "项目部"},
        {"login": "yangdesheng", "name": "杨德胜", "phone": "13990213999", "active": True, "primary_department": "工程部"},
        {
            "login": "duanyijun",
            "name": "段奕俊",
            "phone": "13628105924",
            "active": True,
            "primary_department": "经营部",
            "extra_departments": ("行政部",),
        },
        {"login": "xudan", "name": "徐丹", "phone": "13541712294", "active": True, "primary_department": "行政部"},
        {
            "login": "chentianyou",
            "name": "陈天友",
            "phone": "13980113378",
            "active": True,
            "primary_department": "工程部",
            "extra_departments": ("行政部",),
        },
        {"login": "wennan", "name": "文楠", "phone": "13541719455", "active": True, "primary_department": "财务部"},
        {"login": "lilinxu", "name": "李林旭", "phone": "15282889978", "active": True, "primary_department": "行政部"},
        {"login": "lina", "name": "李娜", "phone": "15283830106", "active": True, "primary_department": "财务部"},
        {
            "login": "jiangyijiao",
            "name": "江一娇",
            "phone": "13881040419",
            "active": True,
            "primary_department": "经营部",
            "extra_departments": ("行政部", "财务部", "项目部"),
        },
        {"login": "yinjiamei", "name": "尹佳梅", "phone": "13281352598", "active": True, "primary_department": "财务部"},
        {"login": "admin", "name": "admin", "phone": False, "active": True, "primary_department": False},
        {"login": "zhangwencui", "name": "张文翠", "phone": "18224022898", "active": True, "primary_department": "经营部"},
        {"login": "lijianfeng", "name": "李俭锋", "phone": "17754915356", "active": True, "primary_department": "经营部"},
        {"login": "yelingyue", "name": "叶凌越", "phone": "15892670626", "active": True, "primary_department": "经营部"},
        {"login": "lidexue", "name": "李德学", "phone": "18380686868", "active": True, "primary_department": "项目部"},
        {
            "login": "chenshuai",
            "name": "陈帅",
            "phone": "13700909923",
            "active": True,
            "primary_department": "成控部",
            "extra_departments": ("项目部",),
        },
        {
            "login": "shuiwujingbanren",
            "name": "税务经办人",
            "phone": "18180385662",
            "active": True,
            "primary_department": False,
        },
        {"login": "xiaohuijiu", "name": "肖辉玖", "phone": "18580396789", "active": True, "primary_department": "经营部"},
        {"login": "luomeng", "name": "罗萌", "phone": "13096101508", "active": True, "primary_department": "财务部"},
        {"login": "hujun", "name": "胡俊", "phone": "13698182176", "active": True, "primary_department": "项目部"},
    )
    _CUSTOMER_SYSTEM_ROLE_GROUP_XMLIDS = {
        "管理员角色": ("smart_construction_custom.group_sc_role_business_admin",),
        "通用角色": ("smart_construction_custom.group_sc_role_owner",),
    }
    _CUSTOMER_USER_SYSTEM_ROLES = {
        "wutao": ("管理员角色", "通用角色"),
        "yangdesheng": ("通用角色",),
        "duanyijun": ("通用角色",),
        "xudan": ("通用角色",),
        "chentianyou": ("通用角色",),
        "wennan": ("通用角色",),
        "lilinxu": ("通用角色",),
        "yinjiamei": ("通用角色",),
        "admin": ("管理员角色", "通用角色"),
        "zhangwencui": ("通用角色",),
        "chenshuai": ("通用角色",),
        "shuiwujingbanren": ("管理员角色",),
        "xiaohuijiu": ("通用角色",),
        "hujun": ("通用角色",),
    }
    _CUSTOMER_USER_PRIMARY_POSTS = {
        "chenshuai": {"primary_post": "总经理", "deferred_extra_posts": ()},
        "duanyijun": {"primary_post": "总经理", "deferred_extra_posts": ()},
        "hujun": {"primary_post": "项目负责人", "deferred_extra_posts": ("总经理",)},
        "jiangyijiao": {"primary_post": "财务助理", "deferred_extra_posts": ()},
        "lidexue": {"primary_post": "临时项目负责人", "deferred_extra_posts": ()},
        "lijianfeng": {"primary_post": "项目负责人", "deferred_extra_posts": ()},
        "lina": {"primary_post": "财务助理", "deferred_extra_posts": ()},
        "luomeng": {"primary_post": "财务助理", "deferred_extra_posts": ()},
        "shuiwujingbanren": {"primary_post": "财务经理", "deferred_extra_posts": ("财务助理",)},
        "wennan": {"primary_post": "财务经理", "deferred_extra_posts": ("副总经理",)},
        "wutao": {"primary_post": "董事长", "deferred_extra_posts": ()},
        "xiaohuijiu": {"primary_post": "项目负责人", "deferred_extra_posts": ()},
    }

    @api.model
    def apply_business_full_policy(self):
        group = self.env.ref("smart_construction_core.group_sc_business_full", raise_if_not_found=False)
        if not group:
            return False

        implied_xmlids = [
            "smart_construction_core.group_sc_internal_user",
            "smart_construction_core.group_sc_cap_contact_manager",
            "smart_construction_core.group_sc_cap_project_manager",
            "smart_construction_core.group_sc_cap_contract_manager",
            "smart_construction_core.group_sc_cap_cost_manager",
            "smart_construction_core.group_sc_cap_material_manager",
            "smart_construction_core.group_sc_cap_purchase_manager",
            "smart_construction_core.group_sc_cap_finance_manager",
            "smart_construction_core.group_sc_cap_settlement_manager",
            "smart_construction_core.group_sc_cap_data_read",
        ]

        to_add = []
        for xmlid in implied_xmlids:
            ref = self.env.ref(xmlid, raise_if_not_found=False)
            if ref and ref not in group.implied_ids:
                to_add.append(ref.id)

        if to_add:
            group.write({"implied_ids": [(4, gid) for gid in to_add]})
        return True

    @api.model
    def apply_role_matrix(self):
        role_specs = [
            ("smart_construction_custom.group_sc_role_project_read", "smart_construction_core.group_sc_cap_project_read"),
            ("smart_construction_custom.group_sc_role_project_user", "smart_construction_core.group_sc_cap_project_user"),
            ("smart_construction_custom.group_sc_role_project_manager", "smart_construction_core.group_sc_cap_project_manager"),
            ("smart_construction_custom.group_sc_role_contract_read", "smart_construction_core.group_sc_cap_contract_read"),
            ("smart_construction_custom.group_sc_role_contract_user", "smart_construction_core.group_sc_cap_contract_user"),
            ("smart_construction_custom.group_sc_role_contract_manager", "smart_construction_core.group_sc_cap_contract_manager"),
            ("smart_construction_custom.group_sc_role_settlement_read", "smart_construction_core.group_sc_cap_settlement_read"),
            ("smart_construction_custom.group_sc_role_settlement_user", "smart_construction_core.group_sc_cap_settlement_user"),
            ("smart_construction_custom.group_sc_role_settlement_manager", "smart_construction_core.group_sc_cap_settlement_manager"),
            ("smart_construction_custom.group_sc_role_payment_read", "smart_construction_core.group_sc_cap_finance_read"),
            ("smart_construction_custom.group_sc_role_payment_user", "smart_construction_core.group_sc_cap_finance_user"),
            ("smart_construction_custom.group_sc_role_payment_manager", "smart_construction_core.group_sc_cap_finance_manager"),
            ("smart_construction_custom.group_sc_role_payment_manager", "smart_core.group_smart_core_finance_approver"),
        ]
        updated = False
        for role_xmlid, cap_xmlid in role_specs:
            role = self.env.ref(role_xmlid, raise_if_not_found=False)
            cap = self.env.ref(cap_xmlid, raise_if_not_found=False)
            if not role or not cap:
                continue
            if cap not in role.implied_ids:
                role.write({"implied_ids": [(4, cap.id)]})
                updated = True

        user_map = {
            "demo_role_project_read": [
                "smart_construction_custom.group_sc_role_project_read",
                "smart_construction_custom.group_sc_role_contract_read",
                "smart_construction_core.group_sc_cap_contract_read",
                "smart_construction_custom.group_sc_role_settlement_read",
                "smart_construction_core.group_sc_cap_settlement_read",
                "smart_construction_custom.group_sc_role_payment_read",
                "smart_construction_core.group_sc_cap_finance_read",
            ],
            "demo_role_project_user": [
                "smart_construction_custom.group_sc_role_project_user",
                "smart_construction_custom.group_sc_role_contract_user",
                "smart_construction_core.group_sc_cap_contract_user",
                "smart_construction_custom.group_sc_role_settlement_user",
                "smart_construction_core.group_sc_cap_settlement_user",
                "smart_construction_custom.group_sc_role_payment_user",
                "smart_construction_core.group_sc_cap_finance_user",
            ],
            "demo_role_project_manager": [
                "smart_construction_custom.group_sc_role_project_manager",
                "smart_construction_custom.group_sc_role_contract_manager",
                "smart_construction_core.group_sc_cap_contract_manager",
                "smart_construction_custom.group_sc_role_settlement_manager",
                "smart_construction_core.group_sc_cap_settlement_manager",
                "smart_construction_custom.group_sc_role_payment_manager",
                "smart_construction_core.group_sc_cap_finance_manager",
            ],
            "demo_role_owner": [
                "smart_construction_custom.group_sc_role_owner",
            ],
            "demo_role_pm": [
                "smart_construction_custom.group_sc_role_pm",
            ],
            "demo_role_finance": [
                "smart_construction_custom.group_sc_role_finance",
            ],
            "demo_role_executive": [
                "smart_construction_custom.group_sc_role_executive",
            ],
        }
        Users = self.env["res.users"].sudo()
        for login, groups in user_map.items():
            user = Users.search([("login", "=", login)], limit=1)
            if not user:
                continue
            to_add = []
            for xmlid in groups:
                group = self.env.ref(xmlid, raise_if_not_found=False)
                if group and group not in user.groups_id:
                    to_add.append(group.id)
            if to_add:
                user.write({"groups_id": [(4, gid) for gid in to_add]})
                updated = True
        return updated or True

    @api.model
    def bootstrap_customer_company_departments(self):
        Company = self.env["res.company"].sudo()
        Department = self.env["hr.department"].sudo()
        Currency = self.env["res.currency"].sudo().with_context(active_test=False)

        currency = self.env.ref("base.CNY", raise_if_not_found=False)
        if not currency:
            currency = Currency.search([("name", "=", "CNY")], limit=1)
        if currency and not currency.active:
            currency.write({"active": True})

        company_values = {"sc_is_active": True}
        if currency:
            company_values["currency_id"] = currency.id

        company = Company.search([("name", "=", self._CUSTOMER_COMPANY_NAME)], limit=1)
        if company:
            company.write(company_values)
        else:
            company = Company.create({"name": self._CUSTOMER_COMPANY_NAME, **company_values})

        created_departments = []
        updated_departments = []
        for department_name, department_type in self._CUSTOMER_DEPARTMENTS:
            department = Department.search(
                [
                    ("company_id", "=", company.id),
                    ("name", "=", department_name),
                ],
                limit=1,
            )
            values = {
                "name": department_name,
                "company_id": company.id,
                "parent_id": False,
                "sc_is_active": True,
            }
            if department:
                department.write(values)
                updated_departments.append(
                    {
                        "name": department_name,
                        "department_type": department_type,
                        "id": department.id,
                    }
                )
                continue
            department = Department.create(values)
            created_departments.append(
                {
                    "name": department_name,
                    "department_type": department_type,
                    "id": department.id,
                }
            )

        return {
            "company": {
                "id": company.id,
                "name": company.name,
            },
            "created_departments": created_departments,
            "updated_departments": updated_departments,
        }

    @api.model
    def bootstrap_customer_users_primary_departments(self):
        bootstrap = self.bootstrap_customer_company_departments()
        company = self.env["res.company"].sudo().browse(bootstrap["company"]["id"])
        Department = self.env["hr.department"].sudo()
        Users = self.env["res.users"].sudo().with_context(no_reset_password=True)

        departments_by_name = {
            department.name: department
            for department in Department.search([("company_id", "=", company.id)])
        }

        created_users = []
        updated_users = []
        deferred_extra_departments = []
        unresolved_departments = []

        for spec in self._CUSTOMER_USERS:
            primary_department_name = spec.get("primary_department")
            department = departments_by_name.get(primary_department_name) if primary_department_name else False
            if primary_department_name and not department:
                unresolved_departments.append(
                    {
                        "login": spec["login"],
                        "primary_department": primary_department_name,
                    }
                )
                continue

            values = {
                "name": spec["name"],
                "login": spec["login"],
                "phone": spec.get("phone") or False,
                "active": bool(spec.get("active", True)),
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "sc_department_id": department.id if department else False,
            }

            user = Users.search([("login", "=", spec["login"])], limit=1)
            if user:
                user.write(values)
                updated_users.append(
                    {
                        "login": spec["login"],
                        "name": spec["name"],
                        "primary_department": primary_department_name or False,
                        "id": user.id,
                    }
                )
            else:
                user = Users.create(values)
                created_users.append(
                    {
                        "login": spec["login"],
                        "name": spec["name"],
                        "primary_department": primary_department_name or False,
                        "id": user.id,
                    }
                )

            extra_departments = tuple(spec.get("extra_departments") or ())
            if extra_departments:
                deferred_extra_departments.append(
                    {
                        "login": spec["login"],
                        "primary_department": primary_department_name,
                        "extra_departments": list(extra_departments),
                    }
                )

        return {
            "company": {
                "id": company.id,
                "name": company.name,
            },
            "created_users": created_users,
            "updated_users": updated_users,
            "deferred_extra_departments": deferred_extra_departments,
            "unresolved_departments": unresolved_departments,
        }

    @api.model
    def customer_system_role_group_xmlids(self):
        return {
            role_label: list(xmlids)
            for role_label, xmlids in self._CUSTOMER_SYSTEM_ROLE_GROUP_XMLIDS.items()
        }

    @api.model
    def bootstrap_customer_user_system_roles(self):
        Users = self.env["res.users"].sudo()

        updated_users = []
        unresolved_users = []
        role_mapping = self.customer_system_role_group_xmlids()
        admin_stale_xmlids = {
            *role_mapping.get("管理员角色", []),
            "smart_construction_core.group_sc_business_full",
        }

        for login, role_labels in self._CUSTOMER_USER_SYSTEM_ROLES.items():
            user = Users.search([("login", "=", login)], limit=1)
            if not user:
                unresolved_users.append({"login": login, "role_labels": list(role_labels)})
                continue

            target_group_ids = []
            for role_label in role_labels:
                for xmlid in role_mapping.get(role_label, []):
                    group = self.env.ref(xmlid, raise_if_not_found=False)
                    if group and group.id not in target_group_ids:
                        target_group_ids.append(group.id)

            commands = []
            for group_id in target_group_ids:
                if group_id not in user.groups_id.ids:
                    commands.append((4, group_id))
            if "管理员角色" not in role_labels:
                for xmlid in admin_stale_xmlids:
                    group = self.env.ref(xmlid, raise_if_not_found=False)
                    if group and group.id in user.groups_id.ids:
                        commands.append((3, group.id))
            if commands:
                user.write({"groups_id": commands})

            updated_users.append(
                {
                    "login": login,
                    "role_labels": list(role_labels),
                    "group_xmlids": [xmlid for role_label in role_labels for xmlid in role_mapping.get(role_label, [])],
                    "id": user.id,
                }
            )

        return {
            "updated_users": updated_users,
            "unresolved_users": unresolved_users,
        }

    @api.model
    def bootstrap_customer_user_primary_posts(self):
        Company = self.env["res.company"].sudo()
        Post = self.env["sc.enterprise.post"].sudo()
        Users = self.env["res.users"].sudo()

        company = Company.search([("name", "=", self._CUSTOMER_COMPANY_NAME)], limit=1)
        if not company:
            return {
                "updated_users": [],
                "created_posts": [],
                "deferred_extra_posts": [],
                "unresolved_users": [{"company": self._CUSTOMER_COMPANY_NAME}],
            }

        created_posts = []
        updated_users = []
        deferred_extra_posts = []
        unresolved_users = []
        posts_by_name = {
            post.name: post
            for post in Post.search([("company_id", "=", company.id)])
        }

        for login, spec in self._CUSTOMER_USER_PRIMARY_POSTS.items():
            primary_post_name = spec["primary_post"]
            post = posts_by_name.get(primary_post_name)
            if not post:
                post = Post.create(
                    {
                        "name": primary_post_name,
                        "company_id": company.id,
                        "active": True,
                    }
                )
                posts_by_name[primary_post_name] = post
                created_posts.append(
                    {
                        "name": primary_post_name,
                        "id": post.id,
                    }
                )

            user = Users.search([("login", "=", login)], limit=1)
            if not user:
                unresolved_users.append({"login": login, "primary_post": primary_post_name})
                continue

            values = {
                "company_id": user.company_id.id or company.id,
                "sc_post_id": post.id,
            }
            user.write(values)
            updated_users.append(
                {
                    "login": login,
                    "primary_post": primary_post_name,
                    "id": user.id,
                }
            )

            extra_posts = tuple(spec.get("deferred_extra_posts") or ())
            if extra_posts:
                deferred_extra_posts.append(
                    {
                        "login": login,
                        "primary_post": primary_post_name,
                        "extra_posts": list(extra_posts),
                    }
                )

        return {
            "updated_users": updated_users,
            "created_posts": created_posts,
            "deferred_extra_posts": deferred_extra_posts,
            "unresolved_users": unresolved_users,
        }

    @api.model
    def bootstrap_customer_user_extra_posts(self):
        Company = self.env["res.company"].sudo()
        Post = self.env["sc.enterprise.post"].sudo()
        Users = self.env["res.users"].sudo()

        company = Company.search([("name", "=", self._CUSTOMER_COMPANY_NAME)], limit=1)
        if not company:
            return {
                "updated_users": [],
                "created_posts": [],
                "unresolved_users": [{"company": self._CUSTOMER_COMPANY_NAME}],
            }

        created_posts = []
        updated_users = []
        unresolved_users = []
        posts_by_name = {
            post.name: post
            for post in Post.search([("company_id", "=", company.id)])
        }

        for login, spec in self._CUSTOMER_USER_PRIMARY_POSTS.items():
            extra_posts = tuple(spec.get("deferred_extra_posts") or ())
            if not extra_posts:
                continue

            user = Users.search([("login", "=", login)], limit=1)
            if not user:
                unresolved_users.append({"login": login, "extra_posts": list(extra_posts)})
                continue

            target_post_ids = list(user.sc_post_ids.ids)
            for post_name in extra_posts:
                post = posts_by_name.get(post_name)
                if not post:
                    post = Post.create(
                        {
                            "name": post_name,
                            "company_id": company.id,
                            "active": True,
                        }
                    )
                    posts_by_name[post_name] = post
                    created_posts.append({"name": post_name, "id": post.id})
                if post.id not in target_post_ids:
                    target_post_ids.append(post.id)

            user.write({"sc_post_ids": [(6, 0, target_post_ids)]})
            updated_users.append(
                {
                    "login": login,
                    "extra_posts": list(extra_posts),
                    "id": user.id,
                }
            )

        return {
            "updated_users": updated_users,
            "created_posts": created_posts,
            "unresolved_users": unresolved_users,
        }

    @api.model
    def bootstrap_customer_user_extra_departments(self):
        Company = self.env["res.company"].sudo()
        Department = self.env["hr.department"].sudo()
        Users = self.env["res.users"].sudo()

        company = Company.search([("name", "=", self._CUSTOMER_COMPANY_NAME)], limit=1)
        if not company:
            return {
                "updated_users": [],
                "unresolved_users": [{"company": self._CUSTOMER_COMPANY_NAME}],
            }

        departments_by_name = {
            department.name: department
            for department in Department.search([("company_id", "=", company.id)])
        }

        updated_users = []
        unresolved_users = []

        for spec in self._CUSTOMER_USERS:
            extra_departments = tuple(spec.get("extra_departments") or ())
            if not extra_departments:
                continue

            user = Users.search([("login", "=", spec["login"])], limit=1)
            if not user:
                unresolved_users.append({"login": spec["login"], "extra_departments": list(extra_departments)})
                continue

            extra_department_ids = list(user.sc_department_ids.ids)
            missing = []
            for department_name in extra_departments:
                department = departments_by_name.get(department_name)
                if not department:
                    missing.append(department_name)
                    continue
                if department.id not in extra_department_ids:
                    extra_department_ids.append(department.id)

            if missing:
                unresolved_users.append(
                    {
                        "login": spec["login"],
                        "extra_departments": list(extra_departments),
                        "missing_departments": missing,
                    }
                )
                continue

            user.write({"sc_department_ids": [(6, 0, extra_department_ids)]})
            updated_users.append(
                {
                    "login": spec["login"],
                    "extra_departments": list(extra_departments),
                    "id": user.id,
                }
            )

        return {
            "updated_users": updated_users,
            "unresolved_users": unresolved_users,
        }
