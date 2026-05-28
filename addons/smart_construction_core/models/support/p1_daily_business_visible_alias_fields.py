# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib

from odoo import fields, models


P1_ALIAS_LABELS = {
    'tender.bid': [
        '单据状态',
        '推送结果',
        '单据编号',
        '项目名称',
        '登记时间',
        '申请人',
        '申请日期',
        '金额',
        '备注',
        '附件',
        '录入人',
        '录入时间',
    ],
    'sc.financing.loan': [
        '单据状态',
        '单据编号',
        '项目名称',
        '借款人',
        '借款金额',
        '用途',
        '约定期限',
        '借款利息',
        '备注',
        '附件',
        '录入人',
        '录入时间',
        '还款金额',
        '借款利率',
        '利息',
        '还款时间',
        '贷款金额',
        '到期利息',
        '未还款金额',
        '贷款日期',
        '还款日期',
        '贷款天数',
        '年利率',
        '贷款账户',
        '贷款银行',
        '实际还款天数',
        '实际年利率',
        '贷款利息',
        '还款账户',
        '填写人',
    ],
    'payment.request': [
        '单据状态',
        '单据编号',
        '项目名称',
        '申请日期',
        '收款单位',
        '申请付款金额',
        '实际付款金额',
        '可用余额',
        '成本分类名称',
        '备注',
        '是否关联单据',
        '付款账号',
        '金额大写',
        '户名',
        '开户行',
        '账号',
        '填写人',
        '附件',
        '录入时间',
    ],
    'sc.tax.deduction.registration': [
        '单据状态',
        '单据编号',
        '是否转出',
        '项目名称',
        '开票单位',
        '发票号',
        '抵扣税额',
        '抵扣总额',
        '抵扣附加税',
        '备注',
        '录入人',
        '单据日期',
    ],
    'sc.payment.execution': [
        '推送结果',
        '金蝶单据编号',
        '单据编号',
        '项目名称',
        '供应商名称',
        '付款日期',
        '付款金额',
        '备注',
        '其它备注',
        '付款方式名称',
        '填写人',
        '开户行',
        '账户',
        '支付申请单号',
        '附件',
    ],
    'sc.fund.account.operation': [
        '单据状态',
        '项目名称',
        '发生时间',
        '账户号码',
        '转账类别',
        '事由',
        '备注',
        '附件',
        '录入人',
        '录入时间',
    ],
    'sc.receipt.income': [
        '单据状态',
        '单据编号',
        '时间',
        '项目名称',
        '本期收款',
        '本期代扣代缴合计',
        '本期拨付金额合计',
        '附件',
        '施工单位',
        '合同金额',
        '录入人',
        '录入时间',
    ],
    'sc.legacy.fund.confirmation.document': [
        '单据状态',
        '单据编号',
        '时间',
        '项目名称',
        '期数',
        '本期收款',
        '本期代扣代缴合计',
        '本期拨付金额合计',
        '附件',
        '施工单位',
        '合同金额',
        '目前形象进度',
        '累计开票金额',
        '上期留存余额',
        '录入人',
        '录入时间',
    ],
    'sc.legacy.fund.daily.snapshot.fact': [
        '单据状态',
        '单据编号',
        '单据日期',
        '当前账户余额',
        '当前账户银行余额',
        '银行系统差额',
        '账户往来',
        '备注',
    ],
    'sc.invoice.registration': [
        '开票状态',
        '合同编号',
        '项目名称',
        '单据编号',
        '申请人',
        '申请日期',
        '受票方名称',
        '累计开票金额',
        '本次开票金额',
        '附件',
        '备注',
        '录入人',
        '录入时间',
        '单据状态',
        '推送结果',
        '金蝶单据编号',
        '含税金额',
        '附加税',
        '发票号',
        '发票种类',
        '开票单位',
        '开票日期',
    ],
    'sc.receipt.invoice.line': [
        '项目名称',
        '经营方式',
        '往来单位',
        '合同编号',
        '单据编号',
        '发票号',
        '开票日期',
        '受票方名称',
        '开票单位',
        '发票金额',
        '附加税',
        '本次收款',
        '累计开票金额',
        '开票登记单号',
        '开票登记状态',
        '附件',
    ],
    'sc.fund.account': [
        '推送结果',
        '账户状态',
        '录入来源',
        '项目名称',
        '单据编号',
        '账号类型',
        '账号名称',
        '开户账号',
        '初期余额',
        '是否默认账号',
        '是否过渡账户',
        '排序号',
    ],
    'sc.material.purchase.request': [
        '单据状态',
        '合同编号',
        '标题',
        '供应商',
        '购货单位',
        '总金额',
        '已开票金额',
        '已付款金额',
        '未付款金额',
        '未开票金额',
        '项目名称',
        '税率',
        '附件',
        '录入人',
        '录入时间',
    ],
    'sc.material.inbound': [
        '单据状态',
        '单据日期',
        '供应商名称',
        '数量',
        '税率',
        '含税金额',
        '入库总数量',
        '付款状态',
        '已付款金额',
        '未付款金额',
        '结算状态',
        '已结算金额',
        '项目名称',
        '附件',
        '采购人',
        '录入人',
        '录入时间',
    ],
    'sc.material.settlement': [
        '单据状态',
        '项目名称',
        '单据编号',
        '标题',
        '结算单位',
        '付款状态',
        '已付款金额',
        '未付款金额',
        '支付申请状态',
        '已申请金额',
        '未申请金额',
        '结算说明',
        '附件',
        '录入人',
        '录入时间',
    ],
    'sc.labor.request': [
        '单据状态',
        '单据编号',
        '项目名称',
        '签订日期',
        '标题',
        '劳务单位',
        '施工队负责人',
        '总含税金额',
        '结算比例',
        '已开票金额',
        '已付款金额',
        '未付款金额',
        '未开票金额',
        '计价方式',
        '施工部位',
        '合同编号',
        '附件',
        '支付条款',
        '推送项目名称',
        '录入人',
    ],
    'sc.labor.usage': [
        '单据状态',
        '单据编号',
        '项目名称',
        '单据日期',
        '标题',
        '施工部位',
        '结算状态',
        '总金额',
        '备注',
        '附件',
        '录入人',
        '录入时间',
    ],
    'sc.labor.settlement': [
        '单据编号',
        '项目名称',
        '单据日期',
        '标题',
        '结算单位',
        '付款状态',
        '已付款金额',
        '未付款金额',
        '支付申请状态',
        '已申请金额',
        '未申请金额',
        '结算说明',
        '附件',
        '合同编号',
        '录入人',
        '录入时间',
    ],
    'sc.subcontract.register': [
        '单据编号',
        '签订时间',
        '标题',
        '分包内容',
        '总数量',
        '金额',
        '合同编号',
        '已开票金额',
        '已付款金额',
        '未付款金额',
        '未开票金额',
        '项目名称',
        '备注',
        '附件',
        '录入人',
        '录入时间',
    ],
    'sc.subcontract.request': [
        '单据状态',
        '单据编号',
        '项目名称',
        '标题',
        '分包商',
        '分包类型',
        '分包内容',
        '数量',
        '单价',
        '金额',
        '本月合价',
        '备注',
        '附件',
        '录入人',
        '录入时间',
    ],
    'sc.subcontract.settlement': [
        '项目名称',
        '单据编号',
        '标题',
        '结算单位',
        '付款状态',
        '已付款金额',
        '未付款金额',
        '支付申请状态',
        '已申请金额',
        '未申请金额',
        '合同编号',
        '起始结算日期',
        '终止结算日期',
        '结算说明',
        '附件',
        '录入人',
        '录入时间',
    ],
    'sc.equipment.request': [
        '单据状态',
        '单据编号',
        '合同编号',
        '项目名称',
        '合同标题',
        '租赁单位',
        '租赁内容',
        '总数量',
        '已开票金额',
        '已付款金额',
        '未付款金额',
        '未开票金额',
        '总金额',
        '签订时间',
        '经办人及电话',
        '税率',
        '增值税类型',
        '备注',
        '附件',
        '录入人',
        '录入时间',
    ],
    'sc.equipment.usage': [
        '单据状态',
        '项目名称',
        '单据编号',
        '单据日期',
        '租赁单位',
        '曾用名单',
        '机械名称',
        '规格型号',
        '单位',
        '工作时间',
        '单价',
        '金额',
        '附件',
        '备注',
        '录入人',
        '录入时间',
    ],
    'sc.equipment.settlement': [
        '单据状态',
        '单据编号',
        '项目名称',
        '单据日期',
        '结算单位',
        '结算内容',
        '总金额',
        '付款状态',
        '已付款金额',
        '未付款金额',
        '支付申请状态',
        '已申请金额',
        '未申请金额',
        '附件',
        '录入人',
        '录入时间',
    ],
    'sc.material.rental.order': [
        '单据编号',
        '合同编号',
        '项目名称',
        '合同标题',
        '租赁单位',
        '单据金额',
        '租赁内容',
        '总金额',
        '已开票金额',
        '已付款金额',
        '未付款金额',
        '未开票金额',
        '开户行',
        '银行账号',
        '开户人姓名',
        '附件',
        '签订时间',
        '单据状态',
        '单据日期',
        '使用单位名称',
        '材料名称',
        '规格型号',
        '数量',
        '单价',
        '租赁押金',
        '备注',
        '录入人',
        '录入时间',
    ],
    'sc.material.rental.settlement': [
        '单据状态',
        '项目名称',
        '单据编号',
        '结算单位',
        '附件',
        '录入人',
        '录入时间',
    ],
    'sc.construction.diary': [
        '单据状态',
        '项目名称',
        '单据编号',
        '日期',
        '施工部位',
        '出勤人数',
        '出勤机械',
        '温度',
        '上午气候',
        '下午气候',
        '当日施工内容',
        '操作负责人',
        '质量情况',
        '施工员',
        '备注',
        '附件',
        '录入人',
        '录入时间',
    ],
}

