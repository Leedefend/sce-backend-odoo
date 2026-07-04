# SCBS55 User Visible Form Operability Probe v1

Status: FAIL
Database: sc_demo
Generated At: 2026-05-28T08:21:11.732126+00:00

| seq | menu | model | old fields | label hits | list facts missing | create | status |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| 10 | 供应商/合作单位 | sc.business.entity | 0 | 0 | 0 | True | PASS |
| 20 | 往来单位 | sc.business.entity | 0 | 0 | 0 | True | PASS |
| 30 | 施工合同 | construction.contract | 0 | 0 | 0 | True | PASS |
| 40 | 公司资料存档 | sc.document.admin.document | 0 | 0 | 0 | True | PASS |
| 50 | 请假/休假审批单 | sc.office.admin.document | 0 | 0 | 0 | True | PASS |
| 60 | 印章使用审批表 | sc.office.admin.document | 0 | 0 | 0 | True | PASS |
| 70 | 组织机构 | hr.department | 0 | 0 | 0 | True | PASS |
| 80 | 公司人员名册（配置） | sc.legacy.user.profile | 0 | 0 | 0 | True | PASS |
| 90 | 社保人员登记 | sc.hr.payroll.document | 0 | 0 | 0 | True | PASS |
| 100 | 社保登记 | sc.hr.payroll.document | 0 | 0 | 0 | True | PASS |
| 110 | 工资登记 | sc.hr.payroll.document | 0 | 0 | 0 | True | PASS |
| 120 | 补助 | sc.hr.payroll.document | 0 | 0 | 0 | True | PASS |
| 130 | 奖金 | sc.hr.payroll.document | 0 | 0 | 0 | True | PASS |
| 140 | 证照登记 | sc.document.admin.document | 0 | 0 | 0 | True | PASS |
| 150 | 借阅申请 | sc.document.admin.document | 0 | 0 | 0 | True | PASS |
| 160 | 投标报名管理 | tender.bid | 0 | 0 | 0 | True | PASS |
| 170 | 投标报名费申请 | tender.doc.purchase | 0 | 0 | 0 | True | PASS |
| 180 | 自筹保证金 | tender.guarantee | 0 | 0 | 0 | True | PASS |
| 190 | 自筹保证金退回 | tender.guarantee | 0 | 0 | 0 | True | PASS |
| 200 | 付款还保证金 | tender.guarantee | 0 | 0 | 0 | True | PASS |
| 210 | 付款还保证金退回 | tender.guarantee | 0 | 0 | 0 | True | PASS |
| 220 | 借款申请 | sc.financing.loan | 0 | 0 | 0 | True | PASS |
| 230 | 还款登记 | sc.financing.loan | 0 | 0 | 0 | True | PASS |
| 240 | 报销申请 | sc.expense.claim | 0 | 0 | 0 | True | PASS |
| 250 | 收入 | sc.receipt.income | 0 | 0 | 0 | True | PASS |
| 260 | 公司财务支出 | sc.expense.claim | 0 | 0 | 0 | True | PASS |
| 270 | 承包人还项目款 | sc.expense.claim | 0 | 0 | 0 | True | PASS |
| 280 | 承包人借项目款 | sc.financing.loan | 0 | 0 | 0 | True | PASS |
| 290 | 支付申请 | payment.request | 0 | 0 | 0 | True | PASS |
| 300 | 扣款单 | sc.tax.deduction.registration | 0 | 0 | 0 | True | PASS |
| 310 | 往来单位付款 | sc.payment.execution | 0 | 0 | 0 | True | PASS |
| 320 | 账户间资金往来 | sc.fund.account.operation | 0 | 0 | 0 | True | PASS |
| 330 | 扣款实缴登记 | sc.expense.claim | 0 | 0 | 0 | True | PASS |
| 340 | 扣款实缴退回 | sc.expense.claim | 0 | 0 | 0 | True | PASS |
| 350 | 到款确认表 | sc.legacy.fund.confirmation.document | 0 | 0 | 0 | True | PASS |
| 360 | 资金日报表 | sc.legacy.fund.daily.line | 0 | 0 | 0 | True | WARN_HIDDEN_REQUIRED_DEFAULTS |
| 370 | 项目借公司款登记 | sc.financing.loan | 0 | 0 | 0 | True | PASS |
| 380 | 项目还公司款登记 | sc.financing.loan | 0 | 0 | 0 | True | PASS |
| 390 | 开票申请 | sc.invoice.registration | 0 | 0 | 0 | True | PASS |
| 400 | 开票登记 | sc.invoice.registration | 0 | 0 | 0 | True | PASS |
| 410 | 预缴税款 | sc.invoice.registration | 0 | 0 | 3 | True | FAIL_FORM_LIST_FACTS |
| 420 | 进项上报 | sc.legacy.invoice.tax.fact | 0 | 0 | 0 | True | PASS |
| 430 | 抵扣登记 | sc.tax.deduction.registration | 0 | 0 | 0 | True | PASS |
| 440 | 外经证登记 | sc.legacy.payment.residual.fact | 0 | 0 | 0 | True | PASS |
| 450 | 供货合同分析 | sc.legacy.supplier.contract.pricing.fact | 0 | 0 | 0 | True | PASS |
| 460 | 库存统计表（新） | sc.material.stock.summary | 0 | 0 | 0 | True | PASS |
| 470 | 账户收支统计表 | sc.account.income.expense.summary | 0 | 0 | 0 | True | PASS |
| 480 | 成本统计表（综合） | sc.comprehensive.cost.summary | 0 | 0 | 0 | True | PASS |
| 490 | 投标保证金报表 | sc.tender.guarantee.summary | 0 | 0 | 0 | True | PASS |
| 500 | 发票成本进度报表 | sc.invoice.cost.progress.summary | 0 | 0 | 0 | True | PASS |
| 510 | 发票分析报表 | sc.invoice.analysis.summary | 0 | 0 | 0 | True | PASS |
| 520 | 项目经营统计表 | sc.project.operation.summary | 0 | 0 | 0 | True | PASS |
| 530 | 应收应付报表 | sc.ar.ap.report.summary | 0 | 0 | 0 | True | PASS |
| 540 | 成本大屏 | sc.dashboard.cockpit.fact | 0 | 0 | 0 | True | PASS |
| 550 | 经营大屏 | sc.operating.metrics.project | 0 | 0 | 0 | True | PASS |

