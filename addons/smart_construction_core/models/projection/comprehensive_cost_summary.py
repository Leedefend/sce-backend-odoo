# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class ScComprehensiveCostSummary(models.Model):
    _name = "sc.comprehensive.cost.summary"
    _description = "成本统计表（综合）"
    _auto = False
    _rec_name = "display_name"
    _order = "project_id"

    display_name = fields.Char(string="汇总项", readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)

    income_contract_amount = fields.Monetary(string="收入合同金额", currency_field="currency_id", readonly=True)
    receipt_amount = fields.Monetary(string="已收款", currency_field="currency_id", readonly=True)
    output_invoice_amount = fields.Monetary(string="已开票", currency_field="currency_id", readonly=True)
    receivable_unpaid_amount = fields.Monetary(string="未收款", currency_field="currency_id", readonly=True)

    payable_contract_amount = fields.Monetary(string="应付合同金额", currency_field="currency_id", readonly=True)
    supplier_contract_amount = fields.Monetary(string="供应商合同金额", currency_field="currency_id", readonly=True)
    material_cost_amount = fields.Monetary(string="材料成本", currency_field="currency_id", readonly=True)
    labor_cost_amount = fields.Monetary(string="劳务/分包成本", currency_field="currency_id", readonly=True)
    lease_cost_amount = fields.Monetary(string="租赁/机械成本", currency_field="currency_id", readonly=True)
    expense_cost_amount = fields.Monetary(string="费用成本", currency_field="currency_id", readonly=True)
    salary_cost_amount = fields.Monetary(string="工资成本", currency_field="currency_id", readonly=True)
    input_invoice_amount = fields.Monetary(string="成本发票金额", currency_field="currency_id", readonly=True)
    paid_amount = fields.Monetary(string="已付款", currency_field="currency_id", readonly=True)
    payable_unpaid_amount = fields.Monetary(string="未付款", currency_field="currency_id", readonly=True)

    total_cost_amount = fields.Monetary(string="成本合计（已承载）", currency_field="currency_id", readonly=True)
    profit_amount = fields.Monetary(string="利润额（已承载）", currency_field="currency_id", readonly=True)
    profit_rate = fields.Float(string="利润率(%)", readonly=True)

    source_line_count = fields.Integer(string="来源明细数", readonly=True)
    material_line_count = fields.Integer(string="材料明细数", readonly=True)
    expense_line_count = fields.Integer(string="费用单数", readonly=True)
    salary_line_count = fields.Integer(string="工资单数", readonly=True)
    coverage_note = fields.Char(string="承载说明", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("成本统计表（综合）是历史事实汇总结果，请从来源业务单据维护数据。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('project_project'),
                to_regclass('res_company'),
                to_regclass('construction_contract'),
                to_regclass('sc_receipt_income'),
                to_regclass('sc_invoice_registration'),
                to_regclass('sc_payment_execution'),
                to_regclass('sc_expense_claim'),
                to_regclass('sc_hr_payroll_document'),
                to_regclass('sc_legacy_material_stock_fact'),
                to_regclass('sc_legacy_labor_subcontract_fact'),
                to_regclass('sc_legacy_equipment_lease_fact'),
                to_regclass('sc_legacy_supplier_contract_pricing_fact')
            """
        )
        if not all(self._cr.fetchone()):
            return
        self._cr.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_class
                    WHERE oid = to_regclass('{self._table}')
                      AND relkind = 'v'
                ) THEN
                    EXECUTE 'DROP VIEW IF EXISTS {self._table} CASCADE';
                ELSIF EXISTS (
                    SELECT 1 FROM pg_class
                    WHERE oid = to_regclass('{self._table}')
                      AND relkind = 'm'
                ) THEN
                    EXECUTE 'DROP MATERIALIZED VIEW IF EXISTS {self._table} CASCADE';
                ELSE
                    EXECUTE 'DROP TABLE IF EXISTS {self._table} CASCADE';
                END IF;
            END $$;
            """
        )
        self._cr.execute(
            f"""
            CREATE TABLE {self._table} AS (
                WITH income_contract AS (
                    SELECT project_id, SUM(COALESCE(amount_total, 0.0)) AS income_contract_amount, COUNT(*)::integer AS cnt
                    FROM construction_contract
                    WHERE type = 'out' AND COALESCE(archived, FALSE) IS FALSE AND state <> 'cancel'
                    GROUP BY project_id
                ),
                payable_contract AS (
                    SELECT project_id, SUM(COALESCE(amount_total, 0.0)) AS payable_contract_amount, COUNT(*)::integer AS cnt
                    FROM construction_contract
                    WHERE type = 'in' AND COALESCE(archived, FALSE) IS FALSE AND state <> 'cancel'
                    GROUP BY project_id
                ),
                supplier_contract AS (
                    SELECT
                        project_id,
                        SUM(COALESCE(amount_total, 0.0)) AS supplier_contract_amount,
                        COUNT(*)::integer AS cnt
                    FROM sc_legacy_supplier_contract_pricing_fact
                    WHERE active IS TRUE
                      AND COALESCE(deleted_flag, '0') IN ('0', '')
                    GROUP BY project_id
                ),
                receipt AS (
                    SELECT project_id, SUM(COALESCE(amount, 0.0)) AS receipt_amount, COUNT(*)::integer AS cnt
                    FROM sc_receipt_income
                    WHERE active IS TRUE AND state <> 'cancel'
                    GROUP BY project_id
                ),
                invoice AS (
                    SELECT
                        project_id,
                        SUM(CASE WHEN direction = 'output' THEN COALESCE(amount_total, 0.0) ELSE 0.0 END)
                            AS output_invoice_amount,
                        SUM(CASE WHEN direction = 'input' THEN COALESCE(amount_total, 0.0) ELSE 0.0 END)
                            AS input_invoice_amount,
                        COUNT(*)::integer AS cnt
                    FROM sc_invoice_registration
                    WHERE active IS TRUE AND state <> 'cancel'
                    GROUP BY project_id
                ),
                payment AS (
                    SELECT
                        project_id,
                        SUM(COALESCE(paid_amount, 0.0)) AS paid_amount,
                        COUNT(*)::integer AS cnt
                    FROM sc_payment_execution
                    WHERE active IS TRUE AND state <> 'cancel'
                    GROUP BY project_id
                ),
                material_cost AS (
                    SELECT
                        project_id,
                        SUM(CASE
                            WHEN fact_type IN ('stock_in', 'stock_in_line', 'scbs_stock_in', 'material_lease_settlement')
                            THEN COALESCE(amount_total, 0.0)
                            ELSE 0.0
                        END) AS material_cost_amount,
                        COUNT(*) FILTER (
                            WHERE fact_type IN ('stock_in', 'stock_in_line', 'scbs_stock_in', 'material_lease_settlement')
                        )::integer AS cnt
                    FROM sc_legacy_material_stock_fact
                    WHERE active IS TRUE AND state <> 'cancel'
                    GROUP BY project_id
                ),
                labor_cost AS (
                    SELECT
                        project_id,
                        SUM(CASE
                            WHEN fact_type IN ('labor_settlement', 'subcontract_settlement')
                            THEN COALESCE(amount_settlement, amount_payable, amount_total, 0.0)
                            WHEN fact_type IN ('labor_contract', 'subcontract_contract')
                            THEN COALESCE(amount_contract, amount_total, 0.0)
                            ELSE 0.0
                        END) AS labor_cost_amount,
                        COUNT(*)::integer AS cnt
                    FROM sc_legacy_labor_subcontract_fact
                    WHERE active IS TRUE AND state <> 'cancel'
                    GROUP BY project_id
                ),
                lease_cost AS (
                    SELECT
                        project_id,
                        SUM(CASE
                            WHEN fact_type IN ('lease_settlement', 'lease_summary', 'equipment_shift', 'lease_contract_line')
                            THEN COALESCE(amount_total, amount_payable, 0.0)
                            WHEN fact_type = 'lease_contract'
                            THEN COALESCE(amount_total, 0.0)
                            ELSE 0.0
                        END) AS lease_cost_amount,
                        COUNT(*)::integer AS cnt
                    FROM sc_legacy_equipment_lease_fact
                    WHERE active IS TRUE AND state <> 'cancel'
                    GROUP BY project_id
                ),
                expense_cost AS (
                    SELECT
                        project_id,
                        SUM(CASE
                            WHEN claim_type = 'expense' THEN COALESCE(approved_amount, amount, 0.0)
                            ELSE 0.0
                        END) AS expense_cost_amount,
                        COUNT(*) FILTER (WHERE claim_type = 'expense')::integer AS cnt
                    FROM sc_expense_claim
                    WHERE active IS TRUE AND state <> 'cancel'
                    GROUP BY project_id
                ),
                salary_cost AS (
                    SELECT
                        project_id,
                        SUM(CASE
                            WHEN fact_type = 'salary_registration' THEN COALESCE(net_salary, gross_amount, 0.0)
                            ELSE 0.0
                        END) AS salary_cost_amount,
                        COUNT(*) FILTER (WHERE fact_type = 'salary_registration')::integer AS cnt
                    FROM sc_hr_payroll_document
                    WHERE active IS TRUE AND state <> 'cancel'
                    GROUP BY project_id
                ),
                project_keys AS (
                    SELECT project_id FROM income_contract
                    UNION SELECT project_id FROM payable_contract
                    UNION SELECT project_id FROM supplier_contract
                    UNION SELECT project_id FROM receipt
                    UNION SELECT project_id FROM invoice
                    UNION SELECT project_id FROM payment
                    UNION SELECT project_id FROM material_cost
                    UNION SELECT project_id FROM labor_cost
                    UNION SELECT project_id FROM lease_cost
                    UNION SELECT project_id FROM expense_cost
                    UNION SELECT project_id FROM salary_cost
                )
                SELECT
                    row_number() OVER (ORDER BY k.project_id NULLS LAST)::integer AS id,
                    CASE
                        WHEN COALESCE(p.name->>'zh_CN', p.name->>'en_US', '') ~ '^[0-9a-fA-F]{{32}}$'
                        THEN CONCAT('历史未归档项目 ', COALESCE(p.name->>'zh_CN', p.name->>'en_US'))
                        ELSE COALESCE(p.name->>'zh_CN', p.name->>'en_US', '未匹配项目')
                    END AS display_name,
                    COALESCE(p.company_id, (SELECT id FROM res_company ORDER BY id LIMIT 1)) AS company_id,
                    k.project_id,
                    CASE
                        WHEN COALESCE(p.name->>'zh_CN', p.name->>'en_US', '') ~ '^[0-9a-fA-F]{{32}}$'
                        THEN CONCAT('历史未归档项目 ', COALESCE(p.name->>'zh_CN', p.name->>'en_US'))
                        ELSE COALESCE(p.name->>'zh_CN', p.name->>'en_US', '未匹配项目')
                    END AS project_name,
                    COALESCE(rc.currency_id, (SELECT currency_id FROM res_company ORDER BY id LIMIT 1)) AS currency_id,
                    COALESCE(ic.income_contract_amount, 0.0) AS income_contract_amount,
                    COALESCE(r.receipt_amount, 0.0) AS receipt_amount,
                    COALESCE(i.output_invoice_amount, 0.0) AS output_invoice_amount,
                    GREATEST(COALESCE(ic.income_contract_amount, 0.0) - COALESCE(r.receipt_amount, 0.0), 0.0)
                        AS receivable_unpaid_amount,
                    COALESCE(pc.payable_contract_amount, 0.0) AS payable_contract_amount,
                    COALESCE(sc.supplier_contract_amount, 0.0) AS supplier_contract_amount,
                    COALESCE(mc.material_cost_amount, 0.0) AS material_cost_amount,
                    COALESCE(lc.labor_cost_amount, 0.0) AS labor_cost_amount,
                    COALESCE(ec.lease_cost_amount, 0.0) AS lease_cost_amount,
                    COALESCE(ex.expense_cost_amount, 0.0) AS expense_cost_amount,
                    COALESCE(sa.salary_cost_amount, 0.0) AS salary_cost_amount,
                    COALESCE(i.input_invoice_amount, 0.0) AS input_invoice_amount,
                    COALESCE(py.paid_amount, 0.0) AS paid_amount,
                    GREATEST(
                        COALESCE(pc.payable_contract_amount, 0.0)
                        + COALESCE(sc.supplier_contract_amount, 0.0)
                        - COALESCE(py.paid_amount, 0.0),
                        0.0
                    ) AS payable_unpaid_amount,
                    (
                        COALESCE(mc.material_cost_amount, 0.0)
                        + COALESCE(lc.labor_cost_amount, 0.0)
                        + COALESCE(ec.lease_cost_amount, 0.0)
                        + COALESCE(ex.expense_cost_amount, 0.0)
                        + COALESCE(sa.salary_cost_amount, 0.0)
                    ) AS total_cost_amount,
                    (
                        COALESCE(r.receipt_amount, 0.0)
                        - COALESCE(mc.material_cost_amount, 0.0)
                        - COALESCE(lc.labor_cost_amount, 0.0)
                        - COALESCE(ec.lease_cost_amount, 0.0)
                        - COALESCE(ex.expense_cost_amount, 0.0)
                        - COALESCE(sa.salary_cost_amount, 0.0)
                    ) AS profit_amount,
                    CASE
                        WHEN COALESCE(r.receipt_amount, 0.0) = 0.0 THEN 0.0
                        ELSE (
                            COALESCE(r.receipt_amount, 0.0)
                            - COALESCE(mc.material_cost_amount, 0.0)
                            - COALESCE(lc.labor_cost_amount, 0.0)
                            - COALESCE(ec.lease_cost_amount, 0.0)
                            - COALESCE(ex.expense_cost_amount, 0.0)
                            - COALESCE(sa.salary_cost_amount, 0.0)
                        ) / COALESCE(r.receipt_amount, 0.0) * 100.0
                    END AS profit_rate,
                    (
                        COALESCE(ic.cnt, 0) + COALESCE(pc.cnt, 0) + COALESCE(sc.cnt, 0)
                        + COALESCE(r.cnt, 0) + COALESCE(i.cnt, 0) + COALESCE(py.cnt, 0)
                    )::integer AS source_line_count,
                    COALESCE(mc.cnt, 0)::integer AS material_line_count,
                    COALESCE(ex.cnt, 0)::integer AS expense_line_count,
                    COALESCE(sa.cnt, 0)::integer AS salary_line_count,
                    CASE
                        WHEN COALESCE(lc.cnt, 0) = 0 AND COALESCE(ec.cnt, 0) = 0 THEN
                            '已承载收入、收款、开票、供应商合同、材料、费用、工资、付款；劳务/设备事实当前为空，综合成本为已承载口径'
                        ELSE
                            '已承载收入、收款、开票、供应商合同、材料、劳务/分包、租赁/机械、费用、工资、付款'
                    END AS coverage_note
                FROM project_keys k
                LEFT JOIN project_project p ON p.id = k.project_id
                LEFT JOIN res_company rc ON rc.id = COALESCE(p.company_id, (SELECT id FROM res_company ORDER BY id LIMIT 1))
                LEFT JOIN income_contract ic ON ic.project_id IS NOT DISTINCT FROM k.project_id
                LEFT JOIN payable_contract pc ON pc.project_id IS NOT DISTINCT FROM k.project_id
                LEFT JOIN supplier_contract sc ON sc.project_id IS NOT DISTINCT FROM k.project_id
                LEFT JOIN receipt r ON r.project_id IS NOT DISTINCT FROM k.project_id
                LEFT JOIN invoice i ON i.project_id IS NOT DISTINCT FROM k.project_id
                LEFT JOIN payment py ON py.project_id IS NOT DISTINCT FROM k.project_id
                LEFT JOIN material_cost mc ON mc.project_id IS NOT DISTINCT FROM k.project_id
                LEFT JOIN labor_cost lc ON lc.project_id IS NOT DISTINCT FROM k.project_id
                LEFT JOIN lease_cost ec ON ec.project_id IS NOT DISTINCT FROM k.project_id
                LEFT JOIN expense_cost ex ON ex.project_id IS NOT DISTINCT FROM k.project_id
                LEFT JOIN salary_cost sa ON sa.project_id IS NOT DISTINCT FROM k.project_id
            )
            """
        )
        self._cr.execute(f"ALTER TABLE {self._table} ADD PRIMARY KEY (id)")
        self._cr.execute(f"CREATE INDEX {self._table}_project_id_idx ON {self._table} (project_id)")
        self._cr.execute(f"CREATE INDEX {self._table}_project_name_idx ON {self._table} (project_name)")