P1_ALIAS_COMPAT_LABELS = {
    # Existing databases may still validate old inherited views before the new
    # view XML removes these fields during module upgrade. Keep field definitions
    # for upgrade compatibility only; user-visible P1 contracts are driven by
    # P1_ALIAS_LABELS above.
    'tender.bid': [
        '收款账号',
        '开户行',
        '收款人',
        '付款方式',
    ],
    'sc.tax.deduction.registration': [
        '数量',
        '发票类型',
        '录入人',
        '录入时间',
        '扣款单位',
        '扣款金额',
        '扣款事由',
        '附件',
        '标题',
        '本次实缴数',
        '是否退回',
        '上缴内容',
        '本次计划已缴数',
        '本次退回数',
        '受票方名称',
        '交税类型',
        '金额',
        '发票开具日期',
        '预缴税款日期',
        '完税凭证号码',
        '受票单位',
        '实际开票单位',
        '价税合计',
        '税额',
        '不含税金额',
        '税率',
    ],
    'sc.receipt.income': [
        '期数',
        '目前形象进度',
        '累计开票金额',
        '上期留存余额',
    ],
    'sc.legacy.fund.daily.snapshot.fact': [
        '账号名称',
        '银行账号',
        '当日累计收入',
        '当日累计支出',
        '录入人',
        '录入时间',
    ],
    'sc.invoice.registration': [
        '状态',
        '交税类型',
        '金额',
        '不含税金额',
        '税额',
        '发票开具日期',
        '预缴税款日期',
        '完税凭证号码',
        '数据类型',
        '预计回款日期',
        '合同额',
        '本次开票张数',
        '开票张数',
        '关联回款金额',
    ],
    'sc.fund.account': [
        '账户操作',
        '账号户名',
        '录入人',
        '录入时间',
    ],
}


