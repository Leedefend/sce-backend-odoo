# Contract Field Implementation Manifest v1

Iteration: `ITER-2026-04-13-1840`

Target model: `construction.contract`

## Implemented Fields

| Field | Type | Index | Copy | User label |
|---|---|---:|---:|---|
| `legacy_contract_id` | `fields.Char` | yes | false | 旧系统合同ID |
| `legacy_project_id` | `fields.Char` | yes | false | 旧系统项目ID |
| `legacy_document_no` | `fields.Char` | no | false | 旧系统单据编号 |
| `legacy_contract_no` | `fields.Char` | yes | false | 旧系统合同编号 |
| `legacy_external_contract_no` | `fields.Char` | no | false | 旧系统外部合同编号 |
| `legacy_status` | `fields.Char` | no | false | 旧系统合同状态 |
| `legacy_deleted_flag` | `fields.Char` | no | false | 旧系统删除标志 |
| `legacy_counterparty_text` | `fields.Char` | no | false | 旧系统相对方文本 |

## Modified Files

- `addons/smart_construction_core/models/support/contract_center.py`
- `addons/smart_construction_core/views/core/contract_views.xml`

## Not Changed

- no importer
- no data import
- no `__manifest__.py`
- no ACL/security/record rules
- no menus
- no frontend
- no payment/settlement/accounting files
- no workflow state logic
- no tax logic
- no amount computation logic

## Upgrade Requirement

Because this batch adds stored model fields, module upgrade is required:

```bash
CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core DB_NAME=sc_demo MODULE=smart_construction_core make mod.upgrade
```

Upgrade was executed in this batch.
