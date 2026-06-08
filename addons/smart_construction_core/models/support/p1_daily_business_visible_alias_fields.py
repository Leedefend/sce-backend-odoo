# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from odoo import api, fields, models


HEX_NAME_RE = re.compile(r"^[0-9a-fA-F]{24,64}(?:\.[A-Za-z0-9]{1,8})?$")
_LEGACY_VISIBLE_ALIAS_PAYLOAD_CACHE = {}
_USER_ACCEPTANCE_VISIBLE_CACHE = {}


P1_ALIAS_LABELS = {'tender.bid': ['单据状态', '推送结果', '单据编号', '项目名称', '登记时间', '申请人', '申请日期', '金额', '备注', '附件', '录入人', '录入时间', '开标时间'],
 'tender.doc.purchase': ['单据状态',
                         '项目名称',
                         '单据编号',
                         '申请人',
                         '申请日期',
                         '收款账号',
                         '开户行',
                         '金额',
                         '备注',
                         '收款人',
                         '付款方式',
                         '附件',
                         '录入人',
                         '录入时间'],
 'sc.financing.loan': ['单据状态',
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
                       '申请部门',
                       '申请时间',
                       '申请人',
                       '是否预算内',
                       '实际借款金额',
                       '主要资金使用安排',
                       '收款人',
                       '收款账户',
                       '开户银行',
                       '公司名称',
                       '付款单位',
                       '收款单位',
                       '往来单位名称',
                       '往来单位账户',
                       '借款账号',
                       '实际批复金额',
                       '申请金额',
                       '预计归还时间',
                       '借款类型'],
 'payment.request': ['单据状态',
                     '单据编号',
                     '项目名称',
                     '申请日期',
                     '收款单位',
                     '实际收款单位',
                     '付款单位',
                     '申请付款金额',
                     '实际付款金额',
                     '可用余额',
                     '成本分类名称',
                     '类型（成本）',
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
                     '申请人',
                     '收款账号',
                     '金额',
                     '收款人',
                     '付款方式',
                     '录入人'],
 'sc.tax.deduction.registration': ['单据状态',
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
                                   '扣款单位',
                                   '扣款金额',
                                   '扣款事由',
                                   '附件',
                                   '录入时间',
                                   '标题',
                                   '本次实缴数',
                                   '是否退回',
                                   '上缴内容',
                                   '本次计划已缴数',
                                   '本次退回数'],
 'sc.payment.execution': ['推送结果',
                          '金蝶单据编号',
                          '单据编号',
                          '项目名称',
                          '供应商名称',
                          '付款日期',
                          '付款金额',
                          '收款单位',
                          '实际收款单位',
                          '支付类别',
                          '付款内容',
                          '备注',
                          '其它备注',
                          '付款方式名称',
                          '类型（成本）',
                          '填写人',
                          '开户行',
                          '账户',
                          '支付申请单号',
                          '附件',
                          '单据状态',
                          '項目名称',
                          '其他备注',
                          '付款账户',
                          '付款账户名称',
                          '凭证号',
                          '录入人',
                          '付款单关联来源',
                          '录入日期'],
 'sc.fund.account.operation': ['单据状态',
                               '项目名称',
                               '发生时间',
                               '账户号码',
                               '转账类别',
                               '事由',
                               '备注',
                               '附件',
                               '录入人',
                               '录入时间',
                               '单据编号',
                               '收款账户',
                               '金额'],
 'sc.receipt.income': ['单据状态',
                       '单据编号',
                       '时间',
                       '项目名称',
                       '往来单位',
                       '承包单位',
                       '施工管理合同',
                       '本期收款',
                       '本期代扣代缴合计',
                       '本期拨付金额合计',
                       '附件',
                       '施工单位',
                       '合同金额',
                       '录入人',
                       '录入时间',
                       '填写人',
                       '收款账户',
                       '进账金额',
                       '收入类别',
                       '收款时间',
                       '备注'],
 'sc.legacy.fund.confirmation.document': ['单据状态',
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
                                          '录入时间'],
 'sc.legacy.fund.daily.snapshot.fact': ['单据状态', '单据编号', '单据日期', '当前账户余额', '当前账户银行余额', '银行系统差额', '账户往来', '备注'],
 'sc.invoice.registration': ['开票状态',
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
                             '状态',
                             '预计回款日期',
                             '合同额',
                             '本次开票张数',
                             '税额',
                             '不含税金额',
                             '开票张数',
                             '税率',
                             '关联回款金额',
                             '受票单位',
                             '实开总金额',
                             '发票号码',
                             '交税类型',
                             '金额',
                             '发票开具日期',
                             '预缴税款日期',
                             '完税凭证号码',
                             '口径',
                             '价税合计',
                             '实际开票单位',
                             '数量',
                             '发票类型',
                             '发票备注'],
 'sc.receipt.invoice.line': ['项目名称',
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
                             '附件'],
 'sc.fund.account': ['推送结果', '账户状态', '录入来源', '项目名称', '单据编号', '账号类型', '账号名称', '开户账号', '初期余额', '是否默认账号', '是否过渡账户', '排序号'],
 'sc.material.purchase.request': ['单据状态',
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
                                  '录入时间'],
 'sc.material.inbound': ['单据状态',
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
                         '录入时间'],
 'sc.material.settlement': ['单据状态',
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
                            '录入时间'],
 'sc.labor.request': ['单据状态',
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
                      '录入人'],
 'sc.labor.usage': ['单据状态', '单据编号', '项目名称', '单据日期', '标题', '施工部位', '结算状态', '总金额', '备注', '附件', '录入人', '录入时间'],
 'sc.labor.settlement': ['单据编号',
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
                         '录入时间'],
 'sc.subcontract.register': ['单据编号',
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
                             '录入时间'],
 'sc.subcontract.request': ['单据状态',
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
                            '录入时间'],
 'sc.subcontract.settlement': ['项目名称',
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
                               '录入时间'],
 'sc.equipment.request': ['单据状态',
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
                          '录入时间'],
 'sc.equipment.usage': ['单据状态',
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
                        '录入时间'],
 'sc.equipment.settlement': ['单据状态',
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
                             '录入时间'],
 'sc.material.rental.order': ['单据编号',
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
                              '录入时间'],
 'sc.material.rental.settlement': ['单据状态', '项目名称', '单据编号', '结算单位', '附件', '录入人', '录入时间'],
 'sc.construction.diary': ['单据状态',
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
                           '录入时间'],
 'sc.business.entity': ['单据状态',
                        '推送结果',
                        '项目名称',
                        '单位编号',
                        '合作类型',
                        '单位名称',
                        '开户银行',
                        '账号',
                        '统一社会信用代码',
                        '主税率',
                        '录入人',
                        '录入时间',
                        '收款金额',
                        '付款金额',
                        '开户姓名',
                        '开户账号',
                        '银行账号'],
 'construction.contract': ['单据状态',
                           '单据编号',
                           '合同订立日期',
                           '原件是否归档',
                           '发包人',
                           '项目名称',
                           '合同标题',
                           '工程类别',
                           '合同编号',
                           '合同金额',
                           '结算金额',
                           '累计开票',
                           '累计收款',
                           '未收款',
                           '未收款比例',
                           '挂靠人',
                           '工程地址',
                           '工程内容',
                           '录入人',
                           '录入时间',
                           '附件'],
 'sc.document.admin.document': ['单据状态',
                                '项目名称',
                                '资料类型',
                                '资料说明',
                                '证照名称',
                                '编号',
                                '持有人',
                                '有效期',
                                '录入人',
                                '备注',
                                '录入时间',
                                '单据编号',
                                '借阅项目名称',
                                '证件名称',
                                '申请日期',
                                '借阅部门或项目部名称',
                                '借阅人',
                                '联系方式',
                                '借阅形式',
                                '借阅日期',
                                '负责人',
                                '归还申请日期',
                                '申请归还时间',
                                '是否归还',
                                '确认归还时间',
                                '归还日期',
                                '附件',
                                '修改人',
                                '修改日期',
                                '修改备注',
                                '审定人',
                                '审定时间',
                                '审定意见'],
 'sc.office.admin.document': ['单据状态',
                              '单据编号',
                              '项目名称',
                              '申请人姓名',
                              '所在部门',
                              '请假天数',
                              '请假类型',
                              '请假时间',
                              '销假时间',
                              '备注',
                              '请假时长',
                              '录入人',
                              '录入时间',
                              '用印时间',
                              '用印部门',
                              '用印申请人',
                              '用印部门负责人签字',
                              '用印种类',
                              '用印文本名称及文号',
                              '经办人签字',
                              '领导签字',
                              '份数',
                              '归还时间',
                              '合同金额',
                              '合同编号',
                              '所属公司',
                              '使用印章公司',
                              '是否外带',
                              '附件'],
 'sc.legacy.user.profile': ['操作',
                            '姓名',
                            '用户名',
                            '部门',
                            '职务',
                            '岗位',
                            '电话号码',
                            '性别',
                            '账号类型',
                            '是否测试账号',
                            '证件类型',
                            '证件号',
                            '居住地址',
                            '是否购买社保',
                            '员工工号',
                            '出生日期',
                            '政治面貌',
                            '民族',
                            '籍贯',
                            '毕业院校',
                            '毕业时间',
                            '所学专业',
                            '学历',
                            '入职日期',
                            '人员类型',
                            '录入人',
                            '录入时间'],
 'sc.hr.payroll.document': ['单据编号',
                            '单据日期',
                            '姓名',
                            '人员类型',
                            '身份证号码',
                            '联系方式',
                            '证书费用',
                            '个人证书',
                            '社保基数',
                            '社保购买单位',
                            '人员状态',
                            '备注',
                            '录入人',
                            '录入时间',
                            '单据状态',
                            '类型',
                            '购买人数',
                            '年度',
                            '月份',
                            '缴费金额',
                            '登记人',
                            '登记时间',
                            '标题',
                            '年份',
                            '部门',
                            '发放单位',
                            '应发工资',
                            '实发工资',
                            '发放人数',
                            '附件',
                            '财务支出登记状态',
                            '状态',
                            '项目名称',
                            '补助事由',
                            '补助人',
                            '补助金额',
                            '部门岗位',
                            '奖金金额',
                            '奖金事由'],
 'tender.guarantee': ['状态',
                      '单据编号',
                      '投标项目名称',
                      '项目名称',
                      '所属公司',
                      '金额',
                      '已退保证金金额',
                      '转款单位',
                      '汇款方式',
                      '保证金类型',
                      '收款账户',
                      '收款账户名称',
                      '备注',
                      '附件',
                      '录入人',
                      '录入时间',
                      '收保证金单号',
                      '退还金额',
                      '退还账号',
                      '退还开户行',
                      '单位',
                      '收款开户行',
                      '收款账号',
                      '推送结果',
                      '金蝶单据编号',
                      '投标项目',
                      '工程项目',
                      '保证金金额',
                      '已退金额',
                      '未退金额',
                      '是否需要退回',
                      '收款单位',
                      '支付账户',
                      '退回单编号',
                      '退回项目',
                      '退回金额',
                      '退回账户',
                      '退回日期'],
 'sc.expense.claim': ['单据状态',
                      '单据编号',
                      '项目名称',
                      '所属公司',
                      '日期',
                      '单据日期',
                      '部门',
                      '报销人',
                      '报销种类',
                      '报销类别',
                      '事项说明',
                      '报销金额',
                      '付款状态',
                      '已付款金额',
                      '未付款金额',
                      '付款方式',
                      '借款人',
                      '借款金额',
                      '还款金额',
                      '用途',
                      '借款利率',
                      '利息',
                      '还款时间',
                      '标题',
                      '本次实缴数',
                      '是否退回',
                      '上缴内容',
                      '本次计划已缴数',
                      '本次退回数',
                      '收款人',
                      '附件',
                      '录入人',
                      '录入时间',
                      '推送结果',
                      '付款时间',
                      '付款金额',
                      '成本类别',
                      '收款单位名称',
                      '付款账户名称',
                      '备注'],
 'sc.legacy.fund.daily.line': ['单据状态',
                               '单据编号',
                               '单据日期',
                               '账号名称',
                               '银行账号',
                               '当前账户余额',
                               '当前账户银行余额',
                               '银行系统差额',
                               '当日累计收入',
                               '当日累计支出',
                               '账户往来',
                               '备注',
                               '录入人',
                               '录入时间'],
 'sc.legacy.invoice.tax.fact': ['状态',
                                '推送结果',
                                '金蝶单据编号',
                                '发票公司类型',
                                '单据编号',
                                '项目名称',
                                '发票开具日期',
                                '开票单位',
                                '发票提供人/单位',
                                '价税合计',
                                '税额',
                                '不含税金额',
                                '发票号码',
                                '发票类型',
                                '附件',
                                '录入人',
                                '发票备注',
                                '录入时间'],
 'sc.legacy.payment.residual.fact': ['单据状态',
                                     '单据编号',
                                     '项目名称',
                                     '纳税人名称',
                                     '纳税人识别号',
                                     '经办人手机',
                                     '区域涉税事项联系人',
                                     '区域涉税事项联系人座机手机',
                                     '跨区域经营地址',
                                     '经营方式',
                                     '合同名称',
                                     '合同金额',
                                     '合同开始日期',
                                     '合同结束日期',
                                     '合同相对方名称',
                                     '合同相对方名称编号',
                                     '跨区域涉税事项报验管理编号',
                                     '附件',
                                     '录入人',
                                     '录入时间']}

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
        '口径',
        '价税合计',
        '实际开票单位',
        '数量',
        '发票类型',
        '发票备注',
        '发票号码',
        '受票单位',
        '开票单位',
        '备注',
        '附件',
        '录入人',
        '录入时间',
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
    '支付申请单号': ['legacy_visible_request_no', 'payment_request_no', 'payment_request_id', 'document_no'],
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
    'sc.receipt.income': {
        '单据状态': ['legacy_document_state_label', 'legacy_document_state', 'state'],
        '项目名称': ['legacy_project_name', 'legacy_visible_project_name', 'project_id'],
        '单据编号': ['document_no', 'name'],
        '往来单位': ['legacy_partner_name', 'partner_id'],
        '承包单位': ['legacy_company_name', 'company_id'],
        '施工管理合同': ['legacy_contract_no', 'contract_id'],
        '填写人': ['creator_name'],
        '收款账户': ['receiving_account_name', 'receiving_account', 'receiving_account_no'],
        '进账金额': ['amount'],
        '收入类别': ['income_category', 'legacy_receipt_subtype'],
        '收款时间': ['date_receipt'],
        '备注': ['note'],
        '附件': ['attachment_ids', 'legacy_attachment_ref'],
        '录入人': ['creator_name'],
        '录入时间': ['created_time'],
    },
    'payment.request': {
        '单据状态': ['legacy_document_state', 'state'],
        '单据编号': ['legacy_visible_document_no', 'document_no', 'name'],
        '项目名称': ['legacy_visible_project_name', 'project_id'],
        '申请日期': ['legacy_visible_request_date', 'date_request', 'request_date', 'document_date', 'create_date'],
        '收款单位': ['legacy_visible_payee_unit', 'partner_id', 'receipt_partner_name', 'owner_id'],
        '实际收款单位': ['actual_payee_unit', 'legacy_visible_actual_payee_unit'],
        '付款单位': ['payer_unit', 'legacy_visible_payer_unit', 'legacy_payment_account_name'],
        '申请付款金额': ['legacy_visible_request_amount', 'amount'],
        '实际付款金额': ['legacy_visible_actual_paid_amount', 'paid_amount_total', 'paid_amount', 'amount'],
        '可用余额': ['legacy_visible_available_balance', 'settlement_amount_payable', 'settlement_remaining_amount'],
        '是否关联单据': ['settlement_id', 'contract_id'],
        '付款账号': ['payment_account_no', 'legacy_payment_account_no', 'partner_bank_account', 'bank_account', 'bank_account_id'],
        '金额大写': ['accepted_amount_uppercase', 'legacy_visible_amount_uppercase', 'amount_uppercase'],
        '户名': ['payment_account_name', 'legacy_payee_account_name', 'partner_account_name'],
        '开户行': ['payment_bank_name', 'legacy_payee_bank_name', 'partner_bank_name', 'bank_name'],
        '账号': ['payment_account_no', 'legacy_payee_account_no', 'account_no', 'partner_bank_account'],
        '附件': ['attachment_ids'],
        '成本分类名称': ['legacy_visible_cost_category_name', 'cost_category_id', 'cost_type_id', 'cost_category_name'],
        '类型（成本）': ['legacy_visible_cost_type', 'legacy_visible_cost_category_name', 'cost_category_name'],
        '备注': ['legacy_visible_remark', 'note'],
        '填写人': ['legacy_visible_writer', 'creator_name'],
        '录入人': ['legacy_visible_writer', 'creator_name'],
        '录入时间': ['created_time'],
    },
    'tender.doc.purchase': {
        '单据状态': ['state'],
        '项目名称': ['legacy_visible_project_name', 'project_id'],
        '单据编号': ['invoice_no', 'legacy_record_id'],
        '申请人': ['applicant_id', 'legacy_source_created_by'],
        '申请日期': ['apply_date'],
        '收款账号': ['receipt_bank_account'],
        '开户行': ['receipt_bank_name'],
        '金额': ['amount'],
        '备注': ['remark'],
        '收款人': ['receipt_payee_name', 'receipt_partner_name'],
        '付款方式': ['payment_method'],
        '附件': ['attachment_ids', 'legacy_attachment_ref'],
        '录入人': ['legacy_source_created_by'],
        '录入时间': ['legacy_source_created_at'],
    },
    'sc.expense.claim': {
        '单据状态': ['legacy_document_state', 'state'],
        '单据编号': ['legacy_document_no', 'name'],
        '项目名称': ['legacy_visible_project_name', 'project_id'],
        '所属公司': ['company_id', 'company_name_text'],
        '日期': ['date_claim', 'fill_date'],
        '单据日期': ['date_claim', 'fill_date'],
        '部门': ['department_name', 'legacy_visible_department'],
        '报销人': ['applicant_name', 'payee'],
        '报销种类': ['expense_type', 'claim_type'],
        '报销类别': ['expense_type', 'claim_type'],
        '事项说明': ['summary', 'note'],
        '报销金额': ['amount', 'approved_amount'],
        '付款状态': ['payment_state', 'state'],
        '已付款金额': ['paid_amount', 'approved_amount'],
        '未付款金额': ['unpaid_amount', 'amount'],
        '付款方式': ['payment_method'],
        '借款人': ['legacy_visible_borrower', 'applicant_name', 'payee'],
        '借款金额': ['legacy_visible_loan_amount', 'amount', 'approved_amount'],
        '还款金额': ['legacy_visible_repayment_amount', 'amount', 'approved_amount'],
        '用途': ['summary', 'expense_type', 'note'],
        '借款利率': ['legacy_visible_loan_rate', 'note'],
        '利息': ['legacy_visible_interest', 'note'],
        '还款时间': ['legacy_visible_repayment_time', 'date_claim', 'fill_date'],
        '付款时间': ['legacy_visible_payment_time', 'date_claim', 'fill_date'],
        '标题': ['legacy_visible_title', 'summary', 'expense_type'],
        '本次实缴数': ['amount', 'approved_amount'],
        '是否退回': ['is_returned', 'legacy_visible_returned_flag', 'claim_type'],
        '上缴内容': ['legacy_visible_adjustment_item', 'summary', 'expense_type'],
        '本次计划已缴数': ['amount', 'approved_amount'],
        '本次退回数': ['amount', 'approved_amount'],
        '收款人': ['payee', 'receipt_account_name'],
        '推送结果': ['legacy_visible_push_result'],
        '付款金额': ['amount', 'approved_amount'],
        '成本类别': ['legacy_visible_expense_type', 'expense_type'],
        '收款单位名称': ['payee', 'partner_id'],
        '付款账户名称': ['payment_account_name'],
        '附件': ['attachment_ids', 'legacy_attachment_ref'],
        '录入人': ['creator_name', 'applicant_name'],
        '录入时间': ['created_time'],
        '备注': ['legacy_visible_note', 'summary', 'note'],
    },
    'sc.invoice.registration': {
        '状态': ['state', 'legacy_document_state'],
        '单据状态': ['state', 'legacy_document_state'],
        '单据编号': ['document_no', 'name'],
        '推送结果': ['push_result', 'legacy_document_state', 'state'],
        '金蝶单据编号': ['kingdee_document_no', 'document_no', 'name'],
        '项目名称': ['legacy_visible_project_name', 'project_id'],
        '预计回款日期': ['expected_receipt_date'],
        '申请人': ['applicant_name', 'creator_name', 'source_created_by'],
        '申请日期': ['application_date', 'document_date', 'legacy_visible_application_date'],
        '受票单位': ['recipient_unit_name', 'partner_id', 'legacy_visible_partner_name', 'legacy_partner_name'],
        '受票方名称': ['recipient_unit_name', 'partner_id', 'legacy_visible_partner_name', 'legacy_partner_name'],
        '交税类型': ['tax_type', 'invoice_content', 'operation_strategy'],
        '数据类型': ['caliber', 'legacy_visible_data_type', 'source_kind'],
        '口径': ['caliber', 'legacy_visible_data_type', 'source_kind'],
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
        '本次开票金额': ['actual_invoice_amount', 'amount_total'],
        '实开总金额': ['actual_invoice_amount', 'amount_total'],
        '合同额': ['contract_amount'],
        '本次开票张数': ['invoice_count'],
        '开票张数': ['invoice_count'],
        '数量': ['invoice_count'],
        '发票号': ['invoice_no'],
        '发票种类': ['invoice_type'],
        '开票单位': ['invoice_issue_company'],
        '实际开票单位': ['actual_invoice_issue_company', 'invoice_issue_company', 'legacy_visible_invoice_issue_company'],
        '开票状态': ['invoice_state', 'state', 'legacy_visible_invoice_state'],
        '合同编号': ['contract_id', 'legacy_visible_contract_no'],
        '开票日期': ['invoice_date'],
        '附件': ['attachment_ids', 'legacy_attachment_ref'],
        '录入人': ['creator_name'],
        '录入时间': ['created_time'],
    },
    'sc.legacy.invoice.tax.fact': {
        '状态': ['legacy_state'],
        '单据状态': ['legacy_state'],
        '单据编号': ['document_no'],
        '项目名称': ['legacy_project_name', 'project_id'],
        '发票开具日期': ['document_date'],
        '开票单位': ['legacy_partner_name'],
        '发票提供人/单位': ['legacy_partner_name'],
        '价税合计': ['source_amount'],
        '税额': ['source_tax_amount'],
        '不含税金额': ['source_amount'],
        '发票号码': ['document_no'],
        '发票类型': ['invoice_type'],
        '发票备注': ['note'],
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
    'sc.legacy.fund.daily.line': {
        '单据状态': ['document_state'],
        '单据编号': ['document_no'],
        '单据日期': ['document_date'],
        '账号名称': ['account_name'],
        '银行账号': ['bank_account_no'],
        '当前账户余额': ['current_account_balance'],
        '当前账户银行余额': ['current_bank_balance'],
        '银行系统差额': ['bank_system_difference'],
        '当日累计收入': ['daily_income'],
        '当日累计支出': ['daily_expense'],
        '账户往来': [],
        '备注': ['note', 'header_note'],
        '录入人': ['creator_name'],
        '录入时间': ['created_time'],
    },
    'sc.legacy.payment.residual.fact': {
        '单据状态': ['document_state_label', 'document_state'],
        '单据编号': ['document_no'],
        '项目名称': ['project_name', 'project_id'],
        '纳税人名称': ['taxpayer_name'],
        '纳税人识别号': ['taxpayer_identifier'],
        '经办人手机': ['handler_phone'],
        '区域涉税事项联系人': ['regional_tax_contact'],
        '区域涉税事项联系人座机手机': ['regional_tax_contact_phone'],
        '跨区域经营地址': ['operation_address'],
        '经营方式': ['payment_method'],
        '合同名称': ['contract_name'],
        '合同金额': ['planned_amount'],
        '合同开始日期': ['contract_start_date'],
        '合同结束日期': ['contract_end_date'],
        '合同相对方名称': ['partner_name', 'partner_id'],
        '合同相对方名称编号': ['counterparty_tax_identifier'],
        '跨区域涉税事项报验管理编号': ['tax_report_management_no'],
        '录入人': ['creator_name'],
        '录入时间': ['created_time'],
    },
    'sc.legacy.user.profile': {
        '操作': ['account_state_label', 'person_state'],
        '用户名': ['source_login', 'generated_login'],
        '部门': ['department_name', 'department_scope_summary'],
        '职务': ['professional_title'],
        '岗位': ['professional_qualification', 'professional_title'],
        '电话号码': ['phone'],
        '是否测试账号': ['user_type', 'account_type'],
        '证件号': ['credential_no'],
        '是否购买社保': ['person_state'],
        '员工工号': ['employee_no', 'tr_user_job_number'],
        '人员类型': ['personnel_type', 'user_type', 'person_state'],
        '录入人': ['display_name', 'source_login'],
        '录入时间': ['legacy_created_at'],
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
        '项目名称': ['legacy_visible_project_name', 'project_id'],
        '开票单位': ['partner_name', 'partner_id'],
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
        '附件': ['attachment_ids'],
    },
    'sc.payment.execution': {
        '单据状态': ['legacy_document_state', 'state'],
        '推送结果': ['push_result'],
        '金蝶单据编号': ['kingdee_document_no'],
        '单据编号': ['legacy_visible_document_no', 'document_no', 'name'],
        '项目名称': ['legacy_visible_project_name', 'project_id'],
        '項目名称': ['legacy_visible_project_name', 'project_id'],
        '收款单位': ['legacy_visible_supplier_name', 'partner_id'],
        '实际收款单位': ['legacy_visible_actual_payee_unit'],
        '供应商名称': ['legacy_visible_supplier_name', 'partner_id'],
        '付款日期': ['legacy_visible_payment_date', 'date_payment'],
        '付款金额': ['legacy_visible_payment_amount', 'paid_amount'],
        '支付类别': ['legacy_visible_payment_category'],
        '付款内容': ['legacy_visible_payment_content'],
        '备注': ['legacy_visible_note', 'note'],
        '其它备注': ['legacy_visible_other_note', 'other_note', 'note'],
        '其他备注': ['legacy_visible_other_note', 'other_note', 'note'],
        '付款方式名称': ['legacy_visible_payment_method', 'payment_family', 'payment_method'],
        '类型（成本）': ['legacy_visible_cost_type'],
        '填写人': ['handler_name', 'creator_name'],
        '开户行': ['legacy_visible_receipt_bank_name', 'receipt_bank_name', 'payment_bank_name'],
        '账户': ['legacy_visible_receipt_account_no', 'receipt_account_no', 'payment_account_no', 'bank_account'],
        '付款账户': ['legacy_visible_payment_account_no', 'payment_account_no', 'bank_account'],
        '付款账户名称': ['legacy_visible_payment_account_name', 'payment_account_name'],
        '支付申请单号': ['legacy_visible_request_no', 'payment_request_id', 'document_no'],
        '附件': ['attachment_ids', 'legacy_attachment_ref'],
        '凭证号': ['legacy_visible_voucher_no'],
        '录入人': ['creator_name'],
        '付款单关联来源': ['legacy_visible_payment_source'],
        '录入日期': ['legacy_visible_entry_date', 'created_time'],
        '录入时间': ['created_time'],
    },
    'sc.hr.payroll.document': {
        '单据状态': ['legacy_document_state', 'state'],
        '状态': ['state'],
        '财务支出登记状态': ['state'],
        '单据编号': ['document_no', 'legacy_document_no', 'name'],
        '单据日期': ['business_date'],
        '项目名称': ['project_id', 'payer_unit', 'payout_unit'],
        '标题': ['name', 'description'],
        '姓名': ['employee_name', 'employee_user_id'],
        '补助人': ['employee_name', 'employee_user_id'],
        '人员状态': ['employee_status'],
        '人员类型': ['employee_type'],
        '身份证号码': ['id_number'],
        '联系方式': ['contact_phone'],
        '部门': ['department_id'],
        '年份': ['period_year'],
        '年度': ['period_year'],
        '月份': ['period_month'],
        '社保购买单位': ['payer_unit'],
        '发放单位': ['payout_unit', 'payer_unit'],
        '购买人数': ['people_count'],
        '发放人数': ['people_count'],
        '社保基数': ['social_security_base'],
        '缴费金额': ['amount', 'company_amount', 'individual_amount'],
        '个人证书': ['certificate_fee'],
        '证书费用': ['certificate_fee'],
        '类型': ['employee_type', 'legacy_visible_type'],
        '应发工资': ['gross_amount'],
        '实发工资': ['net_salary'],
        '补助事由': ['item_type', 'legacy_visible_item_type'],
        '补助金额': ['amount'],
        '备注': ['result_note', 'description', 'legacy_visible_note'],
        '附件': ['attachment_ids'],
        '录入人': ['source_created_by', 'legacy_visible_creator_name'],
        '登记人': ['source_created_by', 'legacy_visible_creator_name'],
        '录入时间': ['source_created_at', 'legacy_visible_created_time'],
        '登记时间': ['source_created_at', 'legacy_visible_created_time'],
    },
    'project.material.plan': {
        '附件': ['attachment_ids'],
    },
    'sc.settlement.order': {
        '单据状态': ['legacy_document_state', 'state'],
        '单据编号': ['name'],
        '项目名称': ['project_id'],
        '单据日期': ['document_date', 'date_settlement', 'declared_date', 'approved_date', 'final_approved_date'],
        '标题/结算内容': ['title', 'settlement_description'],
        '标题': ['title', 'settlement_description'],
        '结算内容': ['title', 'settlement_description'],
        '结算单位': ['settlement_unit_id', 'partner_id', 'legacy_counterparty_name'],
        '往来单位': ['settlement_unit_id', 'partner_id', 'legacy_counterparty_name'],
        '结算金额': ['settlement_amount', 'approved_amount', 'submitted_amount', 'amount_total'],
        '付款状态': ['legacy_payment_state'],
        '已付款金额': ['legacy_paid_amount', 'amount_paid', 'paid_amount'],
        '未付款金额': ['legacy_unpaid_amount', 'unpaid_amount', 'remaining_amount', 'amount_payable'],
        '支付申请状态': ['legacy_payment_request_state'],
        '已申请金额': ['requested_fund_amount'],
        '未申请金额': ['legacy_unrequested_amount'],
        '结算说明/备注': ['settlement_description', 'contract_subject', 'note'],
        '结算说明': ['settlement_description', 'note'],
        '备注': ['settlement_description', 'note'],
        '附件': ['attachment_ids', 'legacy_visible_attachment'],
        '录入人': ['source_created_by', 'entry_user_id'],
        '录入时间': ['source_created_at'],
    },
    'sc.subcontract.request': {
        '附件': ['attachment_ids'],
    },
    'sc.legacy.direct.acceptance.fact': {
        '附件': ['attachment_ids', 'attachment_ref'],
    },
    'sc.labor.usage': {
        '附件': ['attachment_ids'],
    },
    'sc.equipment.usage': {
        '附件': ['attachment_ids'],
    },
    'sc.material.rfq': {
        '附件': ['attachment_ids'],
    },
}