def _alias_field_name(label):
    return "p1_visible_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def _alias_field_string(label):
    return label


LABEL_SOURCE_OVERRIDES = {
    '单据状态': ['state', 'legacy_document_state', 'state_text', 'legacy_state'],
    '状态': ['state', 'legacy_document_state'],
    '开票状态': ['invoice_state', 'state'],
    '账户状态': ['state', 'active'],
    '付款状态': ['payment_state', 'state'],
    '结算状态': ['settlement_state', 'state'],
    '支付申请状态': ['payment_request_state', 'state'],
    '推送结果': ['push_result', 'sync_state', 'legacy_document_state', 'state'],
    '金蝶单据编号': ['kingdee_document_no', 'external_document_no', 'extra_ref', 'document_no', 'name'],
    '单据编号': ['document_no', 'name'],
    '合同编号': ['contract_no', 'contract_id', 'name', 'document_no'],
    '入库单号': ['name', 'document_no'],
    '申请单号': ['name'],
    '项目名称': ['project_id', 'legacy_project_name'],
    '推送项目名称': ['project_id', 'legacy_project_name'],
    '登记时间': ['source_created_at', 'created_time', 'document_date', 'create_date'],
    '录入时间': ['source_created_at', 'created_time'],
    '申请日期': ['request_date', 'date_request', 'document_date', 'create_date'],
    '付款日期': ['date_payment', 'payment_date', 'paid_at', 'document_date'],
    '发生时间': ['operation_date', 'operation_time', 'document_date', 'created_time'],
    '时间': ['date_receipt', 'receipt_date', 'document_date', 'created_time'],
    '单据日期': ['document_date', 'date_request', 'request_date', 'settlement_date', 'snapshot_date', 'date_diary', 'inbound_date', 'outbound_date'],
    '签订日期': ['sign_date', 'contract_date', 'request_date'],
    '签订时间': ['sign_date', 'contract_date', 'request_date'],
    '还款时间': ['repay_date', 'due_date', 'document_date'],
    '贷款日期': ['document_date'],
    '还款日期': ['due_date', 'document_date'],
    '预计回款日期': ['expected_receipt_date', 'due_date'],
    '开票日期': ['invoice_date', 'document_date'],
    '发票开具日期': ['invoice_date', 'document_date'],
    '预缴税款日期': ['prepaid_tax_date', 'document_date'],
    '起始结算日期': ['settlement_start_date', 'settlement_date'],
    '终止结算日期': ['settlement_end_date', 'settlement_date'],
    '日期': ['date_diary', 'document_date', 'report_period_start'],
    '录入人': ['source_created_by', 'creator_name', 'requester_id', 'owner_id', 'handler_name'],
    '填写人': ['source_created_by', 'creator_name', 'requester_id', 'owner_id', 'handler_name'],
    '借款人': ['partner_id', 'legacy_counterparty_name'],
    '约定期限': ['due_date'],
    '申请人': ['requester_id', 'source_created_by', 'creator_name'],
    '采购人': ['buyer_id', 'requester_id', 'source_created_by', 'creator_name'],
    '施工员': ['handler_name', 'source_created_by', 'creator_name'],
    '经办人及电话': ['owner_id', 'handler_name', 'source_created_by', 'creator_name'],
    '操作负责人': ['handler_name', 'project_manager', 'owner_id'],
    '收款单位': ['partner_id', 'receipt_partner_name', 'owner_id'],
    '供应商': ['supplier_id', 'selected_supplier_id', 'partner_id'],
    '供应商名称': ['supplier_id', 'partner_id'],
    '扣款单位': ['partner_id', 'partner_name'],
    '受票方名称': ['partner_id', 'legacy_partner_name'],
    '受票单位': ['partner_id', 'legacy_partner_name'],
    '开票单位': ['invoice_company_name', 'company_id', 'partner_id'],
    '实际开票单位': ['actual_invoice_company_name', 'partner_id'],
    '施工单位': ['construction_unit', 'partner_id'],
    '租赁单位': ['supplier_id', 'partner_id', 'owner_id', 'subcontractor_id'],
    '使用单位名称': ['receiver_id', 'project_id'],
    '劳务单位': ['contractor_id', 'partner_id'],
    '施工队负责人': ['owner_id', 'handler_name'],
    '分包商': ['suggested_subcontractor_id', 'subcontractor_id', 'partner_id'],
    '分包单位': ['subcontractor_id', 'partner_id'],
    '结算单位': ['settlement_unit_id', 'supplier_id', 'contractor_id', 'subcontractor_id', 'partner_id'],
    '购货单位': ['company_id', 'project_id'],
    '收款人': ['receipt_partner_name', 'partner_id'],
    '金额': ['amount', 'amount_total', 'paid_amount', 'invoice_amount_total'],
    '借款金额': ['amount'],
    '还款金额': ['repaid_amount', 'amount'],
    '贷款金额': ['amount'],
    '未还款金额': ['unpaid_amount', 'amount'],
    '申请付款金额': ['amount'],
    '实际付款金额': ['paid_amount_total', 'paid_amount', 'amount'],
    '可用余额': ['settlement_amount_payable', 'settlement_remaining_amount'],
    '付款金额': ['paid_amount', 'amount'],
    '本期收款': ['amount', 'received_amount'],
    '本期代扣代缴合计': ['deducted_invoice_amount', 'tax_amount'],
    '本期拨付金额合计': ['paid_amount', 'amount'],
    '合同金额': ['contract_amount_total', 'amount_total', 'amount'],
    '累计开票金额': ['invoice_amount', 'invoice_amount_total', 'amount_total'],
    '上期留存余额': ['remaining_amount', 'settlement_remaining_amount'],
    '当前账户余额': ['account_balance_total', 'account_balance', 'balance'],
    '当前账户银行余额': ['bank_balance_total', 'bank_balance', 'balance'],
    '银行系统差额': ['bank_system_difference', 'difference_amount'],
    '当日累计收入': ['daily_income', 'income_amount', 'amount_in'],
    '当日累计支出': ['daily_expense', 'expense_amount', 'amount_out'],
    '总金额': ['amount_total', 'amount'],
    '已开票金额': ['invoice_amount', 'invoiced_amount'],
    '已付款金额': ['paid_amount', 'paid_amount_total', 'amount'],
    '未付款金额': ['unpaid_amount', 'amount'],
    '未开票金额': ['uninvoiced_amount'],
    '含税金额': ['amount_total', 'invoice_amount_total'],
    '价税合计': ['invoice_amount_total', 'amount_total'],
    '税额': ['tax_amount', 'invoice_tax_amount'],
    '不含税金额': ['amount_untaxed', 'invoice_amount_untaxed'],
    '附加税': ['surcharge_amount', 'deduction_surcharge_amount', 'tax_amount'],
    '关联回款金额': ['received_amount', 'amount'],
    '开票张数': ['invoice_count'],
    '本次开票张数': ['invoice_count'],
    '本次开票金额': ['invoice_amount', 'amount'],
    '抵扣总额': ['deduction_amount'],
    '抵扣税额': ['deduction_tax_amount'],
    '扣款金额': ['deduction_amount', 'amount'],
    '本次实缴数': ['paid_amount', 'deduction_amount', 'amount'],
    '本次计划已缴数': ['planned_paid_amount', 'deduction_amount', 'amount'],
    '本次退回数': ['refund_amount', 'deduction_amount', 'amount'],
    '租赁押金': ['deposit_amount'],
    '单据金额': ['amount_total', 'amount'],
    '结算金额': ['amount_total'],
    '总含税金额': ['amount_total'],
    '结算比例': ['settlement_ratio'],
    '本月合价': ['amount_total', 'amount'],
    '总数量': ['quantity_total', 'quantity'],
    '数量': ['quantity', 'quantity_total'],
    '单价': ['price_unit'],
    '工作时间': ['work_hours', 'quantity'],
    '借款利息': ['interest_amount', 'rate_label'],
    '到期利息': ['interest_amount', 'rate_label'],
    '利息': ['interest_amount', 'rate_label'],
    '贷款利息': ['interest_amount', 'rate_label'],
    '年利率': ['rate_label'],
    '借款利率': ['rate_label'],
    '实际年利率': ['rate_label'],
    '税率': ['tax_rate', 'tax_rate_text'],
    '备注': ['note', 'purpose', 'description', 'legacy_note', 'remark'],
    '其它备注': ['note'],
    '用途': ['purpose', 'note'],
    '扣款事由': ['purpose', 'note'],
    '事由': ['reason', 'purpose', 'note'],
    '结算说明': ['note'],
    '标题': ['title', 'name'],
    '合同标题': ['title', 'name'],
    '租赁内容': ['description', 'note', 'line_ids'],
    '分包内容': ['subcontract_scope', 'description', 'note'],
    '施工部位': ['construction_part', 'usage_location', 'description'],
    '温度': ['temperature', 'weather'],
    '上午气候': ['morning_weather', 'weather'],
    '下午气候': ['afternoon_weather', 'weather'],
    '当日施工内容': ['description', 'header_description'],
    '质量情况': ['quality_name'],
    '曾用名单': ['legacy_note', 'description'],
    '机械名称': ['equipment_name', 'name'],
    '规格型号': ['material_spec_summary', 'material_spec', 'specification'],
    '单位': ['material_uom_summary', 'uom_id', 'product_uom_id'],
    '材料名称': ['material_name_summary', 'material_name', 'product_id'],
    '出勤人数': ['manpower_count'],
    '目前形象进度': ['progress_description', 'description'],
    '上缴内容': ['description', 'note'],
    '交税类型': ['tax_type', 'operation_strategy'],
    '发票类型': ['invoice_type', 'type'],
    '发票种类': ['invoice_type', 'type'],
    '付款方式': ['payment_method', 'legacy_receipt_type', 'receipt_type', 'type'],
    '付款方式名称': ['payment_method', 'legacy_receipt_type', 'receipt_type', 'type'],
    '转账类别': ['operation_type', 'type'],
    '账户往来': ['document_scope', 'source_family', 'operation_type', 'type'],
    '账户操作': ['operation_type', 'type'],
    '录入来源': ['source_origin', 'legacy_source_table'],
    '账号类型': ['account_type'],
    '开户账号': ['account_no', 'bank_account', 'payment_account_no', 'receipt_account_no'],
    '是否默认账号': ['is_default'],
    '是否过渡账户': ['fixed_account'],
    '初期余额': ['opening_balance'],
    '排序号': ['sequence'],
    '是否关联单据': ['settlement_id', 'contract_id'],
    '是否退回': ['is_refund', 'state'],
    '是否转出': ['is_transfer_out', 'state'],
    '计价方式': ['pricing_method', 'type'],
    '支付条款': ['payment_terms', 'note'],
    '完税凭证号码': ['tax_certificate_no', 'invoice_no'],
    '支付申请单号': ['payment_request_no', 'payment_request_id', 'document_no'],
    '发票号': ['invoice_no'],
    '发票号码': ['invoice_no'],
    '附件': ['attachment_ids', 'biz_attachment_ids', 'tech_attachment_ids', 'message_attachment_count', 'legacy_attachment_ref', 'legacy_attachment_name'],
    '收款账号': ['receipt_account_no', 'receipt_bank_account', 'bank_account_id'],
    '付款账号': ['payment_account_no', 'partner_bank_account', 'bank_account', 'bank_account_id'],
    '开户行': ['payment_bank_name', 'receipt_bank_name', 'partner_bank_name', 'bank_name'],
    '账户': ['bank_account', 'account_no', 'name'],
    '账号': ['account_no', 'payment_account_no', 'receipt_account_no', 'partner_bank_account'],
    '账户号码': ['account_no', 'bank_account', 'payment_account_no', 'receipt_account_no', 'fund_account_id', 'source_account_id', 'target_account_id'],
    '账号名称': ['name', 'account_name'],
    '账号户名': ['account_holder', 'payment_account_name', 'receipt_account_name'],
    '户名': ['payment_account_name', 'receipt_account_name', 'partner_account_name'],
    '银行账号': ['account_no', 'bank_account'],
    '开户人姓名': ['account_holder', 'payment_account_name', 'receipt_account_name'],
    '贷款账户': ['bank_account', 'account_no'],
    '贷款银行': ['bank_name'],
    '还款账户': ['bank_account', 'account_no'],
    '成本分类名称': ['cost_category_id', 'cost_type_id', 'cost_category_name'],
    '期数': ['period_no', 'report_period_start'],
    '实际还款天数': ['actual_days', 'due_date'],
    '贷款天数': ['loan_days', 'due_date'],
}

