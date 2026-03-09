# -*- coding: utf-8 -*-
from odoo import fields, models, tools


class ProjectRisk(models.Model):
    """Risk projection model for workbench/home metric reads."""

    _name = "project.risk"
    _description = "项目风险"
    _rec_name = "name"
    _order = "write_date desc, id desc"
    _auto = False

    project_id = fields.Many2one("project.project", string="项目", required=True, readonly=True, index=True)
    name = fields.Char(string="项目名称", readonly=True)
    health_state = fields.Selection(
        [("ok", "正常"), ("warn", "预警"), ("risk", "风险")],
        string="健康状态",
        readonly=True,
    )
    write_date = fields.Datetime(string="更新时间", readonly=True)
    company_id = fields.Many2one("res.company", string="公司", readonly=True, index=True)

    def init(self):
        self._cr.execute("SELECT to_regclass('project_project')")
        has_project = self._cr.fetchone()[0]
        if not has_project:
            return
        self._cr.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name='project_project' AND column_name='health_state'
            """
        )
        if not self._cr.fetchone():
            return
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    p.id AS id,
                    p.id AS project_id,
                    p.name AS name,
                    p.health_state AS health_state,
                    p.write_date AS write_date,
                    p.company_id AS company_id
                FROM project_project p
                WHERE p.health_state IN ('risk', 'warn')
            )
            """
        )