PAYMENT_REQUEST_DOCUMENT_STATE_LABELS = {
    "-1": "已作废",
    "0": "未审核",
    "1": "审批中",
    "2": "审核通过",
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

RECEIPT_INCOME_DOCUMENT_STATE_LABELS = {
    "-1": "已作废",
    "0": "未审核",
    "1": "审核中",
    "2": "审核通过",
}

BUSINESS_DOCUMENT_STATE_LABELS = {
    "-1": "已作废",
    "0": "未审核",
    "1": "审核中",
    "2": "审核通过",
    "3": "已驳回",
    "4": "已作废",
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
    if len(text) >= 8 and len(text) % 2 == 0 and not text.isdigit():
        half = len(text) // 2
        if text[:half] == text[half:]:
            text = text[:half].strip()
    return "" if text in {"False", "false", "None", "NULL"} else text


def _normalize_payload_alias_value(label, value):
    if value or value in (0, 0.0):
        text = str(value).strip()
        if text in {"False", "false", "None", "NULL"}:
            return ""
        if label in ("单据状态", "状态"):
            return BUSINESS_DOCUMENT_STATE_LABELS.get(text, text)
        return text
    return ""


def _format_progress_receipt_amount_alias(value):
    if value is False or value is None:
        return ""
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return str(value).strip()
    return f"{amount:,.2f}"


def _business_document_state_alias(record):
    for field_name in (
        "legacy_visible_document_state",
        "legacy_document_state",
        "document_state",
        "legacy_state",
        "state",
    ):
        value = _format_alias_value(record, field_name)
        if not value:
            continue
        if value in BUSINESS_DOCUMENT_STATE_LABELS:
            return BUSINESS_DOCUMENT_STATE_LABELS[value]
        if field_name != "state":
            return value
    return ""


def _is_hash_file_name(name):
    return bool(HEX_NAME_RE.match(str(name or "").strip()))


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
        return "附件(1)"
    return "附件(%s)" % len(files)


USER_ACCEPTANCE_ALIAS_LABELS = {
    "支付申请": [
        "单据状态", "单据编号", "申请日期", "项目名称", "收款单位", "实际收款单位", "付款单位",
        "申请付款金额", "实际付款金额", "类型（成本）", "备注", "是否关联单据", "付款账号",
        "金额大写", "户名", "开户行", "账号", "附件", "录入人", "录入时间",
    ],
    "项目费用报销单": [
        "单据状态", "单据编号", "日期", "报销种类", "事项说明", "报销金额", "付款状态",
        "已付款金额", "未付款金额", "付款方式", "报销人", "收款人", "备注", "项目名称",
        "附件", "录入人", "录入时间",
    ],
    "往来单位付款": [
        "单据状态", "付款日期", "收款单位", "实际收款单位", "付款金额", "支付类别", "付款内容",
        "付款方式名称", "类型（成本）", "付款账户名称", "附件", "凭证号", "填写人", "录入人",
        "项目名称", "付款单关联来源", "单据编号",
    ],
}

USER_ACCEPTANCE_ALIAS_INDEXES = {
    "支付申请": {
        "单据状态": 1,
        "单据编号": 2,
        "申请日期": 3,
        "项目名称": 4,
        "收款单位": 5,
        "实际收款单位": 6,
        "付款单位": 7,
        "申请付款金额": 8,
        "实际付款金额": 9,
        "类型（成本）": 11,
        "备注": 12,
        "是否关联单据": 13,
        "付款账号": 14,
        "金额大写": 15,
        "户名": 16,
        "开户行": 17,
        "账号": 18,
        "附件": 19,
        "录入人": 20,
        "录入时间": 21,
    },
}


def _strip_legacy_file_suffix(value):
    text = str(value or "").strip()
    if " | legacy-file-id://" in text:
        return text.split(" | legacy-file-id://", 1)[0].strip()
    return text


def _user_acceptance_alias_context(record):
    if (
        record._name == "payment.request"
        and _format_alias_value(record, "legacy_source_table") == "SCBSLY_DIRECT_PAYMENT_APPLY_ACCEPTED"
    ):
        return "支付申请", ("legacy_visible_document_no", "document_no", "name")
    if (
        record._name == "sc.expense.claim"
        and getattr(record, "claim_type", "") == "expense"
        and _format_alias_value(record, "expense_type") == "项目费用报销单"
    ):
        return "项目费用报销单", ("name",)
    if (
        record._name == "sc.payment.execution"
        and getattr(record, "source_kind", "") == "actual_outflow"
        and _format_alias_value(record, "legacy_source_model") == "online_old_scbsly:T_FK_SUPPLIER:list881"
    ):
        return "往来单位付款", ("legacy_visible_document_no", "document_no", "name")
    return None, ()


def _user_acceptance_alias_value(record, label):
    acceptance_label, doc_fields = _user_acceptance_alias_context(record)
    labels = USER_ACCEPTANCE_ALIAS_LABELS.get(acceptance_label or "")
    if not acceptance_label or label not in (labels or ()):
        return None
    document_no = ""
    for field_name in doc_fields:
        document_no = _format_alias_value(record, field_name)
        if document_no:
            break
    if not document_no or "sc.legacy.direct.acceptance.fact" not in record.env:
        return None
    key = (record.env.cr.dbname, acceptance_label, document_no)
    payload = _USER_ACCEPTANCE_VISIBLE_CACHE.get(key)
    if payload is None:
        fact = record.env["sc.legacy.direct.acceptance.fact"].sudo().search(
            [
                ("active", "=", True),
                ("source_system", "=", "online_old_scbsly"),
                ("acceptance_label", "=", acceptance_label),
                "|",
                ("document_no", "=", document_no),
                ("legacy_record_id", "=", document_no),
            ],
            order="id desc",
            limit=1,
        )
        payload = {}
        if fact:
            indexes = USER_ACCEPTANCE_ALIAS_INDEXES.get(acceptance_label, {})
            for index, visible_label in enumerate(labels, start=1):
                visible_index = indexes.get(visible_label, index)
                payload[visible_label] = getattr(fact, f"legacy_visible_{visible_index:02d}", "")
        _USER_ACCEPTANCE_VISIBLE_CACHE[key] = payload
    if label not in payload:
        return None
    return _strip_legacy_file_suffix(payload.get(label))


def _description_line_value(record, prefix):
    description = _format_alias_value(record, 'description')
    token = str(prefix or '').strip()
    if not description or not token:
        return ""
    marker = token + ':'
    for line in description.splitlines():
        text = line.strip()
        if text.startswith(marker):
            return text[len(marker):].strip()
    return ""


def _legacy_visible_alias_payload(record):
    if not record.id:
        return {}
    key = (record.env.cr.dbname, record._name, record.id)
    if key in _LEGACY_VISIBLE_ALIAS_PAYLOAD_CACHE:
        return _LEGACY_VISIBLE_ALIAS_PAYLOAD_CACHE[key]
    payload = {}
    try:
        record.env.cr.execute("SELECT to_regclass('public.sc_p1_legacy_visible_alias_payload')")
        exists = record.env.cr.fetchone()
        if not exists or not exists[0]:
            _LEGACY_VISIBLE_ALIAS_PAYLOAD_CACHE[key] = payload
            return payload
        record.env.cr.execute(
            """
            SELECT payload
              FROM sc_p1_legacy_visible_alias_payload
             WHERE model = %s AND res_id = %s
             LIMIT 1
            """,
            [record._name, record.id],
        )
        row = record.env.cr.fetchone()
        if row and isinstance(row[0], dict):
            payload = row[0]
    except Exception:
        payload = {}
    _LEGACY_VISIBLE_ALIAS_PAYLOAD_CACHE[key] = payload
    return payload


def _payment_request_c_zfsqgl_alias_value(record, label):
    if record._name != 'payment.request' or _format_alias_value(record, 'legacy_source_table') != 'C_ZFSQGL':
        return None
    if label == '单据状态':
        legacy_state = _format_alias_value(record, 'legacy_document_state')
        return PAYMENT_REQUEST_DOCUMENT_STATE_LABELS.get(legacy_state, legacy_state) if legacy_state else ""
    strict_sources = {
        '单据编号': 'legacy_visible_document_no',
        '项目名称': 'legacy_visible_project_name',
        '申请日期': 'legacy_visible_request_date',
        '收款单位': 'legacy_visible_payee_unit',
        '申请付款金额': 'legacy_visible_request_amount',
        '实际付款金额': 'legacy_visible_actual_paid_amount',
        '可用余额': 'legacy_visible_available_balance',
        '成本分类名称': 'legacy_visible_cost_category_name',
        '备注': 'legacy_visible_remark',
        '付款账号': 'legacy_payment_account_no',
        '金额大写': 'legacy_visible_amount_uppercase',
        '户名': 'legacy_payee_account_name',
        '开户行': 'legacy_payee_bank_name',
        '账号': 'legacy_payee_account_no',
        '填写人': 'legacy_visible_writer',
        '附件': 'legacy_visible_attachment',
        '录入时间': 'created_time',
    }
    if label in strict_sources:
        return _format_alias_value(record, strict_sources[label])
    return None


def _alias_value(record, label):
    acceptance_value = _user_acceptance_alias_value(record, label)
    if acceptance_value is not None:
        return acceptance_value
    strict_value = _payment_request_c_zfsqgl_alias_value(record, label)
    if strict_value is not None:
        return _strip_legacy_file_suffix(strict_value) if label == "附件" else strict_value
    payload = _legacy_visible_alias_payload(record)
    if payload and label in payload:
        return _normalize_payload_alias_value(label, payload.get(label))
    if (
        record._name == 'sc.receipt.income'
        and _format_alias_value(record, 'source_family') == 'engineering_progress_receipt_visible'
    ):
        strict_sources = {
            '单据状态': 'legacy_document_state_label',
            '状态': 'legacy_document_state_label',
            '项目名称': 'legacy_project_name',
            '往来单位': 'legacy_partner_name',
            '承包单位': 'legacy_company_name',
            '施工管理合同': 'legacy_contract_no',
            '单据编号': 'document_no',
            '填写人': 'creator_name',
            '收款账户': 'receiving_account',
            '进账金额': 'amount',
            '收入类别': 'income_category',
            '收款时间': 'date_receipt',
            '备注': 'legacy_note',
            '附件': 'legacy_attachment_ref',
            '录入人': 'creator_name',
            '录入时间': 'created_time',
        }
        field_name = strict_sources.get(label)
        if field_name:
            if label == '进账金额':
                return _format_progress_receipt_amount_alias(record[field_name])
            return _format_alias_value(record, field_name)
        if label in strict_sources:
            return ''
    if record._name == 'sc.business.entity':
        strict_sources = {
            '单据状态': None,
            '推送结果': None,
            '项目名称': 'legacy_xmmc',
            '单位编号': 'legacy_xmid',
            '合作类型': None,
            '单位名称': 'legacy_xmmc',
            '开户银行': None,
            '账号': None,
            '统一社会信用代码': None,
            '主税率': None,
            '录入人': 'legacy_visible_creator_name',
            '录入时间': 'legacy_visible_created_time',
            '收款金额': None,
            '付款金额': None,
            '开户姓名': None,
            '开户账号': None,
            '银行账号': None,
        }
        if label in strict_sources:
            field_name = strict_sources[label]
            return _format_alias_value(record, field_name) if field_name else ''
    if record._name == 'construction.contract':
        if label in ('单据状态', '状态'):
            legacy_state = _format_alias_value(record, 'legacy_visible_document_state')
            if legacy_state:
                return BUSINESS_DOCUMENT_STATE_LABELS.get(legacy_state, legacy_state)
            return ''
        strict_sources = {
            '单据编号': 'legacy_visible_document_no',
            '合同订立日期': 'legacy_visible_contract_date',
            '原件是否归档': 'legacy_visible_archived',
            '发包人': 'legacy_visible_counterparty',
            '项目名称': 'legacy_visible_project_name',
            '合同标题': 'legacy_visible_title',
            '工程类别': 'legacy_visible_category',
            '合同编号': 'legacy_visible_contract_no',
            '合同金额': 'legacy_visible_amount',
            '结算金额': 'legacy_visible_settlement_amount',
            '累计开票': 'legacy_visible_invoice_amount',
            '累计收款': 'legacy_visible_received_amount',
            '未收款': 'legacy_visible_unreceived_amount',
            '未收款比例': 'legacy_visible_unreceived_rate',
            '挂靠人': 'legacy_visible_affiliated_person',
            '工程地址': 'legacy_visible_engineering_address',
            '工程内容': 'legacy_visible_engineering_content',
            '附件': 'legacy_visible_attachment',
            '录入人': 'legacy_visible_creator_name',
            '录入时间': 'legacy_visible_created_time',
        }
        field_name = strict_sources.get(label)
        if field_name:
            return _format_alias_value(record, field_name)
    if record._name == 'sc.document.admin.document':
        if label in ('单据状态', '状态'):
            legacy_state = _format_alias_value(record, 'legacy_document_state')
            if legacy_state:
                return BUSINESS_DOCUMENT_STATE_LABELS.get(legacy_state, legacy_state)
        strict_sources = {
            '单据编号': 'legacy_document_no',
            '项目名称': 'legacy_visible_project_name',
            '借阅项目名称': 'legacy_visible_project_name',
            '资料类型': 'legacy_visible_document_type',
            '资料说明': 'legacy_visible_description',
            '证照名称': 'certificate_name',
            '编号': 'certificate_no',
            '持有人': 'holder_name',
            '有效期': 'valid_until',
            '证件名称': 'document_title',
            '申请日期': 'legacy_visible_application_date',
            '借阅部门或项目部名称': 'legacy_visible_department',
            '借阅人': 'legacy_visible_borrower',
            '联系方式': 'legacy_visible_contact',
            '借阅形式': 'legacy_visible_borrow_form',
            '借阅日期': 'legacy_visible_borrow_date',
            '负责人': 'legacy_visible_responsible_person',
            '归还申请日期': 'legacy_visible_return_request_date',
            '申请归还时间': 'legacy_visible_return_apply_time',
            '是否归还': 'legacy_visible_returned',
            '确认归还时间': 'legacy_visible_return_confirm_time',
            '归还日期': 'legacy_visible_return_date',
            '备注': 'legacy_visible_note',
            '修改人': 'legacy_visible_modifier',
            '修改日期': 'legacy_visible_modified_date',
            '修改备注': 'legacy_visible_modify_note',
            '审定人': 'legacy_visible_reviewer',
            '审定时间': 'legacy_visible_review_time',
            '审定意见': 'legacy_visible_review_opinion',
            '录入人': 'legacy_visible_creator_name',
            '录入时间': 'legacy_visible_created_time',
        }
        field_name = strict_sources.get(label)
        if field_name:
            return _format_alias_value(record, field_name)
    if record._name == 'sc.office.admin.document':
        if label in ('单据状态', '状态'):
            legacy_state = _format_alias_value(record, 'legacy_document_state')
            if legacy_state:
                return BUSINESS_DOCUMENT_STATE_LABELS.get(legacy_state, legacy_state)
        strict_sources = {
            '单据编号': 'legacy_document_no',
            '项目名称': 'legacy_visible_project_name',
            '申请人姓名': 'legacy_visible_applicant',
            '所在部门': 'legacy_visible_department',
            '请假天数': 'legacy_visible_leave_days',
            '请假类型': 'legacy_visible_leave_type',
            '请假时间': 'legacy_visible_leave_time',
            '销假时间': 'legacy_visible_cancel_time',
            '备注': 'legacy_visible_note',
            '请假时长': 'legacy_visible_leave_duration',
            '录入人': 'legacy_visible_creator_name',
            '录入时间': 'legacy_visible_created_time',
            '用印时间': 'legacy_visible_seal_use_time',
            '用印部门': 'legacy_visible_department',
            '用印申请人': 'legacy_visible_applicant',
            '用印部门负责人签字': 'legacy_visible_department_manager_sign',
            '用印种类': 'legacy_visible_seal_type',
            '用印文本名称及文号': 'legacy_visible_seal_text',
            '经办人签字': 'legacy_visible_handler_sign',
            '领导签字': 'legacy_visible_leader_sign',
            '份数': 'legacy_visible_copy_count',
            '归还时间': 'legacy_visible_return_time',
            '合同金额': 'legacy_visible_contract_amount',
            '合同编号': 'legacy_visible_contract_no',
            '所属公司': 'legacy_visible_company',
            '使用印章公司': 'legacy_visible_seal_company',
            '是否外带': 'legacy_visible_take_out',
        }
        field_name = strict_sources.get(label)
        if field_name:
            return _format_alias_value(record, field_name)
    if record._name == 'sc.financing.loan':
        if label in ('单据状态', '状态'):
            legacy_state = _format_alias_value(record, 'legacy_document_state')
            if legacy_state:
                return BUSINESS_DOCUMENT_STATE_LABELS.get(legacy_state, legacy_state)
        strict_sources = {
            '项目名称': 'legacy_visible_project_name',
            '申请部门': 'legacy_visible_request_department',
            '申请时间': 'legacy_visible_request_time',
            '申请人': 'legacy_visible_applicant',
            '是否预算内': 'legacy_visible_budget_included',
            '实际借款金额': 'legacy_visible_actual_loan_amount',
            '主要资金使用安排': 'legacy_visible_fund_usage_plan',
            '收款人': 'legacy_visible_payee',
            '收款账户': 'legacy_visible_receipt_account',
            '开户银行': 'legacy_visible_bank_name',
            '公司名称': 'legacy_visible_company_name',
            '备注': 'legacy_visible_note',
            '付款单位': 'legacy_visible_payer_unit',
            '收款单位': 'legacy_visible_receiver_unit',
            '往来单位名称': 'legacy_visible_counterparty_name',
            '往来单位账户': 'legacy_visible_counterparty_account',
            '借款账号': 'legacy_visible_loan_account',
            '实际批复金额': 'legacy_visible_approved_amount',
            '申请金额': 'legacy_visible_request_amount',
            '预计归还时间': 'legacy_visible_expected_return_time',
            '借款类型': 'legacy_visible_loan_type',
            '借款人': 'legacy_visible_applicant',
            '借款金额': 'legacy_visible_actual_loan_amount',
            '用途': 'legacy_visible_fund_usage_plan',
            '约定期限': 'legacy_visible_expected_return_time',
            '借款利息': 'legacy_visible_loan_interest',
            '贷款金额': 'legacy_visible_actual_loan_amount',
            '到期利息': 'legacy_visible_due_interest',
            '还款金额': 'legacy_visible_repayment_amount',
            '未还款金额': 'legacy_visible_unpaid_amount',
            '贷款日期': 'legacy_visible_loan_date',
            '还款日期': 'legacy_visible_repayment_date',
            '贷款天数': 'legacy_visible_loan_days',
            '年利率': 'legacy_visible_annual_rate',
            '贷款账户': 'legacy_visible_loan_account',
            '贷款银行': 'legacy_visible_loan_bank',
            '实际还款天数': 'legacy_visible_actual_repayment_days',
            '实际年利率': 'legacy_visible_actual_annual_rate',
            '贷款利息': 'legacy_visible_loan_interest',
            '还款账户': 'legacy_visible_repayment_account',
            '填写人': 'legacy_visible_writer',
            '录入人': 'creator_name',
            '录入时间': 'created_time',
        }
        field_name = strict_sources.get(label)
        if field_name:
            return _format_alias_value(record, field_name)
    if record._name == 'sc.invoice.registration' and _format_alias_value(record, 'legacy_source_table') in ('C_JXXP_KJFPSQ', 'C_JXXP_XXKPDJ'):
        if label in ('单据状态', '状态'):
            legacy_state = _format_alias_value(record, 'legacy_document_state')
            if legacy_state:
                return {
                    '-1': '已作废',
                    '0': '未审核',
                    '1': '审核中',
                    '2': '审核通过',
                    '3': '已驳回',
                    '4': '已作废',
                }.get(legacy_state, legacy_state)
        strict_sources = {
            '开票状态': 'invoice_state',
            '合同编号': 'contract_id',
            '项目名称': 'legacy_visible_project_name',
            '申请日期': 'application_date',
            '受票单位': 'recipient_unit_name',
            '受票方名称': 'recipient_unit_name',
            '累计开票金额': 'legacy_visible_cumulative_invoice_amount',
            '本次开票张数': 'invoice_count',
            '开票张数': 'invoice_count',
            '数量': 'invoice_count',
            '本次开票金额': 'actual_invoice_amount',
            '实开总金额': 'actual_invoice_amount',
            '备注': 'legacy_visible_note',
            '推送结果': 'push_result',
            '金蝶单据编号': 'kingdee_document_no',
            '含税金额': 'amount_total',
            '附加税': 'surcharge_amount',
            '税率': 'tax_rate',
            '关联回款金额': 'related_receipt_amount',
            '发票号': 'invoice_no',
            '发票种类': 'invoice_type',
            '开票单位': 'invoice_issue_company',
            '实际开票单位': 'actual_invoice_issue_company',
            '口径': 'caliber',
            '录入人': 'creator_name',
            '录入时间': 'created_time',
        }
        field_name = strict_sources.get(label)
        if field_name:
            return _format_alias_value(record, field_name)
    if record._name == 'tender.guarantee':
        if label in ('状态', '单据状态'):
            legacy_state = _format_alias_value(record, 'legacy_visible_document_state')
            if legacy_state:
                return {
                    '-1': '已作废',
                    '0': '未审核',
                    '1': '审核中',
                    '2': '审核通过',
                    '3': '已驳回',
                    '4': '已作废',
                }.get(legacy_state, legacy_state)
        if label in ('单据编号', '收保证金单号', '退回单编号'):
            return _format_alias_value(record, 'legacy_visible_document_no')
        if label in ('投标项目名称', '项目名称', '投标项目', '工程项目', '退回项目'):
            return _format_alias_value(record, 'legacy_visible_project_name')
        if label in ('金额', '保证金金额'):
            return _format_alias_value(record, 'amount')
        if label == '备注':
            remark = _format_alias_value(record, 'remark')
            return '' if remark.startswith('历史投标保证金') else remark
        if label == '录入人':
            return _format_alias_value(record, 'legacy_visible_creator_name')
        if label == '录入时间':
            return _format_alias_value(record, 'legacy_visible_created_time')
        return ''
    if record._name == 'sc.receipt.income' and label in ('单据状态', '状态'):
        legacy_state = _format_alias_value(record, 'legacy_document_state')
        if legacy_state:
            return RECEIPT_INCOME_DOCUMENT_STATE_LABELS.get(legacy_state, legacy_state)
    if record._name == 'sc.receipt.income' and label == '收款账户':
        for field_name in ('receiving_account_name', 'receiving_account', 'receiving_account_no'):
            value = _format_alias_value(record, field_name)
            if value:
                return value
        return ""
    if record._name == 'sc.fund.account.operation' and _format_alias_value(record, 'legacy_source_table') == 'C_FKGL_ZHJZJWL':
        if label in ('单据状态', '状态'):
            legacy_state = _format_alias_value(record, 'legacy_document_state')
            if legacy_state:
                return {
                    '-1': '已作废',
                    '0': '未审核',
                    '1': '审核中',
                    '2': '审核通过',
                    '3': '已驳回',
                    '4': '已作废',
                }.get(legacy_state, legacy_state)
        strict_sources = {
            '单据编号': 'legacy_visible_document_no',
            '项目名称': 'legacy_visible_project_name',
            '账户号码': 'legacy_visible_account_name',
            '收款账户': 'legacy_visible_counterparty_account_name',
            '转账类别': 'legacy_visible_transfer_type',
            '事由': 'legacy_visible_reason',
            '备注': 'legacy_visible_note',
        }
        field_name = strict_sources.get(label)
        if field_name:
            return _format_alias_value(record, field_name)
    if record._name == 'sc.receipt.income' and label == '备注':
        note = _format_alias_value(record, 'note')
        if note:
            lines = [
                line.strip()
                for line in note.splitlines()
                if line.strip()
                and not line.strip().startswith('[migration:')
                and line.strip() not in {'company_financial_income', 'receipt_confirmation', 'customer_receipt', 'income', 'inflow'}
            ]
            if lines:
                return " ".join(lines)
            return ""
    if record._name == 'sc.expense.claim' and _format_alias_value(record, 'legacy_source_table') == 'C_CWSFK_GSCWZC':
        strict_sources = {
            '付款时间': 'legacy_visible_payment_time',
            '推送结果': 'legacy_visible_push_result',
            '成本类别': 'legacy_visible_expense_type',
            '备注': 'legacy_visible_note',
        }
        field_name = strict_sources.get(label)
        if field_name:
            return _format_alias_value(record, field_name)
    if record._name == 'sc.expense.claim' and _format_alias_value(record, 'legacy_source_table') == 'CWGL_FYBX_CB':
        if label in ('单据状态', '状态'):
            legacy_state = _format_alias_value(record, 'legacy_visible_document_state')
            if legacy_state:
                return {
                    '-1': '已作废',
                    '0': '未审核',
                    '1': '审核中',
                    '2': '审核通过',
                    '3': '已驳回',
                    '4': '已作废',
                }.get(legacy_state, legacy_state)
            return ''
        strict_sources = {
            '单据编号': 'legacy_visible_document_no',
            '日期': 'legacy_visible_date',
            '部门': 'legacy_visible_department',
            '事项说明': 'legacy_visible_summary',
            '报销金额': 'legacy_visible_amount',
            '备注': 'legacy_visible_note',
        }
        field_name = strict_sources.get(label)
        if field_name:
            return _format_alias_value(record, field_name)
    if record._name == 'sc.expense.claim' and _format_alias_value(record, 'legacy_source_table') == 'ZJGL_ZCDFSZ_FXJK_HK':
        strict_sources = {
            '项目名称': 'legacy_visible_project_name',
            '借款人': 'legacy_visible_borrower',
            '借款金额': 'legacy_visible_loan_amount',
            '还款金额': 'legacy_visible_repayment_amount',
            '用途': 'legacy_visible_summary',
            '借款利率': 'legacy_visible_loan_rate',
            '利息': 'legacy_visible_interest',
            '还款时间': 'legacy_visible_repayment_time',
            '备注': 'legacy_visible_note',
        }
        field_name = strict_sources.get(label)
        if field_name:
            return _format_alias_value(record, field_name)
    if record._name == 'payment.request' and label == '单据状态':
        legacy_state = _format_alias_value(record, 'legacy_document_state')
        if legacy_state:
            return PAYMENT_REQUEST_DOCUMENT_STATE_LABELS.get(legacy_state, legacy_state)
    if record._name == 'payment.request' and label == '是否关联单据':
        return "是" if record.settlement_id or record.contract_id or record.outflow_line_ids else "否"
    if record._name == 'tender.doc.purchase' and label == '申请人':
        if _format_alias_value(record, 'legacy_source_table') == 'BGGL_ZTBJHT_TBBM_TBBMFSQ':
            return _format_alias_value(record, 'legacy_visible_applicant_name')
    if record._name == 'tender.doc.purchase' and label == '单据状态':
        state = _format_alias_value(record, 'legacy_visible_document_state')
        if state:
            return {
                '-1': '已驳回',
                '0': '草稿',
                '1': '审批中',
                '2': '已通过',
                '3': '已驳回',
            }.get(state, state)
    if record._name == 'tender.bid':
        if label == '单据状态':
            state = _format_alias_value(record, 'legacy_visible_document_state')
            if state:
                return {
                    '-1': '已作废',
                    '0': '未审核',
                    '1': '审核中',
                    '2': '审核通过',
                    '3': '已驳回',
                    '4': '已作废',
                }.get(state, state)
        strict_sources = {
            '单据编号': 'name',
            '开标时间': 'legacy_visible_opening_time',
            '项目名称': 'legacy_visible_project_name',
            '登记时间': 'legacy_visible_registration_time',
            '录入人': 'legacy_visible_creator_name',
        }
        field_name = strict_sources.get(label)
        if field_name:
            return _format_alias_value(record, field_name)
    if record._name == 'sc.payment.execution' and _format_alias_value(record, 'legacy_source_table') == 'T_FK_Supplier_CB':
        strict_sources = {
            '单据编号': 'legacy_visible_document_no',
            '项目名称': 'legacy_visible_project_name',
            '項目名称': 'legacy_visible_project_name',
            '供应商名称': 'legacy_visible_supplier_name',
            '付款日期': 'legacy_visible_payment_date',
            '备注': 'legacy_visible_note',
            '其它备注': 'legacy_visible_other_note',
            '其他备注': 'legacy_visible_other_note',
            '付款方式名称': 'legacy_visible_payment_method',
            '开户行': 'legacy_visible_receipt_bank_name',
            '账户': 'legacy_visible_receipt_account_no',
            '付款账户': 'legacy_visible_payment_account_no',
            '付款账户名称': 'legacy_visible_payment_account_name',
            '支付申请单号': 'legacy_visible_request_no',
        }
        field_name = strict_sources.get(label)
        if field_name:
            return _format_alias_value(record, field_name)
    if record._name == 'sc.hr.payroll.document':
        if label in ('单据状态', '状态'):
            legacy_state = _format_alias_value(record, 'legacy_document_state')
            if legacy_state:
                return {
                    '-1': '已作废',
                    '0': '未审核',
                    '1': '审核中',
                    '2': '审核通过',
                    '3': '已驳回',
                    '4': '已作废',
                }.get(legacy_state, legacy_state)
            if getattr(record, 'fact_type', '') == 'subsidy' and _format_alias_value(record, 'legacy_source_table'):
                return ''
        description_sources = {
            '标题': '工资标题',
            '联系方式': '联系方式',
            '部门': '部门',
            '人员状态': '人员状态',
        }
        prefix = description_sources.get(label)
        if prefix:
            value = _description_line_value(record, prefix)
            if value:
                return value
        strict_sources = {
            '单据编号': 'legacy_document_no',
            '单据日期': 'business_date',
            '姓名': 'employee_name',
            '人员类型': 'employee_type',
            '身份证号码': 'id_number',
            '证书费用': 'certificate_fee',
            '社保基数': 'social_security_base',
            '社保购买单位': 'payer_unit',
            '人员状态': 'employee_status',
            '项目名称': 'payer_unit',
            '类型': 'employee_type',
            '购买人数': 'people_count',
            '发放人数': 'people_count',
            '标题': 'description',
            '年份': 'period_year',
            '年度': 'period_year',
            '月份': 'period_month',
            '部门': 'department_id',
            '发放单位': 'payout_unit',
            '应发工资': 'gross_amount',
            '实发工资': 'net_salary',
            '缴费金额': 'amount',
            '补助金额': 'amount',
            '补助事由': 'item_type',
            '补助人': 'employee_name',
            '备注': 'result_note',
            '录入人': 'source_created_by',
            '登记人': 'source_created_by',
            '录入时间': 'source_created_at',
            '登记时间': 'source_created_at',
        }
        field_name = strict_sources.get(label)
        if field_name:
            return _format_alias_value(record, field_name)
    if record._name == 'sc.invoice.registration' and label in ('状态', '单据状态'):
        legacy_state = _format_alias_value(record, 'legacy_document_state')
        if legacy_state:
            return INVOICE_DOCUMENT_STATE_LABELS.get(legacy_state, legacy_state)
    if label in ('单据状态', '状态'):
        state_label = _business_document_state_alias(record)
        if state_label:
            return state_label
    if record._name == 'sc.expense.claim' and label == '是否退回':
        legacy_flag = _format_alias_value(record, 'legacy_visible_returned_flag')
        if legacy_flag:
            return legacy_flag
        return '是' if getattr(record, 'claim_type', '') == 'deduction_refund' else '否'
    if record._name == 'sc.expense.claim' and label == '备注' and getattr(record, 'claim_type', '') == 'deduction_refund':
        return _format_alias_value(record, 'legacy_visible_note')
    if (
        record._name == 'sc.tax.deduction.registration'
        and label == '扣款事由'
        and _format_alias_value(record, 'legacy_source_table') == 'C_ZFSQGL_KKD'
    ):
        note = _format_alias_value(record, 'note')
        lines = [
            line.strip()
            for line in note.splitlines()
            if line.strip()
            and line.strip() != 'not_promoted_to_runtime_payment_request'
            and line.strip() != 'missing_partner_anchor'
            and not line.strip().startswith('[migration:')
        ]
        return " ".join(lines)
    if record._name == 'sc.legacy.invoice.tax.fact' and label in ('状态', '单据状态'):
        legacy_state = _format_alias_value(record, 'legacy_state')
        if legacy_state:
            return INVOICE_DOCUMENT_STATE_LABELS.get(legacy_state, legacy_state)
    if record._name == 'sc.invoice.registration' and label == '附件':
        legacy_links = _legacy_attachment_links(record)
        if legacy_links:
            return legacy_links
        for field_name in ('attachment_ids', 'biz_attachment_ids', 'tech_attachment_ids', 'legacy_attachment_name'):
            value = _format_alias_value(record, field_name)
            if value:
                return _strip_legacy_file_suffix(value)
        return ""
    if record._name == 'sc.legacy.fund.confirmation.document' and label == '附件':
        legacy_links = _legacy_attachment_links(record)
        if legacy_links:
            return legacy_links
        return _format_alias_value(record, 'attachment_links')
    if record._name == 'sc.legacy.fund.daily.line' and label == '账户往来':
        return ""
    if label == '附件':
        legacy_links = _legacy_attachment_links(record)
        if legacy_links:
            return legacy_links
        for field_name in ('attachment_ids', 'biz_attachment_ids', 'tech_attachment_ids', 'legacy_attachment_name'):
            value = _format_alias_value(record, field_name)
            if value:
                return _strip_legacy_file_suffix(value)
        return ""
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


class ScPaymentExecutionUserAcceptanceOrder(models.Model):
    _inherit = "sc.payment.execution"

    user_acceptance_partner_payment_sort_id = fields.Integer(
        string="用户验收排序号",
        compute="_compute_user_acceptance_partner_payment_sort_id",
        store=True,
        index=True,
        readonly=True,
    )

    @api.depends("source_kind", "legacy_source_model", "legacy_visible_document_no")
    def _compute_user_acceptance_partner_payment_sort_id(self):
        target_records = self.filtered(
            lambda record: record.source_kind == "actual_outflow"
            and record.legacy_source_model == "online_old_scbsly:T_FK_SUPPLIER:list881"
            and record.legacy_visible_document_no
        )
        values_by_doc = {}
        if target_records and "sc.legacy.direct.acceptance.fact" in self.env:
            docs = list(dict.fromkeys(target_records.mapped("legacy_visible_document_no")))
            facts = self.env["sc.legacy.direct.acceptance.fact"].sudo().search(
                [
                    ("active", "=", True),
                    ("source_system", "=", "online_old_scbsly"),
                    ("acceptance_label", "=", "往来单位付款"),
                    ("legacy_record_id", "in", docs),
                ],
                order="id desc",
            )
            for fact in facts:
                values_by_doc.setdefault(fact.legacy_record_id, fact.id if not fact.document_date else 0)
        for record in self:
            record.user_acceptance_partner_payment_sort_id = values_by_doc.get(record.legacy_visible_document_no, 0)
