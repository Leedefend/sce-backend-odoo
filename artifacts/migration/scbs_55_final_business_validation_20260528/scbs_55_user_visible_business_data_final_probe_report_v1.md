# SCBS55 User Visible Business Data Final Probe v1

Status: REVIEW
Database: sc_demo
Generated At: 2026-05-28T08:24:48.086924+00:00

| seq | menu | model | count | fields | critical empty | hash | double | status |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 10 | 供应商/合作单位 | sc.business.entity | 39 | 12 | 0 | 0 | 0 | PASS |
| 20 | 往来单位 | sc.business.entity | 39 | 11 | 0 | 0 | 0 | PASS |
| 30 | 施工合同 | construction.contract | 9339 | 21 | 0 | 1 | 0 | REVIEW_VISIBLE_VALUE_ANOMALY |
| 40 | 公司资料存档 | sc.document.admin.document | 9049 | 7 | 0 | 0 | 0 | PASS |
| 50 | 请假/休假审批单 | sc.office.admin.document | 339 | 13 | 0 | 0 | 0 | PASS |
| 60 | 印章使用审批表 | sc.office.admin.document | 1565 | 21 | 0 | 0 | 0 | PASS |
| 70 | 组织机构 | hr.department | 28 | 0 | 0 | 0 | 0 | PASS |
| 80 | 公司人员名册（配置） | sc.legacy.user.profile | 66 | 28 | 0 | 0 | 0 | PASS |
| 90 | 社保人员登记 | sc.hr.payroll.document | 156 | 14 | 0 | 0 | 0 | PASS |
| 100 | 社保登记 | sc.hr.payroll.document | 1445 | 13 | 0 | 0 | 0 | PASS |
| 110 | 工资登记 | sc.hr.payroll.document | 3290 | 16 | 0 | 0 | 0 | PASS |
| 120 | 补助 | sc.hr.payroll.document | 116 | 11 | 0 | 0 | 0 | PASS |
| 130 | 奖金 | sc.hr.payroll.document | 0 | 8 | 0 | 0 | 0 | PASS |
| 140 | 证照登记 | sc.document.admin.document | 196 | 0 | 0 | 0 | 0 | PASS |
| 150 | 借阅申请 | sc.document.admin.document | 28 | 26 | 0 | 0 | 0 | PASS |
| 160 | 投标报名管理 | tender.bid | 2936 | 7 | 0 | 0 | 0 | PASS |
| 170 | 投标报名费申请 | tender.doc.purchase | 115 | 14 | 0 | 25 | 0 | REVIEW_VISIBLE_VALUE_ANOMALY |
| 180 | 自筹保证金 | tender.guarantee | 183 | 16 | 0 | 0 | 0 | PASS |
| 190 | 自筹保证金退回 | tender.guarantee | 183 | 15 | 0 | 0 | 0 | PASS |
| 200 | 付款还保证金 | tender.guarantee | 183 | 18 | 0 | 0 | 0 | PASS |
| 210 | 付款还保证金退回 | tender.guarantee | 183 | 14 | 0 | 0 | 0 | PASS |
| 220 | 借款申请 | sc.financing.loan | 37 | 26 | 0 | 0 | 0 | PASS |
| 230 | 还款登记 | sc.financing.loan | 24 | 12 | 0 | 0 | 0 | PASS |
| 240 | 报销申请 | sc.expense.claim | 3549 | 13 | 1 | 0 | 0 | REVIEW_CRITICAL_EMPTY |
| 250 | 收入 | sc.receipt.income | 4674 | 12 | 0 | 0 | 0 | PASS |
| 260 | 公司财务支出 | sc.expense.claim | 2656 | 12 | 3 | 0 | 0 | REVIEW_CRITICAL_EMPTY |
| 270 | 承包人还项目款 | sc.expense.claim | 84 | 14 | 2 | 0 | 0 | REVIEW_CRITICAL_EMPTY |
| 280 | 承包人借项目款 | sc.financing.loan | 166 | 12 | 0 | 0 | 0 | PASS |
| 290 | 支付申请 | payment.request | 13390 | 19 | 1 | 1 | 0 | REVIEW_CRITICAL_EMPTY |
| 300 | 扣款单 | sc.tax.deduction.registration | 137 | 10 | 0 | 0 | 0 | PASS |
| 310 | 往来单位付款 | sc.payment.execution | 6265 | 18 | 0 | 80 | 0 | REVIEW_VISIBLE_VALUE_ANOMALY |
| 320 | 账户间资金往来 | sc.fund.account.operation | 395 | 13 | 0 | 0 | 0 | PASS |
| 330 | 扣款实缴登记 | sc.expense.claim | 6364 | 11 | 0 | 0 | 0 | PASS |
| 340 | 扣款实缴退回 | sc.expense.claim | 1738 | 10 | 1 | 0 | 0 | REVIEW_CRITICAL_EMPTY |
| 350 | 到款确认表 | sc.legacy.fund.confirmation.document | 2595 | 16 | 0 | 38 | 0 | REVIEW_VISIBLE_VALUE_ANOMALY |
| 360 | 资金日报表 | sc.legacy.fund.daily.line | 7454 | 14 | 0 | 0 | 0 | PASS |
| 370 | 项目借公司款登记 | sc.financing.loan | 152 | 17 | 0 | 0 | 0 | PASS |
| 380 | 项目还公司款登记 | sc.financing.loan | 98 | 15 | 0 | 0 | 0 | PASS |
| 390 | 开票申请 | sc.invoice.registration | 225 | 17 | 1 | 0 | 0 | REVIEW_CRITICAL_EMPTY |
| 400 | 开票登记 | sc.invoice.registration | 2931 | 20 | 1 | 0 | 0 | REVIEW_CRITICAL_EMPTY |
| 410 | 预缴税款 | sc.invoice.registration | 5347 | 14 | 0 | 0 | 0 | PASS |
| 420 | 进项上报 | sc.legacy.invoice.tax.fact | 1919 | 18 | 0 | 0 | 0 | PASS |
| 430 | 抵扣登记 | sc.tax.deduction.registration | 4915 | 12 | 0 | 0 | 0 | PASS |
| 440 | 外经证登记 | sc.legacy.payment.residual.fact | 317 | 20 | 0 | 52 | 1 | REVIEW_VISIBLE_VALUE_ANOMALY |
| 450 | 供货合同分析 | sc.legacy.supplier.contract.pricing.fact | 5345 | 0 | 0 | 0 | 0 | PASS |
| 460 | 库存统计表（新） | sc.material.stock.summary | 14 | 0 | 0 | 0 | 0 | PASS |
| 470 | 账户收支统计表 | sc.account.income.expense.summary | 120 | 0 | 0 | 0 | 0 | PASS |
| 480 | 成本统计表（综合） | sc.comprehensive.cost.summary | 819 | 0 | 0 | 0 | 0 | PASS |
| 490 | 投标保证金报表 | sc.tender.guarantee.summary | 2826 | 0 | 0 | 0 | 0 | PASS |
| 500 | 发票成本进度报表 | sc.invoice.cost.progress.summary | 590 | 0 | 0 | 0 | 0 | PASS |
| 510 | 发票分析报表 | sc.invoice.analysis.summary | 596 | 0 | 0 | 0 | 0 | PASS |
| 520 | 项目经营统计表 | sc.project.operation.summary | 693 | 0 | 0 | 0 | 0 | PASS |
| 530 | 应收应付报表 | sc.ar.ap.report.summary | 195 | 0 | 0 | 0 | 0 | PASS |
| 540 | 成本大屏 | sc.dashboard.cockpit.fact | 7802 | 0 | 0 | 0 | 0 | PASS |
| 550 | 经营大屏 | sc.operating.metrics.project | 899 | 0 | 0 | 0 | 0 | PASS |

## Review Rows

