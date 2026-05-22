# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ConstructionContract(models.Model):
    _inherit = "construction.contract"

    def _sync_professional_contract_wrappers(self):
        ids = [record_id for record_id in self.ids if record_id]
        if not ids:
            return
        self.flush_recordset(["type", "create_uid", "create_date", "write_uid", "write_date"])
        self.env.cr.execute(
            """
            DELETE FROM construction_contract_income i
             USING construction_contract c
             WHERE i.contract_id = c.id
               AND c.id = ANY(%s)
               AND c.type != 'out'
            """,
            (ids,),
        )
        self.env["construction.contract.income"].invalidate_model()
        self.env["construction.contract.expense"].invalidate_model()
        self.env.cr.execute(
            """
            DELETE FROM construction_contract_expense e
             USING construction_contract c
             WHERE e.contract_id = c.id
               AND c.id = ANY(%s)
               AND (
                    c.type != 'in'
                    OR COALESCE(c.subject, '') ILIKE '发票关联支出合同%%'
               )
            """,
            (ids,),
        )
        self.env.cr.execute(
            """
            INSERT INTO construction_contract_income
                (contract_id, create_uid, create_date, write_uid, write_date)
            SELECT c.id, COALESCE(c.create_uid, 1), COALESCE(c.create_date, NOW()),
                   COALESCE(c.write_uid, c.create_uid, 1), COALESCE(c.write_date, c.create_date, NOW())
              FROM construction_contract c
              LEFT JOIN construction_contract_income i ON i.contract_id = c.id
             WHERE c.id = ANY(%s)
               AND c.type = 'out'
               AND i.id IS NULL
            """,
            (ids,),
        )
        self.env.cr.execute(
            """
            INSERT INTO construction_contract_expense
                (contract_id, create_uid, create_date, write_uid, write_date)
            SELECT c.id, COALESCE(c.create_uid, 1), COALESCE(c.create_date, NOW()),
                   COALESCE(c.write_uid, c.create_uid, 1), COALESCE(c.write_date, c.create_date, NOW())
              FROM construction_contract c
              LEFT JOIN construction_contract_expense e ON e.contract_id = c.id
             WHERE c.id = ANY(%s)
               AND c.type = 'in'
               AND COALESCE(c.subject, '') NOT ILIKE '发票关联支出合同%%'
               AND e.id IS NULL
            """,
            (ids,),
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("skip_professional_contract_wrapper_sync"):
            records._sync_professional_contract_wrappers()
        return records

    def write(self, vals):
        sync_required = "type" in vals
        res = super().write(vals)
        if sync_required:
            self._sync_professional_contract_wrappers()
        return res


class _ConstructionContractProfessionalMixin(models.AbstractModel):
    _name = "construction.contract.professional.mixin"
    _description = "专业合同模型公共逻辑"

    _contract_type = None

    def _ensure_contract_type(self, vals):
        expected = self._contract_type
        if expected and vals.get("type") not in (None, "", expected):
            raise ValidationError("专业合同入口不允许切换合同收支类型。")
        contract_id = vals.get("contract_id")
        if expected and contract_id:
            contract = self.env["construction.contract"].browse(contract_id).exists()
            if contract and contract.type != expected:
                raise ValidationError("专业合同入口不能绑定其他收支类型的底层合同。")
        if expected:
            vals["type"] = expected
        return vals

    def _delegate_contract_action(self, method_name):
        contracts = self.mapped("contract_id")
        if not contracts:
            return True
        return getattr(contracts, method_name)()

    def action_generate_lines_from_budget(self):
        return self._delegate_contract_action("action_generate_lines_from_budget")

    def action_confirm(self):
        return self._delegate_contract_action("action_confirm")

    def validate_tier(self):
        return self._delegate_contract_action("validate_tier")

    def reject_tier(self):
        return self._delegate_contract_action("reject_tier")

    def action_set_running(self):
        return self._delegate_contract_action("action_set_running")

    def action_close(self):
        return self._delegate_contract_action("action_close")

    def action_cancel(self):
        return self._delegate_contract_action("action_cancel")

    def action_reset_draft(self):
        return self._delegate_contract_action("action_reset_draft")


class ConstructionContractIncome(models.Model):
    _name = "construction.contract.income"
    _description = "收入合同"
    _inherits = {"construction.contract": "contract_id"}
    _inherit = "construction.contract.professional.mixin"
    _order = "project_id, id desc"
    _contract_type = "out"

    contract_id = fields.Many2one(
        "construction.contract",
        string="底层项目合同",
        required=True,
        index=True,
        ondelete="cascade",
    )

    _sql_constraints = [
        ("contract_income_contract_unique", "unique(contract_id)", "收入合同包装记录不能重复。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._ensure_contract_type(dict(vals)) for vals in vals_list]
        return super(
            ConstructionContractIncome,
            self.with_context(skip_professional_contract_wrapper_sync=True),
        ).create(vals_list)

    def write(self, vals):
        vals = self._ensure_contract_type(dict(vals))
        return super().write(vals)

    def init(self):
        self.env.cr.execute(
            """
            INSERT INTO construction_contract_income
                (contract_id, create_uid, create_date, write_uid, write_date)
            SELECT c.id, COALESCE(c.create_uid, 1), COALESCE(c.create_date, NOW()),
                   COALESCE(c.write_uid, c.create_uid, 1), COALESCE(c.write_date, c.create_date, NOW())
              FROM construction_contract c
              LEFT JOIN construction_contract_income i ON i.contract_id = c.id
             WHERE c.type = 'out'
               AND i.id IS NULL
            """
        )


class ConstructionContractExpense(models.Model):
    _name = "construction.contract.expense"
    _description = "支出合同"
    _inherits = {"construction.contract": "contract_id"}
    _inherit = "construction.contract.professional.mixin"
    _order = "project_id, id desc"
    _contract_type = "in"

    contract_id = fields.Many2one(
        "construction.contract",
        string="底层项目合同",
        required=True,
        index=True,
        ondelete="cascade",
    )

    _sql_constraints = [
        ("contract_expense_contract_unique", "unique(contract_id)", "支出合同包装记录不能重复。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._ensure_contract_type(dict(vals)) for vals in vals_list]
        return super(
            ConstructionContractExpense,
            self.with_context(skip_professional_contract_wrapper_sync=True),
        ).create(vals_list)

    def write(self, vals):
        vals = self._ensure_contract_type(dict(vals))
        return super().write(vals)

    def init(self):
        self.env.cr.execute(
            """
            DELETE FROM construction_contract_expense e
             USING construction_contract c
             WHERE e.contract_id = c.id
               AND COALESCE(c.subject, '') ILIKE '发票关联支出合同%%'
            """
        )
        self.env.cr.execute(
            """
            INSERT INTO construction_contract_expense
                (contract_id, create_uid, create_date, write_uid, write_date)
            SELECT c.id, COALESCE(c.create_uid, 1), COALESCE(c.create_date, NOW()),
                   COALESCE(c.write_uid, c.create_uid, 1), COALESCE(c.write_date, c.create_date, NOW())
              FROM construction_contract c
             LEFT JOIN construction_contract_expense e ON e.contract_id = c.id
             WHERE c.type = 'in'
               AND COALESCE(c.subject, '') NOT ILIKE '发票关联支出合同%%'
               AND e.id IS NULL
            """
        )
