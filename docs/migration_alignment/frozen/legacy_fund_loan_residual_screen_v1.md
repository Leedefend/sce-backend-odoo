# Legacy Fund Loan Residual Screen v1

Status: `PASS`

This report screens old-system fund daily, loan registration, and borrowing rows before any model or XML asset decision.

## Scope

- source tables: `D_SCBSJS_ZJGL_ZJSZ_ZJRBB`, `ZJGL_ZJSZ_DKGL_DKDJ`, `ZJGL_ZCDFSZ_FXJK_JK`
- DB writes: `0`
- Odoo shell: `false`

## Source Baseline

- raw rows: `873`
- active rows: `847`
- project-anchored rows: `855`
- counterparty-named rows: `338`

### Source table counts

| Source table | Rows |
|---|---:|
| D_SCBSJS_ZJGL_ZJSZ_ZJRBB | 511 |
| ZJGL_ZJSZ_DKGL_DKDJ | 193 |
| ZJGL_ZCDFSZ_FXJK_JK | 169 |

## Business Fact Classification

| Classification | Rows | Source amount sum |
|---|---:|---:|
| management_snapshot_candidate | 496 | 5339855508.5100 |
| project_anchored_financing_candidate | 318 | 188881819.3700 |
| blocked | 59 | 311074079.6700 |

### Classification by source table

| Source table | Classification counts |
|---|---|
| D_SCBSJS_ZJGL_ZJSZ_ZJRBB | `{"blocked": 15, "management_snapshot_candidate": 496}` |
| ZJGL_ZCDFSZ_FXJK_JK | `{"blocked": 3, "project_anchored_financing_candidate": 166}` |
| ZJGL_ZJSZ_DKGL_DKDJ | `{"blocked": 41, "project_anchored_financing_candidate": 152}` |

### Blocked reasons

| Reason | Rows |
|---|---:|
| deleted | 26 |
| missing_counterparty_name | 24 |
| project_not_assetized | 18 |
| amount_not_positive_or_missing | 4 |
| missing_balance_amounts | 2 |
| missing_document_date | 1 |

## Samples

### blocked

```json
[
  {
    "amount": "5664776.9400",
    "counterparty_name": "",
    "document_date": "2024-01-29 00:00:00",
    "document_no": "ZJRBB-20240129-001",
    "family": "fund_daily_balance_snapshot",
    "legacy_id": "0252916ccd3f431ca85737ef9700ac7b",
    "project_id": "fb0c4133-f011-44a4-a285-59cfd30aec27",
    "project_name": "公司综合平台",
    "reasons": "deleted",
    "route": "blocked",
    "source_table": "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"
  },
  {
    "amount": "5489232.6800",
    "counterparty_name": "",
    "document_date": "2024-01-30 00:00:00",
    "document_no": "ZJRBB-20240130-001",
    "family": "fund_daily_balance_snapshot",
    "legacy_id": "1699877880d54793b2b3cda0c0bd846c",
    "project_id": "fb0c4133-f011-44a4-a285-59cfd30aec27",
    "project_name": "公司综合平台",
    "reasons": "deleted",
    "route": "blocked",
    "source_table": "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"
  },
  {
    "amount": "60550702.0600",
    "counterparty_name": "",
    "document_date": "2024-01-27 00:00:00",
    "document_no": "ZJRBB-20240128-001",
    "family": "fund_daily_balance_snapshot",
    "legacy_id": "21bfebbf22e743d9b748ab055afb332c",
    "project_id": "fb0c4133-f011-44a4-a285-59cfd30aec27",
    "project_name": "公司综合平台",
    "reasons": "deleted",
    "route": "blocked",
    "source_table": "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"
  },
  {
    "amount": "30221609.8300",
    "counterparty_name": "",
    "document_date": "2024-01-27 00:00:00",
    "document_no": "ZJRBB-20240127-002",
    "family": "fund_daily_balance_snapshot",
    "legacy_id": "3563a66d01ed4445a030ffb0dcdc476a",
    "project_id": "fb0c4133-f011-44a4-a285-59cfd30aec27",
    "project_name": "公司综合平台",
    "reasons": "deleted",
    "route": "blocked",
    "source_table": "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"
  },
  {
    "amount": "",
    "counterparty_name": "",
    "document_date": "2024-01-26 00:00:00",
    "document_no": "ZJRBB-20240126-001",
    "family": "fund_daily_balance_snapshot",
    "legacy_id": "4303e315cad84499b1ae21058e3d7387",
    "project_id": "fb0c4133-f011-44a4-a285-59cfd30aec27",
    "project_name": "公司综合平台",
    "reasons": "deleted,missing_balance_amounts",
    "route": "blocked",
    "source_table": "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"
  }
]
```

### management_snapshot_candidate

