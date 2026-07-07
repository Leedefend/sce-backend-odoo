# -*- coding: utf-8 -*-
import json
import re

from odoo import api, fields, models
from odoo.osv import expression


LEGACY_VISIBLE_FIELD_MAP = {
    '施工合同': ['DJZTText', 'DJBH', 'FBF', 'CBF', 'f_XMMC', 'HTBT', 'GCYSZJ', 'LJKPJE', 'LJSKJE', 'KPWSK', 'WSK', 'WSKBL', 'HTBH', 'f_HTDLRQ', 'f_GCDZ', 'f_GCNR', 'f_THGQTS', 'LRR', 'f_LRSJ', 'f_FJ'],
    '分包合同': ['DJZTText', 'DJBH', 'QDSJ', 'BT', 'FBDW', 'FBNR', 'ZSL', 'JE', 'HTBH', 'YKPJE', 'YFKJE', 'WFKJE', 'WKPJE', 'XMMC', 'BZ1', 'f_FJ', 'LRR', 'LRSJ', 'TSXM'],
    '租赁合同': ['DJZTText', 'DJBH', 'HTBH', 'XMMC', 'HTBT', 'FBDW', 'FBNR', 'ZSL', 'YKPJE', 'YFKJE', 'WFKJE', 'WKPJE', 'ZJE', 'QDSJ', 'JBRJDH', 'SLV', 'ZZSLX', 'BZ1', 'f_FJ', 'LRR', 'LRSJ'],
    '供货合同': ['DJZTText', 'f_HTBH', 'BT', 'f_GYSName', 'TSXMMC', 'ZJE', 'YKPJE', 'YFKJE', 'WFKJE', 'WKPJE', 'ProjectName', 'f_LRRQ', 'D_SCBSJS_SL1', 'f_LRR', 'f_FJ'],
    '劳务合同': ['DJZTText', 'DJBH', 'f_GCMC', 'f_QDRQ', 'BT', 'f_BZZ', 'SGDFZR', 'ZHSJE', 'JDJSBL', 'YKPJE', 'YFKJE', 'WFKJE', 'WKPJE', 'JJFSTEXT', 'SGBWMC', 'f_HTBH', 'f_HTWB', 'f_LRR', 'f_HTNR', 'TSXMMC'],
    '机械合同（合同）': ['DJZTText', 'XMMC', 'FBDW', 'HTBH', 'FBNR', 'CBFS', 'HTGQ', 'HTYHS', 'JE', 'XMJL', 'QDSJ', 'FHHTSJ', 'BZ', 'JBRJDH', 'XGRQ', 'SCR', 'SCRQ', 'DJBH', 'XGBZ', 'YHZH', 'KHH', 'KHR', 'ZSL', 'ZJE', 'HTLX', 'GLYHTBH', 'SGBWMC', 'HTBT', 'QYR', 'JBBM', 'WFDW', 'SKDW', 'BiZ', 'HLV', 'ZJE_NO', 'SE', 'SLV', 'CBFX', 'ZMBTEXT', 'ZZSLX', 'BZ1', 'JJFSTEXT', 'ZR_TWJS', 'HZ_TWJS', 'XMJLMC', 'SFJTYY', 'BT', 'JSFS', 'TSXM', 'XMZJYE', 'f_FJ', 'LRR', 'LRSJ'],
    '材料计划': ['DJZTText', 'DJBH', 'DJRQ', 'BZSJ', 'f_CLMC$T_JH_XMZJH', 'f_GGXH$T_JH_XMZJH', 'f_DW$T_JH_XMZJH', 'f_YSCBSL$T_JH_XMZJH', 'D_LYXM_CLBM$T_JH_XMZJH', 'f_BZ$T_JH_XMZJH', 'f_FJ', 'XMMC', 'LRR', 'LRSJ'],
    '报价单': ['DJZTText', 'DJBH', 'XJDW', 'XJSJ', 'HWMC$CGXBJ_CGXJD_CB', 'PPXH$CGXBJ_CGXJD_CB', 'SL$CGXBJ_CGXJD_CB', 'HSDJ$CGXBJ_CGXJD_CB', 'HS_ZJE$CGXBJ_CGXJD_CB', 'ZSL', 'ZJE', 'BZ', 'LXR', 'LXDH', 'f_FJ', 'D_LYXM_SFZB', 'XMMC', 'LRR', 'LRSJ'],
    '入库': ['DJZTText', 'RKDH', 'DJRQ', 'SupplierName', 'CLMC$T_RK_RKDCB', 'GGXH$T_RK_RKDCB', 'SL$T_RK_RKDCB', 'DJ$T_RK_RKDCB', 'SLV', 'HJ$T_RK_RKDCB', 'RK_ZSL', 'CCCC_FKZT', 'CCCC_FKJE', 'CCCC_WFKJE', 'CCCC_FKZT', 'CCCC_JSJE', 'f_ProjectName', 'BZ', 'f_FJ', 'LRR', 'LRRQ', 'CGR'],
    '材料结算单': ['DJZTText', 'XMMC', 'DJBH', 'BT', 'GYDW', 'JSRQ', 'ZJE', 'CCCC_FKZT', 'YFKJE', 'CCCC_WFKJE', 'CCCC_SQZT', 'CCCC_SQJE', 'CCCC_WSQJE', 'JSSM', 'f_FJ', 'LRR', 'LRSJ'],
    '方单': ['DJZTText', 'DJBH', 'f_GCMC', 'DJRQ', 'BT', 'f_LWDW', 'SGBWMC', '__LABOR_USAGE_SETTLEMENT_STATUS__', 'ZJE', 'f_BZ', 'f_FDWB', 'TXR', 'f_LRSJ'],
    '零星用工': ['DJZTText', 'DJBH', 'XMMC', 'DJRQ', 'SGDWMC', 'SGNR$SGGL_LWGL_LXYG_CB', 'GRHJ$SGGL_LWGL_LXYG_CB', 'DJ$SGGL_LWGL_LXYG_CB', 'JE$SGGL_LWGL_LXYG_CB', 'BZ', 'FJ', 'CCCC_JSZT', 'BZ$SGGL_LWGL_LXYG_CB', 'LRR', 'LRSJ'],
    '劳务结算': ['DJZTText', 'DJBH', 'XMMC', 'JSRQ', 'BT', 'GYDW', 'ZJE', 'CCCC_FKZT', 'CCCC_FKJE', 'CCCC_WFKJE', 'CCCC_SQZT', 'CCCC_SQJE', 'CCCC_WSQJE', 'JSSM', 'f_FJ', 'LRR', 'LRSJ', 'HTBH'],
    '分包方单': ['DJZTText', 'DJBH', 'XMMC', 'BT', 'FBS', 'FBNR', 'FBNR$SGGL_FBGL_FBFD_CB', 'BYWCL$SGGL_FBGL_FBFD_CB', 'DJ$SGGL_FBGL_FBFD_CB', 'BYGZJE$SGGL_FBGL_FBFD_CB', 'JEHJ', 'BZ', 'f_FJ', 'LRR', 'LRSJ'],
    '分包结算单': ['DJZTText', 'XMMC', 'DJBH', 'BT', 'GYDW', 'ZJE', 'CCCC_FKZT', 'CCCC_FKJE', 'CCCC_WFKJE', 'CCCC_SQZT', 'CCCC_SQJE', 'CCCC_WSQJE', 'HTBH', 'QSJSRQ', 'ZZJSRQ', 'JSRQ', 'JSSM', 'f_FJ', 'LRR', 'LRSJ'],
    '机械台班记录': ['DJZTText', 'XMMC', 'DJBH', 'DJRQ', 'ZLDW', 'D_LYXM_CYM', 'JXMC$T_ZL_MachineShift_CB', 'GGXH$T_ZL_MachineShift_CB', 'DW$T_ZL_MachineShift_CB', 'GZSJ$T_ZL_MachineShift_CB', 'DJ$T_ZL_MachineShift_CB', 'JE$T_ZL_MachineShift_CB', 'f_FJ', 'BZ', 'LRR', 'LRSJ'],
    '机械结算单': ['DJZTText', 'DJBH', 'XMMC', 'DJRQ', 'JSDW', 'BZ', 'ZJE', 'CCCC_FKZT', 'CCCC_FKJE', 'CCCC_WFKJE', 'CCCC_SQZT', 'CCCC_SQJE', 'CCCC_WSQJE', 'f_FJ', 'LRR', 'LRSJ'],
    '租入': ['DJZTText', 'DJBH', 'f_DJRQ', 'f_SupplierName', 'f_LldwName', 'f_CLMC$T_ZL_ZRDCB', 'f_GGXH$T_ZL_ZRDCB', 'ZRSL$T_ZL_ZRDCB', 'f_DJ$T_ZL_ZRDCB', 'ZLYJ', 'f_BZ', 'FJ', 'f_LRR', 'f_LRSJ', 'ProjectName'],
    '还租': ['DJZTText', 'XMMC', 'JSZT', 'DJBH', 'f_DJRQ', 'f_SupplierName', 'f_JSJE', 'f_PCF', 'f_WXF', 'f_JCCF', 'f_FJ', 'f_BZ', 'f_LRR', 'f_LRSJ', 'DKJE', 'f_LldwName'],
    '租赁结算单': ['DJZTText', 'DJBH', 'XMMC', 'DJRQ', 'JSDW', 'BZ', 'ZJE', 'CCCC_FKZT', 'CCCC_FKJE', 'CCCC_WFKJE', 'CCCC_SQZT', 'CCCC_SQJE', 'CCCC_WSQJE', 'f_FJ', 'LRR', 'LRSJ'],
    '项目费用报销单': ['DJZTText', 'DJBH', 'RQ', 'BXZL', 'SXSM', 'SQBXJE', 'CCCC_FKZT', 'CCCC_FKJE', 'CCCC_WFKJE', 'FKFS', 'BXDW', 'SKR', 'BZ', 'XMMC', 'f_FJ', 'LRR', 'LRSJ'],
    '管理人员工资表': ['DJZTText', 'XMMC', 'DJBH', 'DJRQ', 'GZYF', 'BCSFGZZE', 'BCYFGZZE', 'CCCC_FKZT', 'CCCC_FKJE', 'CCCC_WFKJE', 'BZ', 'f_FJ', 'LRR', 'LRSJ'],
    '油卡登记': ['DJZTText', 'DJBH', 'DJRQ', 'XMMC', 'YKKH', 'CSJE', 'ZYGLR', 'BZ', 'f_FJ', 'LRR', 'LRSJ'],
    '充值登记': ['DJZTText', 'DJBH', 'DJRQ', 'XMMC', 'CZKH$D_LYXM_BG_BX_CZDJCB', 'CZZE', 'CZRQ', 'CZR', 'BZ', 'f_FJ', 'LRR', 'LRSJ'],
    '加油登记': ['DJZTText', 'DJBH', 'JYRQ', 'XMMC', 'JYJE', 'LJJYJE', 'YKSYJE', 'JYKH', 'LJCZJE', 'BZ', 'f_FJ', 'LRR', 'LRSJ'],
    '支付申请': ['DJZTText', 'DJBH', 'f_SQRQ', 'f_XMMC', 'f_GYSMC', 'D_LYXM_SJSKDW', 'FKZHMC', 'f_JHJE', 'FKJE', 'SJKYYE', 'D_LYXM_LX', 'f_Remark', 'SFGLDJ', 'FKZH', 'JEDX', 'HM', 'f_KHH', 'f_ZH', 'f_FJ', 'f_LRR', 'f_LRSJ'],
    '工程进度收款': ['DJZTText', 'DJBH', 'f_RQ', 'WLDWMC', 'SSGS', 'f_SRLBName', 'D_LYXM_JENR3', 'f_BZ', 'SGHTBH', 'XMMC', 'f_FJ', 'LRR', 'LRSJ'],
    '往来单位付款': ['DJZTText', 'f_FKRQ', 'f_SupplierName', 'D_LYXM_SJSKDW', 'f_FKJE', 'f_BZ', 'Remark', 'f_FKFSMC', 'D_LYXM_LX', 'FKZHMC', 'f_FJ', 'BZ', 'f_LRR', 'f_LRR', 'XMMC', 'FKDLY', 'DJBH'],
    '工程结算单': ['DJZTText', 'DJBH', 'DJRQ', 'XMMC', 'SSJE', 'HTZE', 'SDJE', 'BT', 'FBR', 'CBR', 'SZJJE', 'SJDW', 'HTMC', 'SDRQ', 'GCDZ', 'f_FJ', 'LRR', 'LRSJ'],
    '进项上报': ['DJZTText', 'DJBH', 'XMMC', 'KPRQ$C_JXXP_ZYFPJJD_CB', 'FPTGF$C_JXXP_ZYFPJJD_CB', 'GYSMC$C_JXXP_ZYFPJJD_CB', 'D_LYXM_SJKPDW$C_JXXP_ZYFPJJD_CB', 'HJJE$C_JXXP_ZYFPJJD_CB', 'JXSE$C_JXXP_ZYFPJJD_CB', 'JE_NO$C_JXXP_ZYFPJJD_CB', 'FPHM$C_JXXP_ZYFPJJD_CB', 'SL$C_JXXP_ZYFPJJD_CB', 'SLV$C_JXXP_ZYFPJJD_CB', 'FPLX$C_JXXP_ZYFPJJD_CB', 'BZ', 'LRR', 'f_FJ', 'LRSJ'],
    '总包进项上报': ['DJZTText', 'DJBH', 'KPRQ', 'KPDW', 'XMMC', 'SPFMC', 'SKZJE', 'BHSJE', 'ZSE', 'SLVS', 'D_SCBSJS_FJS', 'KPZS', 'GLHKJE', 'FPHM', 'FPZL', 'f_FJ', 'LRR', 'LRSJ'],
    '施工日志（新）': ['DJZTText', 'XMMC', 'DJBH', 'RQ', 'SGBW', 'CQRS', 'D_LYXM_CQJX', 'BZ', 'f_FJ', 'LRR', 'LRSJ']
}

