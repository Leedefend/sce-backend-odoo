# -*- coding: utf-8 -*-

import re
from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import UserError


SUPPLIER_TYPE_SELECTION = [
    ("material", "材料供应商"),
    ("labor", "劳务供应商"),
    ("subcontract", "分包单位"),
    ("service", "服务供应商"),
    ("equipment", "设备供应商"),
    ("other", "其他"),
]


class ScSupplierType(models.Model):
    _name = "sc.supplier.type"
    _description = "供应商类型"
    _inherit = ["sc.delete.guard.mixin"]
    _order = "sequence, id"

    name = fields.Char(string="类型名称", required=True, translate=True)
    code = fields.Char(string="类型编码", required=True, index=True)
    sequence = fields.Integer(string="排序", default=10)
    active = fields.Boolean(string="启用", default=True)

    _sql_constraints = [
        ("code_uniq", "unique(code)", "供应商类型编码必须唯一。"),
    ]

    def unlink(self):
        active_types = self.filtered("active")
        if active_types:
            raise UserError("请先停用供应商类型后再删除。")
        self._sc_raise_delete_blockers(action_label="删除供应商类型")
        return super().unlink()


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "sc.delete.guard.mixin"]
    _sc_delete_guard_blocker_models = (
        "construction.contract",
        "payment.request",
        "project.project",
        "sc.contract.event",
        "sc.expense.claim",
        "sc.financing.loan",
        "sc.invoice.registration",
        "sc.material.acceptance",
        "sc.material.inbound",
        "sc.material.outbound",
        "sc.material.price",
        "sc.material.purchase.request",
        "sc.material.rfq",
        "sc.material.rental.order",
        "sc.material.rental.plan",
        "sc.payment.execution",
        "sc.plan",
        "sc.quality.issue",
        "sc.receipt.income",
        "sc.safety.issue",
        "sc.settlement.adjustment",
        "sc.settlement.order",
        "sc.subcontract.plan",
        "sc.subcontract.register",
        "sc.subcontract.request",
        "sc.subcontract.settlement",
        "sc.tax.deduction.registration",
        "tender.bid",
    )

    sc_supplier_type = fields.Selection(
        SUPPLIER_TYPE_SELECTION,
        string="主供应商类型",
        index=True,
    )
    sc_supplier_type_ids = fields.Many2many(
        "sc.supplier.type",
        "sc_res_partner_supplier_type_rel",
        "partner_id",
        "supplier_type_id",
        string="供应商类型",
    )
    sc_supplier_type_label = fields.Char(
        string="供应商类型汇总",
        compute="_compute_sc_supplier_type_label",
        store=True,
        readonly=True,
    )
    sc_account_name = fields.Char(string="账户名称")
    sc_bank_name = fields.Char(string="开户银行")
    sc_bank_account = fields.Char(string="账号")
    sc_region = fields.Char(string="所属地区", index=True)
    sc_registered_capital = fields.Char(string="注册资本")
    sc_establishment_date = fields.Date(string="成立日期")
    sc_business_term = fields.Char(string="营业期限")
    sc_legal_representative = fields.Char(string="法定代表人")
    sc_contact_name = fields.Char(string="联系人")
    sc_business_scope = fields.Text(string="经营范围")
    sc_default_tax_rate = fields.Float(string="默认税率%", digits=(16, 4))
    sc_default_tax_rate_text = fields.Char(string="税率文本")
    sc_source_partner_code = fields.Char(string="单位编号", index=True)
    sc_source_document_state = fields.Char(string="单据状态", index=True)
    sc_source_push_result = fields.Char(string="推送结果", index=True)
    sc_source_project_name = fields.Text(string="关联项目")
    sc_source_cooperation_type = fields.Char(string="合作类型", index=True)
    sc_source_fact_count = fields.Integer(string="业务事实数")
    sc_source_fact_source = fields.Char(string="关联业务范围")
    sc_source_receipt_amount = fields.Float(string="收款金额", digits=(16, 2))
    sc_source_payment_amount = fields.Float(string="付款金额", digits=(16, 2))
    sc_source_created_by = fields.Char(string="录入人")
    sc_source_created_at = fields.Char(string="录入时间")
    sc_business_fact_line_ids = fields.One2many(
        "sc.partner.business.fact.line",
        "partner_id",
        string="关联业务明细",
        readonly=True,
    )
    sc_supplier_note = fields.Text(string="供应商备注")
    sc_business_role_label = fields.Char(string="业务身份", compute="_compute_sc_business_display", store=True, readonly=True)
    sc_business_fact_basis = fields.Char(string="业务依据", compute="_compute_sc_business_display", store=True, readonly=True)
    sc_legacy_source_label = fields.Char(string="来源类型", compute="_compute_sc_business_display", store=True, readonly=True)
    sc_attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_res_partner_supplier_attachment_rel",
        "partner_id",
        "attachment_id",
        string="供应商附件",
    )

    # Historical identity carrier fields for idempotent migration replay.
    legacy_partner_id = fields.Char(string="历史供应商编号", index=True)
    legacy_partner_source = fields.Char(string="历史来源", index=True)
    legacy_partner_name = fields.Char(string="历史供应商名称")
    legacy_credit_code = fields.Char(string="历史统一信用代码")
    legacy_tax_no = fields.Char(string="历史税号", index=True)
    legacy_deleted_flag = fields.Char(string="历史删除标识")
    legacy_source_evidence = fields.Char(string="历史来源证据")

    @api.depends("sc_supplier_type_ids.name", "sc_supplier_type_ids.sequence", "sc_supplier_type")
    def _compute_sc_supplier_type_label(self):
        selection_labels = dict(SUPPLIER_TYPE_SELECTION)
        for partner in self:
            types = partner.sc_supplier_type_ids.sorted(lambda item: (item.sequence, item.id))
            if types:
                partner.sc_supplier_type_label = "、".join(types.mapped("name"))
            else:
                partner.sc_supplier_type_label = selection_labels.get(partner.sc_supplier_type or "", "")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("sc_skip_supplier_type_sync"):
            for record, vals in zip(records, vals_list):
                record._sc_sync_supplier_type_fields(vals)
        return records

    def write(self, vals):
        result = super().write(vals)
        if vals and not self.env.context.get("sc_skip_supplier_type_sync"):
            self._sc_sync_supplier_type_fields(vals)
        return result

    @api.model
    def _sc_backfill_supplier_type_ids(self):
        partners = self.sudo().with_context(active_test=False).search([("supplier_rank", ">", 0)])
        if not partners:
            return True

        type_by_code = {
            supplier_type.code: supplier_type
            for supplier_type in self.env["sc.supplier.type"].sudo().search([])
            if supplier_type.code
        }
        fallback_type = type_by_code.get("other")
        for partner in partners:
            supplier_type = type_by_code.get(partner.sc_supplier_type or "") or fallback_type
            if supplier_type and supplier_type not in partner.sc_supplier_type_ids:
                partner.with_context(sc_skip_supplier_type_sync=True).write(
                    {"sc_supplier_type_ids": [(4, supplier_type.id)]}
                )
        return True

    def _sc_sync_supplier_type_fields(self, vals):
        if not vals or self.env.context.get("sc_skip_supplier_type_sync"):
            return
        Type = self.env["sc.supplier.type"].sudo()
        for partner in self:
            if "sc_supplier_type_ids" in vals:
                first_type = partner.sc_supplier_type_ids.sorted(lambda item: (item.sequence, item.id))[:1]
                partner.with_context(sc_skip_supplier_type_sync=True).write(
                    {"sc_supplier_type": first_type.code if first_type else False}
                )
                continue
            if "sc_supplier_type" in vals and partner.sc_supplier_type:
                type_rec = Type.search([("code", "=", partner.sc_supplier_type)], limit=1)
                if type_rec and type_rec not in partner.sc_supplier_type_ids:
                    partner.with_context(sc_skip_supplier_type_sync=True).write(
                        {"sc_supplier_type_ids": [(4, type_rec.id)]}
                    )

    @api.depends("customer_rank", "supplier_rank", "legacy_partner_source")
    def _compute_sc_business_display(self):
        for partner in self:
            customer = bool(partner.customer_rank)
            supplier = bool(partner.supplier_rank)
            if customer and supplier:
                partner.sc_business_role_label = "客户/供应商"
            elif customer:
                partner.sc_business_role_label = "客户"
            elif supplier:
                partner.sc_business_role_label = "供应商"
            else:
                partner.sc_business_role_label = "后台留存"

            source = partner.legacy_partner_source or ""
            if customer and supplier:
                partner.sc_business_fact_basis = "收款/收入与供应商业务事实"
            elif customer:
                partner.sc_business_fact_basis = "收款合同/收款/收入业务事实"
            elif supplier:
                partner.sc_business_fact_basis = "供应商合同/付款业务事实"
            else:
                partner.sc_business_fact_basis = "无用户要求展示业务事实"

            if source == "legacy_mssql_customer_business_fact":
                partner.sc_legacy_source_label = "旧业务库客户事实"
            elif source == "xlsx_business_aligned_partner":
                partner.sc_legacy_source_label = "客户供应商整理数据"
            elif source:
                partner.sc_legacy_source_label = source
            else:
                partner.sc_legacy_source_label = ""

    def action_open_sc_partner_business_fact_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "smart_construction_core.action_sc_partner_business_fact_line"
        )
        context = action.get("context") if isinstance(action.get("context"), dict) else {}
        action.update(
            {
                "domain": [("partner_id", "=", self.id)],
                "context": {
                    **context,
                    "search_default_group_source_label": 1,
                    "default_partner_id": self.id,
                },
                "target": "current",
            }
        )
        return action

    @api.model
    def _sc_fact_model(self, model_name):
        if model_name not in self.env.registry:
            return False
        return self.env[model_name].sudo().with_context(active_test=False)

    @api.model
    def _sc_partner_id_from_read(self, value):
        if isinstance(value, (list, tuple)) and value:
            return value[0]
        return value if isinstance(value, int) else False

    @api.model
    def _sc_partner_text_from_read(self, value):
        if isinstance(value, (list, tuple)) and len(value) > 1:
            return value[1] or ""
        return value or ""

    @api.model
    def _sc_is_supplier_business_counterparty(self, partner):
        name = (partner.name or "").strip()
        if not name:
            return False
        if name.lower() in {"admin", "administrator", "odoobot", "system"}:
            return False
        if name.lower().startswith("unknown legacy supplier"):
            return False
        if re.match(r"^\d{1,2}月报销$", name) or name.endswith("报销"):
            return False
        if partner.is_company or partner.vat or partner.legacy_partner_id:
            return True
        return False

    def unlink(self):
        self._sc_raise_delete_blockers(action_label="删除往来单位")
        return super().unlink()

    @api.model
    def _sc_collect_partner_business_facts(self):
        """Collect fact-backed customer/supplier roles from runtime business data.

        User-facing customer/supplier menus should be driven by business facts:
        income contracts or receipt facts make a counterparty a customer; other
        expenditure-side facts make a counterparty a supplier.
        """

        facts = defaultdict(
            lambda: {
                "customer": False,
                "supplier": False,
                "count": 0,
                "receipt_amount": 0.0,
                "payment_amount": 0.0,
                "sources": set(),
                "projects": set(),
                "account_name": "",
                "bank_name": "",
                "bank_account": "",
                "created_by": "",
                "created_at": "",
                "created_sort": "",
            }
        )

        user_display_by_legacy_id = {}
        user_display_by_login = {}
        if "sc.legacy.user.profile" in self.env.registry:
            Profile = self.env["sc.legacy.user.profile"].sudo().with_context(active_test=False)
            for profile in Profile.search([]):
                display_name = (profile.display_name or profile.user_id.name or "").strip()
                if not display_name:
                    continue
                legacy_user_id = (profile.legacy_user_id or "").strip()
                if legacy_user_id:
                    user_display_by_legacy_id[legacy_user_id] = display_name
                for login in (profile.source_login, profile.generated_login):
                    login_text = (login or "").strip().lower()
                    if login_text:
                        user_display_by_login[login_text] = display_name
        for user in self.env["res.users"].sudo().with_context(active_test=False).search([]):
            login = (user.login or "").strip().lower()
            display_name = (user.name or "").strip()
            if login and display_name and login != display_name.lower():
                user_display_by_login.setdefault(login, display_name)

        def clean_text(value):
            if value in (None, False):
                return ""
            text = str(value).strip()
            return "" if text in {"False", "false", "None", "none", "NULL", "null"} else text

        def normalize_source_user(value, legacy_user_id=None):
            def valid_display(text):
                lowered = text.lower()
                return not (
                    lowered in {"odoobot", "administrator", "admin", "system"}
                    or text in {"系统", "系统导入"}
                )

            legacy_key = clean_text(legacy_user_id)
            if legacy_key and legacy_key in user_display_by_legacy_id:
                mapped_legacy_user = user_display_by_legacy_id[legacy_key]
                return mapped_legacy_user if valid_display(mapped_legacy_user) else ""
            text = clean_text(value)
            if not text:
                return ""
            if not valid_display(text):
                return ""
            lowered = text.lower()
            mapped = user_display_by_login.get(lowered)
            if mapped:
                return mapped if valid_display(mapped) else ""
            if re.fullmatch(r"[A-Za-z][A-Za-z0-9_.@-]{1,63}", text) and not re.search(r"[\u4e00-\u9fff]", text):
                return ""
            return text

        def datetime_text(value):
            if not value:
                return ""
            if hasattr(value, "strftime"):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            return clean_text(value)

        def source_sort_value(value):
            if not value:
                return ""
            if hasattr(value, "isoformat"):
                return value.isoformat()
            return clean_text(value)

        def amount_value(value):
            try:
                return float(value or 0.0)
            except (TypeError, ValueError):
                return 0.0

        def should_replace_created_fact(data, created_at):
            current_sort = data.get("created_sort") or ""
            next_sort = source_sort_value(created_at)
            if not data.get("created_by"):
                return True
            if next_sort and (not current_sort or next_sort < current_sort):
                return True
            return False

        def add_records(
            model_name,
            domain,
            *,
            role,
            source_label,
            partner_field="partner_id",
            amount_field=None,
            amount_bucket=None,
            project_field="project_id",
            account_name_field=None,
            bank_name_field=None,
            bank_account_field=None,
            created_by_fields=("creator_name", "created_by_name", "source_operator"),
            created_by_legacy_fields=("creator_legacy_user_id", "created_by_legacy_user_id"),
            created_at_fields=("created_time", "source_time", "legacy_created_at"),
        ):
            Model = self._sc_fact_model(model_name)
            if Model is False or partner_field not in Model._fields:
                return
            fields_to_read = [partner_field]
            for field_name in (
                amount_field,
                project_field,
                account_name_field,
                bank_name_field,
                bank_account_field,
            ):
                if field_name and field_name in Model._fields and field_name not in fields_to_read:
                    fields_to_read.append(field_name)
            source_created_by_fields = [
                field_name for field_name in created_by_fields if field_name and field_name in Model._fields
            ]
            source_created_by_legacy_fields = [
                field_name for field_name in created_by_legacy_fields if field_name and field_name in Model._fields
            ]
            source_created_at_fields = [
                field_name for field_name in created_at_fields if field_name and field_name in Model._fields
            ]
            for field_name in source_created_by_fields + source_created_by_legacy_fields + source_created_at_fields:
                if field_name not in fields_to_read:
                    fields_to_read.append(field_name)
            for row in Model.search_read(domain, fields_to_read):
                partner_id = self._sc_partner_id_from_read(row.get(partner_field))
                if not partner_id:
                    continue
                data = facts[partner_id]
                data[role] = True
                data["count"] += 1
                data["sources"].add(source_label)
                if amount_field and amount_bucket:
                    data[amount_bucket] += amount_value(row.get(amount_field))
                if project_field and project_field in row:
                    project_name = self._sc_partner_text_from_read(row.get(project_field))
                    if project_name:
                        data["projects"].add(project_name)
                if account_name_field and not data["account_name"]:
                    data["account_name"] = row.get(account_name_field) or ""
                if bank_name_field and not data["bank_name"]:
                    data["bank_name"] = row.get(bank_name_field) or ""
                if bank_account_field and not data["bank_account"]:
                    data["bank_account"] = row.get(bank_account_field) or ""
                source_created_by = ""
                for field_name in source_created_by_fields:
                    source_created_by = normalize_source_user(row.get(field_name))
                    if source_created_by:
                        break
                for field_name in source_created_by_legacy_fields:
                    source_legacy_user_id = clean_text(row.get(field_name))
                    if not source_legacy_user_id:
                        continue
                    mapped_user = normalize_source_user(source_created_by, source_legacy_user_id)
                    if mapped_user:
                        source_created_by = mapped_user
                    break
                source_created_at = False
                for field_name in source_created_at_fields:
                    source_created_at = row.get(field_name)
                    if source_created_at:
                        break
                if (source_created_by or source_created_at) and should_replace_created_fact(data, source_created_at):
                    if source_created_by:
                        data["created_by"] = source_created_by
                    if source_created_at:
                        data["created_at"] = datetime_text(source_created_at)
                        data["created_sort"] = source_sort_value(source_created_at)

        add_records(
            "construction.contract",
            [("type", "=", "out"), ("partner_id", "!=", False)],
            role="customer",
            source_label="收入合同",
            amount_field="amount_final",
            amount_bucket="receipt_amount",
            created_by_fields=("entry_user_text",),
            created_by_legacy_fields=(),
            created_at_fields=("entry_time",),
        )
        add_records(
            "sc.receipt.income",
            [("partner_id", "!=", False)],
            role="customer",
            source_label="收款事实",
            amount_field="amount",
            amount_bucket="receipt_amount",
            account_name_field="receiving_account_name",
            bank_name_field="receiving_bank_name",
            bank_account_field="receiving_account_no",
        )
        add_records(
            "payment.request",
            [("type", "=", "receive"), ("partner_id", "!=", False)],
            role="customer",
            source_label="收款申请",
            amount_field="amount",
            amount_bucket="receipt_amount",
        )
        add_records(
            "sc.legacy.receipt.residual.fact",
            [("partner_id", "!=", False)],
            role="customer",
            source_label="历史收款事实",
            amount_field="amount",
            amount_bucket="receipt_amount",
            project_field="project_id",
            bank_account_field="receiving_account",
        )

        add_records(
            "construction.contract",
            [("type", "=", "in"), ("partner_id", "!=", False)],
            role="supplier",
            source_label="支出合同",
            amount_field="amount_final",
            amount_bucket="payment_amount",
            created_by_fields=("entry_user_text",),
            created_by_legacy_fields=(),
            created_at_fields=("entry_time",),
        )
        add_records(
            "payment.request",
            [("type", "=", "pay"), ("partner_id", "!=", False)],
            role="supplier",
            source_label="付款申请",
            amount_field="amount",
            amount_bucket="payment_amount",
        )
        add_records(
            "sc.payment.execution",
            [("partner_id", "!=", False)],
            role="supplier",
            source_label="付款执行",
            amount_field="paid_amount",
            amount_bucket="payment_amount",
            account_name_field="receipt_account_name",
            bank_name_field="receipt_bank_name",
            bank_account_field="receipt_account_no",
        )
        add_records(
            "sc.legacy.payment.residual.fact",
            [("partner_id", "!=", False)],
            role="supplier",
            source_label="历史付款事实",
            amount_field="paid_amount",
            amount_bucket="payment_amount",
            project_field="project_id",
            bank_account_field="bank_account",
        )
        add_records(
            "sc.settlement.order",
            [("partner_id", "!=", False)],
            role="supplier",
            source_label="支出结算",
            amount_field="amount_total",
            amount_bucket="payment_amount",
        )
        add_records(
            "sc.legacy.enterprise.business.fact",
            [("partner_id", "!=", False), ("fact_family", "in", ["payment", "supplier_contract"])],
            role="supplier",
            source_label="历史支出事实",
            amount_field="amount_total",
            amount_bucket="payment_amount",
            project_field="legacy_project_name",
        )
        add_records(
            "sc.legacy.expense.deposit.fact",
            [("partner_id", "!=", False), ("direction", "=", "outflow")],
            role="supplier",
            source_label="历史费用/保证金支出",
            amount_field="source_amount",
            amount_bucket="payment_amount",
        )
        add_records(
            "sc.legacy.supplier.contract.pricing.fact",
            [("partner_id", "!=", False)],
            role="supplier",
            source_label="历史供应商合同",
            amount_field="amount_total",
            amount_bucket="payment_amount",
        )
        add_records(
            "sc.legacy.invoice.registration.line",
            [("partner_id", "!=", False)],
            role="supplier",
            source_label="历史供应商发票",
            amount_field="amount_total",
            amount_bucket="payment_amount",
        )
        return facts

    @api.model
    def action_sc_align_partner_roles_from_business_facts(self, demote_no_fact=True):
        facts = self._sc_collect_partner_business_facts()
        Partner = self.sudo().with_context(active_test=False)
        target_ids = set(facts)
        if demote_no_fact:
            current = Partner.search(["|", ("customer_rank", ">", 0), ("supplier_rank", ">", 0)])
            target_ids.update(current.ids)

        action_counts = defaultdict(int)
        for partner in Partner.browse(sorted(target_ids)).exists():
            data = facts.get(partner.id)
            customer = bool(data and data["customer"])
            supplier = bool(data and data["supplier"] and self._sc_is_supplier_business_counterparty(partner))
            vals = {}
            if customer and not partner.customer_rank:
                vals["customer_rank"] = 1
            elif demote_no_fact and not customer and partner.customer_rank:
                vals["customer_rank"] = 0
            if supplier and not partner.supplier_rank:
                vals["supplier_rank"] = 1
            elif demote_no_fact and not supplier and partner.supplier_rank:
                vals["supplier_rank"] = 0
            if data:
                vals.update(
                    {
                        "sc_source_fact_count": data["count"],
                        "sc_source_fact_source": "；".join(sorted(data["sources"]))[:255],
                        "sc_source_project_name": "；".join(sorted(data["projects"]))[:1000] or False,
                        "sc_source_receipt_amount": data["receipt_amount"],
                        "sc_source_payment_amount": data["payment_amount"],
                    }
                )
                if data["account_name"] and not partner.sc_account_name:
                    vals["sc_account_name"] = data["account_name"]
                if data["bank_name"] and not partner.sc_bank_name:
                    vals["sc_bank_name"] = data["bank_name"]
                if data["bank_account"] and not partner.sc_bank_account:
                    vals["sc_bank_account"] = data["bank_account"]
                if data["created_by"] and (
                    not partner.sc_source_created_by
                    or partner.sc_source_created_by.strip().lower() in {"odoobot", "administrator", "admin", "system"}
                    or partner.sc_source_created_by in {"系统", "系统导入"}
                ):
                    vals["sc_source_created_by"] = data["created_by"]
                if data["created_at"] and (
                    not partner.sc_source_created_at
                    or partner.sc_source_created_at.startswith(("2026-05-08", "2026-05-09"))
                ):
                    vals["sc_source_created_at"] = data["created_at"]
                if supplier and not partner.sc_supplier_type:
                    vals["sc_supplier_type"] = "other"
            if vals:
                partner.write(vals)
                action_counts["updated"] += 1
            else:
                action_counts["unchanged"] += 1

        customer_fact_partners = 0
        supplier_fact_partners = 0
        source_created_by_fact_partners = 0
        source_created_at_fact_partners = 0
        for partner in Partner.browse(sorted(facts)).exists():
            data = facts.get(partner.id)
            if data and data["customer"]:
                customer_fact_partners += 1
            if data and data["supplier"] and self._sc_is_supplier_business_counterparty(partner):
                supplier_fact_partners += 1
            if data and data["created_by"]:
                source_created_by_fact_partners += 1
            if data and data["created_at"]:
                source_created_at_fact_partners += 1

        summary = {
            "status": "PASS",
            "customer_fact_partners": customer_fact_partners,
            "supplier_fact_partners": supplier_fact_partners,
            "source_created_by_fact_partners": source_created_by_fact_partners,
            "source_created_at_fact_partners": source_created_at_fact_partners,
            "fact_partner_total": len(facts),
            "target_partner_total": len(target_ids),
            "demote_no_fact": bool(demote_no_fact),
            "action_counts": dict(sorted(action_counts.items())),
        }
        return summary


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    sc_legacy_external_id = fields.Char(string="历史账户外部键", index=True, copy=False)
    sc_legacy_partner_id = fields.Char(string="历史往来单位编号", index=True)
    sc_legacy_partner_source = fields.Char(string="历史往来单位来源", index=True)
    sc_legacy_partner_name = fields.Char(string="历史往来单位名称")
    sc_account_holder_name = fields.Char(string="账户名称")
    sc_bank_name = fields.Char(string="开户银行", index=True)
    sc_source_evidence = fields.Char(string="历史来源证据")
    sc_import_batch = fields.Char(string="导入批次", index=True)

    _sql_constraints = [
        (
            "sc_legacy_external_id_unique",
            "unique(sc_legacy_external_id)",
            "历史账户外部键必须唯一。",
        ),
    ]