MODEL_LABEL_SOURCE_OVERRIDES = {
    'payment.request': {
        '单据状态': ['legacy_document_state', 'state'],
        '申请日期': ['date_request', 'request_date', 'document_date', 'create_date'],
        '实际付款金额': ['legacy_visible_actual_paid_amount', 'paid_amount_total', 'paid_amount', 'amount'],
        '可用余额': ['legacy_visible_available_balance', 'settlement_amount_payable', 'settlement_remaining_amount'],
        '是否关联单据': ['settlement_id', 'contract_id'],
        '付款账号': ['legacy_payment_account_no', 'payment_account_no', 'partner_bank_account', 'bank_account', 'bank_account_id'],
        '金额大写': ['legacy_visible_amount_uppercase', 'amount_uppercase'],
        '户名': ['legacy_payee_account_name', 'payment_account_name', 'partner_account_name'],
        '开户行': ['legacy_payee_bank_name', 'payment_bank_name', 'partner_bank_name', 'bank_name'],
        '账号': ['legacy_payee_account_no', 'account_no', 'payment_account_no', 'partner_bank_account'],
        '附件': ['attachment_ids'],
        '成本分类名称': ['legacy_visible_cost_category_name', 'cost_category_id', 'cost_type_id', 'cost_category_name'],
        '备注': ['legacy_visible_remark', 'note'],
    },
    'sc.invoice.registration': {
        '状态': ['legacy_document_state', 'state'],
        '推送结果': ['push_result', 'legacy_document_state', 'state'],
        '金蝶单据编号': ['kingdee_document_no', 'document_no', 'name'],
        '预计回款日期': ['expected_receipt_date'],
        '申请人': ['applicant_name', 'creator_name', 'source_created_by'],
        '受票方名称': ['partner_id', 'legacy_partner_name'],
        '交税类型': ['tax_type', 'invoice_content', 'operation_strategy'],
        '数据类型': ['source_kind'],
        '金额': ['amount_total'],
        '发票开具日期': ['invoice_date', 'document_date'],
        '预缴税款日期': ['prepaid_tax_date', 'document_date'],
        '完税凭证号码': ['tax_certificate_no', 'invoice_no'],
        '含税金额': ['amount_total'],
        '不含税金额': ['amount_no_tax'],
        '税额': ['tax_amount'],
        '附加税': ['surcharge_amount'],
        '税率': ['tax_rate'],
        '关联回款金额': ['related_receipt_amount'],
        '累计开票金额': ['amount_total'],
        '本次开票金额': ['amount_total'],
        '合同额': ['contract_amount'],
        '本次开票张数': ['invoice_count'],
        '开票张数': ['invoice_count'],
        '发票号': ['invoice_no'],
        '发票种类': ['invoice_type'],
        '开票单位': ['invoice_issue_company'],
        '开票日期': ['invoice_date'],
    },
    'sc.legacy.fund.confirmation.document': {
        '单据状态': ['document_state'],
        '单据编号': ['document_no'],
        '时间': ['receipt_time'],
        '项目名称': ['project_name'],
        '期数': ['period_no'],
        '本期收款': ['actual_fund_amount'],
        '本期代扣代缴合计': ['deducted_amount_total'],
        '本期拨付金额合计': ['paid_amount_total'],
        '施工单位': ['construction_unit_name'],
        '合同金额': ['contract_amount'],
        '目前形象进度': ['current_project_stage'],
        '累计开票金额': ['accumulated_invoice_amount'],
        '上期留存余额': ['previous_retained_balance'],
        '录入人': ['creator_name'],
        '录入时间': ['created_time'],
    },
    'sc.receipt.invoice.line': {
        '单据编号': ['source_document_no', 'invoice_document_no', 'request_id'],
        '发票号': ['invoice_no'],
        '发票号码': ['invoice_no'],
        '开票日期': ['invoice_date'],
        '受票方名称': ['invoice_party_name', 'partner_id'],
        '开票抬头': ['invoice_party_name', 'partner_id'],
        '开票单位': ['invoice_issue_company'],
        '开票方': ['invoice_issue_company'],
        '发票金额': ['invoice_amount'],
        '含税金额': ['invoice_amount'],
        '附加税': ['surcharge_amount'],
        '本次收款': ['current_receipt_amount'],
        '累计开票金额': ['invoiced_before_amount'],
        '开票登记单号': ['invoice_document_no'],
        '开票登记状态': ['invoice_document_state'],
        '来源表名': ['source_table_name'],
    },
    'sc.tax.deduction.registration': {
        '单据状态': ['legacy_document_state', 'state'],
        '单据编号': ['document_no', 'name'],
        '是否转出': ['is_transfer_out'],
        '项目名称': ['project_id'],
        '开票单位': ['partner_id', 'partner_name'],
        '发票号': ['invoice_no'],
        '抵扣税额': ['deduction_tax_amount'],
        '抵扣总额': ['deduction_amount', 'invoice_amount_total'],
        '抵扣附加税': ['deduction_surcharge_amount'],
        '备注': ['note'],
        '录入人': ['creator_name', 'source_created_by'],
        '单据日期': ['document_date'],
    },
    'sc.material.inbound': {
        '数量': ['total_qty'],
        '入库总数量': ['total_qty'],
        '含税金额': ['amount_total'],
    },
    'sc.payment.execution': {
        '付款方式名称': ['payment_family', 'payment_method'],
    },
}


