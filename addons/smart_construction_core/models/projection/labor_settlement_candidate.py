# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError


class ScLaborSettlementCandidate(models.Model):
    _name = "sc.labor.settlement.candidate"
    _description = "劳务结算候选"
    _auto = False
    _rec_name = "display_name"
    _order = "candidate_state, legacy_settlement_amount desc, last_usage_date desc"

    display_name = fields.Char(string="候选事项", readonly=True)
    project_id = fields.Many2one("project.project", string="项目", readonly=True, index=True)
    contractor_id = fields.Many2one("res.partner", string="劳务单位", readonly=True, index=True)
    legacy_fact_type = fields.Char(string="旧单据类型", readonly=True, index=True)
    legacy_settlement_state = fields.Selection(
        [("unsettled", "未结算"), ("unknown", "未识别")],
        string="旧结算状态",
        readonly=True,
        index=True,
    )
    candidate_state = fields.Selection(
        [("ready", "可核对"), ("needs_review", "需复核")],
        string="候选状态",
        readonly=True,
        index=True,
    )
    usage_count = fields.Integer(string="用工记录数", readonly=True)
    first_usage_date = fields.Date(string="最早用工日期", readonly=True)
    last_usage_date = fields.Date(string="最近用工日期", readonly=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)
    legacy_settlement_amount = fields.Monetary(string="旧系统金额", currency_field="currency_id", readonly=True)
    sample_usage_names = fields.Char(string="来源单号", readonly=True)
    review_reason = fields.Char(string="核对原因", readonly=True)

    def _raise_readonly_projection(self):
        raise UserError("劳务结算候选是只读派生结果，不能直接写回用户已确认历史事实。")

    @api.model_create_multi
    def create(self, vals_list):
        self._raise_readonly_projection()

    def write(self, vals):
        self._raise_readonly_projection()

    def unlink(self):
        self._raise_readonly_projection()

    def action_open_usage_lines(self):
        self.ensure_one()
        domain = [
            ("project_id", "=", self.project_id.id),
            ("contractor_id", "=", self.contractor_id.id),
            ("legacy_fact_type", "=", self.legacy_fact_type),
            ("legacy_settlement_state", "=", self.legacy_settlement_state),
        ]
        return {
            "type": "ir.actions.act_window",
            "name": "劳务用工来源",
            "res_model": "sc.labor.usage",
            "view_mode": "tree,form",
            "domain": domain,
            "context": {"create": False, "search_default_group_project": 1},
        }

    def _source_usage_domain(self):
        self.ensure_one()
        return [
            ("project_id", "=", self.project_id.id),
            ("contractor_id", "=", self.contractor_id.id),
            ("legacy_fact_type", "=", self.legacy_fact_type),
            ("legacy_settlement_state", "=", self.legacy_settlement_state),
        ]

    def action_create_draft_labor_settlement(self):
        self.ensure_one()
        if self.candidate_state != "ready":
            raise UserError("只有旧系统明确标记未结算的候选可以生成劳务结算草稿。")

        usage_records = self.env["sc.labor.usage"].search(self._source_usage_domain(), order="usage_date, id")
        used_usage_ids = set(
            self.env["sc.labor.settlement.line"]
            .search(
                [
                    ("source_usage_id", "in", usage_records.ids),
                    ("settlement_id.state", "!=", "cancel"),
                ]
            )
            .mapped("source_usage_id")
            .ids
        )
        usage_records = usage_records.filtered(lambda usage: usage.id not in used_usage_ids)
        if not usage_records:
            raise UserError("该候选的用工来源已经被未取消劳务结算承接。")

        settlement = self.env["sc.labor.settlement"].create(
            {
                "project_id": self.project_id.id,
                "contractor_id": self.contractor_id.id,
                "settlement_date": fields.Date.context_today(self),
                "currency_id": self.currency_id.id,
                "legacy_fact_model": "sc.labor.settlement.candidate",
                "legacy_fact_type": self.legacy_fact_type,
                "note": "由劳务结算候选核对生成草稿；提交前需人工核对来源用工、数量和金额。",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "source_usage_id": usage.id,
                            "labor_team": usage.labor_team,
                            "work_content": usage.work_content,
                            "qty": 1.0,
                            "unit_name": "项",
                            "unit_price": usage.legacy_settlement_amount,
                            "tax_rate": 0.0,
                            "note": usage.name,
                        },
                    )
                    for usage in usage_records
                ],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": "劳务结算草稿",
            "res_model": "sc.labor.settlement",
            "res_id": settlement.id,
            "view_mode": "form",
            "target": "current",
        }

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH source AS (
                    SELECT
                        usage.project_id,
                        usage.contractor_id,
                        usage.legacy_fact_type,
                        usage.legacy_settlement_state,
                        usage.currency_id,
                        usage.usage_date,
                        usage.name,
                        COALESCE(usage.legacy_settlement_amount, 0.0) AS legacy_settlement_amount
                    FROM sc_labor_usage usage
                    WHERE usage.legacy_fact_type IN ('direct_acceptance:方单', 'direct_acceptance:零星用工')
                      AND usage.legacy_settlement_state IN ('unsettled', 'unknown')
                      AND usage.project_id IS NOT NULL
                      AND usage.contractor_id IS NOT NULL
                      AND NOT EXISTS (
                          SELECT 1
                            FROM sc_labor_settlement_line line
                            JOIN sc_labor_settlement settlement ON settlement.id = line.settlement_id
                           WHERE line.source_usage_id = usage.id
                             AND settlement.state != 'cancel'
                      )
                ),
                grouped AS (
                    SELECT
                        project_id,
                        contractor_id,
                        legacy_fact_type,
                        legacy_settlement_state,
                        currency_id,
                        COUNT(*)::integer AS usage_count,
                        MIN(usage_date) AS first_usage_date,
                        MAX(usage_date) AS last_usage_date,
                        SUM(legacy_settlement_amount)::numeric AS legacy_settlement_amount
                    FROM source
                    GROUP BY project_id, contractor_id, legacy_fact_type, legacy_settlement_state, currency_id
                ),
                sample AS (
                    SELECT
                        project_id,
                        contractor_id,
                        legacy_fact_type,
                        legacy_settlement_state,
                        currency_id,
                        STRING_AGG(name, ', ' ORDER BY usage_date DESC, name) AS sample_usage_names
                    FROM (
                        SELECT
                            source.*,
                            ROW_NUMBER() OVER (
                                PARTITION BY project_id, contractor_id, legacy_fact_type, legacy_settlement_state, currency_id
                                ORDER BY usage_date DESC, name
                            ) AS sample_rank
                        FROM source
                    ) ranked
                    WHERE sample_rank <= 5
                    GROUP BY project_id, contractor_id, legacy_fact_type, legacy_settlement_state, currency_id
                )
                SELECT
                    ROW_NUMBER() OVER (
                        ORDER BY grouped.project_id,
                                 grouped.contractor_id,
                                 grouped.legacy_fact_type,
                                 grouped.legacy_settlement_state,
                                 grouped.currency_id
                    )::integer AS id,
                    CASE
                        WHEN grouped.legacy_fact_type = 'direct_acceptance:方单' THEN '方单'
                        WHEN grouped.legacy_fact_type = 'direct_acceptance:零星用工' THEN '零星用工'
                        ELSE grouped.legacy_fact_type
                    END
                    || ' / '
                    || COALESCE(partner.name, '未识别劳务单位')
                    || ' / '
                    || grouped.usage_count::text
                    || '条' AS display_name,
                    grouped.project_id,
                    grouped.contractor_id,
                    grouped.legacy_fact_type,
                    grouped.legacy_settlement_state,
                    CASE
                        WHEN grouped.legacy_settlement_state = 'unsettled' THEN 'ready'
                        ELSE 'needs_review'
                    END AS candidate_state,
                    grouped.usage_count,
                    grouped.first_usage_date,
                    grouped.last_usage_date,
                    grouped.currency_id,
                    grouped.legacy_settlement_amount,
                    sample.sample_usage_names,
                    CASE
                        WHEN grouped.legacy_settlement_state = 'unsettled'
                        THEN '旧系统明确标记未结算，可进入劳务结算办理前核对'
                        ELSE '旧系统结算状态无法标准识别，需先人工复核'
                    END AS review_reason
                FROM grouped
                LEFT JOIN sample
                  ON sample.project_id = grouped.project_id
                 AND sample.contractor_id = grouped.contractor_id
                 AND sample.legacy_fact_type = grouped.legacy_fact_type
                 AND sample.legacy_settlement_state = grouped.legacy_settlement_state
                 AND sample.currency_id = grouped.currency_id
                LEFT JOIN res_partner partner ON partner.id = grouped.contractor_id
            )
            """
        )
