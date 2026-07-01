#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "p1_daily_business_visible_contract_audit.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "p1_daily_business_visible_contract_audit.md"


P1_ENTRIES: list[dict[str, Any]] = [
    {
        "id": "DBS-019",
        "name": "投标报名管理",
        "domain": "投标",
        "images": "image37",
        "candidates": ["tender.bid", "sc.legacy.tender.registration.fact"],
        "expected_list_fields": ["单据状态", "推送结果", "单据编号", "开标时间", "项目名称", "登记时间", "录入人"],
        "expected_filters": ["投标项目名称"],
        "expected_status_tabs": ["全部", "审核通过", "审批中", "草稿", "否决"],
    },
    {
        "id": "DBS-020",
        "name": "投标报名费申请",
        "domain": "投标/付款",
        "images": "image38",
        "candidates": ["tender.doc.purchase", "payment.request"],
        "expected_list_fields": ["单据状态", "项目名称", "单据编号", "申请人", "申请日期", "收款账号", "开户行", "金额", "备注", "收款人", "付款方式", "附件", "录入人", "录入时间"],
    },
    {
        "id": "DBS-021",
        "name": "承包人借项目款",
        "domain": "借款",
        "images": "image39-image40",
        "candidates": ["sc.financing.loan", "sc.legacy.financing.loan.fact"],
        "expected_list_fields": ["单据状态", "单据编号", "项目名称", "借款人", "借款金额", "用途", "约定期限", "借款利息", "备注", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["基本信息", "收支账户信息", "其它信息"],
    },
    {
        "id": "DBS-022",
        "name": "承包人还项目款",
        "domain": "还款",
        "images": "image41-image42",
        "candidates": ["sc.financing.loan", "sc.fund.account.operation"],
        "expected_list_fields": ["单据编号", "项目名称", "借款人", "借款金额", "还款金额", "用途", "借款利率", "利息", "还款时间", "备注", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["基本信息", "还款信息", "收支账户信息", "附件"],
    },
    {
        "id": "DBS-023",
        "name": "支付申请",
        "domain": "付款",
        "images": "image43-image44",
        "candidates": ["payment.request", "payment.request.line"],
        "expected_list_fields": ["单据状态", "单据编号", "项目名称", "申请日期", "收款单位", "申请付款金额", "实际付款金额", "可用余额", "成本分类名称", "备注", "是否关联单据", "付款账号", "金额大写", "户名", "开户行", "账号", "填写人", "附件", "录入时间"],
        "expected_form_sections": ["申请信息", "关联单据", "附件"],
    },
    {
        "id": "DBS-024",
        "name": "扣款单",
        "domain": "扣款",
        "images": "image45-image46",
        "candidates": ["sc.tax.deduction.registration", "sc.legacy.deduction.adjustment.line"],
        "expected_list_fields": ["单据状态", "单据编号", "项目名称", "扣款单位", "扣款金额", "扣款事由", "单据日期", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["基本信息", "扣款信息", "附件"],
    },
    {
        "id": "DBS-025",
        "name": "往来单位付款",
        "domain": "付款",
        "images": "image47-image48",
        "candidates": ["sc.payment.execution"],
        "expected_list_fields": ["推送结果", "金蝶单据编号", "单据编号", "项目名称", "供应商名称", "付款日期", "付款金额", "备注", "其它备注", "付款方式名称", "填写人", "开户行", "账户", "付款账户", "付款账户名称", "支付申请单号", "附件"],
        "expected_form_sections": ["基本信息", "付款信息", "关联单据", "附件"],
    },
    {
        "id": "DBS-026",
        "name": "账户间资金往来",
        "domain": "资金账户",
        "images": "image49-image50",
        "candidates": ["sc.fund.account.operation", "sc.legacy.account.transaction.line"],
        "expected_list_fields": ["单据状态", "项目名称", "单据编号", "发生时间", "账户号码", "收款账户", "金额", "转账类别", "事由", "备注", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["基本信息", "详情", "项目间借贷", "附件"],
    },
    {
        "id": "DBS-027",
        "name": "扣款实缴登记",
        "domain": "扣款",
        "images": "image51-image52",
        "candidates": ["sc.tax.deduction.registration", "sc.fund.account.operation"],
        "expected_list_fields": ["单据状态", "单据编号", "项目名称", "单据日期", "标题", "本次实缴数", "是否退回", "上缴内容", "本次计划已缴数", "录入人", "录入时间"],
        "expected_form_sections": ["基本信息", "扣款实缴信息", "附件"],
    },
    {
        "id": "DBS-028",
        "name": "扣款实缴退回",
        "domain": "扣款",
        "images": "image53-image54",
        "candidates": ["sc.tax.deduction.registration", "sc.fund.account.operation"],
        "expected_list_fields": ["单据状态", "项目名称", "单据编号", "本次实缴数", "本次退回数", "上缴内容", "备注", "附件", "录入人", "单据日期"],
        "expected_form_sections": ["基本信息", "扣款退回信息", "附件"],
    },
    {
        "id": "DBS-029",
        "name": "到款确认表",
        "domain": "收款",
        "images": "image55-image56",
        "candidates": ["sc.receipt.income", "sc.legacy.fund.confirmation.line"],
        "expected_list_fields": ["单据状态", "单据编号", "时间", "项目名称", "期数", "本期收款", "本期代扣代缴合计", "本期拨付金额合计", "附件", "施工单位", "合同金额", "目前形象进度", "累计开票金额", "上期留存余额", "录入人", "录入时间"],
        "expected_form_sections": ["工程款确认", "代扣代缴明细", "施工队明细"],
    },
    {
        "id": "DBS-030",
        "name": "资金日报表",
        "domain": "资金报表",
        "images": "image57-image58",
        "candidates": ["sc.legacy.fund.daily.snapshot.fact"],
        "expected_list_fields": ["单据状态", "单据编号", "单据日期", "账号名称", "银行账号", "当前账户余额", "当前账户银行余额", "银行系统差额", "当日累计收入", "当日累计支出", "账户往来", "备注", "录入人", "录入时间"],
        "expected_form_sections": ["日报时段", "账户余额合计", "资金详情", "附件"],
    },
    {
        "id": "DBS-031",
        "name": "项目借公司款登记",
        "domain": "借款",
        "images": "image59-image60",
        "candidates": ["sc.financing.loan", "sc.legacy.project.fund.balance.fact"],
        "expected_list_fields": ["单据状态", "单据编号", "项目名称", "贷款金额", "到期利息", "还款金额", "未还款金额", "贷款日期", "还款日期", "贷款天数", "年利率", "贷款账户", "贷款银行", "备注", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["贷款账户", "银行", "金额", "利率", "期限", "附件"],
    },
    {
        "id": "DBS-032",
        "name": "项目还公司款登记",
        "domain": "还款",
        "images": "image61-image62",
        "candidates": ["sc.financing.loan", "sc.fund.account.operation"],
        "expected_list_fields": ["单据编号", "项目名称", "还款金额", "实际还款天数", "实际年利率", "贷款利息", "贷款银行", "贷款账户", "还款账户", "填写人", "备注", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["贷款信息", "还款信息", "附件"],
    },
    {
        "id": "DBS-033",
        "name": "开票申请",
        "domain": "发票税务",
        "images": "image63-image64",
        "candidates": ["sc.invoice.registration"],
        "expected_list_fields": ["状态", "开票状态", "合同编号", "项目名称", "单据编号", "申请人", "预计回款日期", "申请日期", "受票方名称", "累计开票金额", "合同额", "本次开票张数", "本次开票金额", "附件", "备注", "录入人", "录入时间"],
        "expected_form_sections": ["发票标题", "基本信息", "受票方信息", "开票方信息", "本次开票信息", "相关数据", "附件"],
    },
    {
        "id": "DBS-034",
        "name": "销项发票登记",
        "domain": "发票税务",
        "images": "image65-image66",
        "candidates": ["sc.invoice.registration", "sc.legacy.income.invoice.fact"],
        "expected_list_fields": ["单据状态", "推送结果", "金蝶单据编号", "单据编号", "项目名称", "受票方名称", "含税金额", "税额", "不含税金额", "附加税", "开票张数", "税率", "关联回款金额", "发票号", "发票种类", "开票单位", "附件", "录入人", "开票日期"],
        "expected_form_sections": ["开票详情", "发票实开详情", "发票金额", "附件"],
    },
    {
        "id": "DBS-035",
        "name": "预缴税款",
        "domain": "发票税务",
        "images": "image67-image68",
        "candidates": ["sc.invoice.registration"],
        "expected_list_fields": ["状态", "项目名称", "单据编号", "受票方名称", "交税类型", "金额", "发票开具日期", "预缴税款日期", "完税凭证号码", "附件", "录入人"],
        "expected_form_sections": ["开票详情", "预缴税款详情", "附件"],
    },
    {
        "id": "DBS-036",
        "name": "抵扣登记",
        "domain": "发票税务",
        "images": "image69-image70",
        "candidates": ["sc.tax.deduction.registration"],
        "expected_list_fields": ["单据状态", "单据编号", "是否转出", "项目名称", "开票单位", "发票号", "抵扣税额", "抵扣总额", "抵扣附加税", "备注", "录入人", "单据日期"],
        "expected_form_sections": ["抵扣登记信息", "抵扣详情", "附件"],
    },
    {
        "id": "DBS-037",
        "name": "账户",
        "domain": "资金账户基础",
        "images": "image71-image72",
        "candidates": ["sc.fund.account"],
        "expected_list_fields": ["推送结果", "账户状态", "账户操作", "录入来源", "项目名称", "单据编号", "账户类型", "账号名称", "账号户名", "开户行", "初期余额", "录入人", "录入时间"],
        "expected_form_fields": ["项目名称", "单据编号", "账号类型", "账户名称", "开户行", "开户账号", "初期余额", "是否默认账号", "是否过渡账户", "排序号"],
    },
    {
        "id": "DBS-038",
        "name": "进项上报",
        "domain": "进项税务",
        "images": "image73-image74",
        "candidates": ["sc.tax.deduction.registration"],
        "expected_list_fields": ["状态", "单据编号", "项目名称", "发票开具日期", "受票单位", "开票单位", "实际开票单位", "价税合计", "税额", "不含税金额", "发票号码", "数量", "税率", "发票类型", "备注", "录入人", "附件", "录入时间"],
        "expected_form_sections": ["基本信息", "发票信息", "材料信息", "附件"],
    },
    {
        "id": "DBS-039",
        "name": "供货合同",
        "domain": "材料合同",
        "images": "image75-image76",
        "candidates": ["sc.material.purchase.request", "purchase.order"],
        "expected_list_fields": ["单据状态", "合同编号", "标题", "供应商", "购货单位", "总金额", "已开票金额", "已付款金额", "未付款金额", "未开票金额", "项目名称", "录入时间", "税率", "录入人", "附件"],
        "expected_form_sections": ["基本信息", "材料信息", "附件"],
    },
    {
        "id": "DBS-040",
        "name": "入库",
        "domain": "材料入库",
        "images": "image77-image78",
        "candidates": ["sc.material.inbound"],
        "expected_list_fields": ["单据状态", "入库单号", "单据日期", "供应商名称", "材料名称", "规格型号", "数量", "单价", "税率", "含税金额", "入库总数量", "付款状态", "已付款金额", "未付款金额", "结算状态", "已结算金额", "项目名称", "备注", "附件", "录入人", "录入时间", "采购人"],
        "expected_form_sections": ["基本信息", "材料信息", "附件"],
    },
    {
        "id": "DBS-041",
        "name": "材料结算单",
        "domain": "材料结算",
        "images": "image79",
        "candidates": ["sc.material.settlement"],
        "expected_list_fields": ["单据状态", "项目名称", "单据编号", "标题", "结算单位", "结算日期", "结算金额", "付款状态", "已付款金额", "未付款金额", "支付申请状态", "已申请金额", "未申请金额", "结算说明", "附件", "录入人", "录入时间"],
    },
    {
        "id": "DBS-042",
        "name": "劳务合同",
        "domain": "劳务合同",
        "images": "image80-image81",
        "candidates": ["sc.labor.request", "sc.labor.settlement"],
        "expected_list_fields": ["单据状态", "单据编号", "项目名称", "签订日期", "标题", "劳务单位", "施工队负责人", "总含税金额", "结算比例", "已开票金额", "已付款金额", "未付款金额", "未开票金额", "计价方式", "施工部位", "合同编号", "附件", "录入人", "支付条款", "推送项目名称"],
        "expected_form_sections": ["施工单位", "合同信息", "工种信息", "附件"],
    },
    {
        "id": "DBS-043",
        "name": "劳务方单",
        "domain": "劳务方单",
        "images": "image82-image85",
        "candidates": ["sc.labor.usage", "sc.labor.settlement"],
        "expected_list_fields": ["单据状态", "单据编号", "项目名称", "单据日期", "标题", "劳务单位", "施工部位", "结算状态", "总金额", "备注", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["基本信息", "工种/表单信息", "附件"],
    },
    {
        "id": "DBS-044",
        "name": "劳务结算",
        "domain": "劳务结算",
        "images": "image86-image87",
        "candidates": ["sc.labor.settlement"],
        "expected_list_fields": ["状态", "单据编号", "项目名称", "单据日期", "标题", "结算单位", "结算金额", "付款状态", "已付款金额", "未付款金额", "支付申请状态", "已申请金额", "未申请金额", "结算说明", "附件", "录入人", "录入时间", "合同编号"],
        "expected_form_sections": ["基本信息", "汇总信息", "方单详情", "附件"],
    },
    {
        "id": "DBS-045",
        "name": "分包合同",
        "domain": "分包合同",
        "images": "image88-image89",
        "candidates": ["sc.subcontract.register"],
        "expected_list_fields": ["状态", "单据编号", "签订时间", "标题", "分包单位", "分包内容", "总数量", "金额", "合同编号", "已开票金额", "已付款金额", "未付款金额", "未开票金额", "项目名称", "备注", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["基本信息", "合同清单", "附件"],
    },
    {
        "id": "DBS-046",
        "name": "分包方单",
        "domain": "分包方单",
        "images": "image90-image92",
        "candidates": ["sc.subcontract.request", "sc.subcontract.register"],
        "expected_list_fields": ["单据状态", "单据编号", "项目名称", "标题", "分包商", "分包类型", "分包内容", "数量", "单价", "金额", "本月合价", "备注", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["基本信息", "方单详情", "附件"],
    },
    {
        "id": "DBS-047",
        "name": "分包结算单",
        "domain": "分包结算",
        "images": "image93-image94",
        "candidates": ["sc.subcontract.settlement"],
        "expected_list_fields": ["状态", "项目名称", "单据编号", "标题", "结算单位", "结算金额", "付款状态", "已付款金额", "未付款金额", "支付申请状态", "已申请金额", "未申请金额", "合同编号", "起始结算日期", "终止结算日期", "结算日期", "结算说明", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["基本信息", "汇总信息", "方单详情", "附件"],
    },
    {
        "id": "DBS-048",
        "name": "机械合同",
        "domain": "机械合同",
        "images": "image95-image96",
        "candidates": ["sc.equipment.request", "sc.equipment.settlement"],
        "expected_list_fields": ["单据状态", "单据编号", "合同编号", "项目名称", "合同标题", "租赁单位", "租赁内容", "总数量", "已开票金额", "已付款金额", "未付款金额", "未开票金额", "总金额", "签订时间", "经办人及电话", "税率", "增值税类型", "备注", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["机械设备明细", "附件"],
    },
    {
        "id": "DBS-049",
        "name": "机械台班记录",
        "domain": "机械台班",
        "images": "image97-image98",
        "candidates": ["sc.equipment.usage"],
        "expected_list_fields": ["单据状态", "项目名称", "单据编号", "单据日期", "租赁单位", "曾用名单", "机械名称", "规格型号", "单位", "工作时间", "单价", "金额", "附件", "备注", "录入人", "录入时间"],
        "expected_form_sections": ["基本信息", "表单信息", "附件"],
    },
    {
        "id": "DBS-050",
        "name": "机械结算单",
        "domain": "机械结算",
        "images": "image99-image100",
        "candidates": ["sc.equipment.settlement"],
        "expected_list_fields": ["单据状态", "单据编号", "项目名称", "单据日期", "结算单位", "结算内容", "总金额", "付款状态", "已付款金额", "未付款金额", "支付申请状态", "已申请金额", "未申请金额", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["机械设备租赁清单", "结算费用清单", "附件"],
    },
    {
        "id": "DBS-051",
        "name": "租赁合同",
        "domain": "租赁合同",
        "images": "image101-image102",
        "candidates": ["sc.material.rental.order"],
        "expected_list_fields": ["单据编号", "状态", "合同编号", "项目名称", "合同标题", "租赁单位", "单据金额", "租赁内容", "总金额", "已开票金额", "已付款金额", "未付款金额", "未开票金额", "开户行", "银行账号", "开户人姓名", "附件", "签订时间"],
        "expected_form_sections": ["租赁材料清单", "附件"],
    },
    {
        "id": "DBS-052",
        "name": "租赁结算单",
        "domain": "租赁结算",
        "images": "image103-image104",
        "candidates": ["sc.material.rental.settlement"],
        "expected_list_fields": ["单据状态", "项目名称", "单据编号", "结算单位", "结算日期", "结算金额", "附件", "录入人", "录入时间"],
        "expected_form_sections": ["结算材料租赁清单", "结算费用清单", "附件"],
    },
    {
        "id": "DBS-053",
        "name": "租入",
        "domain": "租赁入库/租入",
        "images": "image105",
        "candidates": ["sc.material.rental.order"],
        "expected_list_fields": ["单据状态", "单据编号", "单据日期", "租赁单位", "使用单位名称", "材料名称", "规格型号", "数量", "单价", "租赁押金", "备注", "附件", "录入人", "录入时间", "项目名称"],
    },
    {
        "id": "DBS-054",
        "name": "施工日志（新）",
        "domain": "施工",
        "images": "image106-image107",
        "candidates": ["sc.construction.diary"],
        "expected_list_fields": ["单据状态", "项目名称", "单据编号", "日期", "施工部位", "出勤人数", "出勤机械", "备注", "附件", "录入人", "录入时间"],
        "expected_form_fields": ["单据编号", "项目名称", "日期", "施工部位", "出勤人数", "出勤机械", "温度", "上午气候", "下午气候", "当日施工内容", "材料进场/送检情况", "设计变更或技术核定", "操作负责人", "试块制作", "质量情况", "安全情况", "隐蔽工程验收", "施工员", "备注", "附件"],
    },
]


def _norm(value: Any) -> str:
    return str(value or "").strip()


def _login(intent_url: str) -> tuple[str, str]:
    db_name = _norm(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev")
    login = _norm(os.getenv("P1_AUDIT_LOGIN") or os.getenv("E2E_LOGIN") or os.getenv("ACCEPTANCE_LOGIN") or "wutao")
    password = _norm(
        os.getenv("P1_AUDIT_PASSWORD")
        or os.getenv("E2E_PASSWORD")
        or os.getenv("ACCEPTANCE_PASSWORD")
        or "123456"
    )
    status, payload = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        raise RuntimeError(f"login failed status={status} db={db_name} login={login}")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = _norm(data.get("token") or (data.get("session") or {}).get("token"))
    if not token:
        raise RuntimeError("login succeeded but token is empty")
    return token, login


def _post_contract(intent_url: str, token: str, model: str, view_type: str) -> tuple[int, dict[str, Any]]:
    status, payload = http_post_json(
        intent_url,
        {"intent": "ui.contract", "params": {"op": "model", "model": model, "view_type": view_type}},
        headers={"Authorization": f"Bearer {token}"},
    )
    return int(status), payload if isinstance(payload, dict) else {}


def _extract_columns(data: dict[str, Any]) -> list[dict[str, str]]:
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    tree = views.get("tree") if isinstance(views.get("tree"), dict) else {}
    schema = tree.get("columns_schema") if isinstance(tree.get("columns_schema"), list) else []
    if schema:
        return [
            {
                "name": _norm(row.get("name")),
                "label": _norm(row.get("label") or row.get("string") or row.get("name")),
            }
            for row in schema
            if isinstance(row, dict) and _norm(row.get("name") or row.get("label") or row.get("string"))
        ]
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    columns = tree.get("columns") if isinstance(tree.get("columns"), list) else []
    rows = []
    for item in columns:
        name = _norm(item.get("name") if isinstance(item, dict) else item)
        if not name:
            continue
        meta = fields.get(name) if isinstance(fields.get(name), dict) else {}
        rows.append({"name": name, "label": _norm(meta.get("string") or meta.get("label") or name)})
    return rows


def _extract_search_labels(data: dict[str, Any]) -> list[str]:
    search = data.get("search") if isinstance(data.get("search"), dict) else {}
    rows: list[str] = []
    for key in ("filters", "fields", "group_by", "groupBy", "saved_filters", "savedFilters"):
        values = search.get(key)
        if not isinstance(values, list):
            continue
        for item in values:
            if isinstance(item, dict):
                label = _norm(item.get("label") or item.get("string") or item.get("name") or item.get("field"))
            else:
                label = _norm(item)
            if label and label not in rows:
                rows.append(label)
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    tree_search = (views.get("tree") or {}).get("search") if isinstance(views.get("tree"), dict) else {}
    if isinstance(tree_search, dict):
        for key in ("filters", "fields", "group_by", "groupBy"):
            values = tree_search.get(key)
            if isinstance(values, list):
                for item in values:
                    label = _norm(item.get("label") or item.get("string") or item.get("name")) if isinstance(item, dict) else _norm(item)
                    if label and label not in rows:
                        rows.append(label)
    return rows


def _extract_form_signals(data: dict[str, Any]) -> dict[str, Any]:
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    labels = []
    for name, meta in fields.items():
        if isinstance(meta, dict):
            label = _norm(meta.get("string") or meta.get("label") or name)
        else:
            label = _norm(name)
        if label and label not in labels:
            labels.append(label)
    section_labels: list[str] = []

    def collect_section_labels(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("label", "string", "title"):
                value = _norm(node.get(key))
                if value and value not in section_labels:
                    section_labels.append(value)
            attrs = node.get("attributes")
            if isinstance(attrs, dict):
                value = _norm(attrs.get("string") or attrs.get("label") or attrs.get("title"))
                if value and value not in section_labels:
                    section_labels.append(value)
            for value in node.values():
                collect_section_labels(value)
        elif isinstance(node, list):
            for item in node:
                collect_section_labels(item)

    collect_section_labels(form.get("layout"))
    form_json = json.dumps(form, ensure_ascii=False, sort_keys=True)
    return {
        "field_labels": labels,
        "section_labels": section_labels,
        "has_attachment_signal": any(token in form_json for token in ("attachment", "附件", "message_main_attachment_id")),
        "has_chatter_signal": any(token in form_json for token in ("chatter", "日志", "message_ids", "activity_ids")),
    }


def _missing(expected: list[str], current: list[str]) -> list[str]:
    current_set = {_norm(item) for item in current if _norm(item)}
    return [item for item in expected if _norm(item) and _norm(item) not in current_set]


def _audit_entry(intent_url: str, token: str, entry: dict[str, Any]) -> dict[str, Any]:
    attempts = []
    selected = None
    tree_data: dict[str, Any] = {}
    form_data: dict[str, Any] = {}
    for model in entry["candidates"]:
        status, payload = _post_contract(intent_url, token, model, "tree")
        ok = bool(200 <= status < 300 and payload.get("ok") is True)
        error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
        attempts.append({"model": model, "status": status, "ok": ok, "error": _norm(error.get("message") or error.get("code"))})
        if not ok:
            continue
        selected = model
        tree_data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        form_status, form_payload = _post_contract(intent_url, token, model, "form")
        if 200 <= form_status < 300 and form_payload.get("ok") is True:
            form_data = form_payload.get("data") if isinstance(form_payload.get("data"), dict) else {}
        break

    expected_list = list(entry.get("expected_list_fields") or [])
    expected_filters = list(entry.get("expected_filters") or [])
    expected_form_fields = list(entry.get("expected_form_fields") or [])
    expected_form_sections = list(entry.get("expected_form_sections") or [])
    columns = _extract_columns(tree_data) if selected else []
    current_labels = [row["label"] for row in columns]
    search_labels = _extract_search_labels(tree_data) if selected else []
    form_signals = _extract_form_signals(form_data) if selected else {
        "field_labels": [],
        "section_labels": [],
        "has_attachment_signal": False,
        "has_chatter_signal": False,
    }
    missing_list = _missing(expected_list, current_labels)
    missing_filters = _missing(expected_filters, search_labels)
    missing_form_fields = _missing(expected_form_fields, form_signals["field_labels"])
    form_visible_labels = list(form_signals["section_labels"])
    for label in form_signals["field_labels"]:
        if label not in form_visible_labels:
            form_visible_labels.append(label)
    missing_sections = _missing(expected_form_sections, form_visible_labels)
    has_gap = bool(missing_list or missing_filters or missing_form_fields or missing_sections)
    return {
        "id": entry["id"],
        "name": entry["name"],
        "domain": entry["domain"],
        "images": entry["images"],
        "candidate_models": entry["candidates"],
        "selected_model": selected or "",
        "attempts": attempts,
        "current_list_fields": current_labels,
        "current_column_names": [row["name"] for row in columns],
        "expected_list_fields": expected_list,
        "missing_list_fields": missing_list,
        "expected_filters": expected_filters,
        "current_search_labels": search_labels,
        "missing_filters": missing_filters,
        "expected_form_fields": expected_form_fields,
        "missing_form_fields": missing_form_fields,
        "expected_form_sections": expected_form_sections,
        "missing_form_sections": missing_sections,
        "has_attachment_signal": bool(form_signals["has_attachment_signal"]),
        "has_chatter_signal": bool(form_signals["has_chatter_signal"]),
        "status": "no_contract" if not selected else "aligned" if not has_gap else "gap",
    }


def _write_reports(payload: dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# P1 Daily Business Visible Contract Audit",
        "",
        f"- audit_login: {payload.get('audit_login') or '-'}",
        f"- entry_count: {payload['summary']['entry_count']}",
        f"- contract_entry_count: {payload['summary']['contract_entry_count']}",
        f"- no_contract_count: {payload['summary']['no_contract_count']}",
        f"- aligned_count: {payload['summary']['aligned_count']}",
        f"- gap_count: {payload['summary']['gap_count']}",
        f"- missing_list_field_count: {payload['summary']['missing_list_field_count']}",
        f"- missing_filter_count: {payload['summary']['missing_filter_count']}",
        f"- missing_form_field_count: {payload['summary']['missing_form_field_count']}",
        f"- missing_form_section_count: {payload['summary']['missing_form_section_count']}",
        "",
        "| id | old entry | domain | selected model | status | missing list fields | missing filters | missing form fields | missing form sections | attachment | chatter |",
        "|---|---|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {id} | {name} | {domain} | {model} | {status} | {missing_list} | {missing_filters} | {missing_form_fields} | {missing_form_sections} | {attach} | {chatter} |".format(
                id=row["id"],
                name=row["name"],
                domain=row["domain"],
                model=row["selected_model"] or "-",
                status=row["status"],
                missing_list=len(row["missing_list_fields"]),
                missing_filters=len(row["missing_filters"]),
                missing_form_fields=len(row["missing_form_fields"]),
                missing_form_sections=len(row["missing_form_sections"]),
                attach="Y" if row["has_attachment_signal"] else "N",
                chatter="Y" if row["has_chatter_signal"] else "N",
            )
        )
    lines.extend(["", "## Gap Details", ""])
    for row in payload["rows"]:
        missing = row["missing_list_fields"]
        if row["status"] == "aligned":
            continue
        lines.append(f"### {row['id']} {row['name']}")
        lines.append(f"- selected_model: `{row['selected_model'] or '-'}`")
        if missing:
            lines.append(f"- missing_list_fields: {', '.join(missing)}")
        if row["missing_filters"]:
            lines.append(f"- missing_filters: {', '.join(row['missing_filters'])}")
        if row["missing_form_fields"]:
            lines.append(f"- missing_form_fields: {', '.join(row['missing_form_fields'])}")
        if row["missing_form_sections"]:
            lines.append(f"- missing_form_sections: {', '.join(row['missing_form_sections'])}")
        if row["status"] == "no_contract":
            errors = [f"{item['model']}({item['status']} {item['error']})" for item in row["attempts"]]
            lines.append(f"- attempts: {', '.join(errors)}")
        lines.append("")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    intent_url = f"{get_base_url()}/api/v1/intent"
    token, audit_login = _login(intent_url)
    rows = [_audit_entry(intent_url, token, entry) for entry in P1_ENTRIES]
    summary = {
        "entry_count": len(rows),
        "contract_entry_count": len([row for row in rows if row["selected_model"]]),
        "no_contract_count": len([row for row in rows if row["status"] == "no_contract"]),
        "aligned_count": len([row for row in rows if row["status"] == "aligned"]),
        "gap_count": len([row for row in rows if row["status"] == "gap"]),
        "missing_list_field_count": sum(len(row["missing_list_fields"]) for row in rows),
        "missing_filter_count": sum(len(row["missing_filters"]) for row in rows),
        "missing_form_field_count": sum(len(row["missing_form_fields"]) for row in rows),
        "missing_form_section_count": sum(len(row["missing_form_sections"]) for row in rows),
    }
    payload = {
        "ok": True,
        "scope": "P1 old-system daily-business visible list contract audit",
        "source_doc": "/home/odoo/workspace/partner_import_source/老系统列表，填单页面截图.docx",
        "audit_login": audit_login,
        "summary": summary,
        "rows": rows,
    }
    _write_reports(payload)
    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if summary["no_contract_count"] or summary["gap_count"]:
        print("[p1_daily_business_visible_contract_audit] FAIL")
        return 1
    print("[p1_daily_business_visible_contract_audit] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