PAYMENT_REQUEST_DOCUMENT_STATE_LABELS = {
    "-1": "已作废",
    "0": "未审核",
    "1": "审核中",
    "2": "已审核",
}

TAX_DEDUCTION_DOCUMENT_STATE_LABELS = {
    "-1": "已作废",
    "0": "未审核",
    "1": "审核中",
    "2": "审核通过",
}

INVOICE_DOCUMENT_STATE_LABELS = {
    "-1": "已作废",
    "0": "未审核",
    "1": "审核中",
    "2": "审核通过",
}

FALLBACK_SOURCES = (
    "name", "document_no", "title", "project_id", "partner_id", "supplier_id", "contractor_id",
    "subcontractor_id", "owner_id", "requester_id", "state", "legacy_document_state",
    "document_date", "request_date", "date_request", "settlement_date", "invoice_date",
    "amount", "amount_total", "paid_amount", "unpaid_amount", "note", "purpose",
    "source_created_by", "source_created_at", "creator_name", "created_time",
)


def _format_alias_value(record, field_name):
    field = record._fields.get(field_name)
    if not field:
        return ""
    value = record[field_name]
    if not value and value not in (0, 0.0):
        return ""
    if field.type == "many2one":
        return value.display_name or ""
    if field.type == "many2many" and field.comodel_name == "ir.attachment":
        items = []
        for attachment in value:
            label = str(attachment.name or attachment.display_name or attachment.id).strip()
            if not label:
                continue
            url = attachment.url or f"/web/content/{attachment.id}?download=true"
            label = f"{label} | {url}"
            items.append(label)
        return " ".join(items)
    if field.type in ("one2many", "many2many") or field_name == "message_attachment_count":
        return "有" if value else ""
    if field.type == "selection":
        selection = field.selection
        if callable(selection):
            selection = selection(record)
        return dict(selection or []).get(value, value) or ""
    if field.type == "boolean":
        return "是" if value else "否"
    text = str(value).strip()
    return "" if text in {"False", "false", "None", "NULL"} else text


