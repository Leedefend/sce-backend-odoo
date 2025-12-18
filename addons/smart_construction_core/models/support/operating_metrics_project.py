# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ScOperatingMetricsProject(models.Model):
    """
    经营指标（项目维度）SQL 视图：
    - 只读聚合视图，不在查询时创建数据；
    - 指标口径依赖结算单（store=True）聚合，风险数在视图内近似统计。
    """

    _name = "sc.operating.metrics.project"
    _description = "经营指标（项目）"
    _rec_name = "project_id"
    _order = "project_id desc"
    _auto = False

    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", readonly=True)

    settlement_amount_total = fields.Monetary(string="结算总额", currency_field="currency_id", readonly=True)
    settlement_amount_paid = fields.Monetary(string="已付金额", currency_field="currency_id", readonly=True)
    settlement_amount_payable = fields.Monetary(string="可付余额", currency_field="currency_id", readonly=True)

    overpay_risk_count = fields.Integer(string="超付风险单数", readonly=True)
    three_way_missing_count = fields.Integer(string="三单缺失项", readonly=True)

    def init(self):
        # 依赖的表若尚未创建（新装阶段），跳过视图创建，等待下次加载再建
        self._cr.execute(
            "SELECT to_regclass('sc_settlement_order'), to_regclass('payment_request')"
        )
        has_settlement, has_payment = self._cr.fetchone()
        if not (has_settlement and has_payment):
            return
        # 强制清理残留表/视图，再重建只读视图
        tools.drop_view_if_exists(self._cr, self._table)
        # 若曾误生成表，清理之
        try:
            self._cr.execute(f"DROP TABLE IF EXISTS {self._table} CASCADE")
        except Exception:
            self._cr.rollback()
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH settlement_agg AS (
                    SELECT
                        project_id,
                        COALESCE(SUM(amount_total), 0.0)   AS settlement_amount_total,
                        COALESCE(SUM(amount_paid), 0.0)    AS settlement_amount_paid,
                        COALESCE(SUM(amount_payable), 0.0) AS settlement_amount_payable
                    FROM sc_settlement_order
                    WHERE state = 'approve'
                    GROUP BY project_id
                ),
                overpay_risk AS (
                    -- 近似口径：付款申请金额 > 结算可付余额 视为超付风险（与 UI 标记一致）
                    SELECT
                        pr.project_id,
                        COUNT(*) AS overpay_risk_count
                    FROM payment_request pr
                    JOIN sc_settlement_order s ON s.id = pr.settlement_id
                    WHERE pr.type = 'pay'
                      AND COALESCE(s.amount_payable, 0.0) < COALESCE(pr.amount, 0.0)
                    GROUP BY pr.project_id
                )
                SELECT
                    ROW_NUMBER() OVER() AS id,
                    p.id AS project_id,
                    p.company_id AS company_id,
                    rc.currency_id AS currency_id,

                    COALESCE(sa.settlement_amount_total, 0.0)   AS settlement_amount_total,
                    COALESCE(sa.settlement_amount_paid, 0.0)    AS settlement_amount_paid,
                    COALESCE(sa.settlement_amount_payable, 0.0) AS settlement_amount_payable,

                    COALESCE(rk.overpay_risk_count, 0) AS overpay_risk_count,
                    0::integer AS three_way_missing_count
                FROM project_project p
                LEFT JOIN res_company rc ON rc.id = p.company_id
                LEFT JOIN settlement_agg sa ON sa.project_id = p.id
                LEFT JOIN overpay_risk rk ON rk.project_id = p.id
            )
            """
        )