```json
[
  {
    "action_id": 855,
    "contract_field_count": 21,
    "critical_empty_count": 0,
    "critical_empty_labels": [],
    "delivered_count": 9339,
    "domain": [],
    "double_display_hit_count": 0,
    "double_display_hits": [],
    "field_coverage": [
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_06fa8c6f628f",
        "filled": 80,
        "label": "单据状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_8fa8662ad38f",
        "filled": 80,
        "label": "单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_2585b4ab16bd",
        "filled": 80,
        "label": "合同订立日期",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_202b429f79ca",
        "filled": 80,
        "label": "原件是否归档",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_fadf1135d6a4",
        "filled": 80,
        "label": "发包人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3e7255522b33",
        "filled": 80,
        "label": "项目名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3ec01dd569e2",
        "filled": 80,
        "label": "合同标题",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_0965a7d1e74c",
        "filled": 80,
        "label": "工程类别",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_17b341733b7b",
        "filled": 80,
        "label": "合同编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_75e856a13c7c",
        "filled": 80,
        "label": "合同金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_58a2eb3301c1",
        "filled": 80,
        "label": "结算金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_affba7961481",
        "filled": 80,
        "label": "累计开票",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_da9d3c637407",
        "filled": 80,
        "label": "累计收款",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_75b438b16f10",
        "filled": 80,
        "label": "未收款",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_bf0c9e684289",
        "filled": 80,
        "label": "未收款比例",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_5839c15a34a4",
        "filled": 80,
        "label": "挂靠人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_0cf26c325f34",
        "filled": 80,
        "label": "工程地址",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_7b9f4bb3e3ea",
        "filled": 80,
        "label": "工程内容",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ee6a4d9e2956",
        "filled": 80,
        "label": "录入人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dfc25d77dc39",
        "filled": 80,
        "label": "录入时间",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f6fe6c41ad",
        "filled": 80,
        "label": "附件",
        "ratio": 1.0,
        "sample_size": 80
      }
    ],
    "group": "合同",
    "legacy_source_tables": [
      "T_ProjectContract_Out",
      "T_ProjectContract_Out_CB",
      "T_ProjectContract_Out_CB_BZJ"
    ],
    "missing_alias_fields": [],
    "model": "construction.contract",
    "model_missing": false,
    "name": "施工合同",
    "raw_hash_hit_count": 1,
    "raw_hash_hits": [
      {
        "id": "9352",
        "label": "附件",
        "value": "德昌供港果蔬产业融合项目施工总承包合同(1).pdf | legacy-file://UploadFile/OldSystem/File_New/OutContract/2021/5/20/a2e40baaa0198fff83e10aa80"
      }
    ],
    "sample_rows": [
      {
        "id": "9352",
        "p1_visible_06fa8c6f628f": "审核通过",
        "p1_visible_0965a7d1e74c": "CONIN2601550",
        "p1_visible_0cf26c325f34": "西昌市德昌县高速路出口处",
        "p1_visible_17b341733b7b": "DYS2021-1",
        "p1_visible_202b429f79ca": "是",
        "p1_visible_2585b4ab16bd": "2021-05-13",
        "p1_visible_3e7255522b33": "德昌供港果蔬产业融合项目（测试）",
        "p1_visible_3ec01dd569e2": "德昌供港果蔬产业融合项目",
        "p1_visible_5839c15a34a4": "CONIN2601550",
        "p1_visible_58a2eb3301c1": "0.0",
        "p1_visible_75b438b16f10": "0.0",
        "p1_visible_75e856a13c7c": "150000000.0",
        "p1_visible_7b9f4bb3e3ea": "规划总建筑面积为45000 平方米，主要为供港果蔬示范种植基地\n及该基地所带动的德昌县农户及专业合作社提供果蔬等农副产品仓储、加工、配送、\n农业科技服务、农特产品展示交易（电商）、农村金融服务、食品安全检测等综合配\n套服务，建设成为西南地区标准化的供港果蔬产业链基地。",
        "p1_visible_8fa8662ad38f": "WBHTGL-20210520-001",
        "p1_visible_99f6fe6c41ad": "德昌供港果蔬产业融合项目施工总承包合同(1).pdf | legacy-file://UploadFile/OldSystem/File_New/OutContract/2021/5/20/a2e40baaa0198fff83e10aa80dadcc63.pdf\n德昌供港果蔬产业融合项目施工总承包合同(1).pdf | legacy-file://~/File_New/OutContract/2021/5/20/a2e40baaa0198fff83e10aa80dadcc63.pdf",
        "p1_visible_affba7961481": "0.0",
        "p1_visible_bf0c9e684289": "CONIN2601550",
        "p1_visible_da9d3c637407": "0.0",
        "p1_visible_dfc25d77dc39": "2021-05-20 00:00:00",
        "p1_visible_ee6a4d9e2956": "蒋毅",
        "p1_visible_fadf1135d6a4": "中建地下空间有限公司"
      },
      {
        "id": "9341",
        "p1_visible_06fa8c6f628f": "未提交",
        "p1_visible_0965a7d1e74c": "CONOUT2607802",
        "p1_visible_0cf26c325f34": "CONOUT2607802",
        "p1_visible_17b341733b7b": "CONOUT2607802",
        "p1_visible_202b429f79ca": "否",
        "p1_visible_2585b4ab16bd": "CONOUT2607802",
        "p1_visible_3e7255522b33": "莎车县低压电力设施改造项目施工第二标段",
        "p1_visible_3ec01dd569e2": "发票关联支出合同-陕西仝禾建设工程有限责任公司新疆分公司",
        "p1_visible_5839c15a34a4": "CONOUT2607802",
        "p1_visible_58a2eb3301c1": "0.0",
        "p1_visible_75b438b16f10": "0.0",
        "p1_visible_75e856a13c7c": "0.0",
        "p1_visible_7b9f4bb3e3ea": "CONOUT2607802",
        "p1_visible_8fa8662ad38f": "CONOUT2607802",
        "p1_visible_99f6fe6c41ad": "CONOUT2607802",
        "p1_visible_affba7961481": "0.0",
        "p1_visible_bf0c9e684289": "CONOUT2607802",
        "p1_visible_da9d3c637407": "0.0",
        "p1_visible_dfc25d77dc39": "CONOUT2607802",
        "p1_visible_ee6a4d9e2956": "CONOUT2607802",
        "p1_visible_fadf1135d6a4": "陕西仝禾建设工程有限责任公司新疆分公司"
      },
      {
        "id": "9340",
        "p1_visible_06fa8c6f628f": "未提交",
        "p1_visible_0965a7d1e74c": "CONOUT2607801",
        "p1_visible_0cf26c325f34": "CONOUT2607801",
        "p1_visible_17b341733b7b": "CONOUT2607801",
        "p1_visible_202b429f79ca": "否",
        "p1_visible_2585b4ab16bd": "CONOUT2607801",
        "p1_visible_3e7255522b33": "拉萨市柳梧新区管网改造",
        "p1_visible_3ec01dd569e2": "发票关联支出合同-西藏纵驰水电工程管理有限公司",
        "p1_visible_5839c15a34a4": "CONOUT2607801",
        "p1_visible_58a2eb3301c1": "0.0",
        "p1_visible_75b438b16f10": "0.0",
        "p1_visible_75e856a13c7c": "0.0",
        "p1_visible_7b9f4bb3e3ea": "CONOUT2607801",
        "p1_visible_8fa8662ad38f": "CONOUT2607801",
        "p1_visible_99f6fe6c41ad": "CONOUT2607801",
        "p1_visible_affba7961481": "0.0",
        "p1_visible_bf0c9e684289": "CONOUT2607801",
        "p1_visible_da9d3c637407": "0.0",
        "p1_visible_dfc25d77dc39": "CONOUT2607801",
        "p1_visible_ee6a4d9e2956": "CONOUT2607801",
        "p1_visible_fadf1135d6a4": "西藏纵驰水电工程管理有限公司"
      },
      {
        "id": "9339",
        "p1_visible_06fa8c6f628f": "未提交",
        "p1_visible_0965a7d1e74c": "CONOUT2607800",
        "p1_visible_0cf26c325f34": "CONOUT2607800",
        "p1_visible_17b341733b7b": "CONOUT2607800",
        "p1_visible_202b429f79ca": "否",
        "p1_visible_2585b4ab16bd": "CONOUT2607800",
        "p1_visible_3e7255522b33": "鸿图府项目第一期建筑安装工程",
        "p1_visible_3ec01dd569e2": "发票关联支出合同-德阳市大兴设备安装有限责任公司",
        "p1_visible_5839c15a34a4": "CONOUT2607800",
        "p1_visible_58a2eb3301c1": "0.0",
        "p1_visible_75b438b16f10": "0.0",
        "p1_visible_75e856a13c7c": "0.0",
        "p1_visible_7b9f4bb3e3ea": "CONOUT2607800",
        "p1_visible_8fa8662ad38f": "CONOUT2607800",
        "p1_visible_99f6fe6c41ad": "CONOUT2607800",
        "p1_visible_affba7961481": "0.0",
        "p1_visible_bf0c9e684289": "CONOUT2607800",
        "p1_visible_da9d3c637407": "0.0",
        "p1_visible_dfc25d77dc39": "CONOUT2607800",
        "p1_visible_ee6a4d9e2956": "CONOUT2607800",
        "p1_visible_fadf1135d6a4": "德阳市大兴设备安装有限责任公司"
      },
      {
        "id": "9338",
        "p1_visible_06fa8c6f628f": "未提交",
        "p1_visible_0965a7d1e74c": "CONOUT2607799",
        "p1_visible_0cf26c325f34": "CONOUT2607799",
        "p1_visible_17b341733b7b": "CONOUT2607799",
        "p1_visible_202b429f79ca": "否",
        "p1_visible_2585b4ab16bd": "CONOUT2607799",
        "p1_visible_3e7255522b33": "鸿图府项目第一期建筑安装工程",
        "p1_visible_3ec01dd569e2": "发票关联支出合同-广东拾壹建设工程有限公司",
        "p1_visible_5839c15a34a4": "CONOUT2607799",
        "p1_visible_58a2eb3301c1": "0.0",
        "p1_visible_75b438b16f10": "0.0",
        "p1_visible_75e856a13c7c": "0.0",
        "p1_visible_7b9f4bb3e3ea": "CONOUT2607799",
        "p1_visible_8fa8662ad38f": "CONOUT2607799",
        "p1_visible_99f6fe6c41ad": "CONOUT2607799",
        "p1_visible_affba7961481": "0.0",
        "p1_visible_bf0c9e684289": "CONOUT2607799",
        "p1_visible_da9d3c637407": "0.0",
        "p1_visible_dfc25d77dc39": "CONOUT2607799",
        "p1_visible_ee6a4d9e2956": "CONOUT2607799",
        "p1_visible_fadf1135d6a4": "广东拾壹建设工程有限公司"
      }
    ],
    "seq": 30,
    "status": "REVIEW_VISIBLE_VALUE_ANOMALY",
    "view_id": 2683
  },
  {
    "action_id": 895,
    "contract_field_count": 14,
    "critical_empty_count": 0,
    "critical_empty_labels": [],
    "delivered_count": 115,
    "domain": [
      [
        "legacy_source_table",
        "in",
        [
          "BGGL_ZTBJHT_TBBM_TBBMFSQ"
        ]
      ]
    ],
    "double_display_hit_count": 0,
    "double_display_hits": [],
    "field_coverage": [
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_06fa8c6f628f",
        "filled": 80,
        "label": "单据状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3e7255522b33",
        "filled": 80,
        "label": "项目名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_8fa8662ad38f",
        "filled": 80,
        "label": "单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_880ab989a872",
        "filled": 80,
        "label": "申请人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_2c346345746e",
        "filled": 80,
        "label": "申请日期",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3e5fd432c9df",
        "filled": 78,
        "label": "收款账号",
        "ratio": 0.975,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_48a64eb40c71",
        "filled": 75,
        "label": "开户行",
        "ratio": 0.9375,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_34943c40c9af",
        "filled": 80,
        "label": "金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_e0361480e3a5",
        "filled": 75,
        "label": "备注",
        "ratio": 0.9375,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_bb7c7aeff3e4",
        "filled": 80,
        "label": "收款人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_c6b9a8cfdb21",
        "filled": 70,
        "label": "付款方式",
        "ratio": 0.875,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f6fe6c41ad",
        "filled": 80,
        "label": "附件",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ee6a4d9e2956",
        "filled": 80,
        "label": "录入人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dfc25d77dc39",
        "filled": 80,
        "label": "录入时间",
        "ratio": 1.0,
        "sample_size": 80
      }
    ],
    "group": "投标",
    "legacy_source_tables": [
      "BGGL_ZTBJHT_TBBM_TBBMFSQ"
    ],
    "missing_alias_fields": [],
    "model": "tender.doc.purchase",
    "model_missing": false,
    "name": "投标报名费申请",
    "raw_hash_hit_count": 25,
    "raw_hash_hits": [
      {
        "id": "113",
        "label": "收款账号",
        "value": "021230020120010000263034012371"
      },
      {
        "id": "106",
        "label": "收款账号",
        "value": "021230020120010000263034009269"
      },
      {
        "id": "104",
        "label": "收款账号",
        "value": "021230020120010000263034009248"
      },
      {
        "id": "101",
        "label": "收款账号",
        "value": "021230020120010000263034008550"
      },
      {
        "id": "97",
        "label": "收款账号",
        "value": "021230020120010000263034007913"
      },
      {
        "id": "94",
        "label": "附件",
        "value": "06fb224e40946eb7570e7c644dffe863.jpg | legacy-file://UploadFile/UserFile/2025/08/27/baad951e605a4de8ba84ccd77c22a05f_127"
      },
      {
        "id": "92",
        "label": "收款账号",
        "value": "021230020120010000263034006395"
      },
      {
        "id": "91",
        "label": "收款账号",
        "value": "021230020120010000263034006409"
      },
      {
        "id": "89",
        "label": "收款账号",
        "value": "021230020120010000263034005686"
      },
      {
        "id": "88",
        "label": "收款账号",
        "value": "021230020120010000263034005632"
      },
      {
        "id": "86",
        "label": "收款账号",
        "value": "021230020120010000263034004697"
      },
      {
        "id": "78",
        "label": "收款账号",
        "value": "021230020120010000263034003337"
      },
      {
        "id": "77",
        "label": "收款账号",
        "value": "021230020120010000263034003210"
      },
      {
        "id": "71",
        "label": "收款账号",
        "value": "021230020120010000263034001257"
      },
      {
        "id": "69",
        "label": "收款账号",
        "value": "021230020120010000263034000461"
      },
      {
        "id": "60",
        "label": "附件",
        "value": "37cfdfe0db684839b8722659a3aaea0.png | legacy-file://UploadFile/UserFile/2023/10/12/c28a87f3099c4725b78187e5caa910d4_6048"
      },
      {
        "id": "59",
        "label": "附件",
        "value": "f4abd661008621c447914e2aaf2c174.png | legacy-file://UploadFile/UserFile/2023/10/12/d4ac91395e904cabbf16847fdd54c9b9_8302"
      },
      {
        "id": "58",
        "label": "附件",
        "value": "fcc3cee9cebbfab3444d96a3fdda343.png | legacy-file://UploadFile/UserFile/2023/09/28/2d6987f728f549c48a78c0af506ff7c6_1841"
      },
      {
        "id": "51",
        "label": "附件",
        "value": "6.27-保盛-中国电信股份有限公司喀什分公司2023年大众蓝湾和色利比亚模块局电力引入改造施工项目.docx | legacy-file://UploadFile/OldSystem/File_New/ExpensesClaim/2023"
      },
      {
        "id": "50",
        "label": "附件",
        "value": "6.20-保盛-中国电信股份有限公司喀什分公司2023年大众蓝湾和色利比亚模块局电力引入改造施工项目.docx | legacy-file://UploadFile/OldSystem/File_New/ExpensesClaim/2023"
      }
    ],
    "sample_rows": [
      {
        "id": "115",
        "p1_visible_06fa8c6f628f": "已通过",
        "p1_visible_2c346345746e": "2026-04-09",
        "p1_visible_34943c40c9af": "40.0",
        "p1_visible_3e5fd432c9df": "9902001847235817",
        "p1_visible_3e7255522b33": "公司综合平台",
        "p1_visible_48a64eb40c71": "中国民生银行股份有限公司成都分行营业部",
        "p1_visible_880ab989a872": "张文翠",
        "p1_visible_8fa8662ad38f": "TBBMFSQ-20260409-001",
        "p1_visible_99f6fe6c41ad": "历史附件",
        "p1_visible_bb7c7aeff3e4": "四川华西数产科技集团有限公司",
        "p1_visible_c6b9a8cfdb21": "基本户转账缴纳",
        "p1_visible_dfc25d77dc39": "2026-04-09 00:00:00",
        "p1_visible_e0361480e3a5": "A项目-室内装饰装修专业分包(2号楼、6号楼、7号楼)装修材料采购招标标书费",
        "p1_visible_ee6a4d9e2956": "张文翠"
      },
      {
        "id": "114",
        "p1_visible_06fa8c6f628f": "已通过",
        "p1_visible_2c346345746e": "2026-04-09",
        "p1_visible_34943c40c9af": "40.0",
        "p1_visible_3e5fd432c9df": "9902001847238589",
        "p1_visible_3e7255522b33": "公司综合平台",
        "p1_visible_48a64eb40c71": "中国民生银行股份有限公司成都分行营业部",
        "p1_visible_880ab989a872": "张文翠",
        "p1_visible_8fa8662ad38f": "TBBMFSQ-20260409-002",
        "p1_visible_99f6fe6c41ad": "历史附件",
        "p1_visible_bb7c7aeff3e4": "四川华西数产科技集团有限公司",
        "p1_visible_c6b9a8cfdb21": "基本户转账缴纳",
        "p1_visible_dfc25d77dc39": "2026-04-09 00:00:00",
        "p1_visible_e0361480e3a5": "德阳文德中学建设项目设计施工德阳文德中学建设项目设计施工幕墙专业分包招标标书费",
        "p1_visible_ee6a4d9e2956": "张文翠"
      },
      {
        "id": "113",
        "p1_visible_06fa8c6f628f": "已通过",
        "p1_visible_2c346345746e": "2026-03-23",
        "p1_visible_34943c40c9af": "300.0",
        "p1_visible_3e5fd432c9df": "021230020120010000263034012371",
        "p1_visible_3e7255522b33": "公司综合平台",
        "p1_visible_48a64eb40c71": "成都农商银行玉林支行",
        "p1_visible_880ab989a872": "张文翠",
        "p1_visible_8fa8662ad38f": "TBBMFSQ-20260323-001",
        "p1_visible_99f6fe6c41ad": "历史附件",
        "p1_visible_bb7c7aeff3e4": "成都农村产权交易所有限责任公司",
        "p1_visible_c6b9a8cfdb21": "基本户转账缴纳",
        "p1_visible_dfc25d77dc39": "2026-03-23 00:00:00",
        "p1_visible_e0361480e3a5": "旌阳区德新镇国家农业产业强镇建设二期稻谷产地初加工提升项目（工程建设）标书费",
        "p1_visible_ee6a4d9e2956": "张文翠"
      },
      {
        "id": "112",
        "p1_visible_06fa8c6f628f": "已通过",
        "p1_visible_2c346345746e": "2026-03-11",
        "p1_visible_34943c40c9af": "500.0",
        "p1_visible_3e5fd432c9df": "9902001845181153",
        "p1_visible_3e7255522b33": "公司综合平台",
        "p1_visible_48a64eb40c71": "中国民生银行股份有限公司成都分行营业部",
        "p1_visible_880ab989a872": "张文翠",
        "p1_visible_8fa8662ad38f": "TBBMFSQ-20260311-001",
        "p1_visible_99f6fe6c41ad": "历史附件",
        "p1_visible_bb7c7aeff3e4": "蜀道投资集团有限责任公司材料集采分公司",
        "p1_visible_c6b9a8cfdb21": "基本户转账缴纳",
        "p1_visible_dfc25d77dc39": "2026-03-11 00:00:00",
        "p1_visible_e0361480e3a5": "G108线广汉市向阳镇瓦店村至向阳镇江南村段中修工程、S108线广汉市高坪镇万柏村至高坪镇双石村段中修工程项目劳务合作（第二次）标书费",
        "p1_visible_ee6a4d9e2956": "张文翠"
      },
      {
        "id": "111",
        "p1_visible_06fa8c6f628f": "已通过",
        "p1_visible_2c346345746e": "2026-01-19",
        "p1_visible_34943c40c9af": "500.0",
        "p1_visible_3e5fd432c9df": "9902001841589565",
        "p1_visible_3e7255522b33": "公司综合平台",
        "p1_visible_48a64eb40c71": "中国民生银行股份有限公司成都分行营业部",
        "p1_visible_880ab989a872": "张文翠",
        "p1_visible_8fa8662ad38f": "TBBMFSQ-20260119-001",
        "p1_visible_99f6fe6c41ad": "历史附件",
        "p1_visible_bb7c7aeff3e4": "蜀道投资集团有限责任公司材料集采分公司",
        "p1_visible_c6b9a8cfdb21": "基本户转账缴纳",
        "p1_visible_dfc25d77dc39": "2026-01-19 00:00:00",
        "p1_visible_e0361480e3a5": "G108线广汉市向阳镇瓦店村至向阳镇江南村段中修工程、S108线广汉市高坪镇万柏村至高坪镇双石村段中修工程项目标书费",
        "p1_visible_ee6a4d9e2956": "张文翠"
      }
    ],
    "seq": 170,
    "status": "REVIEW_VISIBLE_VALUE_ANOMALY",
    "view_id": 2723
  },
  {
    "action_id": 874,
    "contract_field_count": 13,
    "critical_empty_count": 1,
    "critical_empty_labels": [
      "附件"
    ],
    "delivered_count": 3549,
    "domain": [
      [
        "legacy_source_table",
        "in",
        [
          "CWGL_FYBX",
          "CWGL_FYBX_CB"
        ]
      ]
    ],
    "double_display_hit_count": 0,
    "double_display_hits": [],
    "field_coverage": [
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_06fa8c6f628f",
        "filled": 80,
        "label": "单据状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_8fa8662ad38f",
        "filled": 80,
        "label": "单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_2559d3f7672e",
        "filled": 80,
        "label": "所属公司",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_b6fed9af8313",
        "filled": 80,
        "label": "日期",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_91061a56c00f",
        "filled": 80,
        "label": "部门",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_2607f43202a3",
        "filled": 80,
        "label": "报销人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_c33f247470b1",
        "filled": 80,
        "label": "报销类别",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ce44aa844fbd",
        "filled": 80,
        "label": "事项说明",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_f79e589b11f6",
        "filled": 80,
        "label": "报销金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_bb7c7aeff3e4",
        "filled": 59,
        "label": "收款人",
        "ratio": 0.7375,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f6fe6c41ad",
        "filled": 0,
        "label": "附件",
        "ratio": 0.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ee6a4d9e2956",
        "filled": 80,
        "label": "录入人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dfc25d77dc39",
        "filled": 80,
        "label": "录入时间",
        "ratio": 1.0,
        "sample_size": 80
      }
    ],
    "group": "费用报销",
    "legacy_source_tables": [
      "CWGL_FYBX",
      "CWGL_FYBX_CB"
    ],
    "missing_alias_fields": [],
    "model": "sc.expense.claim",
    "model_missing": false,
    "name": "报销申请",
    "raw_hash_hit_count": 0,
    "raw_hash_hits": [],
    "sample_rows": [
      {
        "id": "3583",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_2559d3f7672e": "四川保盛建设集团有限公司",
        "p1_visible_2607f43202a3": "徐丹",
        "p1_visible_8fa8662ad38f": "FYBX-20240312-001",
        "p1_visible_91061a56c00f": "LEG-EXP-FYBX-20240312-001",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_b6fed9af8313": "2024-03-12",
        "p1_visible_bb7c7aeff3e4": "成都市筑信职业技能培训学校",
        "p1_visible_c33f247470b1": "教育培训费",
        "p1_visible_ce44aa844fbd": "何翔宇安C继教，之前挂在四公司用",
        "p1_visible_dfc25d77dc39": "2024-03-12 16:03:41",
        "p1_visible_ee6a4d9e2956": "徐丹",
        "p1_visible_f79e589b11f6": "200.0"
      },
      {
        "id": "3582",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_2559d3f7672e": "四川保盛建设集团有限公司",
        "p1_visible_2607f43202a3": "段奕俊",
        "p1_visible_8fa8662ad38f": "FYBX-20260330-002",
        "p1_visible_91061a56c00f": "LEG-EXP-FYBX-20260330-002",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_b6fed9af8313": "2026-03-30",
        "p1_visible_bb7c7aeff3e4": "",
        "p1_visible_c33f247470b1": "交通费",
        "p1_visible_ce44aa844fbd": "北京-成都飞机票",
        "p1_visible_dfc25d77dc39": "2026-03-30 11:41:07",
        "p1_visible_ee6a4d9e2956": "段奕俊",
        "p1_visible_f79e589b11f6": "2428.0"
      },
      {
        "id": "3581",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_2559d3f7672e": "四川保盛建设集团有限公司",
        "p1_visible_2607f43202a3": "段奕俊",
        "p1_visible_8fa8662ad38f": "FYBX-20240318-003",
        "p1_visible_91061a56c00f": "LEG-EXP-FYBX-20240318-003",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_b6fed9af8313": "2024-03-18",
        "p1_visible_bb7c7aeff3e4": "",
        "p1_visible_c33f247470b1": "办公费",
        "p1_visible_ce44aa844fbd": "百度云网盘会员，用于同步备份公司群晖资料",
        "p1_visible_dfc25d77dc39": "2024-03-18 17:23:50",
        "p1_visible_ee6a4d9e2956": "段奕俊",
        "p1_visible_f79e589b11f6": "188.0"
      },
      {
        "id": "3580",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_2559d3f7672e": "四川保盛建设集团有限公司",
        "p1_visible_2607f43202a3": "段奕俊",
        "p1_visible_8fa8662ad38f": "FYBX-20250212-002",
        "p1_visible_91061a56c00f": "LEG-EXP-FYBX-20250212-002",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_b6fed9af8313": "2025-02-12",
        "p1_visible_bb7c7aeff3e4": "",
        "p1_visible_c33f247470b1": "交通费",
        "p1_visible_ce44aa844fbd": "油费5000元（2025.1.1-2025.6.30）",
        "p1_visible_dfc25d77dc39": "2025-02-12 15:09:53",
        "p1_visible_ee6a4d9e2956": "段奕俊",
        "p1_visible_f79e589b11f6": "5000.0"
      },
      {
        "id": "3579",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_2559d3f7672e": "四川保盛建设集团有限公司",
        "p1_visible_2607f43202a3": "刘汉丹",
        "p1_visible_8fa8662ad38f": "SCZHBX-20221202-001",
        "p1_visible_91061a56c00f": "LEG-EXP-SCZHBX-20221202-001",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_b6fed9af8313": "2022-12-01",
        "p1_visible_bb7c7aeff3e4": "四川省水利人才资源开发与档案中心",
        "p1_visible_c33f247470b1": "教育培训费",
        "p1_visible_ce44aa844fbd": "公司水安三类人员参加2023年度的继续教育培训",
        "p1_visible_dfc25d77dc39": "2022-12-02 10:06:13",
        "p1_visible_ee6a4d9e2956": "刘汉丹",
        "p1_visible_f79e589b11f6": "9120.0"
      }
    ],
    "seq": 240,
    "status": "REVIEW_CRITICAL_EMPTY",
    "view_id": 2702
  },
  {
    "action_id": 876,
    "contract_field_count": 12,
    "critical_empty_count": 3,
    "critical_empty_labels": [
      "付款账户名称",
      "录入时间",
      "附件"
    ],
    "delivered_count": 2656,
    "domain": [
      [
        "legacy_source_table",
        "in",
        [
          "C_CWSFK_GSCWZC"
        ]
      ]
    ],
    "double_display_hit_count": 0,
    "double_display_hits": [],
    "field_coverage": [
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_06fa8c6f628f",
        "filled": 80,
        "label": "单据状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_f22832ce4781",
        "filled": 80,
        "label": "推送结果",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_8fa8662ad38f",
        "filled": 80,
        "label": "单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_334ddb69d3cf",
        "filled": 80,
        "label": "付款时间",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_d890d302f7f7",
        "filled": 80,
        "label": "付款金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_80e3d15acaa8",
        "filled": 80,
        "label": "成本类别",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_533775096e5b",
        "filled": 78,
        "label": "收款单位名称",
        "ratio": 0.975,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dacbd33c31fd",
        "filled": 0,
        "label": "付款账户名称",
        "ratio": 0.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_e0361480e3a5",
        "filled": 80,
        "label": "备注",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ee6a4d9e2956",
        "filled": 0,
        "label": "录入人",
        "ratio": 0.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dfc25d77dc39",
        "filled": 0,
        "label": "录入时间",
        "ratio": 0.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f6fe6c41ad",
        "filled": 0,
        "label": "附件",
        "ratio": 0.0,
        "sample_size": 80
      }
    ],
    "group": "收支",
    "legacy_source_tables": [
      "C_CWSFK_GSCWZC"
    ],
    "missing_alias_fields": [],
    "model": "sc.expense.claim",
    "model_missing": false,
    "name": "公司财务支出",
    "raw_hash_hit_count": 0,
    "raw_hash_hits": [],
    "sample_rows": [
      {
        "id": "6239",
        "p1_visible_06fa8c6f628f": "0",
        "p1_visible_334ddb69d3cf": "LEG-DEP-GSCWZC-20231008-001",
        "p1_visible_533775096e5b": "深圳市华商工程担保有限公司",
        "p1_visible_80e3d15acaa8": "company_financial_outflow",
        "p1_visible_8fa8662ad38f": "GSCWZC-20231008-001",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_d890d302f7f7": "200.0",
        "p1_visible_dacbd33c31fd": "",
        "p1_visible_dfc25d77dc39": "",
        "p1_visible_e0361480e3a5": "[migration:expense_claim] legacy_record_id=7934a3d2e1734dcda7aff37e05aab4cd; legacy_project_id=7fa974d0bc674fb48bd98beaad6825ab; source_family=company_financial_outflow; direction=outflow; historical_runtime_projection=true",
        "p1_visible_ee6a4d9e2956": "",
        "p1_visible_f22832ce4781": "0"
      },
      {
        "id": "6238",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_334ddb69d3cf": "LEG-DEP-CWZC-20230321-00004",
        "p1_visible_533775096e5b": "兴业银行",
        "p1_visible_80e3d15acaa8": "company_financial_outflow",
        "p1_visible_8fa8662ad38f": "CWZC-20230321-00004",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_d890d302f7f7": "1.0",
        "p1_visible_dacbd33c31fd": "",
        "p1_visible_dfc25d77dc39": "",
        "p1_visible_e0361480e3a5": "[migration:expense_claim] legacy_record_id=fff5e44563b344bb90069a6e08fa51d4; legacy_project_id=fb0c4133-f011-44a4-a285-59cfd30aec27; source_family=company_financial_outflow; direction=outflow; historical_runtime_projection=true",
        "p1_visible_ee6a4d9e2956": "",
        "p1_visible_f22832ce4781": "2"
      },
      {
        "id": "6237",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_334ddb69d3cf": "LEG-DEP-CWZC-20230419-00001",
        "p1_visible_533775096e5b": "徐丹",
        "p1_visible_80e3d15acaa8": "company_financial_outflow",
        "p1_visible_8fa8662ad38f": "CWZC-20230419-00001",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_d890d302f7f7": "1025.0",
        "p1_visible_dacbd33c31fd": "",
        "p1_visible_dfc25d77dc39": "",
        "p1_visible_e0361480e3a5": "[migration:expense_claim] legacy_record_id=ffc0a751ccf645febdfe4e0759d7c17b; legacy_project_id=fb0c4133-f011-44a4-a285-59cfd30aec27; source_family=company_financial_outflow; direction=outflow; historical_runtime_projection=true",
        "p1_visible_ee6a4d9e2956": "",
        "p1_visible_f22832ce4781": "2"
      },
      {
        "id": "6236",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_334ddb69d3cf": "LEG-DEP-GSCWZC-20240515-044",
        "p1_visible_533775096e5b": "税务局",
        "p1_visible_80e3d15acaa8": "company_financial_outflow",
        "p1_visible_8fa8662ad38f": "GSCWZC-20240515-044",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_d890d302f7f7": "31067.17",
        "p1_visible_dacbd33c31fd": "",
        "p1_visible_dfc25d77dc39": "",
        "p1_visible_e0361480e3a5": "[migration:expense_claim] legacy_record_id=ffb86429d36348628f33a9af9a8448bc; legacy_project_id=fb0c4133-f011-44a4-a285-59cfd30aec27; source_family=company_financial_outflow; direction=outflow; historical_runtime_projection=true",
        "p1_visible_ee6a4d9e2956": "",
        "p1_visible_f22832ce4781": "2"
      },
      {
        "id": "6235",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_334ddb69d3cf": "LEG-DEP-CWZC-20200323-00029",
        "p1_visible_533775096e5b": "四川省建设网",
        "p1_visible_80e3d15acaa8": "company_financial_outflow",
        "p1_visible_8fa8662ad38f": "CWZC-20200323-00029",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_d890d302f7f7": "1963.0",
        "p1_visible_dacbd33c31fd": "",
        "p1_visible_dfc25d77dc39": "",
        "p1_visible_e0361480e3a5": "[migration:expense_claim] legacy_record_id=ff91df7affb44caf84977ff7d777388b; legacy_project_id=fb0c4133-f011-44a4-a285-59cfd30aec27; source_family=company_financial_outflow; direction=outflow; historical_runtime_projection=true",
        "p1_visible_ee6a4d9e2956": "",
        "p1_visible_f22832ce4781": "2"
      }
    ],
    "seq": 260,
    "status": "REVIEW_CRITICAL_EMPTY",
    "view_id": 2704
  },
  {
    "action_id": 896,
    "contract_field_count": 14,
    "critical_empty_count": 2,
    "critical_empty_labels": [
      "附件",
      "录入时间"
    ],
    "delivered_count": 84,
    "domain": [
      [
        "claim_type",
        "=",
        "project_company_repay"
      ],
      [
        "expense_type",
        "=",
        "还款登记"
      ]
    ],
    "double_display_hit_count": 0,
    "double_display_hits": [],
    "field_coverage": [
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_06fa8c6f628f",
        "filled": 80,
        "label": "单据状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_8fa8662ad38f",
        "filled": 80,
        "label": "单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3e7255522b33",
        "filled": 80,
        "label": "项目名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_f65ab1a8427f",
        "filled": 48,
        "label": "借款人",
        "ratio": 0.6,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_f75550069cae",
        "filled": 80,
        "label": "借款金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_9c075c710f62",
        "filled": 80,
        "label": "还款金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_7c49c8f25a7a",
        "filled": 80,
        "label": "用途",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_f13b158f80f7",
        "filled": 51,
        "label": "借款利率",
        "ratio": 0.6375,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_a5b7f233fadc",
        "filled": 51,
        "label": "利息",
        "ratio": 0.6375,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dca067f698a7",
        "filled": 80,
        "label": "还款时间",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_e0361480e3a5",
        "filled": 80,
        "label": "备注",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f6fe6c41ad",
        "filled": 0,
        "label": "附件",
        "ratio": 0.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ee6a4d9e2956",
        "filled": 48,
        "label": "录入人",
        "ratio": 0.6,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dfc25d77dc39",
        "filled": 0,
        "label": "录入时间",
        "ratio": 0.0,
        "sample_size": 80
      }
    ],
    "group": "项目资金",
    "legacy_source_tables": [
      "ZJGL_ZCDFSZ_FXJK_HK"
    ],
    "missing_alias_fields": [],
    "model": "sc.expense.claim",
    "model_missing": false,
    "name": "承包人还项目款",
    "raw_hash_hit_count": 0,
    "raw_hash_hits": [],
    "sample_rows": [
      {
        "id": "43766",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_3e7255522b33": "四川现代农业工程职业学院一期工程（10#教学楼、培训中心）",
        "p1_visible_7c49c8f25a7a": "借现代农业学院工程款",
        "p1_visible_8fa8662ad38f": "HK-20210204-015",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_9c075c710f62": "494903.77",
        "p1_visible_a5b7f233fadc": "誉城国际项目还款",
        "p1_visible_dca067f698a7": "2020-08-03",
        "p1_visible_dfc25d77dc39": "",
        "p1_visible_e0361480e3a5": "誉城国际项目还款",
        "p1_visible_ee6a4d9e2956": "四川保盛建设集团有限公司",
        "p1_visible_f13b158f80f7": "誉城国际项目还款",
        "p1_visible_f65ab1a8427f": "四川保盛建设集团有限公司",
        "p1_visible_f75550069cae": "494903.77"
      },
      {
        "id": "43765",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_3e7255522b33": "【广州市花都区殡仪馆迁建工程施工总承包】项目【室外（园建、绿化、道路及护坡工程）】工程",
        "p1_visible_7c49c8f25a7a": "甲方借款",
        "p1_visible_8fa8662ad38f": "HK-20210206-002",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_9c075c710f62": "300000.0",
        "p1_visible_a5b7f233fadc": "郑常茂还借款",
        "p1_visible_dca067f698a7": "2020-08-18",
        "p1_visible_dfc25d77dc39": "",
        "p1_visible_e0361480e3a5": "郑常茂还借款",
        "p1_visible_ee6a4d9e2956": "四川保盛建设集团有限公司",
        "p1_visible_f13b158f80f7": "郑常茂还借款",
        "p1_visible_f65ab1a8427f": "四川保盛建设集团有限公司",
        "p1_visible_f75550069cae": "300000.0"
      },
      {
        "id": "43764",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_3e7255522b33": "四川现代农业工程职业学院一期工程（10#教学楼、培训中心）",
        "p1_visible_7c49c8f25a7a": "借现代农业学院工程款",
        "p1_visible_8fa8662ad38f": "HK-20210204-014",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_9c075c710f62": "2248001.92",
        "p1_visible_a5b7f233fadc": "誉城国际项目还款",
        "p1_visible_dca067f698a7": "2020-08-19",
        "p1_visible_dfc25d77dc39": "",
        "p1_visible_e0361480e3a5": "誉城国际项目还款",
        "p1_visible_ee6a4d9e2956": "四川保盛建设集团有限公司",
        "p1_visible_f13b158f80f7": "誉城国际项目还款",
        "p1_visible_f65ab1a8427f": "四川保盛建设集团有限公司",
        "p1_visible_f75550069cae": "2248001.92"
      },
      {
        "id": "43763",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_3e7255522b33": "四川现代农业工程职业学院一期工程（10#教学楼、培训中心）",
        "p1_visible_7c49c8f25a7a": "借现代农业学院工程款",
        "p1_visible_8fa8662ad38f": "HK-20210204-013",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_9c075c710f62": "2473123.85",
        "p1_visible_a5b7f233fadc": "誉城国际项目还款",
        "p1_visible_dca067f698a7": "2020-08-31",
        "p1_visible_dfc25d77dc39": "",
        "p1_visible_e0361480e3a5": "誉城国际项目还款",
        "p1_visible_ee6a4d9e2956": "四川保盛建设集团有限公司",
        "p1_visible_f13b158f80f7": "誉城国际项目还款",
        "p1_visible_f65ab1a8427f": "四川保盛建设集团有限公司",
        "p1_visible_f75550069cae": "2473123.85"
      },
      {
        "id": "43762",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_3e7255522b33": "誉城国际一期二批次",
        "p1_visible_7c49c8f25a7a": "借誉城国际工程款付材料款",
        "p1_visible_8fa8662ad38f": "HK-20210204-002",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_9c075c710f62": "71640.41",
        "p1_visible_a5b7f233fadc": "现代农业学院还借款",
        "p1_visible_dca067f698a7": "2020-09-08",
        "p1_visible_dfc25d77dc39": "",
        "p1_visible_e0361480e3a5": "现代农业学院还借款",
        "p1_visible_ee6a4d9e2956": "四川保盛建设集团有限公司",
        "p1_visible_f13b158f80f7": "现代农业学院还借款",
        "p1_visible_f65ab1a8427f": "四川保盛建设集团有限公司",
        "p1_visible_f75550069cae": "71640.41"
      }
    ],
    "seq": 270,
    "status": "REVIEW_CRITICAL_EMPTY",
    "view_id": 2724
  },
  {
    "action_id": 879,
    "contract_field_count": 19,
    "critical_empty_count": 1,
    "critical_empty_labels": [
      "附件"
    ],
    "delivered_count": 13390,
    "domain": [
      [
        "legacy_source_table",
        "in",
        [
          "C_ZFSQGL",
          "C_ZFSQGL_CB"
        ]
      ]
    ],
    "double_display_hit_count": 0,
    "double_display_hits": [],
    "field_coverage": [
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_06fa8c6f628f",
        "filled": 80,
        "label": "单据状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_8fa8662ad38f",
        "filled": 80,
        "label": "单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3e7255522b33",
        "filled": 80,
        "label": "项目名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_2c346345746e",
        "filled": 80,
        "label": "申请日期",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ccfa1326c88f",
        "filled": 80,
        "label": "收款单位",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_c00fc55a25b8",
        "filled": 80,
        "label": "申请付款金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_9469a2ad32f8",
        "filled": 80,
        "label": "实际付款金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ae1abe750af6",
        "filled": 80,
        "label": "可用余额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_63c5facb9f66",
        "filled": 80,
        "label": "成本分类名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_e0361480e3a5",
        "filled": 80,
        "label": "备注",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_1874b0ce5103",
        "filled": 80,
        "label": "是否关联单据",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3759fcfc297a",
        "filled": 79,
        "label": "付款账号",
        "ratio": 0.9875,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_6cf6e39bece9",
        "filled": 80,
        "label": "金额大写",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_a103d7cee046",
        "filled": 80,
        "label": "户名",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_48a64eb40c71",
        "filled": 48,
        "label": "开户行",
        "ratio": 0.6,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_901384917949",
        "filled": 67,
        "label": "账号",
        "ratio": 0.8375,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_71e47f617269",
        "filled": 80,
        "label": "填写人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f6fe6c41ad",
        "filled": 0,
        "label": "附件",
        "ratio": 0.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dfc25d77dc39",
        "filled": 80,
        "label": "录入时间",
        "ratio": 1.0,
        "sample_size": 80
      }
    ],
    "group": "付款",
    "legacy_source_tables": [
      "C_ZFSQGL",
      "C_ZFSQGL_CB"
    ],
    "missing_alias_fields": [],
    "model": "payment.request",
    "model_missing": false,
    "name": "支付申请",
    "raw_hash_hit_count": 1,
    "raw_hash_hits": [
      {
        "id": "32026",
        "label": "项目名称",
        "value": "9280cb5630cf4c97b242976bf616f696"
      }
    ],
    "sample_rows": [
      {
        "id": "32050",
        "p1_visible_06fa8c6f628f": "已审核",
        "p1_visible_1874b0ce5103": "否",
        "p1_visible_2c346345746e": "2022-05-17",
        "p1_visible_3759fcfc297a": "1001 1000 0000 1931",
        "p1_visible_3e7255522b33": "米易县南部新城市政道路及生态湿地公园PPP项目-湿地公园建设项目",
        "p1_visible_48a64eb40c71": "中国农业银行",
        "p1_visible_63c5facb9f66": "零星材料款",
        "p1_visible_6cf6e39bece9": "壹万贰仟壹佰柒拾肆元叁角整",
        "p1_visible_71e47f617269": "文楠",
        "p1_visible_8fa8662ad38f": "PRQ2632050",
        "p1_visible_901384917949": "6228 4824 4945 7867 874",
        "p1_visible_9469a2ad32f8": "0.0",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_a103d7cee046": "凌均明",
        "p1_visible_ae1abe750af6": "0.0",
        "p1_visible_c00fc55a25b8": "12174.3",
        "p1_visible_ccfa1326c88f": "凌均明",
        "p1_visible_dfc25d77dc39": "2022-05-17 11:55:22",
        "p1_visible_e0361480e3a5": "收工程款，付管材进度款。"
      },
      {
        "id": "32049",
        "p1_visible_06fa8c6f628f": "已审核",
        "p1_visible_1874b0ce5103": "否",
        "p1_visible_2c346345746e": "2020-12-03",
        "p1_visible_3759fcfc297a": "1001 1000 0000 1931",
        "p1_visible_3e7255522b33": "喜德县2018年第二批农村公路工程尼波镇打尔村-甘洛村水泥路改建工程",
        "p1_visible_48a64eb40c71": "中国农业银行股份有限公司西昌南坛",
        "p1_visible_63c5facb9f66": "砂石款",
        "p1_visible_6cf6e39bece9": "壹拾壹万捌仟元整",
        "p1_visible_71e47f617269": "文楠",
        "p1_visible_8fa8662ad38f": "PRQ2632049",
        "p1_visible_901384917949": "6228 4809 6963 1383 177",
        "p1_visible_9469a2ad32f8": "0.0",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_a103d7cee046": "史大忠",
        "p1_visible_ae1abe750af6": "0.0",
        "p1_visible_c00fc55a25b8": "118000.0",
        "p1_visible_ccfa1326c88f": "史大忠",
        "p1_visible_dfc25d77dc39": "2020-12-03 09:46:26",
        "p1_visible_e0361480e3a5": "收工程款，付砂石款"
      },
      {
        "id": "32048",
        "p1_visible_06fa8c6f628f": "已审核",
        "p1_visible_1874b0ce5103": "否",
        "p1_visible_2c346345746e": "2020-04-09",
        "p1_visible_3759fcfc297a": "1001 1000 0000 1931",
        "p1_visible_3e7255522b33": "八角片区小街小巷道路改造工程",
        "p1_visible_48a64eb40c71": "",
        "p1_visible_63c5facb9f66": "农民工专户",
        "p1_visible_6cf6e39bece9": "玖拾捌万玖仟玖佰肆拾肆元捌角陆分",
        "p1_visible_71e47f617269": "焦玲",
        "p1_visible_8fa8662ad38f": "PRQ2632048",
        "p1_visible_901384917949": "30-506201040020631",
        "p1_visible_9469a2ad32f8": "0.0",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_a103d7cee046": "农民工专户",
        "p1_visible_ae1abe750af6": "0.0",
        "p1_visible_c00fc55a25b8": "989944.86",
        "p1_visible_ccfa1326c88f": "农民工专户",
        "p1_visible_dfc25d77dc39": "2020-04-09 17:42:21",
        "p1_visible_e0361480e3a5": "补录20年农民工专户工程款"
      },
      {
        "id": "32047",
        "p1_visible_06fa8c6f628f": "已审核",
        "p1_visible_1874b0ce5103": "否",
        "p1_visible_2c346345746e": "2020-08-19",
        "p1_visible_3759fcfc297a": "1001 1000 0000 1931",
        "p1_visible_3e7255522b33": "中江县仓山镇郪江桥梁工程",
        "p1_visible_48a64eb40c71": "中国建设银行成都第二支行",
        "p1_visible_63c5facb9f66": "石材",
        "p1_visible_6cf6e39bece9": "壹拾万元整",
        "p1_visible_71e47f617269": "焦玲",
        "p1_visible_8fa8662ad38f": "PRQ2632047",
        "p1_visible_901384917949": "6217 0038 0000 0998 538",
        "p1_visible_9469a2ad32f8": "0.0",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_a103d7cee046": "罗俊豪",
        "p1_visible_ae1abe750af6": "0.0",
        "p1_visible_c00fc55a25b8": "100000.0",
        "p1_visible_ccfa1326c88f": "罗俊豪",
        "p1_visible_dfc25d77dc39": "2020-08-19 14:34:30",
        "p1_visible_e0361480e3a5": "自筹转入，付石料款"
      },
      {
        "id": "32046",
        "p1_visible_06fa8c6f628f": "已审核",
        "p1_visible_1874b0ce5103": "否",
        "p1_visible_2c346345746e": "2022-04-12",
        "p1_visible_3759fcfc297a": "1001 1000 0000 1931",
        "p1_visible_3e7255522b33": "洛浦县市政基础设施建设及配套项目（施工一标段）",
        "p1_visible_48a64eb40c71": "",
        "p1_visible_63c5facb9f66": "运输费",
        "p1_visible_6cf6e39bece9": "壹拾伍万元整",
        "p1_visible_71e47f617269": "文楠",
        "p1_visible_8fa8662ad38f": "PRQ2632046",
        "p1_visible_901384917949": "1001 1000 0000 1931",
        "p1_visible_9469a2ad32f8": "0.0",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_a103d7cee046": "陈康",
        "p1_visible_ae1abe750af6": "0.0",
        "p1_visible_c00fc55a25b8": "150000.0",
        "p1_visible_ccfa1326c88f": "陈康",
        "p1_visible_dfc25d77dc39": "2022-04-12 14:12:38",
        "p1_visible_e0361480e3a5": "收工程款，付运输费。"
      }
    ],
    "seq": 290,
    "status": "REVIEW_CRITICAL_EMPTY",
    "view_id": 2707
  },
  {
    "action_id": 881,
    "contract_field_count": 18,
    "critical_empty_count": 0,
    "critical_empty_labels": [],
    "delivered_count": 6265,
    "domain": [
      [
        "legacy_source_table",
        "in",
        [
          "T_FK_SUPPLIER",
          "T_FK_Supplier_CB"
        ]
      ]
    ],
    "double_display_hit_count": 0,
    "double_display_hits": [],
    "field_coverage": [
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_06fa8c6f628f",
        "filled": 80,
        "label": "单据状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_f22832ce4781",
        "filled": 80,
        "label": "推送结果",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_7f5da566c14e",
        "filled": 80,
        "label": "金蝶单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_8fa8662ad38f",
        "filled": 80,
        "label": "单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_80f75ce4d56c",
        "filled": 80,
        "label": "項目名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_cf44ec3f55f9",
        "filled": 80,
        "label": "供应商名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_058f511c98cf",
        "filled": 80,
        "label": "付款日期",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_d890d302f7f7",
        "filled": 80,
        "label": "付款金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_e0361480e3a5",
        "filled": 80,
        "label": "备注",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_514ce8cde553",
        "filled": 80,
        "label": "其他备注",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_f35ba3fab897",
        "filled": 80,
        "label": "付款方式名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_71e47f617269",
        "filled": 80,
        "label": "填写人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_48a64eb40c71",
        "filled": 80,
        "label": "开户行",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_c3d92b20c8a3",
        "filled": 80,
        "label": "账户",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_48eb67df430f",
        "filled": 80,
        "label": "付款账户",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dacbd33c31fd",
        "filled": 80,
        "label": "付款账户名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_a4aa6578aa87",
        "filled": 80,
        "label": "支付申请单号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f6fe6c41ad",
        "filled": 80,
        "label": "附件",
        "ratio": 1.0,
        "sample_size": 80
      }
    ],
    "group": "付款",
    "legacy_source_tables": [
      "T_FK_SUPPLIER",
      "T_FK_Supplier_CB"
    ],
    "missing_alias_fields": [],
    "model": "sc.payment.execution",
    "model_missing": false,
    "name": "往来单位付款",
    "raw_hash_hit_count": 80,
    "raw_hash_hits": [
      {
        "id": "22767",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0"
      },
      {
        "id": "22766",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-a0590fbb9d194457a926a4b7109e3de4"
      },
      {
        "id": "22765",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-05171f39113c44fc99d0a4c98e32265d"
      },
      {
        "id": "22764",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-79d090d391534ba8836305afa7a585da"
      },
      {
        "id": "22763",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-82e394d4425a4239a510158176d6e9a5"
      },
      {
        "id": "22762",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-712de6b5906242808e988210b1711287"
      },
      {
        "id": "22761",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-40644870963c4175a5ed02194df0d866"
      },
      {
        "id": "22760",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-e3ac7f9bf8294f22bf72e3b77b16e3ff"
      },
      {
        "id": "22759",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-0d776d2c2b53443886634931453bd162"
      },
      {
        "id": "22758",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-cef707eae00a49cf8c49d7b59cab9b2f"
      },
      {
        "id": "22757",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-09e211dd4e90459784277262af2ae43f"
      },
      {
        "id": "22756",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-38bf7bd0600142119d204b405609ee05"
      },
      {
        "id": "22755",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-62a0553d6c7341cc890b72186062a05c"
      },
      {
        "id": "22754",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-1800438e41354d1995ac3a4719846cc2"
      },
      {
        "id": "22753",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-67466b1aa71744b1b38f51a1c88d010c"
      },
      {
        "id": "22752",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-e0c7313356b441f5bb7bc9c66408c305"
      },
      {
        "id": "22751",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-70d9494802944dfbb82581839698b2fc"
      },
      {
        "id": "22750",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-12699dfcf3b74760a3997ab192f5cb72"
      },
      {
        "id": "22749",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-465d8a6c7b4e4d14851ff53c10811835"
      },
      {
        "id": "22748",
        "label": "附件",
        "value": "LEG-PAY-actual_outflow_line-2045152cd0654e5fb9f87afb9d4bf38d"
      }
    ],
    "sample_rows": [
      {
        "id": "22767",
        "p1_visible_058f511c98cf": "2026-05-11",
        "p1_visible_06fa8c6f628f": "历史已确认",
        "p1_visible_48a64eb40c71": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
        "p1_visible_48eb67df430f": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
        "p1_visible_514ce8cde553": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
        "p1_visible_71e47f617269": "卢燕",
        "p1_visible_7f5da566c14e": "GYSHT-20211018-002",
        "p1_visible_80f75ce4d56c": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
        "p1_visible_8fa8662ad38f": "GYSHT-20211018-002",
        "p1_visible_99f6fe6c41ad": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
        "p1_visible_a4aa6578aa87": "PRQ2630015",
        "p1_visible_c3d92b20c8a3": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
        "p1_visible_cf44ec3f55f9": "格尔木邦乐五金工具钢丝绳",
        "p1_visible_d890d302f7f7": "22000.0",
        "p1_visible_dacbd33c31fd": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
        "p1_visible_e0361480e3a5": "[migration:actual_outflow_line_payment_execution] legacy_line_id=actual_outflow_line:c20a8cf1935e4681a1276d7b38a0e7e0; legacy_parent_id=fe2ce47a4e2c4279989b6dc1a3cc6bc8; source_document_no=GYSHT-20211018-002; source_contract_no=GYSHT-20211018-002; historical_runtime_projection=true",
        "p1_visible_f22832ce4781": "历史已确认",
        "p1_visible_f35ba3fab897": "合同"
      },
      {
        "id": "22766",
        "p1_visible_058f511c98cf": "2026-05-11",
        "p1_visible_06fa8c6f628f": "历史已确认",
        "p1_visible_48a64eb40c71": "LEG-PAY-actual_outflow_line-a0590fbb9d194457a926a4b7109e3de4",
        "p1_visible_48eb67df430f": "LEG-PAY-actual_outflow_line-a0590fbb9d194457a926a4b7109e3de4",
        "p1_visible_514ce8cde553": "LEG-PAY-actual_outflow_line-a0590fbb9d194457a926a4b7109e3de4",
        "p1_visible_71e47f617269": "LEG-PAY-actual_outflow_line-a0590fbb9d194457a926a4b7109e3de4",
        "p1_visible_7f5da566c14e": "GYSHT-20200317-001",
        "p1_visible_80f75ce4d56c": "LEG-PAY-actual_outflow_line-a0590fbb9d194457a926a4b7109e3de4",
        "p1_visible_8fa8662ad38f": "GYSHT-20200317-001",
        "p1_visible_99f6fe6c41ad": "LEG-PAY-actual_outflow_line-a0590fbb9d194457a926a4b7109e3de4",
        "p1_visible_a4aa6578aa87": "PRQ2629986",
        "p1_visible_c3d92b20c8a3": "LEG-PAY-actual_outflow_line-a0590fbb9d194457a926a4b7109e3de4",
        "p1_visible_cf44ec3f55f9": "重庆綦航钢结构工程有限公司",
        "p1_visible_d890d302f7f7": "693600.0",
        "p1_visible_dacbd33c31fd": "LEG-PAY-actual_outflow_line-a0590fbb9d194457a926a4b7109e3de4",
        "p1_visible_e0361480e3a5": "[migration:actual_outflow_line_payment_execution] legacy_line_id=actual_outflow_line:a0590fbb9d194457a926a4b7109e3de4; legacy_parent_id=fd9f362d6e5e417580df84f276126c43; source_document_no=GYSHT-20200317-001; source_contract_no=GYSHT-20200317-001; historical_runtime_projection=true",
        "p1_visible_f22832ce4781": "历史已确认",
        "p1_visible_f35ba3fab897": "合同"
      },
      {
        "id": "22765",
        "p1_visible_058f511c98cf": "2026-05-11",
        "p1_visible_06fa8c6f628f": "历史已确认",
        "p1_visible_48a64eb40c71": "LEG-PAY-actual_outflow_line-05171f39113c44fc99d0a4c98e32265d",
        "p1_visible_48eb67df430f": "LEG-PAY-actual_outflow_line-05171f39113c44fc99d0a4c98e32265d",
        "p1_visible_514ce8cde553": "LEG-PAY-actual_outflow_line-05171f39113c44fc99d0a4c98e32265d",
        "p1_visible_71e47f617269": "卢燕",
        "p1_visible_7f5da566c14e": "GYSHT-20211018-004",
        "p1_visible_80f75ce4d56c": "LEG-PAY-actual_outflow_line-05171f39113c44fc99d0a4c98e32265d",
        "p1_visible_8fa8662ad38f": "GYSHT-20211018-004",
        "p1_visible_99f6fe6c41ad": "LEG-PAY-actual_outflow_line-05171f39113c44fc99d0a4c98e32265d",
        "p1_visible_a4aa6578aa87": "PRQ2629073",
        "p1_visible_c3d92b20c8a3": "LEG-PAY-actual_outflow_line-05171f39113c44fc99d0a4c98e32265d",
        "p1_visible_cf44ec3f55f9": "格尔木奋鼎机械设备安装有限公司",
        "p1_visible_d890d302f7f7": "30000.0",
        "p1_visible_dacbd33c31fd": "LEG-PAY-actual_outflow_line-05171f39113c44fc99d0a4c98e32265d",
        "p1_visible_e0361480e3a5": "[migration:actual_outflow_line_payment_execution] legacy_line_id=actual_outflow_line:05171f39113c44fc99d0a4c98e32265d; legacy_parent_id=eacce154a23b472f816ab3db892fe818; source_document_no=GYSHT-20211018-004; source_contract_no=GYSHT-20211018-004; historical_runtime_projection=true",
        "p1_visible_f22832ce4781": "历史已确认",
        "p1_visible_f35ba3fab897": "合同"
      },
      {
        "id": "22764",
        "p1_visible_058f511c98cf": "2026-05-11",
        "p1_visible_06fa8c6f628f": "历史已确认",
        "p1_visible_48a64eb40c71": "LEG-PAY-actual_outflow_line-79d090d391534ba8836305afa7a585da",
        "p1_visible_48eb67df430f": "LEG-PAY-actual_outflow_line-79d090d391534ba8836305afa7a585da",
        "p1_visible_514ce8cde553": "LEG-PAY-actual_outflow_line-79d090d391534ba8836305afa7a585da",
        "p1_visible_71e47f617269": "卢燕",
        "p1_visible_7f5da566c14e": "GYSHT-20211206-003",
        "p1_visible_80f75ce4d56c": "LEG-PAY-actual_outflow_line-79d090d391534ba8836305afa7a585da",
        "p1_visible_8fa8662ad38f": "GYSHT-20211206-003",
        "p1_visible_99f6fe6c41ad": "LEG-PAY-actual_outflow_line-79d090d391534ba8836305afa7a585da",
        "p1_visible_a4aa6578aa87": "PRQ2628538",
        "p1_visible_c3d92b20c8a3": "LEG-PAY-actual_outflow_line-79d090d391534ba8836305afa7a585da",
        "p1_visible_cf44ec3f55f9": "忠县万权商贸有限公司",
        "p1_visible_d890d302f7f7": "600000.0",
        "p1_visible_dacbd33c31fd": "LEG-PAY-actual_outflow_line-79d090d391534ba8836305afa7a585da",
        "p1_visible_e0361480e3a5": "[migration:actual_outflow_line_payment_execution] legacy_line_id=actual_outflow_line:79d090d391534ba8836305afa7a585da; legacy_parent_id=e0fbfcd31e164377aa6c5fe3b1fdbb75; source_document_no=GYSHT-20211206-003; source_contract_no=GYSHT-20211206-003; historical_runtime_projection=true",
        "p1_visible_f22832ce4781": "历史已确认",
        "p1_visible_f35ba3fab897": "合同"
      },
      {
        "id": "22763",
        "p1_visible_058f511c98cf": "2026-05-11",
        "p1_visible_06fa8c6f628f": "历史已确认",
        "p1_visible_48a64eb40c71": "LEG-PAY-actual_outflow_line-82e394d4425a4239a510158176d6e9a5",
        "p1_visible_48eb67df430f": "LEG-PAY-actual_outflow_line-82e394d4425a4239a510158176d6e9a5",
        "p1_visible_514ce8cde553": "LEG-PAY-actual_outflow_line-82e394d4425a4239a510158176d6e9a5",
        "p1_visible_71e47f617269": "文楠",
        "p1_visible_7f5da566c14e": "GYSHT-20210406-005",
        "p1_visible_80f75ce4d56c": "LEG-PAY-actual_outflow_line-82e394d4425a4239a510158176d6e9a5",
        "p1_visible_8fa8662ad38f": "GYSHT-20210406-005",
        "p1_visible_99f6fe6c41ad": "LEG-PAY-actual_outflow_line-82e394d4425a4239a510158176d6e9a5",
        "p1_visible_a4aa6578aa87": "PRQ2628173",
        "p1_visible_c3d92b20c8a3": "LEG-PAY-actual_outflow_line-82e394d4425a4239a510158176d6e9a5",
        "p1_visible_cf44ec3f55f9": "两江新区翔毅超建材经营部",
        "p1_visible_d890d302f7f7": "60025.0",
        "p1_visible_dacbd33c31fd": "LEG-PAY-actual_outflow_line-82e394d4425a4239a510158176d6e9a5",
        "p1_visible_e0361480e3a5": "[migration:actual_outflow_line_payment_execution] legacy_line_id=actual_outflow_line:82e394d4425a4239a510158176d6e9a5; legacy_parent_id=d9fcb94ce0e840b6a267e84c7a01ec11; source_document_no=GYSHT-20210406-005; source_contract_no=GYSHT-20210406-005; historical_runtime_projection=true",
        "p1_visible_f22832ce4781": "历史已确认",
        "p1_visible_f35ba3fab897": "合同"
      }
    ],
    "seq": 310,
    "status": "REVIEW_VISIBLE_VALUE_ANOMALY",
    "view_id": 2709
  },
  {
    "action_id": 898,
    "contract_field_count": 10,
    "critical_empty_count": 1,
    "critical_empty_labels": [
      "附件"
    ],
    "delivered_count": 1738,
    "domain": [
      [
        "claim_type",
        "=",
        "deduction_refund"
      ],
      [
        "expense_type",
        "=",
        "扣款实缴退回"
      ]
    ],
    "double_display_hit_count": 0,
    "double_display_hits": [],
    "field_coverage": [
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_06fa8c6f628f",
        "filled": 80,
        "label": "单据状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3e7255522b33",
        "filled": 80,
        "label": "项目名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_8fa8662ad38f",
        "filled": 80,
        "label": "单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_62e5cf441092",
        "filled": 80,
        "label": "本次实缴数",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3ade9df90bf8",
        "filled": 80,
        "label": "本次退回数",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dbbcd74271cd",
        "filled": 80,
        "label": "上缴内容",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_e0361480e3a5",
        "filled": 80,
        "label": "备注",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f6fe6c41ad",
        "filled": 0,
        "label": "附件",
        "ratio": 0.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ee6a4d9e2956",
        "filled": 80,
        "label": "录入人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_1e62803e196c",
        "filled": 80,
        "label": "单据日期",
        "ratio": 1.0,
        "sample_size": 80
      }
    ],
    "group": "扣款",
    "legacy_source_tables": [
      "T_KK_SJTHB",
      "T_KK_SJTHB_CB"
    ],
    "missing_alias_fields": [],
    "model": "sc.expense.claim",
    "model_missing": false,
    "name": "扣款实缴退回",
    "raw_hash_hit_count": 0,
    "raw_hash_hits": [],
    "sample_rows": [
      {
        "id": "64850",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_1e62803e196c": "2017-01-22",
        "p1_visible_3ade9df90bf8": "627731.5",
        "p1_visible_3e7255522b33": "中江县2016年抗旱应急水源工程",
        "p1_visible_62e5cf441092": "627731.5",
        "p1_visible_8fa8662ad38f": "KKSJTH-20210901-007",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_dbbcd74271cd": "扣款实缴退回 / 风险责任金 / 扣款实缴退回",
        "p1_visible_e0361480e3a5": "[migration:deduction_paid_refund] legacy_account_transaction_line_id=14; source_key=15f6a770643d42c3b6a5508884f61c59:deduction_payment_refund; account=1001 1000 0000 1931; counterparty=风险责任金",
        "p1_visible_ee6a4d9e2956": "wennan"
      },
      {
        "id": "64849",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_1e62803e196c": "2018-10-31",
        "p1_visible_3ade9df90bf8": "66389.48",
        "p1_visible_3e7255522b33": "城西片区青衣江路西段道路五段",
        "p1_visible_62e5cf441092": "66389.48",
        "p1_visible_8fa8662ad38f": "KKSJTH-20210531-001",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_dbbcd74271cd": "扣款实缴退回 / 增值税 / 扣款实缴退回",
        "p1_visible_e0361480e3a5": "[migration:deduction_paid_refund] legacy_account_transaction_line_id=44; source_key=0e594cd90d804356a18b1d033b1da5d6:deduction_payment_refund; account=; counterparty=增值税",
        "p1_visible_ee6a4d9e2956": "wennan"
      },
      {
        "id": "64848",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_1e62803e196c": "2019-04-25",
        "p1_visible_3ade9df90bf8": "6000.0",
        "p1_visible_3e7255522b33": "旌阳区孝感镇灵庙村2017年节水型社会重点县建设项目",
        "p1_visible_62e5cf441092": "6000.0",
        "p1_visible_8fa8662ad38f": "KKSJTH-20210127-003",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_dbbcd74271cd": "扣款实缴退回 / 暂扣成本票 / 扣款实缴退回",
        "p1_visible_e0361480e3a5": "[migration:deduction_paid_refund] legacy_account_transaction_line_id=87; source_key=9c2dbe15dac54bde8ea598945db9abca:deduction_payment_refund; account=6225613300000009183; counterparty=暂扣成本票",
        "p1_visible_ee6a4d9e2956": "wennan"
      },
      {
        "id": "64847",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_1e62803e196c": "2019-06-05",
        "p1_visible_3ade9df90bf8": "13204.69",
        "p1_visible_3e7255522b33": "西昌市市政建设工程管理处亮化材料（含安装）采购项目",
        "p1_visible_62e5cf441092": "13204.69",
        "p1_visible_8fa8662ad38f": "KKSJTH-20220301-001",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_dbbcd74271cd": "扣款实缴退回 / 增值税 / 扣款实缴退回",
        "p1_visible_e0361480e3a5": "[migration:deduction_paid_refund] legacy_account_transaction_line_id=107; source_key=babbcf6f75cd4cc38d432d00d85bd77c:deduction_payment_refund; account=; counterparty=增值税",
        "p1_visible_ee6a4d9e2956": "wennan"
      },
      {
        "id": "64846",
        "p1_visible_06fa8c6f628f": "2",
        "p1_visible_1e62803e196c": "2019-12-10",
        "p1_visible_3ade9df90bf8": "4219.0",
        "p1_visible_3e7255522b33": "孝感镇和平村1、2、3、6、7组墓地迁建区域配套项目",
        "p1_visible_62e5cf441092": "4219.0",
        "p1_visible_8fa8662ad38f": "KKSJTH-20210120-006",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_dbbcd74271cd": "扣款实缴退回 / 增值税 / 扣款实缴退回",
        "p1_visible_e0361480e3a5": "[migration:deduction_paid_refund] legacy_account_transaction_line_id=275; source_key=cdf29758dbda43739e4d0eb49c74d7f2:deduction_payment_refund; account=1001 1000 0000 1931; counterparty=增值税",
        "p1_visible_ee6a4d9e2956": "wennan"
      }
    ],
    "seq": 340,
    "status": "REVIEW_CRITICAL_EMPTY",
    "view_id": 2726
  },
  {
    "action_id": 885,
    "contract_field_count": 16,
    "critical_empty_count": 0,
    "critical_empty_labels": [],
    "delivered_count": 2595,
    "domain": [],
    "double_display_hit_count": 0,
    "double_display_hits": [],
    "field_coverage": [
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_06fa8c6f628f",
        "filled": 80,
        "label": "单据状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_8fa8662ad38f",
        "filled": 80,
        "label": "单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_89b4aa6364ce",
        "filled": 80,
        "label": "时间",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3e7255522b33",
        "filled": 80,
        "label": "项目名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_389372a58a16",
        "filled": 80,
        "label": "期数",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_fc06f3f3d307",
        "filled": 80,
        "label": "本期收款",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99219180c1b9",
        "filled": 80,
        "label": "本期代扣代缴合计",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_50f529884746",
        "filled": 80,
        "label": "本期拨付金额合计",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f6fe6c41ad",
        "filled": 80,
        "label": "附件",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_17d0f48c07fb",
        "filled": 76,
        "label": "施工单位",
        "ratio": 0.95,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_75e856a13c7c",
        "filled": 80,
        "label": "合同金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_689407e406ab",
        "filled": 64,
        "label": "目前形象进度",
        "ratio": 0.8,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_0d8979d08c09",
        "filled": 80,
        "label": "累计开票金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_aa6152009ab0",
        "filled": 80,
        "label": "上期留存余额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ee6a4d9e2956",
        "filled": 80,
        "label": "录入人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dfc25d77dc39",
        "filled": 80,
        "label": "录入时间",
        "ratio": 1.0,
        "sample_size": 80
      }
    ],
    "group": "收款",
    "legacy_source_tables": [
      "ZJGL_SZQR_DKQRB"
    ],
    "missing_alias_fields": [],
    "model": "sc.legacy.fund.confirmation.document",
    "model_missing": false,
    "name": "到款确认表",
    "raw_hash_hit_count": 38,
    "raw_hash_hits": [
      {
        "id": "2655",
        "label": "附件",
        "value": "image.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/10/10/95b99242549273606530ffa7f945e85d.png i"
      },
      {
        "id": "2653",
        "label": "附件",
        "value": "到款确认表.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/6/23/ff11f3f589d53d49ce8802658e524f0c.png 到款"
      },
      {
        "id": "2651",
        "label": "附件",
        "value": "微信图片_20231218170528.png | legacy-file://UploadFile/UserFile/2023/12/18/ccc1e263e6054908a6655108f47f468b_24216.png 0de293"
      },
      {
        "id": "2644",
        "label": "附件",
        "value": "70b1315859de4a04050b480e021524c.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/10/12/22a1d4e0d90f"
      },
      {
        "id": "2640",
        "label": "附件",
        "value": "image.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2023/1/18/313a9fd345ddac87f00dbb336892548c.png im"
      },
      {
        "id": "2639",
        "label": "附件",
        "value": "到款确认表.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/7/14/89d650d4ace107b019662ffd782c2b0d.png 到款"
      },
      {
        "id": "2638",
        "label": "附件",
        "value": "0c7d61e6e34495cc1db309c6277c0dc.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/6/24/b71a281bad209"
      },
      {
        "id": "2636",
        "label": "附件",
        "value": "到款确认表.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/4/1/b29232a56946db706df07a0dc124b10e.png 到款确"
      },
      {
        "id": "2634",
        "label": "附件",
        "value": "a5b98b76669196b335c0ef9efb8f935.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/11/12/683324a64fa0"
      },
      {
        "id": "2633",
        "label": "附件",
        "value": "7d825661c65c6796eb3bbb6bd625c4d.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/12/1/1db59eb4f24ed"
      },
      {
        "id": "2629",
        "label": "附件",
        "value": "f16a8c887e3370289c269a21aa427d4.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/9/1/c6cc10e23ae26f"
      },
      {
        "id": "2626",
        "label": "附件",
        "value": "20210202.jpg | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/2/2/a853ae0e0178fc4025a193fb5c67d09f.jpg "
      },
      {
        "id": "2623",
        "label": "附件",
        "value": "dc6f612089a42e34aca81d0487d86f2.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/1/28/6ce8c8f52fe0e"
      },
      {
        "id": "2621",
        "label": "附件",
        "value": "image.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2023/3/16/b6977df5bcad50b590ee427c9f46b18a.png im"
      },
      {
        "id": "2619",
        "label": "附件",
        "value": "image.png | legacy-file://UploadFile/UserFile/2025/01/14/6e2d16d5f669441781eccdd56df5fe75_36841.png 50ef1cfe04148a010393"
      },
      {
        "id": "2618",
        "label": "附件",
        "value": "314a7e58af12fd6898f0d55a3d274fd.png | legacy-file://UploadFile/UserFile/2025/03/31/84f9b8577fa34b25925cf672c22829b1_4938"
      },
      {
        "id": "2617",
        "label": "附件",
        "value": "image.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/7/11/502ea6689282e95057e8f780ae7259c2.png im"
      },
      {
        "id": "2616",
        "label": "附件",
        "value": "image.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/11/3/b847ac400e62e7c45661fd0ea9f4ff05.png im"
      },
      {
        "id": "2615",
        "label": "附件",
        "value": "81a40419e760d67c3098edaf9c90ac6.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/11/17/fc53048579ef"
      },
      {
        "id": "2614",
        "label": "附件",
        "value": "到款确认表.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/7/28/b7b8f6ccb1c305865d335a7ecfdd7d70.png 到款"
      }
    ],
    "sample_rows": [
      {
        "id": "2655",
        "p1_visible_06fa8c6f628f": "审核通过",
        "p1_visible_0d8979d08c09": "127226.94",
        "p1_visible_17d0f48c07fb": "刘伟",
        "p1_visible_389372a58a16": "1",
        "p1_visible_3e7255522b33": "刘伟零星工程项目",
        "p1_visible_50f529884746": "52650.420000000006",
        "p1_visible_689407e406ab": "施工中",
        "p1_visible_75e856a13c7c": "169085.94",
        "p1_visible_89b4aa6364ce": "2022-09-30 00:00:00",
        "p1_visible_8fa8662ad38f": "DKQR-20221010-005",
        "p1_visible_99219180c1b9": "14525.519999999999",
        "p1_visible_99f6fe6c41ad": "image.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/10/10/95b99242549273606530ffa7f945e85d.png image.png | legacy-file://~/File_New/CollectionPlan/2022/10/10/95b99242549273606530ffa7f945e85d.png image.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/10/10/df4fef8ace57858a82c4123399c0b15e.png image.png | legacy-file://~/File_New/CollectionPlan/2022/10/10/df4fef8ace57858a82c4123399c0b15e.png",
        "p1_visible_aa6152009ab0": "0.0",
        "p1_visible_dfc25d77dc39": "2022-10-10 14:45:37",
        "p1_visible_ee6a4d9e2956": "文楠",
        "p1_visible_fc06f3f3d307": "67175.94"
      },
      {
        "id": "2654",
        "p1_visible_06fa8c6f628f": "审核通过",
        "p1_visible_0d8979d08c09": "686885.9",
        "p1_visible_17d0f48c07fb": "黄超",
        "p1_visible_389372a58a16": "6",
        "p1_visible_3e7255522b33": "中国电信泸州分公司2024-2026年房屋装修、维修服务项目",
        "p1_visible_50f529884746": "57815.92",
        "p1_visible_689407e406ab": "施工中",
        "p1_visible_75e856a13c7c": "1650000.0",
        "p1_visible_89b4aa6364ce": "2025-01-24 00:00:00",
        "p1_visible_8fa8662ad38f": "DKQRB-20250124-006",
        "p1_visible_99219180c1b9": "6602.92",
        "p1_visible_99f6fe6c41ad": "image.png | legacy-file://UploadFile/UserFile/2025/01/24/1f028339b44948249af944eeadaf8a77_52871.png",
        "p1_visible_aa6152009ab0": "0.0",
        "p1_visible_dfc25d77dc39": "2025-01-24 14:19:55",
        "p1_visible_ee6a4d9e2956": "江一娇",
        "p1_visible_fc06f3f3d307": "64418.84"
      },
      {
        "id": "2653",
        "p1_visible_06fa8c6f628f": "审核通过",
        "p1_visible_0d8979d08c09": "24029854.7",
        "p1_visible_17d0f48c07fb": "蒋军",
        "p1_visible_389372a58a16": "10",
        "p1_visible_3e7255522b33": "布拖县2016年—2019年安全住房地质隐患应急抢险项目",
        "p1_visible_50f529884746": "915280.78",
        "p1_visible_689407e406ab": "施工中",
        "p1_visible_75e856a13c7c": "52400000.0",
        "p1_visible_89b4aa6364ce": "2021-06-23 16:00:00",
        "p1_visible_8fa8662ad38f": "DKQR-20210623-002",
        "p1_visible_99219180c1b9": "437483.08",
        "p1_visible_99f6fe6c41ad": "到款确认表.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/6/23/ff11f3f589d53d49ce8802658e524f0c.png 到款确认表.png | legacy-file://~/File_New/CollectionPlan/2021/6/23/ff11f3f589d53d49ce8802658e524f0c.png 风险责任书.png | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/6/23/8a5cb4b27374744a5d5bc011a6ba0e3c.png 风险责任书.png | legacy-file://~/File_New/CollectionPlan/2021/6/23/8a5cb4b27374744a5d5bc011a6ba0e3c.png",
        "p1_visible_aa6152009ab0": "0.0",
        "p1_visible_dfc25d77dc39": "2021-06-23 17:22:07",
        "p1_visible_ee6a4d9e2956": "尹佳梅",
        "p1_visible_fc06f3f3d307": "1352763.86"
      },
      {
        "id": "2652",
        "p1_visible_06fa8c6f628f": "审核通过",
        "p1_visible_0d8979d08c09": "0.0",
        "p1_visible_17d0f48c07fb": "李德学",
        "p1_visible_389372a58a16": "13",
        "p1_visible_3e7255522b33": "引入社会资金共同打造游泳高水平运动员后备人才培养项目",
        "p1_visible_50f529884746": "700000.0",
        "p1_visible_689407e406ab": "施工中",
        "p1_visible_75e856a13c7c": "40896688.0",
        "p1_visible_89b4aa6364ce": "2025-08-29 00:00:00",
        "p1_visible_8fa8662ad38f": "DKQRB-20250829-001",
        "p1_visible_99219180c1b9": "0.0",
        "p1_visible_99f6fe6c41ad": "历史附件",
        "p1_visible_aa6152009ab0": "0.0",
        "p1_visible_dfc25d77dc39": "2025-08-29 11:52:41",
        "p1_visible_ee6a4d9e2956": "文楠",
        "p1_visible_fc06f3f3d307": "700000.0"
      },
      {
        "id": "2651",
        "p1_visible_06fa8c6f628f": "审核通过",
        "p1_visible_0d8979d08c09": "807975.0",
        "p1_visible_17d0f48c07fb": "何东",
        "p1_visible_389372a58a16": "1",
        "p1_visible_3e7255522b33": "伽师县工业园区空气源供热建设项目（二次）二标段",
        "p1_visible_50f529884746": "708998.38",
        "p1_visible_689407e406ab": "施工中",
        "p1_visible_75e856a13c7c": "807975.0",
        "p1_visible_89b4aa6364ce": "2023-12-19 09:54:30.823000",
        "p1_visible_8fa8662ad38f": "DKQRB-20231218-001",
        "p1_visible_99219180c1b9": "98976.62",
        "p1_visible_99f6fe6c41ad": "微信图片_20231218170528.png | legacy-file://UploadFile/UserFile/2023/12/18/ccc1e263e6054908a6655108f47f468b_24216.png 0de29371671ec6aacfa4d66822614cc.png | legacy-file://UploadFile/UserFile/2023/12/19/6523017101da4e639da0c9ea3ffd11ad_24274.png",
        "p1_visible_aa6152009ab0": "0.0",
        "p1_visible_dfc25d77dc39": "2023-12-18 17:14:23",
        "p1_visible_ee6a4d9e2956": "江一娇",
        "p1_visible_fc06f3f3d307": "807975.0"
      }
    ],
    "seq": 350,
    "status": "REVIEW_VISIBLE_VALUE_ANOMALY",
    "view_id": 2713
  },
  {
    "action_id": 889,
    "contract_field_count": 17,
    "critical_empty_count": 1,
    "critical_empty_labels": [
      "附件"
    ],
    "delivered_count": 225,
    "domain": [
      [
        "legacy_source_table",
        "in",
        [
          "C_JXXP_KJFPSQ"
        ]
      ]
    ],
    "double_display_hit_count": 0,
    "double_display_hits": [],
    "field_coverage": [
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_62e951a692ff",
        "filled": 80,
        "label": "状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3b66293fbe70",
        "filled": 80,
        "label": "开票状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_17b341733b7b",
        "filled": 80,
        "label": "合同编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3e7255522b33",
        "filled": 80,
        "label": "项目名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_8fa8662ad38f",
        "filled": 80,
        "label": "单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_880ab989a872",
        "filled": 0,
        "label": "申请人",
        "ratio": 0.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ed9ce3e5ab3c",
        "filled": 1,
        "label": "预计回款日期",
        "ratio": 0.0125,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_2c346345746e",
        "filled": 80,
        "label": "申请日期",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_f9cc22d53aff",
        "filled": 80,
        "label": "受票方名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_0d8979d08c09",
        "filled": 80,
        "label": "累计开票金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_83e1d169c7a2",
        "filled": 80,
        "label": "合同额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_4f43764bd23d",
        "filled": 80,
        "label": "本次开票张数",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_c5e161f03e08",
        "filled": 80,
        "label": "本次开票金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f6fe6c41ad",
        "filled": 0,
        "label": "附件",
        "ratio": 0.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_e0361480e3a5",
        "filled": 80,
        "label": "备注",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ee6a4d9e2956",
        "filled": 80,
        "label": "录入人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dfc25d77dc39",
        "filled": 80,
        "label": "录入时间",
        "ratio": 1.0,
        "sample_size": 80
      }
    ],
    "group": "发票税务",
    "legacy_source_tables": [
      "C_JXXP_KJFPSQ"
    ],
    "missing_alias_fields": [],
    "model": "sc.invoice.registration",
    "model_missing": false,
    "name": "开票申请",
    "raw_hash_hit_count": 0,
    "raw_hash_hits": [],
    "sample_rows": [
      {
        "id": "534134",
        "p1_visible_0d8979d08c09": "-3553.01",
        "p1_visible_17b341733b7b": "FPSQ-20200804-002",
        "p1_visible_2c346345746e": "2020-04-14",
        "p1_visible_3b66293fbe70": "历史已确认",
        "p1_visible_3e7255522b33": "中国移动四川公司全省市州分公司2019-2022年管理用房及生产枢纽楼公共区域零星维修服务项目（标包1）",
        "p1_visible_4f43764bd23d": "0",
        "p1_visible_62e951a692ff": "审核通过",
        "p1_visible_83e1d169c7a2": "0.0",
        "p1_visible_880ab989a872": "",
        "p1_visible_8fa8662ad38f": "FPSQ-20200804-002",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_c5e161f03e08": "-3553.01",
        "p1_visible_dfc25d77dc39": "FPSQ-20200804-002",
        "p1_visible_e0361480e3a5": "[migration:invoice_registration_tax] legacy_record_id=252766840c1d4b118ba28e5d17a81afa\noutput_invoice\ninvoice_issue_request\n中国移动四川公司全省市州分公司2019-2022年管理用房及生产枢纽楼公共区域零星维修服务项目（标包1）\n中国移动通信集团四川有限公司成都分公司\n补录2020年开票记录",
        "p1_visible_ed9ce3e5ab3c": "",
        "p1_visible_ee6a4d9e2956": "FPSQ-20200804-002",
        "p1_visible_f9cc22d53aff": "中国移动通信集团四川有限公司成都分公司"
      },
      {
        "id": "534133",
        "p1_visible_0d8979d08c09": "-0.19",
        "p1_visible_17b341733b7b": "FPSQ-20201028-002",
        "p1_visible_2c346345746e": "2020-10-28",
        "p1_visible_3b66293fbe70": "历史已确认",
        "p1_visible_3e7255522b33": "中国移动四川公司全省市州分公司2019-2022年管理用房及生产枢纽楼公共区域零星维修服务项目（标包1）",
        "p1_visible_4f43764bd23d": "0",
        "p1_visible_62e951a692ff": "审核通过",
        "p1_visible_83e1d169c7a2": "0.0",
        "p1_visible_880ab989a872": "",
        "p1_visible_8fa8662ad38f": "FPSQ-20201028-002",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_c5e161f03e08": "-0.19",
        "p1_visible_dfc25d77dc39": "FPSQ-20201028-002",
        "p1_visible_e0361480e3a5": "[migration:invoice_registration_tax] legacy_record_id=1d68b04d30ef4056a77937d38abdf5cb\noutput_invoice\ninvoice_issue_request\n中国移动四川公司全省市州分公司2019-2022年管理用房及生产枢纽楼公共区域零星维修服务项目（标包1）\n中国移动通信集团四川有限公司成都分公司\n对方提供金额有误，作废重开，调减0.19元",
        "p1_visible_ed9ce3e5ab3c": "",
        "p1_visible_ee6a4d9e2956": "FPSQ-20201028-002",
        "p1_visible_f9cc22d53aff": "中国移动通信集团四川有限公司成都分公司"
      },
      {
        "id": "528561",
        "p1_visible_0d8979d08c09": "-363.63",
        "p1_visible_17b341733b7b": "FPSQ-20200728-003",
        "p1_visible_2c346345746e": "2020-04-20",
        "p1_visible_3b66293fbe70": "历史已确认",
        "p1_visible_3e7255522b33": "中国移动四川分公司南充片区2018-2020年渠道零星维修项目（标包9）",
        "p1_visible_4f43764bd23d": "0",
        "p1_visible_62e951a692ff": "审核通过",
        "p1_visible_83e1d169c7a2": "0.0",
        "p1_visible_880ab989a872": "",
        "p1_visible_8fa8662ad38f": "FPSQ-20200728-003",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_c5e161f03e08": "-363.63",
        "p1_visible_dfc25d77dc39": "FPSQ-20200728-003",
        "p1_visible_e0361480e3a5": "[migration:invoice_registration_tax] legacy_record_id=d420476be8f74dfd9cb95c7ff39bc079\noutput_invoice\ninvoice_issue_request\n中国移动四川分公司南充片区2018-2020年渠道零星维修项目（标包9）\n中国移动通信集团四川有限公司南充分公司\n补录2020.4.20开票记录",
        "p1_visible_ed9ce3e5ab3c": "",
        "p1_visible_ee6a4d9e2956": "FPSQ-20200728-003",
        "p1_visible_f9cc22d53aff": "中国移动通信集团四川有限公司南充分公司"
      },
      {
        "id": "22317",
        "p1_visible_0d8979d08c09": "175000.0",
        "p1_visible_17b341733b7b": "FPSQ-20200515-001",
        "p1_visible_2c346345746e": "2020-05-15",
        "p1_visible_3b66293fbe70": "历史已确认",
        "p1_visible_3e7255522b33": "宁南县骑骡沟镇曹家营、董家龙潭饮用水源地保护工程施工合同",
        "p1_visible_4f43764bd23d": "0",
        "p1_visible_62e951a692ff": "审核通过",
        "p1_visible_83e1d169c7a2": "0.0",
        "p1_visible_880ab989a872": "",
        "p1_visible_8fa8662ad38f": "FPSQ-20200515-001",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_c5e161f03e08": "175000.0",
        "p1_visible_dfc25d77dc39": "FPSQ-20200515-001",
        "p1_visible_e0361480e3a5": "[migration:invoice_registration_tax] legacy_record_id=fe9bd158c4984380a1c9e20c19b3dd0f\noutput_invoice\ninvoice_issue_request\n宁南县骑骡沟镇曹家营、董家龙潭饮用水源地保护工程施工合同\n宁南县环境保护局",
        "p1_visible_ed9ce3e5ab3c": "",
        "p1_visible_ee6a4d9e2956": "FPSQ-20200515-001",
        "p1_visible_f9cc22d53aff": "宁南县环境保护局"
      },
      {
        "id": "22316",
        "p1_visible_0d8979d08c09": "21500000.0",
        "p1_visible_17b341733b7b": "FPSQ-20200317-015",
        "p1_visible_2c346345746e": "2019-12-31",
        "p1_visible_3b66293fbe70": "历史已确认",
        "p1_visible_3e7255522b33": "罗江翰林豪锦苑一期工程",
        "p1_visible_4f43764bd23d": "0",
        "p1_visible_62e951a692ff": "审核通过",
        "p1_visible_83e1d169c7a2": "0.0",
        "p1_visible_880ab989a872": "",
        "p1_visible_8fa8662ad38f": "FPSQ-20200317-015",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_c5e161f03e08": "21500000.0",
        "p1_visible_dfc25d77dc39": "FPSQ-20200317-015",
        "p1_visible_e0361480e3a5": "[migration:invoice_registration_tax] legacy_record_id=fe2ae2f57fdd4f70b7b8ca32d266eb58\noutput_invoice\ninvoice_issue_request\n罗江翰林豪锦苑一期工程\n德阳禾顺房地产开发有限公司\n补录2019年开票记录",
        "p1_visible_ed9ce3e5ab3c": "",
        "p1_visible_ee6a4d9e2956": "FPSQ-20200317-015",
        "p1_visible_f9cc22d53aff": "德阳禾顺房地产开发有限公司"
      }
    ],
    "seq": 390,
    "status": "REVIEW_CRITICAL_EMPTY",
    "view_id": 2717
  },
  {
    "action_id": 890,
    "contract_field_count": 20,
    "critical_empty_count": 1,
    "critical_empty_labels": [
      "附件"
    ],
    "delivered_count": 2931,
    "domain": [
      [
        "legacy_source_table",
        "in",
        [
          "C_JXXP_XXKPDJ",
          "C_JXXP_XXKPDJ_CB"
        ]
      ]
    ],
    "double_display_hit_count": 0,
    "double_display_hits": [],
    "field_coverage": [
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_06fa8c6f628f",
        "filled": 80,
        "label": "单据状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_f22832ce4781",
        "filled": 80,
        "label": "推送结果",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_7f5da566c14e",
        "filled": 80,
        "label": "金蝶单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_8fa8662ad38f",
        "filled": 80,
        "label": "单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3e7255522b33",
        "filled": 80,
        "label": "项目名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_f9cc22d53aff",
        "filled": 80,
        "label": "受票方名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_c73a8eab0d57",
        "filled": 80,
        "label": "含税金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f753ed6262",
        "filled": 80,
        "label": "税额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_007363f27191",
        "filled": 80,
        "label": "不含税金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_c1b95b8ca332",
        "filled": 80,
        "label": "附加税",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_0e2126d6cf82",
        "filled": 80,
        "label": "开票张数",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_37d56ad493cf",
        "filled": 74,
        "label": "税率",
        "ratio": 0.925,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_964a2edc6942",
        "filled": 80,
        "label": "关联回款金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ada9a85eab00",
        "filled": 33,
        "label": "发票号",
        "ratio": 0.4125,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_bbe7bbee241e",
        "filled": 30,
        "label": "发票种类",
        "ratio": 0.375,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_be5462bd6a62",
        "filled": 80,
        "label": "开票单位",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f6fe6c41ad",
        "filled": 0,
        "label": "附件",
        "ratio": 0.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ee6a4d9e2956",
        "filled": 80,
        "label": "录入人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_d42c2d26610f",
        "filled": 80,
        "label": "开票日期",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dfc25d77dc39",
        "filled": 80,
        "label": "录入时间",
        "ratio": 1.0,
        "sample_size": 80
      }
    ],
    "group": "发票税务",
    "legacy_source_tables": [
      "C_JXXP_XXKPDJ",
      "C_JXXP_XXKPDJ_CB"
    ],
    "missing_alias_fields": [],
    "model": "sc.invoice.registration",
    "model_missing": false,
    "name": "开票登记",
    "raw_hash_hit_count": 0,
    "raw_hash_hits": [],
    "sample_rows": [
      {
        "id": "531538",
        "p1_visible_007363f27191": "38627.19",
        "p1_visible_06fa8c6f628f": "已作废",
        "p1_visible_0e2126d6cf82": "0",
        "p1_visible_37d56ad493cf": "9%",
        "p1_visible_3e7255522b33": "公司综合平台",
        "p1_visible_7f5da566c14e": "XXKPDJ-20250625-006",
        "p1_visible_8fa8662ad38f": "XXKPDJ-20250625-006",
        "p1_visible_964a2edc6942": "0.0",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_99f753ed6262": "3476.45",
        "p1_visible_ada9a85eab00": "",
        "p1_visible_bbe7bbee241e": "",
        "p1_visible_be5462bd6a62": "四川保盛建设集团有限公司",
        "p1_visible_c1b95b8ca332": "0.0",
        "p1_visible_c73a8eab0d57": "42103.64",
        "p1_visible_d42c2d26610f": "2025-06-09",
        "p1_visible_dfc25d77dc39": "XXKPDJ-20250625-006",
        "p1_visible_ee6a4d9e2956": "XXKPDJ-20250625-006",
        "p1_visible_f22832ce4781": "-1",
        "p1_visible_f9cc22d53aff": "重庆渝数科技有限公司"
      },
      {
        "id": "531460",
        "p1_visible_007363f27191": "88939.7",
        "p1_visible_06fa8c6f628f": "已作废",
        "p1_visible_0e2126d6cf82": "0",
        "p1_visible_37d56ad493cf": "9%",
        "p1_visible_3e7255522b33": "公司综合平台",
        "p1_visible_7f5da566c14e": "XXKPDJ-20250627-004",
        "p1_visible_8fa8662ad38f": "XXKPDJ-20250627-004",
        "p1_visible_964a2edc6942": "0.0",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_99f753ed6262": "8004.57",
        "p1_visible_ada9a85eab00": "",
        "p1_visible_bbe7bbee241e": "",
        "p1_visible_be5462bd6a62": "四川保盛建设集团有限公司",
        "p1_visible_c1b95b8ca332": "0.0",
        "p1_visible_c73a8eab0d57": "96944.27",
        "p1_visible_d42c2d26610f": "2025-06-26",
        "p1_visible_dfc25d77dc39": "XXKPDJ-20250627-004",
        "p1_visible_ee6a4d9e2956": "XXKPDJ-20250627-004",
        "p1_visible_f22832ce4781": "-1",
        "p1_visible_f9cc22d53aff": "中国移动通信集团四川有限公司成都分公司"
      },
      {
        "id": "531379",
        "p1_visible_007363f27191": "-37276.39",
        "p1_visible_06fa8c6f628f": "已作废",
        "p1_visible_0e2126d6cf82": "0",
        "p1_visible_37d56ad493cf": "9%",
        "p1_visible_3e7255522b33": "公司综合平台",
        "p1_visible_7f5da566c14e": "XXKPDJ-20250625-010",
        "p1_visible_8fa8662ad38f": "XXKPDJ-20250625-010",
        "p1_visible_964a2edc6942": "0.0",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_99f753ed6262": "-3354.88",
        "p1_visible_ada9a85eab00": "",
        "p1_visible_bbe7bbee241e": "",
        "p1_visible_be5462bd6a62": "四川保盛建设集团有限公司",
        "p1_visible_c1b95b8ca332": "0.0",
        "p1_visible_c73a8eab0d57": "-40631.27",
        "p1_visible_d42c2d26610f": "2025-06-20",
        "p1_visible_dfc25d77dc39": "XXKPDJ-20250625-010",
        "p1_visible_ee6a4d9e2956": "XXKPDJ-20250625-010",
        "p1_visible_f22832ce4781": "-1",
        "p1_visible_f9cc22d53aff": "中国移动通信集团四川有限公司成都分公司"
      },
      {
        "id": "531302",
        "p1_visible_007363f27191": "82.57",
        "p1_visible_06fa8c6f628f": "已作废",
        "p1_visible_0e2126d6cf82": "0",
        "p1_visible_37d56ad493cf": "9%",
        "p1_visible_3e7255522b33": "公司综合平台",
        "p1_visible_7f5da566c14e": "XXKPDJ-20250625-007",
        "p1_visible_8fa8662ad38f": "XXKPDJ-20250625-007",
        "p1_visible_964a2edc6942": "0.0",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_99f753ed6262": "7.43",
        "p1_visible_ada9a85eab00": "",
        "p1_visible_bbe7bbee241e": "",
        "p1_visible_be5462bd6a62": "四川保盛建设集团有限公司",
        "p1_visible_c1b95b8ca332": "0.0",
        "p1_visible_c73a8eab0d57": "90.0",
        "p1_visible_d42c2d26610f": "2025-06-25",
        "p1_visible_dfc25d77dc39": "XXKPDJ-20250625-007",
        "p1_visible_ee6a4d9e2956": "XXKPDJ-20250625-007",
        "p1_visible_f22832ce4781": "-1",
        "p1_visible_f9cc22d53aff": "绵阳市游仙区交通运输局公路管理所"
      },
      {
        "id": "531102",
        "p1_visible_007363f27191": "-345856.5",
        "p1_visible_06fa8c6f628f": "审核中",
        "p1_visible_0e2126d6cf82": "0",
        "p1_visible_37d56ad493cf": "9%",
        "p1_visible_3e7255522b33": "公司综合平台",
        "p1_visible_7f5da566c14e": "XXKPDJ-20250825-004",
        "p1_visible_8fa8662ad38f": "XXKPDJ-20250825-004",
        "p1_visible_964a2edc6942": "0.0",
        "p1_visible_99f6fe6c41ad": "",
        "p1_visible_99f753ed6262": "-31127.09",
        "p1_visible_ada9a85eab00": "",
        "p1_visible_bbe7bbee241e": "",
        "p1_visible_be5462bd6a62": "四川保盛建设集团有限公司",
        "p1_visible_c1b95b8ca332": "0.0",
        "p1_visible_c73a8eab0d57": "-376983.59",
        "p1_visible_d42c2d26610f": "2025-08-22",
        "p1_visible_dfc25d77dc39": "XXKPDJ-20250825-004",
        "p1_visible_ee6a4d9e2956": "XXKPDJ-20250825-004",
        "p1_visible_f22832ce4781": "1",
        "p1_visible_f9cc22d53aff": "中国建筑第六工程局有限公司"
      }
    ],
    "seq": 400,
    "status": "REVIEW_CRITICAL_EMPTY",
    "view_id": 2718
  },
  {
    "action_id": 894,
    "contract_field_count": 20,
    "critical_empty_count": 0,
    "critical_empty_labels": [],
    "delivered_count": 317,
    "domain": [
      [
        "source_table",
        "in",
        [
          "ZJGL_WJZ_WJZDJB"
        ]
      ]
    ],
    "double_display_hit_count": 1,
    "double_display_hits": [
      {
        "id": "4154",
        "label": "跨区域经营地址",
        "value": "四川省绵阳市游仙区盐泉镇四川省绵阳市游仙区盐泉镇"
      }
    ],
    "field_coverage": [
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_06fa8c6f628f",
        "filled": 80,
        "label": "单据状态",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_8fa8662ad38f",
        "filled": 80,
        "label": "单据编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_3e7255522b33",
        "filled": 80,
        "label": "项目名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_c1947c4b9d4a",
        "filled": 80,
        "label": "纳税人名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_c237c1b31858",
        "filled": 80,
        "label": "纳税人识别号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_a81dc7a3d1c9",
        "filled": 80,
        "label": "经办人手机",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_d2f17f6ee06c",
        "filled": 80,
        "label": "区域涉税事项联系人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_099c01b9d72a",
        "filled": 80,
        "label": "区域涉税事项联系人座机手机",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_026768aaad3c",
        "filled": 80,
        "label": "跨区域经营地址",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_764d417cabd2",
        "filled": 80,
        "label": "经营方式",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_b8fbf277a7b1",
        "filled": 80,
        "label": "合同名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_75e856a13c7c",
        "filled": 80,
        "label": "合同金额",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ba13d5091f9a",
        "filled": 80,
        "label": "合同开始日期",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_43c2e2732d0a",
        "filled": 80,
        "label": "合同结束日期",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_a943bac2de74",
        "filled": 80,
        "label": "合同相对方名称",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_00be183a4b2a",
        "filled": 80,
        "label": "合同相对方名称编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_46c54c70dedb",
        "filled": 80,
        "label": "跨区域涉税事项报验管理编号",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_99f6fe6c41ad",
        "filled": 80,
        "label": "附件",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_ee6a4d9e2956",
        "filled": 80,
        "label": "录入人",
        "ratio": 1.0,
        "sample_size": 80
      },
      {
        "coverage_mode": "sample_nonstored",
        "field": "p1_visible_dfc25d77dc39",
        "filled": 80,
        "label": "录入时间",
        "ratio": 1.0,
        "sample_size": 80
      }
    ],
    "group": "发票税务",
    "legacy_source_tables": [
      "ZJGL_WJZ_WJZDJB"
    ],
    "missing_alias_fields": [],
    "model": "sc.legacy.payment.residual.fact",
    "model_missing": false,
    "name": "外经证登记",
    "raw_hash_hit_count": 52,
    "raw_hash_hits": [
      {
        "id": "4227",
        "label": "附件",
        "value": "（2021）857重庆花园路项目外经证.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/6/10/ed97339d5f47a6f31a6025dc6"
      },
      {
        "id": "4226",
        "label": "附件",
        "value": "〔2022〕 23#岳普湖县20年棚户区改造项目 外经证 .pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/1/4/281b308ba8bfa2ca"
      },
      {
        "id": "4225",
        "label": "附件",
        "value": "〔2022〕 1312# 荣昌仁义中学项目.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/9/27/344b0438218b3d32df477dd"
      },
      {
        "id": "4223",
        "label": "附件",
        "value": "（2018）54  -安居区.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/8/11/8cc62d852a39e244ad2a03b5e056b6"
      },
      {
        "id": "4222",
        "label": "附件",
        "value": "（2020）1628 布拖县补洛乡.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/12/8/61b8b4f18984d172952ff0d1926"
      },
      {
        "id": "4220",
        "label": "附件",
        "value": "（2020）642#-移动车库改机房外经证.jpg | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/8/11/3434f1d4ac5fc9464f4433d"
      },
      {
        "id": "4219",
        "label": "附件",
        "value": "1.21 最新〔2020〕 270 剑阁莲石笋七标段.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/1/21/af8a175ee241f82766"
      },
      {
        "id": "4213",
        "label": "附件",
        "value": "（2018）3  珠峰一标段.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/8/11/96b7981023eb03e5df12243b3aa8f6"
      },
      {
        "id": "4211",
        "label": "附件",
        "value": "（2021）920柳梧新区防洪渠外经证.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/6/24/64a308baa66b67b431112f29c"
      },
      {
        "id": "4209",
        "label": "附件",
        "value": "（2021）337二坪镇外经证.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/2/3/b27169b927e2d1de76497530bcd2fd"
      },
      {
        "id": "4208",
        "label": "附件",
        "value": "（2019）300-移动乐山.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/12/15/a1bc538723555d8dad38fc5760d0c"
      },
      {
        "id": "4205",
        "label": "附件",
        "value": "〔2023〕 712 号璧山区2022年广普镇丘陵山区高标准农田改造提升示范工程试点项目五标段.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2023/6/"
      },
      {
        "id": "4204",
        "label": "附件",
        "value": "铜梁区太平镇（2020）1107#.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/9/11/4a4be7557f5ca6d099871fd7ce1"
      },
      {
        "id": "4203",
        "label": "附件",
        "value": "（2018）-26  #三供一业.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/8/11/9986bed243439c5e41254f2f79af"
      },
      {
        "id": "4202",
        "label": "附件",
        "value": "（2020）1590.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/12/4/cadd2ece227ed002552b5a107692c9f5.p"
      },
      {
        "id": "4201",
        "label": "附件",
        "value": "（2020）1514#苍溪县2020高标.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/11/30/b6444019e5ec7b8bebe6e73"
      },
      {
        "id": "4199",
        "label": "附件",
        "value": "（2019）469-德昌县宽裕镇花园村文化休闲广外经证.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/8/12/a5aa8056a5b4058dc"
      },
      {
        "id": "4197",
        "label": "附件",
        "value": "（2020）1406#梦溪苑.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/11/24/55d255a393f5a852f1235a3c8b5d7"
      },
      {
        "id": "4196",
        "label": "附件",
        "value": "〔2022〕 1789 号移动省本部.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/12/21/25e5cf5d4cdae77162f3262bb"
      },
      {
        "id": "4195",
        "label": "附件",
        "value": "〔2022〕 699#米易县高铁站前广场环境整治.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/5/19/3449ac859adf6310a4e5"
      }
    ],
    "sample_rows": [
      {
        "id": "4227",
        "p1_visible_00be183a4b2a": "WJZDJ-20210610-001",
        "p1_visible_026768aaad3c": "南岸区花园路街道古楼片区",
        "p1_visible_06fa8c6f628f": "审核通过",
        "p1_visible_099c01b9d72a": "WJZDJ-20210610-001",
        "p1_visible_3e7255522b33": "花园路街道古楼片区配套基础设施建设工程",
        "p1_visible_43c2e2732d0a": "2022-12-31",
        "p1_visible_46c54c70dedb": "旌税 税跨报 〔2021〕 857 号",
        "p1_visible_75e856a13c7c": "7261193.39",
        "p1_visible_764d417cabd2": "建筑安装",
        "p1_visible_8fa8662ad38f": "WJZDJ-20210610-001",
        "p1_visible_99f6fe6c41ad": "（2021）857重庆花园路项目外经证.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2021/6/10/ed97339d5f47a6f31a6025dc6ef693c1.pdf （2021）857重庆花园路项目外经证.pdf | legacy-file://~/File_New/CollectionPlan/2021/6/10/ed97339d5f47a6f31a6025dc6ef693c1.pdf",
        "p1_visible_a81dc7a3d1c9": "WJZDJ-20210610-001",
        "p1_visible_a943bac2de74": "重庆市南岸区人民政 府花园路街道办事处",
        "p1_visible_b8fbf277a7b1": "花园路街道古楼片区 配套基础设施建设工 程",
        "p1_visible_ba13d5091f9a": "2021-06-10",
        "p1_visible_c1947c4b9d4a": "四川保盛建设集团有 限公司",
        "p1_visible_c237c1b31858": "9151060005217562XR",
        "p1_visible_d2f17f6ee06c": "WJZDJ-20210610-001",
        "p1_visible_dfc25d77dc39": "2021-06-10 11:08:20",
        "p1_visible_ee6a4d9e2956": "尹佳梅"
      },
      {
        "id": "4226",
        "p1_visible_00be183a4b2a": "WJZDJ-20220104-001",
        "p1_visible_026768aaad3c": "新疆喀什地区岳普湖县",
        "p1_visible_06fa8c6f628f": "审核通过",
        "p1_visible_099c01b9d72a": "WJZDJ-20220104-001",
        "p1_visible_3e7255522b33": "岳普湖县2020年棚户区改造安置小区建设项目一标段",
        "p1_visible_43c2e2732d0a": "2025-01-03",
        "p1_visible_46c54c70dedb": "旌税 税跨报 〔2022〕 23 号",
        "p1_visible_75e856a13c7c": "14563617.91",
        "p1_visible_764d417cabd2": "建筑安装",
        "p1_visible_8fa8662ad38f": "WJZDJ-20220104-001",
        "p1_visible_99f6fe6c41ad": "〔2022〕 23#岳普湖县20年棚户区改造项目 外经证 .pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/1/4/281b308ba8bfa2ca8b88217c796e7fd6.pdf 〔2022〕 23#岳普湖县20年棚户区改造项目 外经证 .pdf | legacy-file://~/File_New/CollectionPlan/2022/1/4/281b308ba8bfa2ca8b88217c796e7fd6.pdf",
        "p1_visible_a81dc7a3d1c9": "WJZDJ-20220104-001",
        "p1_visible_a943bac2de74": "中铁十九局集团有限公司",
        "p1_visible_b8fbf277a7b1": "岳普湖县2020年棚户区改造安置小区建设项目一标段",
        "p1_visible_ba13d5091f9a": "2022-01-04",
        "p1_visible_c1947c4b9d4a": "四川保盛建设集团有限公司",
        "p1_visible_c237c1b31858": "9151060005217562XR",
        "p1_visible_d2f17f6ee06c": "WJZDJ-20220104-001",
        "p1_visible_dfc25d77dc39": "2022-01-04 18:39:04",
        "p1_visible_ee6a4d9e2956": "李林旭"
      },
      {
        "id": "4225",
        "p1_visible_00be183a4b2a": "WJZDJ-20220927-001",
        "p1_visible_026768aaad3c": "荣昌区仁义镇中学路 8 号",
        "p1_visible_06fa8c6f628f": "审核通过",
        "p1_visible_099c01b9d72a": "WJZDJ-20220927-001",
        "p1_visible_3e7255522b33": "荣昌区仁义中学校舍建设项目",
        "p1_visible_43c2e2732d0a": "2025-09-26",
        "p1_visible_46c54c70dedb": "旌税 税跨报 〔2022〕 1312 号",
        "p1_visible_75e856a13c7c": "15616342.64",
        "p1_visible_764d417cabd2": "建筑安装",
        "p1_visible_8fa8662ad38f": "WJZDJ-20220927-001",
        "p1_visible_99f6fe6c41ad": "〔2022〕 1312# 荣昌仁义中学项目.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2022/9/27/344b0438218b3d32df477dd79a054443.pdf 〔2022〕 1312# 荣昌仁义中学项目.pdf | legacy-file://~/File_New/CollectionPlan/2022/9/27/344b0438218b3d32df477dd79a054443.pdf",
        "p1_visible_a81dc7a3d1c9": "WJZDJ-20220927-001",
        "p1_visible_a943bac2de74": "重庆市荣昌仁义中学校",
        "p1_visible_b8fbf277a7b1": "WJZDJ-20220927-001",
        "p1_visible_ba13d5091f9a": "2022-09-27",
        "p1_visible_c1947c4b9d4a": "四川保盛建设集团有限公司",
        "p1_visible_c237c1b31858": "9151060005217562XR",
        "p1_visible_d2f17f6ee06c": "WJZDJ-20220927-001",
        "p1_visible_dfc25d77dc39": "2022-09-27 11:14:06",
        "p1_visible_ee6a4d9e2956": "李林旭"
      },
      {
        "id": "4224",
        "p1_visible_00be183a4b2a": "WJZDJB-20240801-001",
        "p1_visible_026768aaad3c": "绵阳市磨家镇",
        "p1_visible_06fa8c6f628f": "审核通过",
        "p1_visible_099c01b9d72a": "WJZDJB-20240801-001",
        "p1_visible_3e7255522b33": "绵阳市公安局高新技术产业开发区分局磨家派出所改造工程",
        "p1_visible_43c2e2732d0a": "2025-12-31",
        "p1_visible_46c54c70dedb": "旌税天 税跨报 〔2024〕 401 号",
        "p1_visible_75e856a13c7c": "927500.0",
        "p1_visible_764d417cabd2": "建筑安装",
        "p1_visible_8fa8662ad38f": "WJZDJB-20240801-001",
        "p1_visible_99f6fe6c41ad": "2024（401号）.pdf | legacy-file://UploadFile/UserFile/2024/08/01/59a3d44a1a894f188fc9be9e7aa5b83a_195883.pdf",
        "p1_visible_a81dc7a3d1c9": "WJZDJB-20240801-001",
        "p1_visible_a943bac2de74": "绵阳市公安局高新技术产业开发区分局",
        "p1_visible_b8fbf277a7b1": "绵阳市公安局高新技术产业开发区分局磨家派出所改造工程",
        "p1_visible_ba13d5091f9a": "2024-08-01",
        "p1_visible_c1947c4b9d4a": "四川保盛建设集团有限公司",
        "p1_visible_c237c1b31858": "9151060005217562XR",
        "p1_visible_d2f17f6ee06c": "WJZDJB-20240801-001",
        "p1_visible_dfc25d77dc39": "2024-08-01 14:58:43",
        "p1_visible_ee6a4d9e2956": "李娜"
      },
      {
        "id": "4223",
        "p1_visible_00be183a4b2a": "WJZDJ-20200811-032",
        "p1_visible_026768aaad3c": "遂宁市安居区",
        "p1_visible_06fa8c6f628f": "审核通过",
        "p1_visible_099c01b9d72a": "WJZDJ-20200811-032",
        "p1_visible_3e7255522b33": "全国新增1000亿斤粮食生产能力安居区2018年田间工程建设项目二标段",
        "p1_visible_43c2e2732d0a": "2020-11-21",
        "p1_visible_46c54c70dedb": "旌税城南 税跨报（2018）54号",
        "p1_visible_75e856a13c7c": "5750219.0",
        "p1_visible_764d417cabd2": "其他",
        "p1_visible_8fa8662ad38f": "WJZDJ-20200811-032",
        "p1_visible_99f6fe6c41ad": "（2018）54  -安居区.pdf | legacy-file://UploadFile/OldSystem/File_New/CollectionPlan/2020/8/11/8cc62d852a39e244ad2a03b5e056b62f.pdf （2018）54  -安居区.pdf | legacy-file://~/File_New/CollectionPlan/2020/8/11/8cc62d852a39e244ad2a03b5e056b62f.pdf",
        "p1_visible_a81dc7a3d1c9": "WJZDJ-20200811-032",
        "p1_visible_a943bac2de74": "遂宁市安居区土壤肥料与生态工作站",
        "p1_visible_b8fbf277a7b1": "全国新增1000亿斤粮食生产能力安居区2018年田间工程建设项目二标段",
        "p1_visible_ba13d5091f9a": "2018-11-22",
        "p1_visible_c1947c4b9d4a": "四川保盛建设集团有限公司",
        "p1_visible_c237c1b31858": "9151060005217562XR",
        "p1_visible_d2f17f6ee06c": "WJZDJ-20200811-032",
        "p1_visible_dfc25d77dc39": "2020-08-11 19:59:59",
        "p1_visible_ee6a4d9e2956": "李林旭"
      }
    ],
    "seq": 440,
    "status": "REVIEW_VISIBLE_VALUE_ANOMALY",
    "view_id": 2722
  }
]
```