def _legacy_attachment_links(record):
    attachment_ref = _format_alias_value(record, 'legacy_attachment_ref')
    if not attachment_ref:
        attachment_ref = _format_alias_value(record, 'attachment_ref')
    if not attachment_ref or 'sc.legacy.file.index' not in record.env:
        return ""
    files = record.env['sc.legacy.file.index'].sudo().search([
        ('active', '=', True),
        ('bill_id', '=', attachment_ref),
    ], order='upload_time, id')
    if not files:
        return "历史附件"
    lines = []
    seen = set()
    for item in files:
        name = str(item.file_name or item.display_name or item.legacy_file_id or "").strip()
        path = str(item.file_path or item.preview_path or "").strip()
        if path:
            url = "legacy-file://" + path.lstrip("/")
        else:
            url = "legacy-file-id://" + str(item.legacy_file_id or item.id).strip()
        key = (name, url)
        if not name or key in seen:
            continue
        seen.add(key)
        lines.append(f"{name} | {url}")
    return " ".join(lines) if lines else "历史附件"


def _alias_value(record, label):
    if record._name == 'payment.request' and label == '单据状态':
        legacy_state = _format_alias_value(record, 'legacy_document_state')
        if legacy_state:
            return PAYMENT_REQUEST_DOCUMENT_STATE_LABELS.get(legacy_state, legacy_state)
    if record._name == 'payment.request' and label == '是否关联单据':
        return "是" if record.settlement_id or record.contract_id or record.outflow_line_ids else "否"
    if record._name == 'sc.invoice.registration' and label in ('状态', '单据状态'):
        legacy_state = _format_alias_value(record, 'legacy_document_state')
        if legacy_state:
            return INVOICE_DOCUMENT_STATE_LABELS.get(legacy_state, legacy_state)
    if record._name == 'sc.invoice.registration' and label == '附件':
        legacy_links = _legacy_attachment_links(record)
        if legacy_links:
            return legacy_links
        for field_name in ('attachment_ids', 'biz_attachment_ids', 'tech_attachment_ids', 'legacy_attachment_name'):
            value = _format_alias_value(record, field_name)
            if value:
                return value
        return ""
    if record._name == 'sc.legacy.fund.confirmation.document' and label == '附件':
        legacy_links = _legacy_attachment_links(record)
        if legacy_links:
            return legacy_links
        return _format_alias_value(record, 'attachment_links')
    if record._name == 'sc.tax.deduction.registration' and label == '单据状态':
        legacy_state = _format_alias_value(record, 'legacy_document_state')
        if legacy_state:
            return TAX_DEDUCTION_DOCUMENT_STATE_LABELS.get(legacy_state, legacy_state)
    if record._name == 'sc.tax.deduction.registration' and label == '是否转出':
        return _format_alias_value(record, 'is_transfer_out') if 'is_transfer_out' in record._fields else "否"
    model_sources = MODEL_LABEL_SOURCE_OVERRIDES.get(record._name, {}).get(label)
    if model_sources is not None:
        for field_name in model_sources:
            value = _format_alias_value(record, field_name)
            if value:
                return value
        return ""
    for field_name, field in record._fields.items():
        if field.string == label and not field_name.startswith("p1_visible_"):
            value = _format_alias_value(record, field_name)
            if value:
                return value
    for field_name in LABEL_SOURCE_OVERRIDES.get(label, ()):
        value = _format_alias_value(record, field_name)
        if value:
            return value
    for field_name in FALLBACK_SOURCES:
        value = _format_alias_value(record, field_name)
        if value:
            return value
    return ""


