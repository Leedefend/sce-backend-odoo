# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScArApProjectSummary(models.Model):
    _name = "sc.ar.ap.project.summary"
    _description = "应收应付报表（项目）"
    _auto = False
    _rec_name = "display_name"
    _order = "project_id, partner_name"

    display_name = fields.Char(string="汇总项", readonly=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    project_name = fields.Char(string="项目名称", readonly=True)
    partner_id = fields.Many2one("res.partner", string="往来单位记录", readonly=True, index=True)
    partner_key = fields.Char(string="往来单位键", readonly=True, index=True)
    partner_name = fields.Char(string="往来单位", readonly=True, index=True)
    income_contract_amount = fields.Float(string="收入合同金额", readonly=True)
    output_invoice_amount = fields.Float(string="已开票", readonly=True)
    receipt_amount = fields.Float(string="已收款", readonly=True)
    receivable_unpaid_amount = fields.Float(string="未收款", readonly=True)
    invoiced_unreceived_amount = fields.Float(string="已开票未收款", readonly=True)
    received_uninvoiced_amount = fields.Float(string="已收款未开票", readonly=True)
    payable_contract_amount = fields.Float(string="应付合同金额", readonly=True)
    payable_pricing_method_text = fields.Char(string="计价方式", readonly=True)
    input_invoice_amount = fields.Float(string="已收供应商发票", readonly=True)
    paid_amount = fields.Float(string="已付款", readonly=True)
    payable_unpaid_amount = fields.Float(string="未付款", readonly=True)
    paid_uninvoiced_amount = fields.Float(string="付款超票", readonly=True)
    output_tax_amount = fields.Float(string="销项税额", readonly=True)
    input_tax_amount = fields.Float(string="进项税额", readonly=True)
    deduction_tax_amount = fields.Float(string="抵扣税额", readonly=True)
    tax_deduction_rate = fields.Float(string="抵扣比例", readonly=True)
    output_surcharge_amount = fields.Float(string="销项附加税", readonly=True)
    input_surcharge_amount = fields.Float(string="进项附加税", readonly=True)
    deduction_surcharge_amount = fields.Float(string="抵扣附加税", readonly=True)
    self_funding_income_amount = fields.Float(string="自筹收入金额", readonly=True)
    self_funding_refund_amount = fields.Float(string="自筹退回金额", readonly=True)
    self_funding_unreturned_amount = fields.Float(string="自筹未退金额", readonly=True)
    actual_available_balance = fields.Float(string="实际可用余额", readonly=True)

    def init(self):
        self._cr.execute(
            """
            SELECT
                to_regclass('construction_contract'),
                to_regclass('sc_receipt_income'),
                to_regclass('sc_invoice_registration'),
                to_regclass('sc_treasury_ledger'),
                to_regclass('sc_legacy_invoice_surcharge_fact'),
                to_regclass('sc_legacy_tax_deduction_fact'),
                to_regclass('sc_legacy_self_funding_fact'),
                to_regclass('sc_legacy_supplier_contract_pricing_fact'),
                to_regclass('sc_legacy_project_fund_balance_fact')
            """
        )
        if not all(self._cr.fetchone()):
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH income_contract AS (
                    SELECT
                        c.project_id,
                        c.partner_id,
                        'partner:' || c.partner_id::varchar AS partner_key,
                        rp.name AS partner_name,
                        SUM(COALESCE(c.amount_total, 0.0)) AS income_contract_amount
                    FROM construction_contract c
                    JOIN res_partner rp ON rp.id = c.partner_id
                    WHERE c.type = 'out'
                    GROUP BY c.project_id, c.partner_id, rp.name
                ),
                payable_contract AS (
                    SELECT
                        c.project_id,
                        c.partner_id,
                        'partner:' || c.partner_id::varchar AS partner_key,
                        rp.name AS partner_name,
                        SUM(COALESCE(c.amount_total, 0.0)) AS payable_contract_amount
                    FROM construction_contract c
                    JOIN res_partner rp ON rp.id = c.partner_id
                    WHERE c.type = 'in'
                    GROUP BY c.project_id, c.partner_id, rp.name
                ),
                receipt AS (
                    SELECT
                        r.project_id,
                        r.partner_id,
                        'partner:' || r.partner_id::varchar AS partner_key,
                        rp.name AS partner_name,
                        SUM(COALESCE(r.amount, 0.0)) AS receipt_amount
                    FROM sc_receipt_income r
                    JOIN res_partner rp ON rp.id = r.partner_id
                    WHERE r.active IS TRUE
                      AND r.partner_id IS NOT NULL
                    GROUP BY r.project_id, r.partner_id, rp.name
                ),
                paid_out AS (
                    SELECT
                        l.project_id,
                        l.partner_id,
                        'partner:' || l.partner_id::varchar AS partner_key,
                        rp.name AS partner_name,
                        SUM(COALESCE(l.amount, 0.0)) AS paid_amount
                    FROM sc_treasury_ledger l
                    JOIN res_partner rp ON rp.id = l.partner_id
                    WHERE l.direction = 'out'
                      AND l.state = 'posted'
                    GROUP BY l.project_id, l.partner_id, rp.name
                ),
                partner_name_map AS (
                    SELECT
                        lower(trim(name)) AS partner_name_key,
                        MIN(id) AS partner_id,
                        MIN(name) AS partner_name
                    FROM res_partner
                    WHERE name IS NOT NULL
                      AND trim(name) != ''
                    GROUP BY lower(trim(name))
                ),
                invoice_norm AS (
                    SELECT
                        i.project_id,
                        COALESCE(i.partner_id, pnm.partner_id) AS partner_id,
                        CASE
                            WHEN COALESCE(i.partner_id, pnm.partner_id) IS NOT NULL
                                THEN 'partner:' || COALESCE(i.partner_id, pnm.partner_id)::varchar
                            ELSE 'name:' || lower(trim(COALESCE(NULLIF(i.legacy_partner_name, ''), '未填往来单位')))
                        END AS partner_key,
                        COALESCE(rp.name, pnm.partner_name, NULLIF(i.legacy_partner_name, ''), '未填往来单位')
                            AS partner_name,
                        i.direction,
                        COALESCE(i.amount_total, 0.0) AS amount_total,
                        COALESCE(i.tax_amount, 0.0) AS tax_amount
                    FROM sc_invoice_registration i
                    LEFT JOIN res_partner rp ON rp.id = i.partner_id
                    LEFT JOIN partner_name_map pnm
                        ON pnm.partner_name_key = lower(trim(i.legacy_partner_name))
                    WHERE i.active IS TRUE
                      AND i.direction IN ('input', 'output')
                ),
                output_invoice AS (
                    SELECT
                        project_id,
                        CASE WHEN partner_id IS NULL THEN NULL ELSE partner_id END AS partner_id,
                        partner_key,
                        partner_name,
                        SUM(amount_total) AS output_invoice_amount,
                        SUM(tax_amount) AS output_tax_amount
                    FROM invoice_norm
                    WHERE direction = 'output'
                    GROUP BY project_id, partner_id, partner_key, partner_name
                ),
                input_invoice AS (
                    SELECT
                        project_id,
                        CASE WHEN partner_id IS NULL THEN NULL ELSE partner_id END AS partner_id,
                        partner_key,
                        partner_name,
                        SUM(amount_total) AS input_invoice_amount,
                        SUM(tax_amount) AS input_tax_amount
                    FROM invoice_norm
                    WHERE direction = 'input'
                    GROUP BY project_id, partner_id, partner_key, partner_name
                ),
                tax_deduction_norm AS (
                    SELECT
                        d.project_id,
                        COALESCE(d.partner_id, pnm.partner_id) AS partner_id,
                        CASE
                            WHEN COALESCE(d.partner_id, pnm.partner_id) IS NOT NULL
                                THEN 'partner:' || COALESCE(d.partner_id, pnm.partner_id)::varchar
                            ELSE 'name:' || lower(trim(COALESCE(NULLIF(d.partner_name, ''), '未填往来单位')))
                        END AS partner_key,
                        COALESCE(rp.name, pnm.partner_name, NULLIF(d.partner_name, ''), '未填往来单位')
                            AS partner_name,
                        COALESCE(d.deduction_tax_amount, 0.0) AS deduction_tax_amount,
                        COALESCE(d.deduction_surcharge_amount, 0.0) AS deduction_surcharge_amount
                    FROM sc_legacy_tax_deduction_fact d
                    LEFT JOIN res_partner rp ON rp.id = d.partner_id
                    LEFT JOIN partner_name_map pnm
                        ON pnm.partner_name_key = lower(trim(d.partner_name))
                    WHERE d.active IS TRUE
                      AND COALESCE(d.deleted_flag, '0') IN ('0', '')
                      AND COALESCE(d.document_state, '0') = '2'
                ),
                tax_deduction AS (
                    SELECT
                        project_id,
                        partner_id,
                        partner_key,
                        partner_name,
                        SUM(deduction_tax_amount) AS deduction_tax_amount,
                        SUM(deduction_surcharge_amount) AS deduction_surcharge_amount
                    FROM tax_deduction_norm
                    GROUP BY project_id, partner_id, partner_key, partner_name
                ),
                invoice_surcharge_norm AS (
                    SELECT
                        s.project_id,
                        COALESCE(s.partner_id, pnm.partner_id) AS partner_id,
                        CASE
                            WHEN COALESCE(s.partner_id, pnm.partner_id) IS NOT NULL
                                THEN 'partner:' || COALESCE(s.partner_id, pnm.partner_id)::varchar
                            ELSE 'name:' || lower(trim(COALESCE(NULLIF(s.partner_name, ''), '未填往来单位')))
                        END AS partner_key,
                        COALESCE(rp.name, pnm.partner_name, NULLIF(s.partner_name, ''), '未填往来单位')
                            AS partner_name,
                        s.direction,
                        COALESCE(s.surcharge_amount, 0.0) AS surcharge_amount
                    FROM sc_legacy_invoice_surcharge_fact s
                    LEFT JOIN res_partner rp ON rp.id = s.partner_id
                    LEFT JOIN partner_name_map pnm
                        ON pnm.partner_name_key = lower(trim(s.partner_name))
                    WHERE s.active IS TRUE
                      AND COALESCE(s.deleted_flag, '0') IN ('0', '')
                      AND COALESCE(s.document_state, '0') = '2'
                ),
                invoice_surcharge AS (
                    SELECT
                        project_id,
                        partner_id,
                        partner_key,
                        partner_name,
                        SUM(CASE WHEN direction = 'output' THEN surcharge_amount ELSE 0.0 END)
                            AS output_surcharge_amount,
                        SUM(CASE WHEN direction = 'input' THEN surcharge_amount ELSE 0.0 END)
                            AS input_surcharge_amount
                    FROM invoice_surcharge_norm
                    GROUP BY project_id, partner_id, partner_key, partner_name
                ),
                supplier_contract_pricing_norm AS (
                    SELECT
                        f.project_id,
                        COALESCE(f.partner_id, pnm.partner_id) AS partner_id,
                        CASE
                            WHEN COALESCE(f.partner_id, pnm.partner_id) IS NOT NULL
                                THEN 'partner:' || COALESCE(f.partner_id, pnm.partner_id)::varchar
                            ELSE 'name:' || lower(trim(COALESCE(NULLIF(f.partner_name, ''), '未填往来单位')))
                        END AS partner_key,
                        COALESCE(rp.name, pnm.partner_name, NULLIF(f.partner_name, ''), '未填往来单位')
                            AS partner_name,
                        NULLIF(trim(f.pricing_method_text), '') AS pricing_method_text
                    FROM sc_legacy_supplier_contract_pricing_fact f
                    LEFT JOIN res_partner rp ON rp.id = f.partner_id
                    LEFT JOIN partner_name_map pnm
                        ON pnm.partner_name_key = lower(trim(f.partner_name))
                    WHERE f.active IS TRUE
                      AND COALESCE(f.deleted_flag, '0') IN ('0', '')
                      AND COALESCE(f.document_state, '0') = '2'
                      AND NULLIF(trim(f.pricing_method_text), '') IS NOT NULL
                ),
                supplier_contract_pricing AS (
                    SELECT
                        project_id,
                        partner_id,
                        partner_key,
                        partner_name,
                        string_agg(DISTINCT pricing_method_text, ', ' ORDER BY pricing_method_text)
                            AS payable_pricing_method_text
                    FROM supplier_contract_pricing_norm
                    GROUP BY project_id, partner_id, partner_key, partner_name
                ),
                self_funding_norm AS (
                    SELECT
                        s.project_id,
                        COALESCE(s.partner_id, pnm.partner_id) AS partner_id,
                        CASE
                            WHEN COALESCE(s.partner_id, pnm.partner_id) IS NOT NULL
                                THEN 'partner:' || COALESCE(s.partner_id, pnm.partner_id)::varchar
                            ELSE 'name:' || lower(trim(COALESCE(NULLIF(s.partner_name, ''), '未填往来单位')))
                        END AS partner_key,
                        COALESCE(rp.name, pnm.partner_name, NULLIF(s.partner_name, ''), '未填往来单位')
                            AS partner_name,
                        COALESCE(s.self_funding_amount, 0.0) AS self_funding_income_amount,
                        COALESCE(s.refund_amount, 0.0) AS self_funding_refund_amount
                    FROM sc_legacy_self_funding_fact s
                    LEFT JOIN res_partner rp ON rp.id = s.partner_id
                    LEFT JOIN partner_name_map pnm
                        ON pnm.partner_name_key = lower(trim(s.partner_name))
                    WHERE s.active IS TRUE
                      AND COALESCE(s.deleted_flag, '0') IN ('0', '')
                ),
                self_funding AS (
                    SELECT
                        project_id,
                        partner_id,
                        partner_key,
                        partner_name,
                        SUM(self_funding_income_amount) AS self_funding_income_amount,
                        SUM(self_funding_refund_amount) AS self_funding_refund_amount
                    FROM self_funding_norm
                    GROUP BY project_id, partner_id, partner_key, partner_name
                ),
                project_fund_balance AS (
                    SELECT
                        project_id,
                        MAX(COALESCE(actual_available_balance, 0.0)) AS actual_available_balance
                    FROM sc_legacy_project_fund_balance_fact
                    WHERE active IS TRUE
                      AND project_id IS NOT NULL
                    GROUP BY project_id
                ),
                business_keys AS (
                    SELECT project_id, partner_id, partner_key, partner_name FROM income_contract
                    UNION
                    SELECT project_id, partner_id, partner_key, partner_name FROM payable_contract
                    UNION
                    SELECT project_id, partner_id, partner_key, partner_name FROM receipt
                    UNION
                    SELECT project_id, partner_id, partner_key, partner_name FROM paid_out
                    UNION
                    SELECT project_id, partner_id, partner_key, partner_name FROM output_invoice
                    UNION
                    SELECT project_id, partner_id, partner_key, partner_name FROM input_invoice
                    UNION
                    SELECT project_id, partner_id, partner_key, partner_name FROM tax_deduction
                    UNION
                    SELECT project_id, partner_id, partner_key, partner_name FROM invoice_surcharge
                    UNION
                    SELECT project_id, partner_id, partner_key, partner_name FROM supplier_contract_pricing
                    UNION
                    SELECT project_id, partner_id, partner_key, partner_name FROM self_funding
                ),
                keys AS (
                    SELECT project_id, partner_id, partner_key, partner_name FROM business_keys
                    UNION
                    SELECT
                        pfb.project_id,
                        NULL::integer AS partner_id,
                        'project_balance:' || pfb.project_id::varchar AS partner_key,
                        '项目级余额' AS partner_name
                    FROM project_fund_balance pfb
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM business_keys bk
                        WHERE bk.project_id = pfb.project_id
                    )
                )
                SELECT
                    row_number() OVER (ORDER BY k.project_id, k.partner_name, k.partner_key) AS id,
                    COALESCE(p.name->>'zh_CN', p.name->>'en_US', '未匹配项目') || ' / ' ||
                        COALESCE(k.partner_name, '未填往来单位') AS display_name,
                    k.project_id,
                    COALESCE(p.name->>'zh_CN', p.name->>'en_US') AS project_name,
                    k.partner_id,
                    k.partner_key,
                    k.partner_name,
                    COALESCE(ic.income_contract_amount, 0.0) AS income_contract_amount,
                    COALESCE(oi.output_invoice_amount, 0.0) AS output_invoice_amount,
                    COALESCE(r.receipt_amount, 0.0) AS receipt_amount,
                    COALESCE(ic.income_contract_amount, 0.0) - COALESCE(r.receipt_amount, 0.0)
                        AS receivable_unpaid_amount,
                    GREATEST(COALESCE(oi.output_invoice_amount, 0.0) - COALESCE(r.receipt_amount, 0.0), 0.0)
                        AS invoiced_unreceived_amount,
                    GREATEST(COALESCE(r.receipt_amount, 0.0) - COALESCE(oi.output_invoice_amount, 0.0), 0.0)
                        AS received_uninvoiced_amount,
                    COALESCE(pc.payable_contract_amount, 0.0) AS payable_contract_amount,
                    COALESCE(scp.payable_pricing_method_text, '') AS payable_pricing_method_text,
                    COALESCE(ii.input_invoice_amount, 0.0) AS input_invoice_amount,
                    COALESCE(po.paid_amount, 0.0) AS paid_amount,
                    GREATEST(COALESCE(ii.input_invoice_amount, 0.0) - COALESCE(po.paid_amount, 0.0), 0.0)
                        AS payable_unpaid_amount,
                    GREATEST(COALESCE(po.paid_amount, 0.0) - COALESCE(ii.input_invoice_amount, 0.0), 0.0)
                        AS paid_uninvoiced_amount,
                    COALESCE(oi.output_tax_amount, 0.0) AS output_tax_amount,
                    COALESCE(ii.input_tax_amount, 0.0) AS input_tax_amount,
                    COALESCE(td.deduction_tax_amount, 0.0) AS deduction_tax_amount,
                    CASE
                        WHEN COALESCE(oi.output_tax_amount, 0.0) > 0.0
                            THEN COALESCE(td.deduction_tax_amount, 0.0) / COALESCE(oi.output_tax_amount, 0.0)
                        ELSE 0.0
                    END AS tax_deduction_rate,
                    COALESCE(ins.output_surcharge_amount, 0.0) AS output_surcharge_amount,
                    COALESCE(ins.input_surcharge_amount, 0.0) AS input_surcharge_amount,
                    COALESCE(td.deduction_surcharge_amount, 0.0) AS deduction_surcharge_amount,
                    COALESCE(sf.self_funding_income_amount, 0.0) AS self_funding_income_amount,
                    COALESCE(sf.self_funding_refund_amount, 0.0) AS self_funding_refund_amount,
                    COALESCE(sf.self_funding_income_amount, 0.0) - COALESCE(sf.self_funding_refund_amount, 0.0)
                        AS self_funding_unreturned_amount,
                    COALESCE(pfb.actual_available_balance, 0.0) AS actual_available_balance
                FROM keys k
                LEFT JOIN project_project p ON p.id = k.project_id
                LEFT JOIN income_contract ic
                    ON ic.project_id IS NOT DISTINCT FROM k.project_id AND ic.partner_key = k.partner_key
                LEFT JOIN payable_contract pc
                    ON pc.project_id IS NOT DISTINCT FROM k.project_id AND pc.partner_key = k.partner_key
                LEFT JOIN receipt r
                    ON r.project_id IS NOT DISTINCT FROM k.project_id AND r.partner_key = k.partner_key
                LEFT JOIN paid_out po
                    ON po.project_id IS NOT DISTINCT FROM k.project_id AND po.partner_key = k.partner_key
                LEFT JOIN output_invoice oi
                    ON oi.project_id IS NOT DISTINCT FROM k.project_id AND oi.partner_key = k.partner_key
                LEFT JOIN input_invoice ii
                    ON ii.project_id IS NOT DISTINCT FROM k.project_id AND ii.partner_key = k.partner_key
                LEFT JOIN tax_deduction td
                    ON td.project_id IS NOT DISTINCT FROM k.project_id AND td.partner_key = k.partner_key
                LEFT JOIN invoice_surcharge ins
                    ON ins.project_id IS NOT DISTINCT FROM k.project_id AND ins.partner_key = k.partner_key
                LEFT JOIN supplier_contract_pricing scp
                    ON scp.project_id IS NOT DISTINCT FROM k.project_id AND scp.partner_key = k.partner_key
                LEFT JOIN self_funding sf
                    ON sf.project_id IS NOT DISTINCT FROM k.project_id AND sf.partner_key = k.partner_key
                LEFT JOIN project_fund_balance pfb
                    ON pfb.project_id = k.project_id
            )
            """
        )