## Failures

```json
[
  {
    "access_error": "",
    "attachment_required": true,
    "chatter_required": true,
    "contract_form_field_count": 58,
    "create_access": true,
    "form_arch_field_count": 47,
    "form_view_id": 0,
    "get_view_error": "",
    "group": "发票税务",
    "hidden_required_without_defaults": [],
    "list_fact_count": 14,
    "missing_list_alias_count": 3,
    "missing_list_alias_fields": [
      "p1_visible_007363f27191",
      "p1_visible_99f753ed6262",
      "p1_visible_b031dc9a8507"
    ],
    "model": "sc.invoice.registration",
    "model_missing": false,
    "name": "预缴税款",
    "old_form_field_count": 0,
    "old_label_hits": [],
    "old_label_match_count": 0,
    "old_sections": [],
    "planned_sections": [
      {
        "legacy_labels": [
          "状态",
          "项目名称",
          "单据编号",
          "受票方名称",
          "交税类型",
          "金额",
          "发票开具日期",
          "预缴税款日期",
          "完税凭证号码",
          "附件",
          "录入人"
        ],
        "sequence": 10,
        "source": "scbs_live_lowcode_config",
        "title": "老系统列表字段"
      },
      {
        "required": true,
        "sequence": 90,
        "source": "scbs_live_lowcode_config",
        "title": "附件"
      },
      {
        "required": true,
        "sequence": 100,
        "source": "unified_daily_business_form_structure",
        "title": "日志"
      }
    ],
    "seq": 410,
    "status": "FAIL_FORM_LIST_FACTS",
    "view_id": 2719
  }
]
```