LEGACY_DJZT_DISPLAY = {
    '-1': '否决',
    '0': '草稿',
    '1': '审批中',
    '2': '审核通过',
}

LEGACY_PAYMENT_STATUS_DISPLAY = {
    "0": "未付款",
    "1": "部分付款",
    "2": "已付款",
}

LEGACY_PAYMENT_REQUEST_STATUS_DISPLAY = {
    "0": "未申请",
    "1": "部分申请",
    "2": "全部申请",
}

LEGACY_SETTLEMENT_STATUS_DISPLAY = {
    "0": "未结算",
    "1": "部分结算",
    "2": "已结算",
}
LEGACY_ATTACHMENT_LABEL_RE = re.compile(r"^附件\([1-9]\d*\)$")
LEGACY_ATTACHMENT_ID_RE = re.compile(r"^[0-9a-fA-F]{32}$")


def _legacy_visible_search(self, operator, value):
    op = str(operator or "").strip() or "ilike"
    if op not in ("ilike", "like", "=ilike", "=like", "not ilike", "not like"):
        return [("id", "=", 0)]
    term = str(value or "").strip()
    if not term:
        return [("id", "=", 0)]
    fields_to_search = [
        "raw_payload",
        "document_no",
        "document_title",
        "project_name",
        "partner_name",
        "creator_name",
        "note",
    ]
    tokens = [token for token in re.split(r"\s+", term) if token]
    leaves = [
        ("raw_payload", op, term),
        ("document_no", op, term),
        ("document_title", op, term),
        ("project_name", op, term),
        ("partner_name", op, term),
        ("creator_name", op, term),
        ("note", op, term),
    ]
    domains = [[leaf] for leaf in leaves]
    if op in ("ilike", "like", "=ilike", "=like") and len(tokens) > 1:
        domains.extend(
            expression.AND([[(field_name, op, token)] for token in tokens])
            for field_name in fields_to_search
        )
    return expression.OR(domains)