```json
[
  {
    "amount": "10688210.3800",
    "counterparty_name": "",
    "document_date": "2026-01-12 00:00:00",
    "document_no": "ZJRBB-20260112-001",
    "family": "fund_daily_balance_snapshot",
    "legacy_id": "025f5de581114619975fd74b4d525ed4",
    "project_id": "fb0c4133-f011-44a4-a285-59cfd30aec27",
    "project_name": "公司综合平台",
    "reasons": "",
    "route": "management_snapshot_candidate",
    "source_table": "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"
  },
  {
    "amount": "2219842.5900",
    "counterparty_name": "",
    "document_date": "2025-12-08 00:00:00",
    "document_no": "ZJRBB-20251208-001",
    "family": "fund_daily_balance_snapshot",
    "legacy_id": "0398505eea6546e596a6cc7e030b1cde",
    "project_id": "fb0c4133-f011-44a4-a285-59cfd30aec27",
    "project_name": "公司综合平台",
    "reasons": "",
    "route": "management_snapshot_candidate",
    "source_table": "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"
  },
  {
    "amount": "10243620.2000",
    "counterparty_name": "",
    "document_date": "2026-02-04 00:00:00",
    "document_no": "ZJRBB-20260204-001",
    "family": "fund_daily_balance_snapshot",
    "legacy_id": "03d557167f004103abd47d37ee7abbd7",
    "project_id": "fb0c4133-f011-44a4-a285-59cfd30aec27",
    "project_name": "公司综合平台",
    "reasons": "",
    "route": "management_snapshot_candidate",
    "source_table": "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"
  },
  {
    "amount": "8028745.6900",
    "counterparty_name": "",
    "document_date": "2024-11-21 00:00:00",
    "document_no": "ZJRBB-20241121-001",
    "family": "fund_daily_balance_snapshot",
    "legacy_id": "047c8d05099a4714b1c59fef5e663c57",
    "project_id": "fb0c4133-f011-44a4-a285-59cfd30aec27",
    "project_name": "公司综合平台",
    "reasons": "",
    "route": "management_snapshot_candidate",
    "source_table": "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"
  },
  {
    "amount": "3502424.5300",
    "counterparty_name": "",
    "document_date": "2025-11-17 00:00:00",
    "document_no": "ZJRBB-20251117-001",
    "family": "fund_daily_balance_snapshot",
    "legacy_id": "0529ca759dd44f56b60b3fc2152894ea",
    "project_id": "fb0c4133-f011-44a4-a285-59cfd30aec27",
    "project_name": "公司综合平台",
    "reasons": "",
    "route": "management_snapshot_candidate",
    "source_table": "D_SCBSJS_ZJGL_ZJSZ_ZJRBB"
  }
]
```

### project_anchored_financing_candidate

```json
[
  {
    "amount": "2248001.9200",
    "counterparty_name": "誉城国际",
    "document_date": "2020-05-29 00:00:00",
    "document_no": "JK-20210204-014",
    "family": "borrowing_request",
    "legacy_id": "00705d43b2b649d2b5d30e0af73f4d98",
    "project_id": "ce7c47d08d88409da91cd433099d5cee",
    "project_name": "四川现代农业工程职业学院一期工程（10#教学楼、培训中心）",
    "reasons": "",
    "route": "project_anchored_financing_candidate",
    "source_table": "ZJGL_ZCDFSZ_FXJK_JK"
  },
  {
    "amount": "300000.0000",
    "counterparty_name": "雅瑶小学项目",
    "document_date": "2021-03-26 00:00:00",
    "document_no": "JK-20210326-001",
    "family": "borrowing_request",
    "legacy_id": "035193ee4849403084df15d265b858bc",
    "project_id": "52278e622558409db167eca9eba8c8b8",
    "project_name": "【广州市花都区殡仪馆迁建工程施工总承包】项目【室外（园建、绿化、道路及护坡工程）】工程",
    "reasons": "",
    "route": "project_anchored_financing_candidate",
    "source_table": "ZJGL_ZCDFSZ_FXJK_JK"
  },
  {
    "amount": "250000.0000",
    "counterparty_name": "倪德珍",
    "document_date": "2025-09-23 00:00:00",
    "document_no": "JK-20250923-001",
    "family": "borrowing_request",
    "legacy_id": "036534953b0d49f2ab4aae19c36d8bf1",
    "project_id": "4f86be86dc0f46508613c812126849d5",
    "project_name": "保盛公司采购平台",
    "reasons": "",
    "route": "project_anchored_financing_candidate",
    "source_table": "ZJGL_ZCDFSZ_FXJK_JK"
  },
  {
    "amount": "33136.0000",
    "counterparty_name": "誉城国际",
    "document_date": "2021-02-04 00:00:00",
    "document_no": "JK-20210204-015",
    "family": "borrowing_request",
    "legacy_id": "04834533dca546edab4d789fab16b0e5",
    "project_id": "ce7c47d08d88409da91cd433099d5cee",
    "project_name": "四川现代农业工程职业学院一期工程（10#教学楼、培训中心）",
    "reasons": "",
    "route": "project_anchored_financing_candidate",
    "source_table": "ZJGL_ZCDFSZ_FXJK_JK"
  },
  {
    "amount": "45958.0000",
    "counterparty_name": "四川现代农业学院",
    "document_date": "2020-09-03 00:00:00",
    "document_no": "JK-20210204-012",
    "family": "borrowing_request",
    "legacy_id": "04ad7a4806434d628aa77b290ceecfce",
    "project_id": "e198e1afc1324069844bfe3a310cfe91",
    "project_name": "誉城国际一期二批次",
    "reasons": "",
    "route": "project_anchored_financing_candidate",
    "source_table": "ZJGL_ZCDFSZ_FXJK_JK"
  }
]
```

## Next Recommendation

- recommendation: `open_fund_loan_model_design_for_project_anchored_financing`
- judgment: loan registration and borrowing rows with positive amount, document date, project anchor, and counterparty name are durable business facts.
- judgment: fund daily rows are management balance snapshots, not payment or settlement transactions; they should not be forced into the payment model.
- next lane: if accepted, open a model-design batch for a neutral legacy financing/loan fact carrier before XML asset generation.