class ScPartnerImportReview(models.Model):
    _name = "sc.partner.import.review"
    _description = "客户供应商导入复核"
    _order = "review_state, review_reason, partner_name"
    _rec_name = "partner_name"

    import_batch = fields.Char(string="导入批次", required=True, default="partner_business_fit_v1", index=True)
    legacy_partner_source = fields.Char(string="历史来源", required=True, index=True)
    legacy_partner_id = fields.Char(string="历史身份键", required=True, index=True)
    partner_name = fields.Char(string="往来单位名称", required=True, index=True)
    company_type = fields.Selection([("company", "企业/组织"), ("person", "个人")], string="类型", default="company", index=True)
    review_reason = fields.Selection(
        [
            ("background_only_no_user_requested_business_fact", "后台留存"),
            ("unknown_business_role", "角色不明确"),
            ("personal_fragment_review", "个人片段复核"),
            ("invalid_bank_account_review", "银行账户异常"),
            ("invalid_or_placeholder_credit", "信用代码异常"),
            ("multiple_current_payload_matches", "多目标匹配"),
            ("update_only_not_found", "仅更新目标未命中"),
            ("update_only_ambiguous", "仅更新目标歧义"),
            ("mixed_blocker", "多重阻断"),
        ],
        string="复核原因",
        required=True,
        default="mixed_blocker",
        index=True,
    )
    review_state = fields.Selection(
        [
            ("candidate", "待复核"),
            ("resolved", "已处理"),
            ("ignored", "忽略"),
        ],
        string="复核状态",
        required=True,
        default="candidate",
        index=True,
    )
    suggested_customer_rank = fields.Integer(string="建议客户标识")
    suggested_supplier_rank = fields.Integer(string="建议供应商标识")
    confirmed_customer_rank = fields.Integer(string="确认客户标识")
    confirmed_supplier_rank = fields.Integer(string="确认供应商标识")
    target_partner_id = fields.Many2one("res.partner", string="目标往来单位", index=True, ondelete="set null")
    sc_supplier_type = fields.Char(string="供应商类型")
    sc_region = fields.Char(string="所属地区", index=True)
    street = fields.Char(string="地址")
    sc_registered_capital = fields.Char(string="注册资本")
    sc_business_scope = fields.Text(string="经营范围")
    sc_default_tax_rate = fields.Float(string="默认税率%", digits=(16, 4))
    sc_default_tax_rate_text = fields.Char(string="历史税率文本")
    vat = fields.Char(string="统一社会信用代码", index=True)
    sc_account_name = fields.Char(string="账户名称")
    sc_bank_name = fields.Char(string="开户银行")
    sc_bank_account = fields.Char(string="账号")
    source_created_by = fields.Char(string="来源创建人")
    source_created_at = fields.Char(string="来源创建时间")
    source_document_state = fields.Char(string="来源单据状态")
    source_push_result = fields.Char(string="来源推送结果")
    source_project_name = fields.Text(string="来源项目")
    source_files = fields.Text(string="来源文件")
    review_flags = fields.Char(string="复核标记")
    gate_reason = fields.Char(string="阻断原因")
    evidence = fields.Text(string="证据")
    reviewer_id = fields.Many2one("res.users", string="处理人", readonly=True, ondelete="set null")
    reviewed_at = fields.Datetime(string="处理时间", readonly=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "sc_partner_import_review_identity_unique",
            "unique(import_batch, legacy_partner_source, legacy_partner_id)",
            "同一导入批次的客户供应商复核身份必须唯一。",
        ),
    ]

    def _mark_resolved(self, customer_rank: int, supplier_rank: int) -> None:
        self.write(
            {
                "review_state": "resolved",
                "confirmed_customer_rank": customer_rank,
                "confirmed_supplier_rank": supplier_rank,
                "reviewer_id": self.env.user.id,
                "reviewed_at": fields.Datetime.now(),
            }
        )

    def action_resolve_customer(self):
        self._mark_resolved(1, 0)

    def action_resolve_supplier(self):
        self._mark_resolved(0, 1)

    def action_resolve_customer_supplier(self):
        self._mark_resolved(1, 1)

    def action_ignore(self):
        self.write(
            {
                "review_state": "ignored",
                "reviewer_id": self.env.user.id,
                "reviewed_at": fields.Datetime.now(),
            }
        )