class ScLegacyDirectAcceptanceFact(models.Model):
    _name = "sc.legacy.direct.acceptance.fact"
    _description = "直营历史验收事实"
    _order = "document_date desc, id desc"

    source_system = fields.Char(string="来源系统", required=True, index=True)
    acceptance_label = fields.Char(string="验收菜单", required=True, index=True)
    category = fields.Char(string="验收分类", index=True)
    legacy_config_id = fields.Char(string="历史配置ID", index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    legacy_parent_id = fields.Char(string="历史父记录ID", index=True)
    row_index = fields.Integer(string="历史行号", index=True)
    document_no = fields.Char(string="单据编号", index=True)
    document_title = fields.Char(string="标题/事项", index=True)
    document_date = fields.Datetime(string="单据日期", index=True)
    document_state = fields.Char(string="单据状态", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    project_legacy_id = fields.Char(string="历史项目ID", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    partner_name = fields.Char(string="往来单位/人员", index=True)
    amount_total = fields.Float(string="金额")
    quantity = fields.Float(string="数量")
    creator_name = fields.Char(string="录入人", index=True)
    creator_legacy_user_id = fields.Char(string="录入人ID", index=True)
    created_time = fields.Datetime(string="录入时间", index=True)
    attachment_ref = fields.Char(string="历史附件引用")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_legacy_direct_acceptance_fact_attachment_rel",
        "fact_id",
        "attachment_id",
        string="附件",
    )
    note = fields.Text(string="备注")
    raw_payload = fields.Text(string="历史原始行JSON")

    for _legacy_visible_index in range(1, 61):
        locals()[f"_search_legacy_visible_{_legacy_visible_index:02d}"] = _legacy_visible_search
        locals()[f"legacy_visible_{_legacy_visible_index:02d}"] = fields.Char(
            string="",
            compute="_compute_legacy_visible_fields",
            search=f"_search_legacy_visible_{_legacy_visible_index:02d}",
        )
    del _legacy_visible_index

    active = fields.Boolean(string="有效", default=True, index=True)

    @api.depends("acceptance_label", "raw_payload")
    def _compute_legacy_visible_fields(self):
        for record in self:
            payload = record._legacy_raw_payload_dict()
            fields_for_label = LEGACY_VISIBLE_FIELD_MAP.get(record.acceptance_label or "", [])
            for index in range(1, 61):
                value = ""
                if index <= len(fields_for_label):
                    value = record._legacy_payload_value(
                        payload,
                        fields_for_label[index - 1],
                        acceptance_label=record.acceptance_label or "",
                        visible_index=index,
                        attachment_ref=record.attachment_ref or "",
                    )
                setattr(record, f"legacy_visible_{index:02d}", value)

    def _legacy_raw_payload_dict(self):
        try:
            payload = json.loads(self.raw_payload or "{}")
        except (TypeError, ValueError):
            return {}
        return payload if isinstance(payload, dict) else {}

    @classmethod
    def _legacy_payload_value(cls, payload, field_name, acceptance_label="", visible_index=0, attachment_ref=""):
        display_value = cls._legacy_attachment_display_value(payload, field_name)
        if display_value:
            return display_value

        if acceptance_label == "还租" and field_name in {"f_LRR", "f_LRSJ"}:
            fallback_field = "XGR" if field_name == "f_LRR" else "XGSJ"
            value = payload.get(field_name) or payload.get(fallback_field)
            if value is not None and value is not False:
                return str(value).strip()
        if acceptance_label == "入库":
            value = cls._legacy_stock_in_computed_visible_value(payload, visible_index)
            if value:
                return value
        if field_name == "__LABOR_USAGE_SETTLEMENT_STATUS__":
            return cls._legacy_labor_usage_settlement_status(payload)
        value = cls._legacy_common_computed_visible_value(payload, field_name)
        if value:
            return value

        if field_name == "DJZTText":
            for status_field in ("DJZTText", "DJZT"):
                djzt = payload.get(status_field)
                if djzt is None or djzt is False:
                    continue
                text = str(djzt).strip()
                if text in LEGACY_DJZT_DISPLAY:
                    return LEGACY_DJZT_DISPLAY[text]
                if text:
                    return text
            return ""

        is_attachment_field = field_name.endswith("FJ") or field_name.endswith("_FJ") or field_name == "FJ"
        if is_attachment_field:
            if acceptance_label == "分包方单" and field_name == "f_FJ":
                value = payload.get("f_FJ")
                text = "" if value is None or value is False else str(value).strip()
                return text if LEGACY_ATTACHMENT_LABEL_RE.match(text) else ""
            display_candidates = [f"{field_name}_FJ", field_name, "f_FJ", "FJ", "f_FJ_FJ", "FJ_FJ"]
            for candidate in display_candidates:
                value = payload.get(candidate)
                if value is None or value is False:
                    continue
                text = str(value).strip()
                if text:
                    if LEGACY_ATTACHMENT_LABEL_RE.match(text):
                        return text
                    clean_attachment_ref = str(attachment_ref or "").strip()
                    if clean_attachment_ref and text == clean_attachment_ref:
                        return "附件(1)"
                    if LEGACY_ATTACHMENT_ID_RE.match(text):
                        return "附件(1)"
                    return ""
            raw_value = payload.get(field_name)
            raw_text = "" if raw_value is None or raw_value is False else str(raw_value).strip()
            clean_attachment_ref = str(attachment_ref or "").strip()
            if raw_text and clean_attachment_ref and raw_text == clean_attachment_ref:
                return "附件(1)"
            if LEGACY_ATTACHMENT_ID_RE.match(raw_text):
                return "附件(1)"
            return ""

        candidates = []
        if field_name:
            candidates.append(field_name)
        for candidate in candidates:
            value = payload.get(candidate)
            if value is None or value is False:
                continue
            if isinstance(value, (list, dict)):
                return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            text = str(value).strip()
            if text:
                if field_name in {"SLV", "SLVS", "D_SCBSJS_SL1", "SLV$C_JXXP_ZYFPJJD_CB"}:
                    return cls._legacy_tax_rate_text(text)
                return text
        if field_name == "SLVS":
            untaxed_amount = cls._legacy_number(payload, "BHSJE", "JE_NO$C_JXXP_ZYFPJJD_CB")
            tax_amount = cls._legacy_number(payload, "ZSE", "JXSE$C_JXXP_ZYFPJJD_CB")
            if untaxed_amount and tax_amount:
                return cls._legacy_tax_rate_text(tax_amount / untaxed_amount)
        return ""

    @staticmethod
    def _legacy_attachment_display_value(payload, field_name):
        if not field_name:
            return ""
        value = payload.get(f"{field_name}_FJ")
        if value is None or value is False:
            return ""
        text = str(value).strip()
        return text if LEGACY_ATTACHMENT_LABEL_RE.match(text) else ""

    @staticmethod
    def _legacy_number(payload, *field_names):
        for field_name in field_names:
            value = payload.get(field_name)
            if value is None or value is False:
                continue
            text = str(value).strip().replace(",", "")
            if not text:
                continue
            try:
                return float(text)
            except ValueError:
                continue
        return 0.0

    @staticmethod
    def _legacy_number_text(value):
        if value is None:
            return ""
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value).strip()
        return str(number)

    @staticmethod
    def _legacy_tax_rate_text(value):
        if value is None or value is False:
            return ""
        text = str(value).strip()
        if not text:
            return ""
        if "%" in text:
            return text
        try:
            number = float(text.replace(",", ""))
        except ValueError:
            return text
        percent = number * 100 if abs(number) <= 1 else number
        if percent.is_integer():
            return f"{int(percent)}%"
        return f"{percent:.4f}".rstrip("0").rstrip(".") + "%"

    @staticmethod
    def _legacy_has_payload_value(payload, *field_names):
        for field_name in field_names:
            value = payload.get(field_name)
            if value is None or value is False:
                continue
            if str(value).strip():
                return True
        return False

    @staticmethod
    def _legacy_stock_in_note_numbers(payload):
        note = str(payload.get("BZ") or payload.get("f_BZ") or "").strip()
        if not note:
            return 0.0, 0.0
        match = re.search(
            r"(?P<qty>\d+(?:\.\d+)?)\s*(?:\*|×|x|X)\s*(?P<price>\d+(?:\.\d+)?)\s*(?:=|＝)\s*(?P<amount>\d+(?:\.\d+)?)",
            note,
        )
        if match:
            return float(match.group("qty")), float(match.group("amount"))
        match = re.search(r"(?P<qty>\d+(?:\.\d+)?)\s*(?:个|件|吨|方|米|袋|匹|卷|车|台|套|根|桶|盒|包|张|块|瓶)", note)
        if match:
            return float(match.group("qty")), 0.0
        return 0.0, 0.0

    @classmethod
    def _legacy_amount_status(cls, paid, total, *, paid_label, partial_label, unpaid_label):
        if total <= 0:
            return unpaid_label
        if paid <= 0:
            return unpaid_label
        if paid + 0.000001 >= total:
            return paid_label
        return partial_label

    @classmethod
    def _legacy_labor_usage_settlement_status(cls, payload):
        for field_name in ("CCCC_JSZT", "JSZT", "CCCC_FKZT"):
            raw = payload.get(field_name)
            if raw is None or raw is False:
                continue
            text = str(raw).strip()
            if text:
                return LEGACY_SETTLEMENT_STATUS_DISPLAY.get(text, text)
        return ""

    @classmethod
    def _legacy_stock_in_computed_visible_value(cls, payload, visible_index):
        total_amount = cls._legacy_number(payload, "ZJE", "RK_ZJE", "HJ$T_RK_RKDCB")
        note_quantity, note_amount = cls._legacy_stock_in_note_numbers(payload)
        if total_amount <= 0 and note_amount:
            total_amount = note_amount
        paid_amount = cls._legacy_number(payload, "CCCC_FKJE", "YFJE$T_RK_RKDCB")
        settled_amount = cls._legacy_number(payload, "CCCC_JSJE", "ZJE", "RK_ZJE", "HJ$T_RK_RKDCB")
        if settled_amount <= 0 and total_amount:
            settled_amount = total_amount
        if visible_index == 11:
            quantity_fields = ("RK_ZSL", "ZSL", "SL$T_RK_RKDCB")
            quantity = cls._legacy_number(payload, *quantity_fields)
            if quantity <= 0 and note_quantity:
                quantity = note_quantity
            if quantity or cls._legacy_has_payload_value(payload, *quantity_fields):
                return cls._legacy_number_text(quantity)
            if total_amount:
                return cls._legacy_number_text(0.0)
            return ""
        if visible_index == 12:
            raw_status = payload.get("CCCC_FKZT")
            text = "" if raw_status is None or raw_status is False else str(raw_status).strip()
            return LEGACY_PAYMENT_STATUS_DISPLAY.get(text, text) if text else cls._legacy_amount_status(
                paid_amount,
                total_amount,
                paid_label="已付款",
                partial_label="部分付款",
                unpaid_label="未付款",
            )
        if visible_index == 13:
            return cls._legacy_number_text(paid_amount)
        if visible_index == 14:
            unpaid_amount = max(total_amount - paid_amount, 0.0)
            return cls._legacy_number_text(unpaid_amount)
        if visible_index == 15:
            raw_status = payload.get("CCCC_JSZT")
            text = "" if raw_status is None or raw_status is False else str(raw_status).strip()
            return LEGACY_SETTLEMENT_STATUS_DISPLAY.get(text, text) if text else cls._legacy_amount_status(
                settled_amount,
                total_amount,
                paid_label="已结算",
                partial_label="部分结算",
                unpaid_label="未结算",
            )
        if visible_index == 16:
            return cls._legacy_number_text(settled_amount)
        return ""

    @classmethod
    def _legacy_common_computed_visible_value(cls, payload, field_name):
        if field_name not in {
            "CCCC_FKZT",
            "CCCC_FKJE",
            "CCCC_WFKJE",
            "CCCC_SQZT",
            "CCCC_SQJE",
            "CCCC_WSQJE",
            "CCCC_JSZT",
            "JSZT",
        }:
            return ""

        raw = payload.get(field_name)
        if raw is not None and raw is not False and str(raw).strip():
            text = str(raw).strip()
            if field_name == "CCCC_FKZT":
                return LEGACY_PAYMENT_STATUS_DISPLAY.get(text, text)
            if field_name == "CCCC_SQZT":
                return LEGACY_PAYMENT_REQUEST_STATUS_DISPLAY.get(text, text)
            if field_name == "CCCC_JSZT":
                return LEGACY_SETTLEMENT_STATUS_DISPLAY.get(text, text)
            if field_name not in {"CCCC_WFKJE", "CCCC_WSQJE"}:
                return str(raw).strip()

        total_amount = cls._legacy_number(
            payload,
            "ZJE",
            "JEHJ",
            "JE",
            "ZHSJE",
            "SQBXJE",
            "f_JSJE",
            "SSJE",
            "HJ$T_RK_RKDCB",
            "RK_ZJE",
        )
        paid_amount = cls._legacy_number(payload, "CCCC_FKJE", "YFKJE", "YFJE$T_RK_RKDCB", "FKJE")
        applied_amount = cls._legacy_number(payload, "CCCC_SQJE", "SQJE")
        settlement_amount = cls._legacy_number(payload, "f_JSJE", "JSJE", "ZJE")

        if field_name == "JSZT":
            if settlement_amount > 0:
                return "已结算"
            return "未结算"
        if field_name == "CCCC_JSZT":
            return cls._legacy_amount_status(
                settlement_amount,
                total_amount,
                paid_label="已结算",
                partial_label="部分结算",
                unpaid_label="未结算",
            )

        if field_name == "CCCC_FKZT":
            return cls._legacy_amount_status(
                paid_amount,
                total_amount,
                paid_label="已付款",
                partial_label="部分付款",
                unpaid_label="未付款",
            )
        if field_name == "CCCC_FKJE":
            return cls._legacy_number_text(paid_amount)
        if field_name == "CCCC_WFKJE":
            raw_unpaid = cls._legacy_number(payload, "WFKJE")
            unpaid_amount = raw_unpaid if raw_unpaid > 0 else max(total_amount - paid_amount, 0.0)
            return cls._legacy_number_text(unpaid_amount)
        if field_name == "CCCC_SQZT":
            return cls._legacy_amount_status(
                applied_amount,
                total_amount,
                paid_label="全部申请",
                partial_label="部分申请",
                unpaid_label="未申请",
            )
        if field_name == "CCCC_SQJE":
            return cls._legacy_number_text(applied_amount)
        if field_name == "CCCC_WSQJE":
            raw_unapplied = cls._legacy_number(payload, "WSQJE")
            unapplied_amount = raw_unapplied if raw_unapplied > 0 else max(total_amount - applied_amount, 0.0)
            return cls._legacy_number_text(unapplied_amount)
        return ""

    _sql_constraints = [
        (
            "legacy_direct_acceptance_fact_unique",
            "unique(source_system, acceptance_label, legacy_record_id)",
            "同一历史验收行只能导入一次。",
        ),
    ]