def _compute_p1_daily_business_visible_aliases(self):
    labels = list(dict.fromkeys(
        list(P1_ALIAS_LABELS.get(self._name, ())) + P1_ALIAS_COMPAT_LABELS.get(self._name, [])
    ))
    field_pairs = [(_alias_field_name(label), label) for label in labels]
    for record in self:
        for field_name, label in field_pairs:
            record[field_name] = _alias_value(record, label)


_ALIAS_MODEL_FIELD_LABELS = {
    _model_name: list(dict.fromkeys(list(_labels) + P1_ALIAS_COMPAT_LABELS.get(_model_name, [])))
    for _model_name, _labels in P1_ALIAS_LABELS.items()
}


for _index, (_model_name, _labels) in enumerate(_ALIAS_MODEL_FIELD_LABELS.items(), start=1):
    _attrs = {
        "__module__": __name__,
        "_inherit": _model_name,
        "_compute_p1_daily_business_visible_aliases": _compute_p1_daily_business_visible_aliases,
    }
    for _label in _labels:
        _attrs[_alias_field_name(_label)] = fields.Char(
            string=_alias_field_string(_label),
            compute="_compute_p1_daily_business_visible_aliases",
            readonly=True,
        )
    globals()[f"P1DailyBusinessVisibleAlias{_index}"] = type(
        f"P1DailyBusinessVisibleAlias{_index}",
        (models.Model,),
        _attrs,
    )