## Named Samples

```json
[
  {
    "model": "sc.business.entity",
    "name": "供应商/合作单位",
    "record": {
      "id": "33",
      "p1_visible_06fa8c6f628f": ",,,,,,,,,",
      "p1_visible_0d083785a541": ",,,,,,,,,",
      "p1_visible_0faf3e63f1f4": ",,,,,,,,,",
      "p1_visible_25b047589d9e": ",,,,,,,,,",
      "p1_visible_3e0225610e0b": ",,,,,,,,,",
      "p1_visible_3e7255522b33": ",,,,,,,,,",
      "p1_visible_901384917949": ",,,,,,,,,",
      "p1_visible_cf4210e06be7": ",,,,,,,,,",
      "p1_visible_dfc25d77dc39": ",,,,,,,,,",
      "p1_visible_ee6a4d9e2956": ",,,,,,,,,",
      "p1_visible_f22832ce4781": ",,,,,,,,,",
      "p1_visible_ff13e7689bd2": ",,,,,,,,,"
    },
    "seq": 10,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.business.entity",
    "name": "供应商/合作单位",
    "record": {
      "id": "33",
      "p1_visible_06fa8c6f628f": ",,,,,,,,,",
      "p1_visible_0d083785a541": ",,,,,,,,,",
      "p1_visible_0faf3e63f1f4": ",,,,,,,,,",
      "p1_visible_25b047589d9e": ",,,,,,,,,",
      "p1_visible_3e0225610e0b": ",,,,,,,,,",
      "p1_visible_3e7255522b33": ",,,,,,,,,",
      "p1_visible_901384917949": ",,,,,,,,,",
      "p1_visible_cf4210e06be7": ",,,,,,,,,",
      "p1_visible_dfc25d77dc39": ",,,,,,,,,",
      "p1_visible_ee6a4d9e2956": ",,,,,,,,,",
      "p1_visible_f22832ce4781": ",,,,,,,,,",
      "p1_visible_ff13e7689bd2": ",,,,,,,,,"
    },
    "seq": 10,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.business.entity",
    "name": "往来单位",
    "record": {
      "id": "33",
      "p1_visible_06fa8c6f628f": ",,,,,,,,,",
      "p1_visible_0b959af0bd69": ",,,,,,,,,",
      "p1_visible_25b047589d9e": ",,,,,,,,,",
      "p1_visible_3e0225610e0b": ",,,,,,,,,",
      "p1_visible_3e7255522b33": ",,,,,,,,,",
      "p1_visible_53178a0b4360": ",,,,,,,,,",
      "p1_visible_7b434f7160f0": ",,,,,,,,,",
      "p1_visible_d890d302f7f7": ",,,,,,,,,",
      "p1_visible_dfc25d77dc39": ",,,,,,,,,",
      "p1_visible_ecaf440fd399": ",,,,,,,,,",
      "p1_visible_ee6a4d9e2956": ",,,,,,,,,"
    },
    "seq": 20,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.business.entity",
    "name": "往来单位",
    "record": {
      "id": "33",
      "p1_visible_06fa8c6f628f": ",,,,,,,,,",
      "p1_visible_0b959af0bd69": ",,,,,,,,,",
      "p1_visible_25b047589d9e": ",,,,,,,,,",
      "p1_visible_3e0225610e0b": ",,,,,,,,,",
      "p1_visible_3e7255522b33": ",,,,,,,,,",
      "p1_visible_53178a0b4360": ",,,,,,,,,",
      "p1_visible_7b434f7160f0": ",,,,,,,,,",
      "p1_visible_d890d302f7f7": ",,,,,,,,,",
      "p1_visible_dfc25d77dc39": ",,,,,,,,,",
      "p1_visible_ecaf440fd399": ",,,,,,,,,",
      "p1_visible_ee6a4d9e2956": ",,,,,,,,,"
    },
    "seq": 20,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "construction.contract",
    "name": "施工合同",
    "record": {
      "id": "6956",
      "p1_visible_06fa8c6f628f": "审核通过",
      "p1_visible_0965a7d1e74c": "CONIN2601505",
      "p1_visible_0cf26c325f34": "CONIN2601505",
      "p1_visible_17b341733b7b": "EZDZL2020-012号",
      "p1_visible_202b429f79ca": "是",
      "p1_visible_2585b4ab16bd": "2020-04-24",
      "p1_visible_3e7255522b33": "125t电炸炉项目部分建筑窗户改造工程",
      "p1_visible_3ec01dd569e2": "125t电炸炉项目部分建筑窗户改造工程",
      "p1_visible_5839c15a34a4": "易静（13547083119）",
      "p1_visible_58a2eb3301c1": "0.0",
      "p1_visible_75b438b16f10": "0.0",
      "p1_visible_75e856a13c7c": "38500.0",
      "p1_visible_7b9f4bb3e3ea": "CONIN2601505",
      "p1_visible_8fa8662ad38f": "WBHTGL-20200424-001",
      "p1_visible_99f6fe6c41ad": "1_125t电渣炉项目部分建筑窗户改造工程施工合同.doc | legacy-file://UploadFile/OldSystem/File_New/OutContract/2020/4/24/2fa682a54f30e33bc1741e8f79df92bb.doc\n1_125t电渣炉项目部分建筑窗户改造工程施工合同.doc | legacy-file://~/File_New/OutContract/2020/4/24/2fa682a54f30e33bc1741e8f79df92bb.doc",
      "p1_visible_affba7961481": "0.0",
      "p1_visible_bf0c9e684289": "CONIN2601505",
      "p1_visible_da9d3c637407": "0.0",
      "p1_visible_dfc25d77dc39": "2020-04-26 00:00:00",
      "p1_visible_ee6a4d9e2956": "邓洪英",
      "p1_visible_fadf1135d6a4": "二重（德阳）重型装备有限公司"
    },
    "seq": 30,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "construction.contract",
    "name": "施工合同",
    "record": {
      "id": "6956",
      "p1_visible_06fa8c6f628f": "审核通过",
      "p1_visible_0965a7d1e74c": "CONIN2601505",
      "p1_visible_0cf26c325f34": "CONIN2601505",
      "p1_visible_17b341733b7b": "EZDZL2020-012号",
      "p1_visible_202b429f79ca": "是",
      "p1_visible_2585b4ab16bd": "2020-04-24",
      "p1_visible_3e7255522b33": "125t电炸炉项目部分建筑窗户改造工程",
      "p1_visible_3ec01dd569e2": "125t电炸炉项目部分建筑窗户改造工程",
      "p1_visible_5839c15a34a4": "易静（13547083119）",
      "p1_visible_58a2eb3301c1": "0.0",
      "p1_visible_75b438b16f10": "0.0",
      "p1_visible_75e856a13c7c": "38500.0",
      "p1_visible_7b9f4bb3e3ea": "CONIN2601505",
      "p1_visible_8fa8662ad38f": "WBHTGL-20200424-001",
      "p1_visible_99f6fe6c41ad": "1_125t电渣炉项目部分建筑窗户改造工程施工合同.doc | legacy-file://UploadFile/OldSystem/File_New/OutContract/2020/4/24/2fa682a54f30e33bc1741e8f79df92bb.doc\n1_125t电渣炉项目部分建筑窗户改造工程施工合同.doc | legacy-file://~/File_New/OutContract/2020/4/24/2fa682a54f30e33bc1741e8f79df92bb.doc",
      "p1_visible_affba7961481": "0.0",
      "p1_visible_bf0c9e684289": "CONIN2601505",
      "p1_visible_da9d3c637407": "0.0",
      "p1_visible_dfc25d77dc39": "2020-04-26 00:00:00",
      "p1_visible_ee6a4d9e2956": "邓洪英",
      "p1_visible_fadf1135d6a4": "二重（德阳）重型装备有限公司"
    },
    "seq": 30,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.document.admin.document",
    "name": "公司资料存档",
    "record": {
      "id": "8641",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_0791e483b4d2": "公司资料存档",
      "p1_visible_3e7255522b33": "公司资料存档",
      "p1_visible_8fdc4ab6f3dc": "公司资料存档",
      "p1_visible_dfc25d77dc39": "公司资料存档",
      "p1_visible_e0361480e3a5": "旧文件路径: UploadFile/UserFile/2026/04/10/faad486d11854e7f9012afb913bd3ff8_162042.pdf\n扩展名: pdf\n上传人: 江一娇\n上传时间: 2026-04-10 11:40:40.96\n文件大小: 162042\n分类规则: company_file_name\nsource_table=BASE_SYSTEM_FILE; source=0; group_company=",
      "p1_visible_ee6a4d9e2956": "公司资料存档"
    },
    "seq": 40,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.document.admin.document",
    "name": "公司资料存档",
    "record": {
      "id": "8641",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_0791e483b4d2": "公司资料存档",
      "p1_visible_3e7255522b33": "公司资料存档",
      "p1_visible_8fdc4ab6f3dc": "公司资料存档",
      "p1_visible_dfc25d77dc39": "公司资料存档",
      "p1_visible_e0361480e3a5": "旧文件路径: UploadFile/UserFile/2026/04/10/faad486d11854e7f9012afb913bd3ff8_162042.pdf\n扩展名: pdf\n上传人: 江一娇\n上传时间: 2026-04-10 11:40:40.96\n文件大小: 162042\n分类规则: company_file_name\nsource_table=BASE_SYSTEM_FILE; source=0; group_company=",
      "p1_visible_ee6a4d9e2956": "公司资料存档"
    },
    "seq": 40,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.office.admin.document",
    "name": "请假/休假审批单",
    "record": {
      "id": "137",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_1509ea5aa328": "病假",
      "p1_visible_342372602a87": "请假/休假审批 - 罗萌",
      "p1_visible_3e7255522b33": "请假/休假审批 - 罗萌",
      "p1_visible_3f36b5502196": "请假/休假审批 - 罗萌",
      "p1_visible_4f1b37216d49": "请假/休假审批 - 罗萌",
      "p1_visible_8fa8662ad38f": "QJXJSPB-20260402-001",
      "p1_visible_a8e78b10a188": "请假/休假审批 - 罗萌",
      "p1_visible_b03bc1337add": "请假/休假审批 - 罗萌",
      "p1_visible_b56f68e8a4db": "请假/休假审批 - 罗萌",
      "p1_visible_dfc25d77dc39": "请假/休假审批 - 罗萌",
      "p1_visible_e0361480e3a5": "旧系统备注: 医院看病\n申请人: 罗萌\n部门: 财务部\n请假类型: 病假\n请假时长: 4.0小时 / 0.5天\n附件引用: c7ad1b4c10bac33cc442d636baf26cb5",
      "p1_visible_ee6a4d9e2956": "请假/休假审批 - 罗萌"
    },
    "seq": 50,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.office.admin.document",
    "name": "请假/休假审批单",
    "record": {
      "id": "137",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_1509ea5aa328": "病假",
      "p1_visible_342372602a87": "请假/休假审批 - 罗萌",
      "p1_visible_3e7255522b33": "请假/休假审批 - 罗萌",
      "p1_visible_3f36b5502196": "请假/休假审批 - 罗萌",
      "p1_visible_4f1b37216d49": "请假/休假审批 - 罗萌",
      "p1_visible_8fa8662ad38f": "QJXJSPB-20260402-001",
      "p1_visible_a8e78b10a188": "请假/休假审批 - 罗萌",
      "p1_visible_b03bc1337add": "请假/休假审批 - 罗萌",
      "p1_visible_b56f68e8a4db": "请假/休假审批 - 罗萌",
      "p1_visible_dfc25d77dc39": "请假/休假审批 - 罗萌",
      "p1_visible_e0361480e3a5": "旧系统备注: 医院看病\n申请人: 罗萌\n部门: 财务部\n请假类型: 病假\n请假时长: 4.0小时 / 0.5天\n附件引用: c7ad1b4c10bac33cc442d636baf26cb5",
      "p1_visible_ee6a4d9e2956": "请假/休假审批 - 罗萌"
    },
    "seq": 50,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.office.admin.document",
    "name": "印章使用审批表",
    "record": {
      "id": "721",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_17b341733b7b": "章管家2023年10月盖章记录",
      "p1_visible_2559d3f7672e": "章管家2023年10月盖章记录",
      "p1_visible_2715f827834b": "章管家2023年10月盖章记录",
      "p1_visible_2d158ad0c744": "章管家2023年10月盖章记录",
      "p1_visible_2d3cea857f5c": "章管家2023年10月盖章记录",
      "p1_visible_324929811990": "章管家2023年10月盖章记录",
      "p1_visible_39169745e6a4": "章管家2023年10月盖章记录",
      "p1_visible_6c35ddfb6034": "章管家2023年10月盖章记录",
      "p1_visible_75e856a13c7c": "0.0",
      "p1_visible_7abb0844fb4c": "章管家2023年10月盖章记录",
      "p1_visible_88c9f74d6c60": "章管家2023年10月盖章记录",
      "p1_visible_8fa8662ad38f": "YZSYSPB-20231121-001",
      "p1_visible_99f6fe6c41ad": "章管家2023年10月盖章记录",
      "p1_visible_9be1ef3a84d7": "章管家2023年10月盖章记录",
      "p1_visible_a8b6e96c9036": "章管家2023年10月盖章记录",
      "p1_visible_b74d956638f0": "章管家2023年10月盖章记录",
      "p1_visible_dfc25d77dc39": "章管家2023年10月盖章记录",
      "p1_visible_e0361480e3a5": "旧系统标题: 章管家2023年10月盖章记录\n申请人: 李林旭\n部门: 公司员工\n印章资料: 7910001\n使用类型: 11550001\n紧急程度: \n附件引用: d3e1780f6197fd4444ed3ca5a2a56a34\n旧系统说明: 章管家2023年10月盖章记录 / 章管家2023年10月盖章记录",
      "p1_visible_e8f87f5bc217": "章管家2023年10月盖章记录",
      "p1_visible_ee6a4d9e2956": "章管家2023年10月盖章记录"
    },
    "seq": 60,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.office.admin.document",
    "name": "印章使用审批表",
    "record": {
      "id": "721",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_17b341733b7b": "章管家2023年10月盖章记录",
      "p1_visible_2559d3f7672e": "章管家2023年10月盖章记录",
      "p1_visible_2715f827834b": "章管家2023年10月盖章记录",
      "p1_visible_2d158ad0c744": "章管家2023年10月盖章记录",
      "p1_visible_2d3cea857f5c": "章管家2023年10月盖章记录",
      "p1_visible_324929811990": "章管家2023年10月盖章记录",
      "p1_visible_39169745e6a4": "章管家2023年10月盖章记录",
      "p1_visible_6c35ddfb6034": "章管家2023年10月盖章记录",
      "p1_visible_75e856a13c7c": "0.0",
      "p1_visible_7abb0844fb4c": "章管家2023年10月盖章记录",
      "p1_visible_88c9f74d6c60": "章管家2023年10月盖章记录",
      "p1_visible_8fa8662ad38f": "YZSYSPB-20231121-001",
      "p1_visible_99f6fe6c41ad": "章管家2023年10月盖章记录",
      "p1_visible_9be1ef3a84d7": "章管家2023年10月盖章记录",
      "p1_visible_a8b6e96c9036": "章管家2023年10月盖章记录",
      "p1_visible_b74d956638f0": "章管家2023年10月盖章记录",
      "p1_visible_dfc25d77dc39": "章管家2023年10月盖章记录",
      "p1_visible_e0361480e3a5": "旧系统标题: 章管家2023年10月盖章记录\n申请人: 李林旭\n部门: 公司员工\n印章资料: 7910001\n使用类型: 11550001\n紧急程度: \n附件引用: d3e1780f6197fd4444ed3ca5a2a56a34\n旧系统说明: 章管家2023年10月盖章记录 / 章管家2023年10月盖章记录",
      "p1_visible_e8f87f5bc217": "章管家2023年10月盖章记录",
      "p1_visible_ee6a4d9e2956": "章管家2023年10月盖章记录"
    },
    "seq": 60,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.legacy.user.profile",
    "name": "公司人员名册（配置）",
    "record": {
      "id": "1",
      "p1_visible_11e70a588ac6": "",
      "p1_visible_1f45acad0522": "",
      "p1_visible_227aa7349ee6": "",
      "p1_visible_24d16fdd11e9": "0",
      "p1_visible_2934a0209489": "",
      "p1_visible_3ac5adffdcf6": "",
      "p1_visible_3b60c4db720a": "",
      "p1_visible_3f253e92f54e": "0",
      "p1_visible_4ffe06c7ad15": "管理员角色,通用角色",
      "p1_visible_5c44c9fc30d5": "",
      "p1_visible_6fa4ff6b5525": "",
      "p1_visible_8673de005959": "",
      "p1_visible_88a0e7c9869e": "",
      "p1_visible_8d45eb63982a": "",
      "p1_visible_91061a56c00f": "四川保盛建设集团有限公司",
      "p1_visible_9bf4a979d81d": "",
      "p1_visible_a1aaf352cb07": "admin",
      "p1_visible_a1cd13bcc550": "",
      "p1_visible_be4c2616b177": "admin",
      "p1_visible_df36a836d415": "",
      "p1_visible_dfc25d77dc39": "",
      "p1_visible_ee6a4d9e2956": "admin",
      "p1_visible_f0f3e908c213": "",
      "p1_visible_f3ea6d345e2a": "启用",
      "p1_visible_f63da5b6950e": "",
      "p1_visible_f6db3f132d90": "",
      "p1_visible_fe8aa4ef93bd": ""
    },
    "seq": 80,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.legacy.user.profile",
    "name": "公司人员名册（配置）",
    "record": {
      "id": "1",
      "p1_visible_11e70a588ac6": "",
      "p1_visible_1f45acad0522": "",
      "p1_visible_227aa7349ee6": "",
      "p1_visible_24d16fdd11e9": "0",
      "p1_visible_2934a0209489": "",
      "p1_visible_3ac5adffdcf6": "",
      "p1_visible_3b60c4db720a": "",
      "p1_visible_3f253e92f54e": "0",
      "p1_visible_4ffe06c7ad15": "管理员角色,通用角色",
      "p1_visible_5c44c9fc30d5": "",
      "p1_visible_6fa4ff6b5525": "",
      "p1_visible_8673de005959": "",
      "p1_visible_88a0e7c9869e": "",
      "p1_visible_8d45eb63982a": "",
      "p1_visible_91061a56c00f": "四川保盛建设集团有限公司",
      "p1_visible_9bf4a979d81d": "",
      "p1_visible_a1aaf352cb07": "admin",
      "p1_visible_a1cd13bcc550": "",
      "p1_visible_be4c2616b177": "admin",
      "p1_visible_df36a836d415": "",
      "p1_visible_dfc25d77dc39": "",
      "p1_visible_ee6a4d9e2956": "admin",
      "p1_visible_f0f3e908c213": "",
      "p1_visible_f3ea6d345e2a": "启用",
      "p1_visible_f63da5b6950e": "",
      "p1_visible_f6db3f132d90": "",
      "p1_visible_fe8aa4ef93bd": ""
    },
    "seq": 80,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.hr.payroll.document",
    "name": "社保人员登记",
    "record": {
      "id": "5165",
      "p1_visible_0e251e3ec516": "社保人员登记 - 郑淼",
      "p1_visible_1e62803e196c": "社保人员登记 - 郑淼",
      "p1_visible_3f253e92f54e": "社保人员登记 - 郑淼",
      "p1_visible_4fdb9ce5c61b": "社保人员登记 - 郑淼",
      "p1_visible_60beedc8f22b": "社保人员登记 - 郑淼",
      "p1_visible_80e04d40f1d5": "社保人员登记 - 郑淼",
      "p1_visible_84622b941985": "社保人员登记 - 郑淼",
      "p1_visible_8fa8662ad38f": "SBRY-20260120-001",
      "p1_visible_9c56d919cf1c": "社保人员登记 - 郑淼",
      "p1_visible_be4c2616b177": "社保人员登记 - 郑淼",
      "p1_visible_ca67e373988f": "1612.68",
      "p1_visible_dfc25d77dc39": "社保人员登记 - 郑淼",
      "p1_visible_e0361480e3a5": "人员类型: 个人挂靠\n人员状态: 启用\n联系方式: 13628107997\n证书/备注: 四川保盛建设集团有限公司\n公司金额: 312.56\n养老金额: 1083.58\n失业金额: 216.54\n附件引用: da6a3b969a7b9f5c22e5cbd63b1e2e4b",
      "p1_visible_ee6a4d9e2956": "社保人员登记 - 郑淼"
    },
    "seq": 90,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.hr.payroll.document",
    "name": "社保人员登记",
    "record": {
      "id": "5165",
      "p1_visible_0e251e3ec516": "社保人员登记 - 郑淼",
      "p1_visible_1e62803e196c": "社保人员登记 - 郑淼",
      "p1_visible_3f253e92f54e": "社保人员登记 - 郑淼",
      "p1_visible_4fdb9ce5c61b": "社保人员登记 - 郑淼",
      "p1_visible_60beedc8f22b": "社保人员登记 - 郑淼",
      "p1_visible_80e04d40f1d5": "社保人员登记 - 郑淼",
      "p1_visible_84622b941985": "社保人员登记 - 郑淼",
      "p1_visible_8fa8662ad38f": "SBRY-20260120-001",
      "p1_visible_9c56d919cf1c": "社保人员登记 - 郑淼",
      "p1_visible_be4c2616b177": "社保人员登记 - 郑淼",
      "p1_visible_ca67e373988f": "1612.68",
      "p1_visible_dfc25d77dc39": "社保人员登记 - 郑淼",
      "p1_visible_e0361480e3a5": "人员类型: 个人挂靠\n人员状态: 启用\n联系方式: 13628107997\n证书/备注: 四川保盛建设集团有限公司\n公司金额: 312.56\n养老金额: 1083.58\n失业金额: 216.54\n附件引用: da6a3b969a7b9f5c22e5cbd63b1e2e4b",
      "p1_visible_ee6a4d9e2956": "社保人员登记 - 郑淼"
    },
    "seq": 90,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.hr.payroll.document",
    "name": "社保登记",
    "record": {
      "id": "4946",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_3f2c92346bec": "2026-05-21 07:57:12.209328",
      "p1_visible_51d806399a4e": "2",
      "p1_visible_57301575f310": "社保登记 - 刘汶衔 2026-02",
      "p1_visible_60beedc8f22b": "社保登记 - 刘汶衔 2026-02",
      "p1_visible_74ba6d25c64e": "2026",
      "p1_visible_7afa7e3935c5": "社保登记 - 刘汶衔 2026-02",
      "p1_visible_80e04d40f1d5": "社保登记 - 刘汶衔 2026-02",
      "p1_visible_8c47a7ab1349": "社保登记 - 刘汶衔 2026-02",
      "p1_visible_8fa8662ad38f": "GZ-20260320-001",
      "p1_visible_be4c2616b177": "社保登记 - 刘汶衔 2026-02",
      "p1_visible_e0361480e3a5": "工资单号: GZ-20260320-001\n人员: 刘汶衔\n部门: 项目部\n工资期间: 2026-2\n工资社保扣款: 477.1500\n附件引用: 0081d871a49c926cf8243f9f9b6c55f6\n行备注:",
      "p1_visible_e4e46c7235d1": "社保登记 - 刘汶衔 2026-02"
    },
    "seq": 100,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.hr.payroll.document",
    "name": "社保登记",
    "record": {
      "id": "4946",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_3f2c92346bec": "2026-05-21 07:57:12.209328",
      "p1_visible_51d806399a4e": "2",
      "p1_visible_57301575f310": "社保登记 - 刘汶衔 2026-02",
      "p1_visible_60beedc8f22b": "社保登记 - 刘汶衔 2026-02",
      "p1_visible_74ba6d25c64e": "2026",
      "p1_visible_7afa7e3935c5": "社保登记 - 刘汶衔 2026-02",
      "p1_visible_80e04d40f1d5": "社保登记 - 刘汶衔 2026-02",
      "p1_visible_8c47a7ab1349": "社保登记 - 刘汶衔 2026-02",
      "p1_visible_8fa8662ad38f": "GZ-20260320-001",
      "p1_visible_be4c2616b177": "社保登记 - 刘汶衔 2026-02",
      "p1_visible_e0361480e3a5": "工资单号: GZ-20260320-001\n人员: 刘汶衔\n部门: 项目部\n工资期间: 2026-2\n工资社保扣款: 477.1500\n附件引用: 0081d871a49c926cf8243f9f9b6c55f6\n行备注:",
      "p1_visible_e4e46c7235d1": "社保登记 - 刘汶衔 2026-02"
    },
    "seq": 100,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.hr.payroll.document",
    "name": "工资登记",
    "record": {
      "id": "3458",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_1329bae177ec": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_51d806399a4e": "2",
      "p1_visible_66819a676970": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_6b7f34b5b51c": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_748d7dc7e321": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_74cf2fb16ad9": "10522.85",
      "p1_visible_8fa8662ad38f": "GZ-20260320-001",
      "p1_visible_91061a56c00f": "四川保盛建设集团有限公司 / 项目部",
      "p1_visible_99f6fe6c41ad": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_b4226e43b871": "11000.0",
      "p1_visible_be4c2616b177": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_c668c7a28f7c": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_dfc25d77dc39": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_e0361480e3a5": "工资单号: GZ-20260320-001\n工资标题: 2月工资\n人员: 刘汶衔\n部门: 项目部\n岗位: \n社保扣款: 477.1500\n公积金: \n个税: \n附件引用: 0081d871a49c926cf8243f9f9b6c55f6\n行备注:",
      "p1_visible_ee6a4d9e2956": "工资登记 - 刘汶衔 2026-02"
    },
    "seq": 110,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.hr.payroll.document",
    "name": "工资登记",
    "record": {
      "id": "3458",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_1329bae177ec": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_51d806399a4e": "2",
      "p1_visible_66819a676970": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_6b7f34b5b51c": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_748d7dc7e321": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_74cf2fb16ad9": "10522.85",
      "p1_visible_8fa8662ad38f": "GZ-20260320-001",
      "p1_visible_91061a56c00f": "四川保盛建设集团有限公司 / 项目部",
      "p1_visible_99f6fe6c41ad": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_b4226e43b871": "11000.0",
      "p1_visible_be4c2616b177": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_c668c7a28f7c": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_dfc25d77dc39": "工资登记 - 刘汶衔 2026-02",
      "p1_visible_e0361480e3a5": "工资单号: GZ-20260320-001\n工资标题: 2月工资\n人员: 刘汶衔\n部门: 项目部\n岗位: \n社保扣款: 477.1500\n公积金: \n个税: \n附件引用: 0081d871a49c926cf8243f9f9b6c55f6\n行备注:",
      "p1_visible_ee6a4d9e2956": "工资登记 - 刘汶衔 2026-02"
    },
    "seq": 110,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.hr.payroll.document",
    "name": "补助",
    "record": {
      "id": "4983",
      "p1_visible_3e7255522b33": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_4b4bd90c12ba": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_51d806399a4e": "6",
      "p1_visible_62e951a692ff": "已完成",
      "p1_visible_67d4f7d4cc3e": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_74ba6d25c64e": "2025",
      "p1_visible_8fa8662ad38f": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_91061a56c00f": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_be515165d80b": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_dfc25d77dc39": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_ee6a4d9e2956": "补助 - 杨德胜 绵阳游泳项目检查"
    },
    "seq": 120,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.hr.payroll.document",
    "name": "补助",
    "record": {
      "id": "4983",
      "p1_visible_3e7255522b33": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_4b4bd90c12ba": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_51d806399a4e": "6",
      "p1_visible_62e951a692ff": "已完成",
      "p1_visible_67d4f7d4cc3e": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_74ba6d25c64e": "2025",
      "p1_visible_8fa8662ad38f": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_91061a56c00f": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_be515165d80b": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_dfc25d77dc39": "补助 - 杨德胜 绵阳游泳项目检查",
      "p1_visible_ee6a4d9e2956": "补助 - 杨德胜 绵阳游泳项目检查"
    },
    "seq": 120,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.document.admin.document",
    "name": "借阅申请",
    "record": {
      "id": "210",
      "p1_visible_000378f72584": "借阅申请 - 借款合同、付款委托",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_0f851fd0b341": "借阅申请 - 借款合同、付款委托",
      "p1_visible_175a9b118cfb": "借阅申请 - 借款合同、付款委托",
      "p1_visible_17a5ebcb2d04": "借阅申请 - 借款合同、付款委托",
      "p1_visible_1a3669b6d0b3": "借阅申请 - 借款合同、付款委托",
      "p1_visible_28507194f2ef": "借阅申请 - 借款合同、付款委托",
      "p1_visible_2c346345746e": "2026-05-21 07:57:28.618859",
      "p1_visible_30187403acc2": "2026-04-02",
      "p1_visible_5b4aca8845f1": "借阅申请 - 借款合同、付款委托",
      "p1_visible_60beedc8f22b": "借阅申请 - 借款合同、付款委托",
      "p1_visible_6f9a8c4e1834": "借阅申请 - 借款合同、付款委托",
      "p1_visible_7200f83d9ede": "借阅申请 - 借款合同、付款委托",
      "p1_visible_809c55b63d56": "借阅申请 - 借款合同、付款委托",
      "p1_visible_8fa8662ad38f": "WJHQ-20260402-001",
      "p1_visible_9719894bb9d8": "借阅申请 - 借款合同、付款委托",
      "p1_visible_974d383f3698": "借阅申请 - 借款合同、付款委托",
      "p1_visible_99f6fe6c41ad": "借阅申请 - 借款合同、付款委托",
      "p1_visible_a7e811434780": "借阅申请 - 借款合同、付款委托",
      "p1_visible_dfc25d77dc39": "借阅申请 - 借款合同、付款委托",
      "p1_visible_e001fb68d7f2": "借阅申请 - 借款合同、付款委托",
      "p1_visible_e0361480e3a5": "来源表: BGGL_TZXX_WJHQ\n文件类型: 其他\n快递/文件编号: SF1464125012747(对方支付）\n签收/借阅人: ***\n项目: 四川广元昭化中国食品产业发展重点园区（工业园区泉坝台阶地）项目场平、道路工程施工\n原始说明: 借款合同、付款委托，已移交财务文楠",
      "p1_visible_edb1f6f12f51": "借阅申请 - 借款合同、付款委托",
      "p1_visible_ee6a4d9e2956": "借阅申请 - 借款合同、付款委托",
      "p1_visible_f1ec63ea5126": "借阅申请 - 借款合同、付款委托",
      "p1_visible_fb2f8cfd18bf": "徐丹"
    },
    "seq": 150,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.document.admin.document",
    "name": "借阅申请",
    "record": {
      "id": "210",
      "p1_visible_000378f72584": "借阅申请 - 借款合同、付款委托",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_0f851fd0b341": "借阅申请 - 借款合同、付款委托",
      "p1_visible_175a9b118cfb": "借阅申请 - 借款合同、付款委托",
      "p1_visible_17a5ebcb2d04": "借阅申请 - 借款合同、付款委托",
      "p1_visible_1a3669b6d0b3": "借阅申请 - 借款合同、付款委托",
      "p1_visible_28507194f2ef": "借阅申请 - 借款合同、付款委托",
      "p1_visible_2c346345746e": "2026-05-21 07:57:28.618859",
      "p1_visible_30187403acc2": "2026-04-02",
      "p1_visible_5b4aca8845f1": "借阅申请 - 借款合同、付款委托",
      "p1_visible_60beedc8f22b": "借阅申请 - 借款合同、付款委托",
      "p1_visible_6f9a8c4e1834": "借阅申请 - 借款合同、付款委托",
      "p1_visible_7200f83d9ede": "借阅申请 - 借款合同、付款委托",
      "p1_visible_809c55b63d56": "借阅申请 - 借款合同、付款委托",
      "p1_visible_8fa8662ad38f": "WJHQ-20260402-001",
      "p1_visible_9719894bb9d8": "借阅申请 - 借款合同、付款委托",
      "p1_visible_974d383f3698": "借阅申请 - 借款合同、付款委托",
      "p1_visible_99f6fe6c41ad": "借阅申请 - 借款合同、付款委托",
      "p1_visible_a7e811434780": "借阅申请 - 借款合同、付款委托",
      "p1_visible_dfc25d77dc39": "借阅申请 - 借款合同、付款委托",
      "p1_visible_e001fb68d7f2": "借阅申请 - 借款合同、付款委托",
      "p1_visible_e0361480e3a5": "来源表: BGGL_TZXX_WJHQ\n文件类型: 其他\n快递/文件编号: SF1464125012747(对方支付）\n签收/借阅人: ***\n项目: 四川广元昭化中国食品产业发展重点园区（工业园区泉坝台阶地）项目场平、道路工程施工\n原始说明: 借款合同、付款委托，已移交财务文楠",
      "p1_visible_edb1f6f12f51": "借阅申请 - 借款合同、付款委托",
      "p1_visible_ee6a4d9e2956": "借阅申请 - 借款合同、付款委托",
      "p1_visible_f1ec63ea5126": "借阅申请 - 借款合同、付款委托",
      "p1_visible_fb2f8cfd18bf": "徐丹"
    },
    "seq": 150,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "tender.bid",
    "name": "投标报名管理",
    "record": {
      "id": "2830",
      "p1_visible_06fa8c6f628f": "已提交",
      "p1_visible_3e7255522b33": "公司综合平台",
      "p1_visible_3f2c92346bec": "2026-04-10 00:00:00",
      "p1_visible_7ebedce2d014": "2026-04-13 00:00:00",
      "p1_visible_8fa8662ad38f": "GCBMGL-20260410-001",
      "p1_visible_ee6a4d9e2956": "李俭锋",
      "p1_visible_f22832ce4781": "已提交"
    },
    "seq": 160,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "tender.bid",
    "name": "投标报名管理",
    "record": {
      "id": "2830",
      "p1_visible_06fa8c6f628f": "已提交",
      "p1_visible_3e7255522b33": "公司综合平台",
      "p1_visible_3f2c92346bec": "2026-04-10 00:00:00",
      "p1_visible_7ebedce2d014": "2026-04-13 00:00:00",
      "p1_visible_8fa8662ad38f": "GCBMGL-20260410-001",
      "p1_visible_ee6a4d9e2956": "李俭锋",
      "p1_visible_f22832ce4781": "已提交"
    },
    "seq": 160,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "tender.doc.purchase",
    "name": "投标报名费申请",
    "record": {
      "id": "1",
      "p1_visible_06fa8c6f628f": "已通过",
      "p1_visible_2c346345746e": "2020-03-23",
      "p1_visible_34943c40c9af": "200.0",
      "p1_visible_3e5fd432c9df": "951008010000856807",
      "p1_visible_3e7255522b33": "公司综合平台",
      "p1_visible_48a64eb40c71": "中国邮政储蓄银行股份有限公司雅安市南二路支行",
      "p1_visible_880ab989a872": "邓世娇",
      "p1_visible_8fa8662ad38f": "TBBMFSQ-20200323-001",
      "p1_visible_99f6fe6c41ad": "历史附件",
      "p1_visible_bb7c7aeff3e4": "北京筑龙信息技术有限责任公司",
      "p1_visible_c6b9a8cfdb21": "",
      "p1_visible_dfc25d77dc39": "2020-03-23 16:33:03",
      "p1_visible_e0361480e3a5": "四川省雅安市汉源县2019年高标准农田建设项目九襄片区(第二次）",
      "p1_visible_ee6a4d9e2956": "邓世娇"
    },
    "seq": 170,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "tender.doc.purchase",
    "name": "投标报名费申请",
    "record": {
      "id": "1",
      "p1_visible_06fa8c6f628f": "已通过",
      "p1_visible_2c346345746e": "2020-03-23",
      "p1_visible_34943c40c9af": "200.0",
      "p1_visible_3e5fd432c9df": "951008010000856807",
      "p1_visible_3e7255522b33": "公司综合平台",
      "p1_visible_48a64eb40c71": "中国邮政储蓄银行股份有限公司雅安市南二路支行",
      "p1_visible_880ab989a872": "邓世娇",
      "p1_visible_8fa8662ad38f": "TBBMFSQ-20200323-001",
      "p1_visible_99f6fe6c41ad": "历史附件",
      "p1_visible_bb7c7aeff3e4": "北京筑龙信息技术有限责任公司",
      "p1_visible_c6b9a8cfdb21": "",
      "p1_visible_dfc25d77dc39": "2020-03-23 16:33:03",
      "p1_visible_e0361480e3a5": "四川省雅安市汉源县2019年高标准农田建设项目九襄片区(第二次）",
      "p1_visible_ee6a4d9e2956": "邓世娇"
    },
    "seq": 170,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "tender.guarantee",
    "name": "自筹保证金",
    "record": {
      "id": "1",
      "p1_visible_1932637f45ee": "公司综合平台",
      "p1_visible_2559d3f7672e": "公司综合平台",
      "p1_visible_34943c40c9af": "180000.0",
      "p1_visible_3e7255522b33": "公司综合平台",
      "p1_visible_49a5d541678c": "公司综合平台",
      "p1_visible_62e951a692ff": "草稿",
      "p1_visible_87fa6ef6554a": "公司综合平台",
      "p1_visible_8fa8662ad38f": "公司综合平台",
      "p1_visible_9664566d48ce": "公司综合平台",
      "p1_visible_99f6fe6c41ad": "公司综合平台",
      "p1_visible_af37d8d6ef07": "公司综合平台",
      "p1_visible_dfc25d77dc39": "公司综合平台",
      "p1_visible_e0361480e3a5": "历史投标保证金：ZBBM-20200301-004",
      "p1_visible_e1182de05c3f": "公司综合平台",
      "p1_visible_e32341fe14e8": "公司综合平台",
      "p1_visible_ee6a4d9e2956": "公司综合平台"
    },
    "seq": 180,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "tender.guarantee",
    "name": "自筹保证金",
    "record": {
      "id": "1",
      "p1_visible_1932637f45ee": "公司综合平台",
      "p1_visible_2559d3f7672e": "公司综合平台",
      "p1_visible_34943c40c9af": "180000.0",
      "p1_visible_3e7255522b33": "公司综合平台",
      "p1_visible_49a5d541678c": "公司综合平台",
      "p1_visible_62e951a692ff": "草稿",
      "p1_visible_87fa6ef6554a": "公司综合平台",
      "p1_visible_8fa8662ad38f": "公司综合平台",
      "p1_visible_9664566d48ce": "公司综合平台",
      "p1_visible_99f6fe6c41ad": "公司综合平台",
      "p1_visible_af37d8d6ef07": "公司综合平台",
      "p1_visible_dfc25d77dc39": "公司综合平台",
      "p1_visible_e0361480e3a5": "历史投标保证金：ZBBM-20200301-004",
      "p1_visible_e1182de05c3f": "公司综合平台",
      "p1_visible_e32341fe14e8": "公司综合平台",
      "p1_visible_ee6a4d9e2956": "公司综合平台"
    },
    "seq": 180,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "tender.guarantee",
    "name": "自筹保证金退回",
    "record": {
      "id": "1",
      "p1_visible_1ccf3b6408df": "公司综合平台",
      "p1_visible_3e5fd432c9df": "公司综合平台",
      "p1_visible_3e7255522b33": "公司综合平台",
      "p1_visible_488cfebeaf9d": "公司综合平台",
      "p1_visible_62e951a692ff": "草稿",
      "p1_visible_6ef508189cc0": "公司综合平台",
      "p1_visible_8ec8c8c712be": "公司综合平台",
      "p1_visible_8fa8662ad38f": "公司综合平台",
      "p1_visible_93997ec88a8a": "公司综合平台",
      "p1_visible_99f6fe6c41ad": "公司综合平台",
      "p1_visible_c8839fd18cdd": "公司综合平台",
      "p1_visible_dfc25d77dc39": "公司综合平台",
      "p1_visible_e0361480e3a5": "历史投标保证金：ZBBM-20200301-004",
      "p1_visible_e32341fe14e8": "公司综合平台",
      "p1_visible_ee6a4d9e2956": "公司综合平台"
    },
    "seq": 190,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "tender.guarantee",
    "name": "自筹保证金退回",
    "record": {
      "id": "1",
      "p1_visible_1ccf3b6408df": "公司综合平台",
      "p1_visible_3e5fd432c9df": "公司综合平台",
      "p1_visible_3e7255522b33": "公司综合平台",
      "p1_visible_488cfebeaf9d": "公司综合平台",
      "p1_visible_62e951a692ff": "草稿",
      "p1_visible_6ef508189cc0": "公司综合平台",
      "p1_visible_8ec8c8c712be": "公司综合平台",
      "p1_visible_8fa8662ad38f": "公司综合平台",
      "p1_visible_93997ec88a8a": "公司综合平台",
      "p1_visible_99f6fe6c41ad": "公司综合平台",
      "p1_visible_c8839fd18cdd": "公司综合平台",
      "p1_visible_dfc25d77dc39": "公司综合平台",
      "p1_visible_e0361480e3a5": "历史投标保证金：ZBBM-20200301-004",
      "p1_visible_e32341fe14e8": "公司综合平台",
      "p1_visible_ee6a4d9e2956": "公司综合平台"
    },
    "seq": 190,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "tender.guarantee",
    "name": "付款还保证金",
    "record": {
      "id": "1",
      "p1_visible_1484fc99a1d3": "公司综合平台",
      "p1_visible_2559d3f7672e": "公司综合平台",
      "p1_visible_2f40d268a798": "公司综合平台",
      "p1_visible_62e951a692ff": "草稿",
      "p1_visible_667eee716adf": "公司综合平台",
      "p1_visible_6eceee6e57dd": "公司综合平台",
      "p1_visible_7f5da566c14e": "公司综合平台",
      "p1_visible_8fa8662ad38f": "公司综合平台",
      "p1_visible_9664566d48ce": "公司综合平台",
      "p1_visible_99f6fe6c41ad": "公司综合平台",
      "p1_visible_ccfa1326c88f": "公司综合平台",
      "p1_visible_dfc25d77dc39": "公司综合平台",
      "p1_visible_e0361480e3a5": "历史投标保证金：ZBBM-20200301-004",
      "p1_visible_e626b428509f": "公司综合平台",
      "p1_visible_ee6a4d9e2956": "公司综合平台",
      "p1_visible_efb7cd864aa6": "公司综合平台",
      "p1_visible_f22832ce4781": "草稿",
      "p1_visible_fff7e95a48d8": "公司综合平台"
    },
    "seq": 200,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "tender.guarantee",
    "name": "付款还保证金",
    "record": {
      "id": "1",
      "p1_visible_1484fc99a1d3": "公司综合平台",
      "p1_visible_2559d3f7672e": "公司综合平台",
      "p1_visible_2f40d268a798": "公司综合平台",
      "p1_visible_62e951a692ff": "草稿",
      "p1_visible_667eee716adf": "公司综合平台",
      "p1_visible_6eceee6e57dd": "公司综合平台",
      "p1_visible_7f5da566c14e": "公司综合平台",
      "p1_visible_8fa8662ad38f": "公司综合平台",
      "p1_visible_9664566d48ce": "公司综合平台",
      "p1_visible_99f6fe6c41ad": "公司综合平台",
      "p1_visible_ccfa1326c88f": "公司综合平台",
      "p1_visible_dfc25d77dc39": "公司综合平台",
      "p1_visible_e0361480e3a5": "历史投标保证金：ZBBM-20200301-004",
      "p1_visible_e626b428509f": "公司综合平台",
      "p1_visible_ee6a4d9e2956": "公司综合平台",
      "p1_visible_efb7cd864aa6": "公司综合平台",
      "p1_visible_f22832ce4781": "草稿",
      "p1_visible_fff7e95a48d8": "公司综合平台"
    },
    "seq": 200,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "tender.guarantee",
    "name": "付款还保证金退回",
    "record": {
      "id": "1",
      "p1_visible_2559d3f7672e": "公司综合平台",
      "p1_visible_62e951a692ff": "草稿",
      "p1_visible_6b05c4e240c0": "公司综合平台",
      "p1_visible_9664566d48ce": "公司综合平台",
      "p1_visible_9909f5df1a75": "公司综合平台",
      "p1_visible_99f6fe6c41ad": "公司综合平台",
      "p1_visible_9ea4037225af": "公司综合平台",
      "p1_visible_a0b2e8bb26c8": "公司综合平台",
      "p1_visible_c6baf132e1dd": "公司综合平台",
      "p1_visible_ccfa1326c88f": "公司综合平台",
      "p1_visible_e0361480e3a5": "历史投标保证金：ZBBM-20200301-004",
      "p1_visible_e32341fe14e8": "公司综合平台",
      "p1_visible_ee6a4d9e2956": "公司综合平台",
      "p1_visible_f22832ce4781": "草稿"
    },
    "seq": 210,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "tender.guarantee",
    "name": "付款还保证金退回",
    "record": {
      "id": "1",
      "p1_visible_2559d3f7672e": "公司综合平台",
      "p1_visible_62e951a692ff": "草稿",
      "p1_visible_6b05c4e240c0": "公司综合平台",
      "p1_visible_9664566d48ce": "公司综合平台",
      "p1_visible_9909f5df1a75": "公司综合平台",
      "p1_visible_99f6fe6c41ad": "公司综合平台",
      "p1_visible_9ea4037225af": "公司综合平台",
      "p1_visible_a0b2e8bb26c8": "公司综合平台",
      "p1_visible_c6baf132e1dd": "公司综合平台",
      "p1_visible_ccfa1326c88f": "公司综合平台",
      "p1_visible_e0361480e3a5": "历史投标保证金：ZBBM-20200301-004",
      "p1_visible_e32341fe14e8": "公司综合平台",
      "p1_visible_ee6a4d9e2956": "公司综合平台",
      "p1_visible_f22832ce4781": "草稿"
    },
    "seq": 210,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.financing.loan",
    "name": "借款申请",
    "record": {
      "id": "4831",
      "p1_visible_06d4e36b5786": "JKSQ-20210107-001",
      "p1_visible_06fa8c6f628f": "历史已确认",
      "p1_visible_160ebab6202d": "JKSQ-20210107-001",
      "p1_visible_21f4d7e3c978": "JKSQ-20210107-001",
      "p1_visible_25b047589d9e": "JKSQ-20210107-001",
      "p1_visible_26cbd48d6c5a": "JKSQ-20210107-001",
      "p1_visible_3e7255522b33": "中国移动四川西区二枢纽“车库改机房”土建工程",
      "p1_visible_3f91cf4fc953": "JKSQ-20210107-001",
      "p1_visible_49a5d541678c": "JKSQ-20210107-001",
      "p1_visible_5dd6b34dec39": "JKSQ-20210107-001",
      "p1_visible_7a915500e3a7": "JKSQ-20210107-001",
      "p1_visible_880ab989a872": "文楠",
      "p1_visible_886e0fcaba60": "JKSQ-20210107-001",
      "p1_visible_8fa8662ad38f": "JKSQ-20210107-001",
      "p1_visible_94c4852ffb13": "JKSQ-20210107-001",
      "p1_visible_99f6fe6c41ad": "JKSQ-20210107-001",
      "p1_visible_9eb4e5019601": "JKSQ-20210107-001",
      "p1_visible_b72214024f6c": "JKSQ-20210107-001",
      "p1_visible_bb7c7aeff3e4": "JKSQ-20210107-001",
      "p1_visible_ccfa1326c88f": "JKSQ-20210107-001",
      "p1_visible_da7f7ebd086f": "JKSQ-20210107-001",
      "p1_visible_dfc25d77dc39": "2021-01-07 16:05:45",
      "p1_visible_e0361480e3a5": "[migration:employee_loan]\nsource_table=BGGL_JHK_JKSQ\nlegacy_record_id=a97b89cd78a9472f8829a0f718ad99f6\ncounterparty=文楠\n344ef4f45b2f4dfea5dc2063960eb1e6",
      "p1_visible_e85ad6ea52fd": "JKSQ-20210107-001",
      "p1_visible_ee6a4d9e2956": "文楠",
      "p1_visible_f256aa66ca92": "JKSQ-20210107-001"
    },
    "seq": 220,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.financing.loan",
    "name": "借款申请",
    "record": {
      "id": "4831",
      "p1_visible_06d4e36b5786": "JKSQ-20210107-001",
      "p1_visible_06fa8c6f628f": "历史已确认",
      "p1_visible_160ebab6202d": "JKSQ-20210107-001",
      "p1_visible_21f4d7e3c978": "JKSQ-20210107-001",
      "p1_visible_25b047589d9e": "JKSQ-20210107-001",
      "p1_visible_26cbd48d6c5a": "JKSQ-20210107-001",
      "p1_visible_3e7255522b33": "中国移动四川西区二枢纽“车库改机房”土建工程",
      "p1_visible_3f91cf4fc953": "JKSQ-20210107-001",
      "p1_visible_49a5d541678c": "JKSQ-20210107-001",
      "p1_visible_5dd6b34dec39": "JKSQ-20210107-001",
      "p1_visible_7a915500e3a7": "JKSQ-20210107-001",
      "p1_visible_880ab989a872": "文楠",
      "p1_visible_886e0fcaba60": "JKSQ-20210107-001",
      "p1_visible_8fa8662ad38f": "JKSQ-20210107-001",
      "p1_visible_94c4852ffb13": "JKSQ-20210107-001",
      "p1_visible_99f6fe6c41ad": "JKSQ-20210107-001",
      "p1_visible_9eb4e5019601": "JKSQ-20210107-001",
      "p1_visible_b72214024f6c": "JKSQ-20210107-001",
      "p1_visible_bb7c7aeff3e4": "JKSQ-20210107-001",
      "p1_visible_ccfa1326c88f": "JKSQ-20210107-001",
      "p1_visible_da7f7ebd086f": "JKSQ-20210107-001",
      "p1_visible_dfc25d77dc39": "2021-01-07 16:05:45",
      "p1_visible_e0361480e3a5": "[migration:employee_loan]\nsource_table=BGGL_JHK_JKSQ\nlegacy_record_id=a97b89cd78a9472f8829a0f718ad99f6\ncounterparty=文楠\n344ef4f45b2f4dfea5dc2063960eb1e6",
      "p1_visible_e85ad6ea52fd": "JKSQ-20210107-001",
      "p1_visible_ee6a4d9e2956": "文楠",
      "p1_visible_f256aa66ca92": "JKSQ-20210107-001"
    },
    "seq": 220,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.financing.loan",
    "name": "还款登记",
    "record": {
      "id": "4794",
      "p1_visible_06d4e36b5786": "HKDJ-20210129-001",
      "p1_visible_06fa8c6f628f": "草稿",
      "p1_visible_3e7255522b33": "中江县小型汽车驾驶人考场建设项目",
      "p1_visible_7a915500e3a7": "HKDJ-20210129-001",
      "p1_visible_880ab989a872": "admin",
      "p1_visible_8fa8662ad38f": "HKDJ-20210129-001",
      "p1_visible_99f6fe6c41ad": "HKDJ-20210129-001",
      "p1_visible_9eb4e5019601": "HKDJ-20210129-001",
      "p1_visible_dfc25d77dc39": "2021-01-29 13:26:18",
      "p1_visible_e85ad6ea52fd": "HKDJ-20210129-001",
      "p1_visible_ee6a4d9e2956": "admin",
      "p1_visible_f75550069cae": "900000.0"
    },
    "seq": 230,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.financing.loan",
    "name": "还款登记",
    "record": {
      "id": "4794",
      "p1_visible_06d4e36b5786": "HKDJ-20210129-001",
      "p1_visible_06fa8c6f628f": "草稿",
      "p1_visible_3e7255522b33": "中江县小型汽车驾驶人考场建设项目",
      "p1_visible_7a915500e3a7": "HKDJ-20210129-001",
      "p1_visible_880ab989a872": "admin",
      "p1_visible_8fa8662ad38f": "HKDJ-20210129-001",
      "p1_visible_99f6fe6c41ad": "HKDJ-20210129-001",
      "p1_visible_9eb4e5019601": "HKDJ-20210129-001",
      "p1_visible_dfc25d77dc39": "2021-01-29 13:26:18",
      "p1_visible_e85ad6ea52fd": "HKDJ-20210129-001",
      "p1_visible_ee6a4d9e2956": "admin",
      "p1_visible_f75550069cae": "900000.0"
    },
    "seq": 230,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.expense.claim",
    "name": "报销申请",
    "record": {
      "id": "381",
      "p1_visible_06fa8c6f628f": "2",
      "p1_visible_2559d3f7672e": "四川保盛建设集团有限公司",
      "p1_visible_2607f43202a3": "徐丹",
      "p1_visible_8fa8662ad38f": "FYBX-20260410-001",
      "p1_visible_91061a56c00f": "LEG-EXP-FYBX-20260410-001",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_b6fed9af8313": "2026-04-10",
      "p1_visible_bb7c7aeff3e4": "德阳市建筑房地产业联合协会",
      "p1_visible_c33f247470b1": "教育培训费",
      "p1_visible_ce44aa844fbd": "安管人员继续教育培训费（8人，请参看附件信息）",
      "p1_visible_dfc25d77dc39": "2026-04-10 16:40:25",
      "p1_visible_ee6a4d9e2956": "徐丹",
      "p1_visible_f79e589b11f6": "2080.0"
    },
    "seq": 240,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.expense.claim",
    "name": "报销申请",
    "record": {
      "id": "381",
      "p1_visible_06fa8c6f628f": "2",
      "p1_visible_2559d3f7672e": "四川保盛建设集团有限公司",
      "p1_visible_2607f43202a3": "徐丹",
      "p1_visible_8fa8662ad38f": "FYBX-20260410-001",
      "p1_visible_91061a56c00f": "LEG-EXP-FYBX-20260410-001",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_b6fed9af8313": "2026-04-10",
      "p1_visible_bb7c7aeff3e4": "德阳市建筑房地产业联合协会",
      "p1_visible_c33f247470b1": "教育培训费",
      "p1_visible_ce44aa844fbd": "安管人员继续教育培训费（8人，请参看附件信息）",
      "p1_visible_dfc25d77dc39": "2026-04-10 16:40:25",
      "p1_visible_ee6a4d9e2956": "徐丹",
      "p1_visible_f79e589b11f6": "2080.0"
    },
    "seq": 240,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.receipt.income",
    "name": "收入",
    "record": {
      "id": "3550",
      "p1_visible_06fa8c6f628f": "历史已确认",
      "p1_visible_0d20172efa91": "GSCWSR-20260410-002",
      "p1_visible_2ff90909b29b": "GSCWSR-20260410-002",
      "p1_visible_3e7255522b33": "公司综合平台",
      "p1_visible_49a5d541678c": "GSCWSR-20260410-002",
      "p1_visible_71e47f617269": "GSCWSR-20260410-002",
      "p1_visible_807b71479e35": "利息公司",
      "p1_visible_8fa8662ad38f": "GSCWSR-20260410-002",
      "p1_visible_99f6fe6c41ad": "GSCWSR-20260410-002",
      "p1_visible_dfc25d77dc39": "GSCWSR-20260410-002",
      "p1_visible_e0361480e3a5": "[migration:receipt_income] legacy_record_id=c1cc1f0e49bc4fe0be52078cfe73a6b5\ncompany_financial_income\ninflow\n5218账户利息",
      "p1_visible_ee6a4d9e2956": "GSCWSR-20260410-002"
    },
    "seq": 250,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.receipt.income",
    "name": "收入",
    "record": {
      "id": "3550",
      "p1_visible_06fa8c6f628f": "历史已确认",
      "p1_visible_0d20172efa91": "GSCWSR-20260410-002",
      "p1_visible_2ff90909b29b": "GSCWSR-20260410-002",
      "p1_visible_3e7255522b33": "公司综合平台",
      "p1_visible_49a5d541678c": "GSCWSR-20260410-002",
      "p1_visible_71e47f617269": "GSCWSR-20260410-002",
      "p1_visible_807b71479e35": "利息公司",
      "p1_visible_8fa8662ad38f": "GSCWSR-20260410-002",
      "p1_visible_99f6fe6c41ad": "GSCWSR-20260410-002",
      "p1_visible_dfc25d77dc39": "GSCWSR-20260410-002",
      "p1_visible_e0361480e3a5": "[migration:receipt_income] legacy_record_id=c1cc1f0e49bc4fe0be52078cfe73a6b5\ncompany_financial_income\ninflow\n5218账户利息",
      "p1_visible_ee6a4d9e2956": "GSCWSR-20260410-002"
    },
    "seq": 250,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.expense.claim",
    "name": "公司财务支出",
    "record": {
      "id": "6239",
      "p1_visible_06fa8c6f628f": "0",
      "p1_visible_334ddb69d3cf": "LEG-DEP-GSCWZC-20231008-001",
      "p1_visible_533775096e5b": "深圳市华商工程担保有限公司",
      "p1_visible_80e3d15acaa8": "company_financial_outflow",
      "p1_visible_8fa8662ad38f": "GSCWZC-20231008-001",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_d890d302f7f7": "200.0",
      "p1_visible_dacbd33c31fd": "",
      "p1_visible_dfc25d77dc39": "",
      "p1_visible_e0361480e3a5": "[migration:expense_claim] legacy_record_id=7934a3d2e1734dcda7aff37e05aab4cd; legacy_project_id=7fa974d0bc674fb48bd98beaad6825ab; source_family=company_financial_outflow; direction=outflow; historical_runtime_projection=true",
      "p1_visible_ee6a4d9e2956": "",
      "p1_visible_f22832ce4781": "0"
    },
    "seq": 260,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.expense.claim",
    "name": "公司财务支出",
    "record": {
      "id": "6239",
      "p1_visible_06fa8c6f628f": "0",
      "p1_visible_334ddb69d3cf": "LEG-DEP-GSCWZC-20231008-001",
      "p1_visible_533775096e5b": "深圳市华商工程担保有限公司",
      "p1_visible_80e3d15acaa8": "company_financial_outflow",
      "p1_visible_8fa8662ad38f": "GSCWZC-20231008-001",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_d890d302f7f7": "200.0",
      "p1_visible_dacbd33c31fd": "",
      "p1_visible_dfc25d77dc39": "",
      "p1_visible_e0361480e3a5": "[migration:expense_claim] legacy_record_id=7934a3d2e1734dcda7aff37e05aab4cd; legacy_project_id=7fa974d0bc674fb48bd98beaad6825ab; source_family=company_financial_outflow; direction=outflow; historical_runtime_projection=true",
      "p1_visible_ee6a4d9e2956": "",
      "p1_visible_f22832ce4781": "0"
    },
    "seq": 260,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.expense.claim",
    "name": "承包人还项目款",
    "record": {
      "id": "43683",
      "p1_visible_06fa8c6f628f": "2",
      "p1_visible_3e7255522b33": "德阳经济技术开发区产城融合示范园区基础设施建设 旌湖路 、 太湖路道路改造工程",
      "p1_visible_7c49c8f25a7a": "借项目工程款",
      "p1_visible_8fa8662ad38f": "HK-20230519-001",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_9c075c710f62": "79200.0",
      "p1_visible_a5b7f233fadc": "",
      "p1_visible_dca067f698a7": "",
      "p1_visible_dfc25d77dc39": "",
      "p1_visible_e0361480e3a5": "借项目工程款",
      "p1_visible_ee6a4d9e2956": "长城华西银行股份有限公司营业部",
      "p1_visible_f13b158f80f7": "",
      "p1_visible_f65ab1a8427f": "长城华西银行股份有限公司营业部",
      "p1_visible_f75550069cae": "79200.0"
    },
    "seq": 270,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.expense.claim",
    "name": "承包人还项目款",
    "record": {
      "id": "43683",
      "p1_visible_06fa8c6f628f": "2",
      "p1_visible_3e7255522b33": "德阳经济技术开发区产城融合示范园区基础设施建设 旌湖路 、 太湖路道路改造工程",
      "p1_visible_7c49c8f25a7a": "借项目工程款",
      "p1_visible_8fa8662ad38f": "HK-20230519-001",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_9c075c710f62": "79200.0",
      "p1_visible_a5b7f233fadc": "",
      "p1_visible_dca067f698a7": "",
      "p1_visible_dfc25d77dc39": "",
      "p1_visible_e0361480e3a5": "借项目工程款",
      "p1_visible_ee6a4d9e2956": "长城华西银行股份有限公司营业部",
      "p1_visible_f13b158f80f7": "",
      "p1_visible_f65ab1a8427f": "长城华西银行股份有限公司营业部",
      "p1_visible_f75550069cae": "79200.0"
    },
    "seq": 270,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.financing.loan",
    "name": "承包人借项目款",
    "record": {
      "id": "78",
      "p1_visible_06fa8c6f628f": "历史已确认",
      "p1_visible_0f6aab17d203": "JK-20260214-001",
      "p1_visible_3e7255522b33": "重庆市綦江区育英高级中学建设工程（一标段）",
      "p1_visible_547c71732ac4": "JK-20260214-001",
      "p1_visible_7c49c8f25a7a": "李俭锋借项目款（后期退回开票支付）",
      "p1_visible_8fa8662ad38f": "JK-20260214-001",
      "p1_visible_99f6fe6c41ad": "JK-20260214-001",
      "p1_visible_dfc25d77dc39": "JK-20260214-001",
      "p1_visible_e0361480e3a5": "[migration:financing_loan] legacy_record_id=6a2270816db84b61b9963ab88392cbbb\nborrowing_request\nborrowed_fund\n重庆市綦江区育英高级中学建设工程（一标段）\n李俭锋\n后期退回开票支付",
      "p1_visible_ee6a4d9e2956": "JK-20260214-001",
      "p1_visible_f65ab1a8427f": "李俭锋",
      "p1_visible_f75550069cae": "350000.0"
    },
    "seq": 280,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.financing.loan",
    "name": "承包人借项目款",
    "record": {
      "id": "78",
      "p1_visible_06fa8c6f628f": "历史已确认",
      "p1_visible_0f6aab17d203": "JK-20260214-001",
      "p1_visible_3e7255522b33": "重庆市綦江区育英高级中学建设工程（一标段）",
      "p1_visible_547c71732ac4": "JK-20260214-001",
      "p1_visible_7c49c8f25a7a": "李俭锋借项目款（后期退回开票支付）",
      "p1_visible_8fa8662ad38f": "JK-20260214-001",
      "p1_visible_99f6fe6c41ad": "JK-20260214-001",
      "p1_visible_dfc25d77dc39": "JK-20260214-001",
      "p1_visible_e0361480e3a5": "[migration:financing_loan] legacy_record_id=6a2270816db84b61b9963ab88392cbbb\nborrowing_request\nborrowed_fund\n重庆市綦江区育英高级中学建设工程（一标段）\n李俭锋\n后期退回开票支付",
      "p1_visible_ee6a4d9e2956": "JK-20260214-001",
      "p1_visible_f65ab1a8427f": "李俭锋",
      "p1_visible_f75550069cae": "350000.0"
    },
    "seq": 280,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "payment.request",
    "name": "支付申请",
    "record": {
      "id": "32050",
      "p1_visible_06fa8c6f628f": "已审核",
      "p1_visible_1874b0ce5103": "否",
      "p1_visible_2c346345746e": "2022-05-17",
      "p1_visible_3759fcfc297a": "1001 1000 0000 1931",
      "p1_visible_3e7255522b33": "米易县南部新城市政道路及生态湿地公园PPP项目-湿地公园建设项目",
      "p1_visible_48a64eb40c71": "中国农业银行",
      "p1_visible_63c5facb9f66": "零星材料款",
      "p1_visible_6cf6e39bece9": "壹万贰仟壹佰柒拾肆元叁角整",
      "p1_visible_71e47f617269": "文楠",
      "p1_visible_8fa8662ad38f": "PRQ2632050",
      "p1_visible_901384917949": "6228 4824 4945 7867 874",
      "p1_visible_9469a2ad32f8": "0.0",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_a103d7cee046": "凌均明",
      "p1_visible_ae1abe750af6": "0.0",
      "p1_visible_c00fc55a25b8": "12174.3",
      "p1_visible_ccfa1326c88f": "凌均明",
      "p1_visible_dfc25d77dc39": "2022-05-17 11:55:22",
      "p1_visible_e0361480e3a5": "收工程款，付管材进度款。"
    },
    "seq": 290,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "payment.request",
    "name": "支付申请",
    "record": {
      "id": "32050",
      "p1_visible_06fa8c6f628f": "已审核",
      "p1_visible_1874b0ce5103": "否",
      "p1_visible_2c346345746e": "2022-05-17",
      "p1_visible_3759fcfc297a": "1001 1000 0000 1931",
      "p1_visible_3e7255522b33": "米易县南部新城市政道路及生态湿地公园PPP项目-湿地公园建设项目",
      "p1_visible_48a64eb40c71": "中国农业银行",
      "p1_visible_63c5facb9f66": "零星材料款",
      "p1_visible_6cf6e39bece9": "壹万贰仟壹佰柒拾肆元叁角整",
      "p1_visible_71e47f617269": "文楠",
      "p1_visible_8fa8662ad38f": "PRQ2632050",
      "p1_visible_901384917949": "6228 4824 4945 7867 874",
      "p1_visible_9469a2ad32f8": "0.0",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_a103d7cee046": "凌均明",
      "p1_visible_ae1abe750af6": "0.0",
      "p1_visible_c00fc55a25b8": "12174.3",
      "p1_visible_ccfa1326c88f": "凌均明",
      "p1_visible_dfc25d77dc39": "2022-05-17 11:55:22",
      "p1_visible_e0361480e3a5": "收工程款，付管材进度款。"
    },
    "seq": 290,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.tax.deduction.registration",
    "name": "扣款单",
    "record": {
      "id": "4916",
      "p1_visible_06fa8c6f628f": "审核通过",
      "p1_visible_16e91e3d2738": "not_promoted_to_runtime_payment_request\n2024.4.29 项目检查开会 项目经理 技术负责人 安全员 出场\n[migration:deduction_bill] legacy_record_id=093a818aad9c41b8aaefdec7ee96d2b8",
      "p1_visible_1e62803e196c": "2024-04-29",
      "p1_visible_3e7255522b33": "引入社会资金共同打造游泳高水平运动员后备人才培养项目",
      "p1_visible_8fa8662ad38f": "KKD-20240429-001",
      "p1_visible_99f6fe6c41ad": "KKD-20240429-001",
      "p1_visible_9b5c1b5cbd69": "3000.0",
      "p1_visible_dfc25d77dc39": "2024-04-29 17:54:13",
      "p1_visible_ea75d3bba41c": "四川保盛建设集团有限公司（供应商）",
      "p1_visible_ee6a4d9e2956": "段奕俊"
    },
    "seq": 300,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.tax.deduction.registration",
    "name": "扣款单",
    "record": {
      "id": "4916",
      "p1_visible_06fa8c6f628f": "审核通过",
      "p1_visible_16e91e3d2738": "not_promoted_to_runtime_payment_request\n2024.4.29 项目检查开会 项目经理 技术负责人 安全员 出场\n[migration:deduction_bill] legacy_record_id=093a818aad9c41b8aaefdec7ee96d2b8",
      "p1_visible_1e62803e196c": "2024-04-29",
      "p1_visible_3e7255522b33": "引入社会资金共同打造游泳高水平运动员后备人才培养项目",
      "p1_visible_8fa8662ad38f": "KKD-20240429-001",
      "p1_visible_99f6fe6c41ad": "KKD-20240429-001",
      "p1_visible_9b5c1b5cbd69": "3000.0",
      "p1_visible_dfc25d77dc39": "2024-04-29 17:54:13",
      "p1_visible_ea75d3bba41c": "四川保盛建设集团有限公司（供应商）",
      "p1_visible_ee6a4d9e2956": "段奕俊"
    },
    "seq": 300,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.payment.execution",
    "name": "往来单位付款",
    "record": {
      "id": "22767",
      "p1_visible_058f511c98cf": "2026-05-11",
      "p1_visible_06fa8c6f628f": "历史已确认",
      "p1_visible_48a64eb40c71": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_48eb67df430f": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_514ce8cde553": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_71e47f617269": "卢燕",
      "p1_visible_7f5da566c14e": "GYSHT-20211018-002",
      "p1_visible_80f75ce4d56c": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_8fa8662ad38f": "GYSHT-20211018-002",
      "p1_visible_99f6fe6c41ad": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_a4aa6578aa87": "PRQ2630015",
      "p1_visible_c3d92b20c8a3": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_cf44ec3f55f9": "格尔木邦乐五金工具钢丝绳",
      "p1_visible_d890d302f7f7": "22000.0",
      "p1_visible_dacbd33c31fd": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_e0361480e3a5": "[migration:actual_outflow_line_payment_execution] legacy_line_id=actual_outflow_line:c20a8cf1935e4681a1276d7b38a0e7e0; legacy_parent_id=fe2ce47a4e2c4279989b6dc1a3cc6bc8; source_document_no=GYSHT-20211018-002; source_contract_no=GYSHT-20211018-002; historical_runtime_projection=true",
      "p1_visible_f22832ce4781": "历史已确认",
      "p1_visible_f35ba3fab897": "合同"
    },
    "seq": 310,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.payment.execution",
    "name": "往来单位付款",
    "record": {
      "id": "22767",
      "p1_visible_058f511c98cf": "2026-05-11",
      "p1_visible_06fa8c6f628f": "历史已确认",
      "p1_visible_48a64eb40c71": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_48eb67df430f": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_514ce8cde553": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_71e47f617269": "卢燕",
      "p1_visible_7f5da566c14e": "GYSHT-20211018-002",
      "p1_visible_80f75ce4d56c": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_8fa8662ad38f": "GYSHT-20211018-002",
      "p1_visible_99f6fe6c41ad": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_a4aa6578aa87": "PRQ2630015",
      "p1_visible_c3d92b20c8a3": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_cf44ec3f55f9": "格尔木邦乐五金工具钢丝绳",
      "p1_visible_d890d302f7f7": "22000.0",
      "p1_visible_dacbd33c31fd": "LEG-PAY-actual_outflow_line-c20a8cf1935e4681a1276d7b38a0e7e0",
      "p1_visible_e0361480e3a5": "[migration:actual_outflow_line_payment_execution] legacy_line_id=actual_outflow_line:c20a8cf1935e4681a1276d7b38a0e7e0; legacy_parent_id=fe2ce47a4e2c4279989b6dc1a3cc6bc8; source_document_no=GYSHT-20211018-002; source_contract_no=GYSHT-20211018-002; historical_runtime_projection=true",
      "p1_visible_f22832ce4781": "历史已确认",
      "p1_visible_f35ba3fab897": "合同"
    },
    "seq": 310,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.fund.account.operation",
    "name": "账户间资金往来",
    "record": {
      "id": "2",
      "p1_visible_0675851fc19e": "[migration:fund_account_between] legacy_account_transaction_line_id=41361; document_no=ZHJZJWL-20260410-002; source_table=C_FKGL_ZHJZJWL; source_account=保盛长城华西; target_account=吴永涛长城华西",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_34943c40c9af": "500000.0",
      "p1_visible_3e7255522b33": "公司综合平台",
      "p1_visible_43f67c096554": "保盛长城华西 / 1001100000001931 / 长城华西银行股份有限公司营业部",
      "p1_visible_49a5d541678c": "吴永涛长城华西 / 6225633300000605218 / 长城华西银行股份有限公司德阳天山路支行",
      "p1_visible_51f85a78cac4": "2026-04-10",
      "p1_visible_8fa8662ad38f": "FAO2600002",
      "p1_visible_99f6fe6c41ad": "FAO2600002",
      "p1_visible_df6e7b1e9eac": "资金调拨",
      "p1_visible_dfc25d77dc39": "2026-04-10 17:03:42",
      "p1_visible_e0361480e3a5": "[migration:fund_account_between] legacy_account_transaction_line_id=41361; document_no=ZHJZJWL-20260410-002; source_table=C_FKGL_ZHJZJWL; source_account=保盛长城华西; target_account=吴永涛长城华西",
      "p1_visible_ee6a4d9e2956": "文楠"
    },
    "seq": 320,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.fund.account.operation",
    "name": "账户间资金往来",
    "record": {
      "id": "2",
      "p1_visible_0675851fc19e": "[migration:fund_account_between] legacy_account_transaction_line_id=41361; document_no=ZHJZJWL-20260410-002; source_table=C_FKGL_ZHJZJWL; source_account=保盛长城华西; target_account=吴永涛长城华西",
      "p1_visible_06fa8c6f628f": "已完成",
      "p1_visible_34943c40c9af": "500000.0",
      "p1_visible_3e7255522b33": "公司综合平台",
      "p1_visible_43f67c096554": "保盛长城华西 / 1001100000001931 / 长城华西银行股份有限公司营业部",
      "p1_visible_49a5d541678c": "吴永涛长城华西 / 6225633300000605218 / 长城华西银行股份有限公司德阳天山路支行",
      "p1_visible_51f85a78cac4": "2026-04-10",
      "p1_visible_8fa8662ad38f": "FAO2600002",
      "p1_visible_99f6fe6c41ad": "FAO2600002",
      "p1_visible_df6e7b1e9eac": "资金调拨",
      "p1_visible_dfc25d77dc39": "2026-04-10 17:03:42",
      "p1_visible_e0361480e3a5": "[migration:fund_account_between] legacy_account_transaction_line_id=41361; document_no=ZHJZJWL-20260410-002; source_table=C_FKGL_ZHJZJWL; source_account=保盛长城华西; target_account=吴永涛长城华西",
      "p1_visible_ee6a4d9e2956": "文楠"
    },
    "seq": 320,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.expense.claim",
    "name": "扣款实缴登记",
    "record": {
      "id": "56754",
      "p1_visible_06fa8c6f628f": "2",
      "p1_visible_1da8ed2551df": "费用报销",
      "p1_visible_1e62803e196c": "2026-04-10",
      "p1_visible_3e7255522b33": "马踏洞安置房停车场相关基础设施项目",
      "p1_visible_62e5cf441092": "6422.02",
      "p1_visible_748d7dc7e321": "扣款实缴登记 / 增值税 / 扣款实缴登记",
      "p1_visible_8fa8662ad38f": "SJDJB-20260410-001",
      "p1_visible_b0bff5c45de7": "6422.02",
      "p1_visible_dbbcd74271cd": "扣款实缴登记 / 增值税 / 扣款实缴登记",
      "p1_visible_dfc25d77dc39": "2026-04-10 13:59:28",
      "p1_visible_ee6a4d9e2956": "江一娇"
    },
    "seq": 330,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.expense.claim",
    "name": "扣款实缴登记",
    "record": {
      "id": "56754",
      "p1_visible_06fa8c6f628f": "2",
      "p1_visible_1da8ed2551df": "费用报销",
      "p1_visible_1e62803e196c": "2026-04-10",
      "p1_visible_3e7255522b33": "马踏洞安置房停车场相关基础设施项目",
      "p1_visible_62e5cf441092": "6422.02",
      "p1_visible_748d7dc7e321": "扣款实缴登记 / 增值税 / 扣款实缴登记",
      "p1_visible_8fa8662ad38f": "SJDJB-20260410-001",
      "p1_visible_b0bff5c45de7": "6422.02",
      "p1_visible_dbbcd74271cd": "扣款实缴登记 / 增值税 / 扣款实缴登记",
      "p1_visible_dfc25d77dc39": "2026-04-10 13:59:28",
      "p1_visible_ee6a4d9e2956": "江一娇"
    },
    "seq": 330,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.expense.claim",
    "name": "扣款实缴退回",
    "record": {
      "id": "63113",
      "p1_visible_06fa8c6f628f": "2",
      "p1_visible_1e62803e196c": "2026-04-10",
      "p1_visible_3ade9df90bf8": "5825.24",
      "p1_visible_3e7255522b33": "中建四局-刘兴宇项目",
      "p1_visible_62e5cf441092": "5825.24",
      "p1_visible_8fa8662ad38f": "SJTHB-20260410-001",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_dbbcd74271cd": "扣款实缴退回 / 增值税 / 扣款实缴退回",
      "p1_visible_e0361480e3a5": "[migration:deduction_paid_refund] legacy_account_transaction_line_id=41356; source_key=076bab1491544dcbb3c35b213b0ecbf7:deduction_payment_refund; account=; counterparty=增值税",
      "p1_visible_ee6a4d9e2956": "文楠"
    },
    "seq": 340,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.expense.claim",
    "name": "扣款实缴退回",
    "record": {
      "id": "63113",
      "p1_visible_06fa8c6f628f": "2",
      "p1_visible_1e62803e196c": "2026-04-10",
      "p1_visible_3ade9df90bf8": "5825.24",
      "p1_visible_3e7255522b33": "中建四局-刘兴宇项目",
      "p1_visible_62e5cf441092": "5825.24",
      "p1_visible_8fa8662ad38f": "SJTHB-20260410-001",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_dbbcd74271cd": "扣款实缴退回 / 增值税 / 扣款实缴退回",
      "p1_visible_e0361480e3a5": "[migration:deduction_paid_refund] legacy_account_transaction_line_id=41356; source_key=076bab1491544dcbb3c35b213b0ecbf7:deduction_payment_refund; account=; counterparty=增值税",
      "p1_visible_ee6a4d9e2956": "文楠"
    },
    "seq": 340,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.legacy.fund.confirmation.document",
    "name": "到款确认表",
    "record": {
      "id": "353",
      "p1_visible_06fa8c6f628f": "审核通过",
      "p1_visible_0d8979d08c09": "16270000.0",
      "p1_visible_17d0f48c07fb": "李德学",
      "p1_visible_389372a58a16": "25",
      "p1_visible_3e7255522b33": "引入社会资金共同打造游泳高水平运动员后备人才培养项目",
      "p1_visible_50f529884746": "200000.0",
      "p1_visible_689407e406ab": "施工中",
      "p1_visible_75e856a13c7c": "40896688.0",
      "p1_visible_89b4aa6364ce": "",
      "p1_visible_8fa8662ad38f": "DKQRB-20260206-006",
      "p1_visible_99219180c1b9": "0.0",
      "p1_visible_99f6fe6c41ad": "image.png | legacy-file://UploadFile/UserFile/2026/02/06/83e3919481c644a89c582524a7d3761e_45554.png",
      "p1_visible_aa6152009ab0": "0.0",
      "p1_visible_dfc25d77dc39": "2026-02-06 15:18:34",
      "p1_visible_ee6a4d9e2956": "江一娇",
      "p1_visible_fc06f3f3d307": "200000.0"
    },
    "seq": 350,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.legacy.fund.confirmation.document",
    "name": "到款确认表",
    "record": {
      "id": "353",
      "p1_visible_06fa8c6f628f": "审核通过",
      "p1_visible_0d8979d08c09": "16270000.0",
      "p1_visible_17d0f48c07fb": "李德学",
      "p1_visible_389372a58a16": "25",
      "p1_visible_3e7255522b33": "引入社会资金共同打造游泳高水平运动员后备人才培养项目",
      "p1_visible_50f529884746": "200000.0",
      "p1_visible_689407e406ab": "施工中",
      "p1_visible_75e856a13c7c": "40896688.0",
      "p1_visible_89b4aa6364ce": "",
      "p1_visible_8fa8662ad38f": "DKQRB-20260206-006",
      "p1_visible_99219180c1b9": "0.0",
      "p1_visible_99f6fe6c41ad": "image.png | legacy-file://UploadFile/UserFile/2026/02/06/83e3919481c644a89c582524a7d3761e_45554.png",
      "p1_visible_aa6152009ab0": "0.0",
      "p1_visible_dfc25d77dc39": "2026-02-06 15:18:34",
      "p1_visible_ee6a4d9e2956": "江一娇",
      "p1_visible_fc06f3f3d307": "200000.0"
    },
    "seq": 350,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.legacy.fund.daily.line",
    "name": "资金日报表",
    "record": {
      "id": "7738",
      "p1_visible_0027be5d5d7e": "ZJRBB-20260410-001",
      "p1_visible_06fa8c6f628f": "ZJRBB-20260410-001",
      "p1_visible_1e62803e196c": "2026-04-10",
      "p1_visible_3f2da24264f0": "保盛（微信）",
      "p1_visible_5b112952b526": "ZJRBB-20260410-001",
      "p1_visible_834c5de2f288": "50000.0",
      "p1_visible_8fa8662ad38f": "ZJRBB-20260410-001",
      "p1_visible_af4cdd8ce788": "418.0",
      "p1_visible_bed51835debf": "0.0",
      "p1_visible_dfc25d77dc39": "2026-04-10 18:02:15",
      "p1_visible_e0361480e3a5": "倪个人用款",
      "p1_visible_e5bf37733141": "1700.0",
      "p1_visible_ecaf440fd399": "1111",
      "p1_visible_ee6a4d9e2956": "文楠"
    },
    "seq": 360,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.legacy.fund.daily.line",
    "name": "资金日报表",
    "record": {
      "id": "7738",
      "p1_visible_0027be5d5d7e": "ZJRBB-20260410-001",
      "p1_visible_06fa8c6f628f": "ZJRBB-20260410-001",
      "p1_visible_1e62803e196c": "2026-04-10",
      "p1_visible_3f2da24264f0": "保盛（微信）",
      "p1_visible_5b112952b526": "ZJRBB-20260410-001",
      "p1_visible_834c5de2f288": "50000.0",
      "p1_visible_8fa8662ad38f": "ZJRBB-20260410-001",
      "p1_visible_af4cdd8ce788": "418.0",
      "p1_visible_bed51835debf": "0.0",
      "p1_visible_dfc25d77dc39": "2026-04-10 18:02:15",
      "p1_visible_e0361480e3a5": "倪个人用款",
      "p1_visible_e5bf37733141": "1700.0",
      "p1_visible_ecaf440fd399": "1111",
      "p1_visible_ee6a4d9e2956": "文楠"
    },
    "seq": 360,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.financing.loan",
    "name": "项目借公司款登记",
    "record": {
      "id": "286",
      "p1_visible_06fa8c6f628f": "历史已确认",
      "p1_visible_099f8b5c680a": "DKDJ-20260203-001",
      "p1_visible_3bee2141cdb1": "118",
      "p1_visible_3e7255522b33": "保盛公司采购平台",
      "p1_visible_628f2a7878b3": "DKDJ-20260203-001",
      "p1_visible_701ce5416c52": "5000000.0",
      "p1_visible_8ab2d41e7757": "5000000.0",
      "p1_visible_8fa8662ad38f": "DKDJ-20260203-001",
      "p1_visible_982d68c74aeb": "2026-06-01",
      "p1_visible_99f6fe6c41ad": "DKDJ-20260203-001",
      "p1_visible_9c075c710f62": "5000000.0",
      "p1_visible_a12b85cb38e6": "118",
      "p1_visible_dfc25d77dc39": "DKDJ-20260203-001",
      "p1_visible_e0361480e3a5": "[migration:financing_loan] legacy_record_id=cdaccb62ee0b4aba8a4ce24ef87cd877\nloan_registration\nfinancing_in\n保盛公司采购平台\n长城华西银行股份有限公司营业部\n长城华西银行贷款",
      "p1_visible_e242a03dd5b6": "2026-02-03",
      "p1_visible_ed43f478ec3d": "2026-06-01",
      "p1_visible_ee6a4d9e2956": "DKDJ-20260203-001"
    },
    "seq": 370,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.financing.loan",
    "name": "项目借公司款登记",
    "record": {
      "id": "286",
      "p1_visible_06fa8c6f628f": "历史已确认",
      "p1_visible_099f8b5c680a": "DKDJ-20260203-001",
      "p1_visible_3bee2141cdb1": "118",
      "p1_visible_3e7255522b33": "保盛公司采购平台",
      "p1_visible_628f2a7878b3": "DKDJ-20260203-001",
      "p1_visible_701ce5416c52": "5000000.0",
      "p1_visible_8ab2d41e7757": "5000000.0",
      "p1_visible_8fa8662ad38f": "DKDJ-20260203-001",
      "p1_visible_982d68c74aeb": "2026-06-01",
      "p1_visible_99f6fe6c41ad": "DKDJ-20260203-001",
      "p1_visible_9c075c710f62": "5000000.0",
      "p1_visible_a12b85cb38e6": "118",
      "p1_visible_dfc25d77dc39": "DKDJ-20260203-001",
      "p1_visible_e0361480e3a5": "[migration:financing_loan] legacy_record_id=cdaccb62ee0b4aba8a4ce24ef87cd877\nloan_registration\nfinancing_in\n保盛公司采购平台\n长城华西银行股份有限公司营业部\n长城华西银行贷款",
      "p1_visible_e242a03dd5b6": "2026-02-03",
      "p1_visible_ed43f478ec3d": "2026-06-01",
      "p1_visible_ee6a4d9e2956": "DKDJ-20260203-001"
    },
    "seq": 370,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.financing.loan",
    "name": "项目还公司款登记",
    "record": {
      "id": "4832",
      "p1_visible_06fa8c6f628f": "历史已确认",
      "p1_visible_099f8b5c680a": "HKDJ-20230802-001",
      "p1_visible_393c1d188de6": "0.0000",
      "p1_visible_3e7255522b33": "保盛公司采购平台",
      "p1_visible_628f2a7878b3": "HKDJ-20230802-001",
      "p1_visible_71e47f617269": "HKDJ-20230802-001",
      "p1_visible_8fa8662ad38f": "HKDJ-20230802-001",
      "p1_visible_94f294dac442": "HKDJ-20230802-001",
      "p1_visible_99f6fe6c41ad": "HKDJ-20230802-001",
      "p1_visible_9c075c710f62": "3000000.0",
      "p1_visible_a97833656ba0": "0.0000",
      "p1_visible_b3620ea08897": "2023-07-27",
      "p1_visible_dfc25d77dc39": "HKDJ-20230802-001",
      "p1_visible_e0361480e3a5": "出纳",
      "p1_visible_ee6a4d9e2956": "HKDJ-20230802-001"
    },
    "seq": 380,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.financing.loan",
    "name": "项目还公司款登记",
    "record": {
      "id": "4832",
      "p1_visible_06fa8c6f628f": "历史已确认",
      "p1_visible_099f8b5c680a": "HKDJ-20230802-001",
      "p1_visible_393c1d188de6": "0.0000",
      "p1_visible_3e7255522b33": "保盛公司采购平台",
      "p1_visible_628f2a7878b3": "HKDJ-20230802-001",
      "p1_visible_71e47f617269": "HKDJ-20230802-001",
      "p1_visible_8fa8662ad38f": "HKDJ-20230802-001",
      "p1_visible_94f294dac442": "HKDJ-20230802-001",
      "p1_visible_99f6fe6c41ad": "HKDJ-20230802-001",
      "p1_visible_9c075c710f62": "3000000.0",
      "p1_visible_a97833656ba0": "0.0000",
      "p1_visible_b3620ea08897": "2023-07-27",
      "p1_visible_dfc25d77dc39": "HKDJ-20230802-001",
      "p1_visible_e0361480e3a5": "出纳",
      "p1_visible_ee6a4d9e2956": "HKDJ-20230802-001"
    },
    "seq": 380,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.invoice.registration",
    "name": "开票申请",
    "record": {
      "id": "22238",
      "p1_visible_0d8979d08c09": "855778.62",
      "p1_visible_17b341733b7b": "FPSQ-20201118-001",
      "p1_visible_2c346345746e": "2020-11-18",
      "p1_visible_3b66293fbe70": "历史已确认",
      "p1_visible_3e7255522b33": "大興壹號售楼部装修项目",
      "p1_visible_4f43764bd23d": "0",
      "p1_visible_62e951a692ff": "审核通过",
      "p1_visible_83e1d169c7a2": "0.0",
      "p1_visible_880ab989a872": "",
      "p1_visible_8fa8662ad38f": "FPSQ-20201118-001",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_c5e161f03e08": "855778.62",
      "p1_visible_dfc25d77dc39": "FPSQ-20201118-001",
      "p1_visible_e0361480e3a5": "[migration:invoice_registration_tax] legacy_record_id=9fcef1fd6c874996ac87f772deecd8da\noutput_invoice\ninvoice_issue_request\n大興壹號售楼部装修项目\n雅安城投建筑工程有限公司\n附完税凭证，附收款承诺书",
      "p1_visible_ed9ce3e5ab3c": "2020-11-23",
      "p1_visible_ee6a4d9e2956": "FPSQ-20201118-001",
      "p1_visible_f9cc22d53aff": "雅安城投建筑工程有限公司"
    },
    "seq": 390,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.invoice.registration",
    "name": "开票申请",
    "record": {
      "id": "22238",
      "p1_visible_0d8979d08c09": "855778.62",
      "p1_visible_17b341733b7b": "FPSQ-20201118-001",
      "p1_visible_2c346345746e": "2020-11-18",
      "p1_visible_3b66293fbe70": "历史已确认",
      "p1_visible_3e7255522b33": "大興壹號售楼部装修项目",
      "p1_visible_4f43764bd23d": "0",
      "p1_visible_62e951a692ff": "审核通过",
      "p1_visible_83e1d169c7a2": "0.0",
      "p1_visible_880ab989a872": "",
      "p1_visible_8fa8662ad38f": "FPSQ-20201118-001",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_c5e161f03e08": "855778.62",
      "p1_visible_dfc25d77dc39": "FPSQ-20201118-001",
      "p1_visible_e0361480e3a5": "[migration:invoice_registration_tax] legacy_record_id=9fcef1fd6c874996ac87f772deecd8da\noutput_invoice\ninvoice_issue_request\n大興壹號售楼部装修项目\n雅安城投建筑工程有限公司\n附完税凭证，附收款承诺书",
      "p1_visible_ed9ce3e5ab3c": "2020-11-23",
      "p1_visible_ee6a4d9e2956": "FPSQ-20201118-001",
      "p1_visible_f9cc22d53aff": "雅安城投建筑工程有限公司"
    },
    "seq": 390,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.invoice.registration",
    "name": "开票登记",
    "record": {
      "id": "25041",
      "p1_visible_007363f27191": "31564.12",
      "p1_visible_06fa8c6f628f": "审核通过",
      "p1_visible_0e2126d6cf82": "2",
      "p1_visible_37d56ad493cf": "9%",
      "p1_visible_3e7255522b33": "深圳友唱技术有限公司万达零星维修工程",
      "p1_visible_7f5da566c14e": "XXKPDJ-20260410-002",
      "p1_visible_8fa8662ad38f": "XXKPDJ-20260410-002",
      "p1_visible_964a2edc6942": "0.0",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_99f753ed6262": "2840.77",
      "p1_visible_ada9a85eab00": "26512000001474061986",
      "p1_visible_bbe7bbee241e": "增值税专用发票",
      "p1_visible_be5462bd6a62": "四川保盛建设集团有限公司",
      "p1_visible_c1b95b8ca332": "340.89",
      "p1_visible_c73a8eab0d57": "34404.89",
      "p1_visible_d42c2d26610f": "2026-04-10",
      "p1_visible_dfc25d77dc39": "XXKPDJ-20260410-002",
      "p1_visible_ee6a4d9e2956": "XXKPDJ-20260410-002",
      "p1_visible_f22832ce4781": "2",
      "p1_visible_f9cc22d53aff": "深圳友唱技术有限公司"
    },
    "seq": 400,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.invoice.registration",
    "name": "开票登记",
    "record": {
      "id": "25041",
      "p1_visible_007363f27191": "31564.12",
      "p1_visible_06fa8c6f628f": "审核通过",
      "p1_visible_0e2126d6cf82": "2",
      "p1_visible_37d56ad493cf": "9%",
      "p1_visible_3e7255522b33": "深圳友唱技术有限公司万达零星维修工程",
      "p1_visible_7f5da566c14e": "XXKPDJ-20260410-002",
      "p1_visible_8fa8662ad38f": "XXKPDJ-20260410-002",
      "p1_visible_964a2edc6942": "0.0",
      "p1_visible_99f6fe6c41ad": "",
      "p1_visible_99f753ed6262": "2840.77",
      "p1_visible_ada9a85eab00": "26512000001474061986",
      "p1_visible_bbe7bbee241e": "增值税专用发票",
      "p1_visible_be5462bd6a62": "四川保盛建设集团有限公司",
      "p1_visible_c1b95b8ca332": "340.89",
      "p1_visible_c73a8eab0d57": "34404.89",
      "p1_visible_d42c2d26610f": "2026-04-10",
      "p1_visible_dfc25d77dc39": "XXKPDJ-20260410-002",
      "p1_visible_ee6a4d9e2956": "XXKPDJ-20260410-002",
      "p1_visible_f22832ce4781": "2",
      "p1_visible_f9cc22d53aff": "深圳友唱技术有限公司"
    },
    "seq": 400,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.invoice.registration",
    "name": "预缴税款",
    "record": {
      "id": "568426",
      "p1_visible_007363f27191": "22234.32",
      "p1_visible_34943c40c9af": "8.89",
      "p1_visible_3e7255522b33": "深圳友唱技术有限公司万达零星维修工程",
      "p1_visible_61b3896f8414": "地方教育附加",
      "p1_visible_62319711f425": "2026-04-03",
      "p1_visible_62e951a692ff": "审核通过",
      "p1_visible_6514c1bee4d7": "350015260400035115",
      "p1_visible_8fa8662ad38f": "YJSKDJ-20260410-002",
      "p1_visible_99f6fe6c41ad": "20260403171643-2.pdf | legacy-file://UploadFile/UserFile/2026/04/10/b26769c36899421e9ac18d6fbe730063_100699.pdf 20260403171643-1.pdf | legacy-file://UploadFile/UserFile/2026/04/10/3a7c2adc18bf42c09fa2eadd8570ed76_96669.pdf",
      "p1_visible_99f753ed6262": "8.89",
      "p1_visible_a3c1a28bd34c": "2026-04-09",
      "p1_visible_b031dc9a8507": "预缴税",
      "p1_visible_ee6a4d9e2956": "李娜",
      "p1_visible_f9cc22d53aff": "深圳友唱技术有限公司"
    },
    "seq": 410,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.invoice.registration",
    "name": "预缴税款",
    "record": {
      "id": "568426",
      "p1_visible_007363f27191": "22234.32",
      "p1_visible_34943c40c9af": "8.89",
      "p1_visible_3e7255522b33": "深圳友唱技术有限公司万达零星维修工程",
      "p1_visible_61b3896f8414": "地方教育附加",
      "p1_visible_62319711f425": "2026-04-03",
      "p1_visible_62e951a692ff": "审核通过",
      "p1_visible_6514c1bee4d7": "350015260400035115",
      "p1_visible_8fa8662ad38f": "YJSKDJ-20260410-002",
      "p1_visible_99f6fe6c41ad": "20260403171643-2.pdf | legacy-file://UploadFile/UserFile/2026/04/10/b26769c36899421e9ac18d6fbe730063_100699.pdf 20260403171643-1.pdf | legacy-file://UploadFile/UserFile/2026/04/10/3a7c2adc18bf42c09fa2eadd8570ed76_96669.pdf",
      "p1_visible_99f753ed6262": "8.89",
      "p1_visible_a3c1a28bd34c": "2026-04-09",
      "p1_visible_b031dc9a8507": "预缴税",
      "p1_visible_ee6a4d9e2956": "李娜",
      "p1_visible_f9cc22d53aff": "深圳友唱技术有限公司"
    },
    "seq": 410,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.legacy.invoice.tax.fact",
    "name": "进项上报",
    "record": {
      "id": "5506",
      "p1_visible_007363f27191": "FPJJD-20230818-006",
      "p1_visible_22ebb0de8297": "FPJJD-20230818-006",
      "p1_visible_3d0afdf3736d": "FPJJD-20230818-006",
      "p1_visible_3e7255522b33": "绵阳市游仙区盐泉镇道碑观索桥危桥改造工程项目",
      "p1_visible_4e657cdb9d10": "FPJJD-20230818-006",
      "p1_visible_62e951a692ff": "FPJJD-20230818-006",
      "p1_visible_7f5da566c14e": "FPJJD-20230818-006",
      "p1_visible_8fa8662ad38f": "FPJJD-20230818-006",
      "p1_visible_9769980c060d": "FPJJD-20230818-006",
      "p1_visible_99f6fe6c41ad": "FPJJD-20230818-006",
      "p1_visible_99f753ed6262": "FPJJD-20230818-006",
      "p1_visible_a3c1a28bd34c": "2023-08-18",
      "p1_visible_be5462bd6a62": "FPJJD-20230818-006",
      "p1_visible_d09b05103331": "FPJJD-20230818-006",
      "p1_visible_dfc25d77dc39": "FPJJD-20230818-006",
      "p1_visible_ed582efc6e34": "FPJJD-20230818-006",
      "p1_visible_ee6a4d9e2956": "FPJJD-20230818-006",
      "p1_visible_f22832ce4781": "FPJJD-20230818-006"
    },
    "seq": 420,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.legacy.invoice.tax.fact",
    "name": "进项上报",
    "record": {
      "id": "5506",
      "p1_visible_007363f27191": "FPJJD-20230818-006",
      "p1_visible_22ebb0de8297": "FPJJD-20230818-006",
      "p1_visible_3d0afdf3736d": "FPJJD-20230818-006",
      "p1_visible_3e7255522b33": "绵阳市游仙区盐泉镇道碑观索桥危桥改造工程项目",
      "p1_visible_4e657cdb9d10": "FPJJD-20230818-006",
      "p1_visible_62e951a692ff": "FPJJD-20230818-006",
      "p1_visible_7f5da566c14e": "FPJJD-20230818-006",
      "p1_visible_8fa8662ad38f": "FPJJD-20230818-006",
      "p1_visible_9769980c060d": "FPJJD-20230818-006",
      "p1_visible_99f6fe6c41ad": "FPJJD-20230818-006",
      "p1_visible_99f753ed6262": "FPJJD-20230818-006",
      "p1_visible_a3c1a28bd34c": "2023-08-18",
      "p1_visible_be5462bd6a62": "FPJJD-20230818-006",
      "p1_visible_d09b05103331": "FPJJD-20230818-006",
      "p1_visible_dfc25d77dc39": "FPJJD-20230818-006",
      "p1_visible_ed582efc6e34": "FPJJD-20230818-006",
      "p1_visible_ee6a4d9e2956": "FPJJD-20230818-006",
      "p1_visible_f22832ce4781": "FPJJD-20230818-006"
    },
    "seq": 420,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.tax.deduction.registration",
    "name": "抵扣登记",
    "record": {
      "id": "1",
      "p1_visible_06fa8c6f628f": "审核通过",
      "p1_visible_1e62803e196c": "2026-04-10",
      "p1_visible_3540b47897be": "否",
      "p1_visible_3e7255522b33": "中建四局-刘兴宇项目",
      "p1_visible_8acf4918f1f1": "5825.24",
      "p1_visible_8fa8662ad38f": "DKDJ-20260410-001",
      "p1_visible_ada9a85eab00": "26442000002557446826",
      "p1_visible_be5462bd6a62": "广州永晟建筑工程有限公司",
      "p1_visible_e0361480e3a5": "认证税金",
      "p1_visible_eaa05c7105f7": "0.0",
      "p1_visible_ee19dd75350c": "200000.0",
      "p1_visible_ee6a4d9e2956": "文楠"
    },
    "seq": 430,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.tax.deduction.registration",
    "name": "抵扣登记",
    "record": {
      "id": "1",
      "p1_visible_06fa8c6f628f": "审核通过",
      "p1_visible_1e62803e196c": "2026-04-10",
      "p1_visible_3540b47897be": "否",
      "p1_visible_3e7255522b33": "中建四局-刘兴宇项目",
      "p1_visible_8acf4918f1f1": "5825.24",
      "p1_visible_8fa8662ad38f": "DKDJ-20260410-001",
      "p1_visible_ada9a85eab00": "26442000002557446826",
      "p1_visible_be5462bd6a62": "广州永晟建筑工程有限公司",
      "p1_visible_e0361480e3a5": "认证税金",
      "p1_visible_eaa05c7105f7": "0.0",
      "p1_visible_ee19dd75350c": "200000.0",
      "p1_visible_ee6a4d9e2956": "文楠"
    },
    "seq": 430,
    "token": "YJSKDJ-20260410"
  },
  {
    "model": "sc.legacy.payment.residual.fact",
    "name": "外经证登记",
    "record": {
      "id": "4072",
      "p1_visible_00be183a4b2a": "WJZDJB-20260319-001",
      "p1_visible_026768aaad3c": "眉山天府新区视高街道舒坪社区",
      "p1_visible_06fa8c6f628f": "审核通过",
      "p1_visible_099c01b9d72a": "WJZDJB-20260319-001",
      "p1_visible_3e7255522b33": "眉山环天水务有限公司各条线服务供应商项目（包2）-舒坪社区管网工程",
      "p1_visible_43c2e2732d0a": "2026-12-31",
      "p1_visible_46c54c70dedb": "旌税 税跨报 〔2026〕 769 号",
      "p1_visible_75e856a13c7c": "36091.9",
      "p1_visible_764d417cabd2": "建筑安装",
      "p1_visible_8fa8662ad38f": "WJZDJB-20260319-001",
      "p1_visible_99f6fe6c41ad": "2026（769号）.pdf | legacy-file://UploadFile/UserFile/2026/03/19/cb5f5b05a95d4a118f2bd1f5406be539_174096.pdf",
      "p1_visible_a81dc7a3d1c9": "WJZDJB-20260319-001",
      "p1_visible_a943bac2de74": "眉山环天水务工程有 限公司",
      "p1_visible_b8fbf277a7b1": "舒坪社区管网修复",
      "p1_visible_ba13d5091f9a": "2026-03-19",
      "p1_visible_c1947c4b9d4a": "四川保盛建设集团有 限公司",
      "p1_visible_c237c1b31858": "四川保盛建设集团有 限公司",
      "p1_visible_d2f17f6ee06c": "WJZDJB-20260319-001",
      "p1_visible_dfc25d77dc39": "2026-03-19 15:26:37",
      "p1_visible_ee6a4d9e2956": "李娜"
    },
    "seq": 440,
    "token": "DKQRB-20260206-006"
  },
  {
    "model": "sc.legacy.payment.residual.fact",
    "name": "外经证登记",
    "record": {
      "id": "4072",
      "p1_visible_00be183a4b2a": "WJZDJB-20260319-001",
      "p1_visible_026768aaad3c": "眉山天府新区视高街道舒坪社区",
      "p1_visible_06fa8c6f628f": "审核通过",
      "p1_visible_099c01b9d72a": "WJZDJB-20260319-001",
      "p1_visible_3e7255522b33": "眉山环天水务有限公司各条线服务供应商项目（包2）-舒坪社区管网工程",
      "p1_visible_43c2e2732d0a": "2026-12-31",
      "p1_visible_46c54c70dedb": "旌税 税跨报 〔2026〕 769 号",
      "p1_visible_75e856a13c7c": "36091.9",
      "p1_visible_764d417cabd2": "建筑安装",
      "p1_visible_8fa8662ad38f": "WJZDJB-20260319-001",
      "p1_visible_99f6fe6c41ad": "2026（769号）.pdf | legacy-file://UploadFile/UserFile/2026/03/19/cb5f5b05a95d4a118f2bd1f5406be539_174096.pdf",
      "p1_visible_a81dc7a3d1c9": "WJZDJB-20260319-001",
      "p1_visible_a943bac2de74": "眉山环天水务工程有 限公司",
      "p1_visible_b8fbf277a7b1": "舒坪社区管网修复",
      "p1_visible_ba13d5091f9a": "2026-03-19",
      "p1_visible_c1947c4b9d4a": "四川保盛建设集团有 限公司",
      "p1_visible_c237c1b31858": "四川保盛建设集团有 限公司",
      "p1_visible_d2f17f6ee06c": "WJZDJB-20260319-001",
      "p1_visible_dfc25d77dc39": "2026-03-19 15:26:37",
      "p1_visible_ee6a4d9e2956": "李娜"
    },
    "seq": 440,
    "token": "YJSKDJ-20260410"
  }
]
```
