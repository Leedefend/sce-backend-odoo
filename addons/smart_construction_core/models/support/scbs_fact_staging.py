# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ScLegacyScbsFactStaging(models.Model):
    _name = "sc.legacy.scbs.fact.staging"
    _description = "SCBS旧库事实暂存"
    _order = "document_date desc, source_table, legacy_record_id"
    _rec_name = "display_name"

    display_name = fields.Char(string="显示名称", compute="_compute_display_name", store=True)
    source_domain = fields.Char(string="来源域", default="SCBS", required=True, index=True)
    source_table = fields.Char(string="来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="来源记录ID", required=True, index=True)
    legacy_pid = fields.Char(string="来源PID", index=True)
    fact_family = fields.Selection(
        [
            ("payment", "付款"),
            ("supplier_contract", "供应商合同"),
            ("stock_in", "入库"),
            ("fund_daily", "资金日报"),
        ],
        string="事实族",
        required=True,
        index=True,
    )
    document_no = fields.Char(string="单号", index=True)
    document_date = fields.Date(string="单据日期", index=True)
    document_state = fields.Char(string="旧库状态", index=True)
    deleted_flag = fields.Char(string="旧库删除标识", index=True)
    amount_total = fields.Float(string="金额/余额信号")

    legacy_xmid = fields.Char(string="旧业务主体ID", index=True)
    legacy_xmmc = fields.Char(string="旧业务主体名称", index=True)
    business_entity_map_id = fields.Many2one(
        "sc.legacy.business.entity.map",
        string="业务主体映射",
        index=True,
        ondelete="set null",
    )
    business_entity_id = fields.Many2one(
        "sc.business.entity",
        string="业务核算主体",
        related="business_entity_map_id.business_entity_id",
        store=True,
        readonly=True,
        index=True,
    )
    business_entity_mapping_state = fields.Selection(
        related="business_entity_map_id.mapping_state",
        string="业务主体映射状态",
        store=True,
        readonly=True,
        index=True,
    )

    legacy_gcmc = fields.Char(string="旧工程名称", index=True)
    project_map_id = fields.Many2one("sc.legacy.project.map", string="项目映射", index=True, ondelete="set null")
    project_id = fields.Many2one(
        "project.project",
        string="目标项目",
        related="project_map_id.project_id",
        store=True,
        readonly=True,
        index=True,
    )
    project_mapping_state = fields.Selection(
        related="project_map_id.mapping_state",
        string="项目映射状态",
        store=True,
        readonly=True,
        index=True,
    )

    legacy_partner_id = fields.Char(string="旧往来单位ID", index=True)
    legacy_partner_name = fields.Char(string="旧往来单位", index=True)
    legacy_partner_tax_code = fields.Char(string="旧税号/信用代码", index=True)
    partner_map_id = fields.Many2one("sc.legacy.partner.map", string="往来单位映射", index=True, ondelete="set null")
    partner_id = fields.Many2one(
        "res.partner",
        string="目标往来单位",
        related="partner_map_id.partner_id",
        store=True,
        readonly=True,
        index=True,
    )
    partner_mapping_state = fields.Selection(
        related="partner_map_id.mapping_state",
        string="往来单位映射状态",
        store=True,
        readonly=True,
        index=True,
    )

    mapping_gate_state = fields.Selection(
        [
            ("projection_ready", "可正式投影"),
            ("staging_ready", "仅可暂存"),
            ("blocked", "缺映射"),
            ("conflict", "映射冲突"),
        ],
        string="映射闸口",
        compute="_compute_mapping_gate_state",
        store=True,
        index=True,
    )
    note = fields.Text(string="备注")
    import_batch = fields.Char(string="导入批次", default="scbs_fact_staging_v1", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "fact_stage_src_rec_uniq",
            "unique(source_table, legacy_record_id)",
            "同一旧库来源表的记录只能暂存一次。",
        ),
    ]

    @api.depends("source_table", "legacy_record_id", "document_no")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s/%s" % (rec.source_table or "", rec.document_no or rec.legacy_record_id or "")

    @api.depends(
        "legacy_xmid",
        "business_entity_map_id",
        "business_entity_mapping_state",
        "legacy_gcmc",
        "project_map_id",
        "project_mapping_state",
        "legacy_partner_name",
        "partner_map_id",
        "partner_mapping_state",
    )
    def _compute_mapping_gate_state(self):
        for rec in self:
            states = []
            missing_required = False
            for legacy_value, map_record, mapping_state in [
                (rec.legacy_xmid, rec.business_entity_map_id, rec.business_entity_mapping_state),
                (rec.legacy_gcmc, rec.project_map_id, rec.project_mapping_state),
                (rec.legacy_partner_name, rec.partner_map_id, rec.partner_mapping_state),
            ]:
                if not legacy_value:
                    continue
                if not map_record:
                    missing_required = True
                    continue
                states.append(mapping_state)
            if "conflict" in states:
                rec.mapping_gate_state = "conflict"
            elif missing_required:
                rec.mapping_gate_state = "blocked"
            elif states and all(state == "confirmed" for state in states):
                rec.mapping_gate_state = "projection_ready"
            else:
                rec.mapping_gate_state = "staging_ready"
