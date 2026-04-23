# 迁移数据资产 Manifest Schema v1

状态：Frozen Migration Governance
上位方案：`docs/migration_alignment/frozen/legacy_business_fact_asset_rebuild_plan_v1.md`
目标：为后续资产生成器、loader、fresh DB rebuild runner 提供统一 manifest 契约。

## 1. 定位

本 schema 定义 `migration_assets/manifest` 的最小必需结构。

后续迁移批次必须先生成资产 manifest，再生成或装载资产文件。没有 manifest 的 XML、CSV、JSON 或 loader 输入不得视为可重建资产。

## 2. 目录约定

```text
migration_assets/
  00_base/
  10_master/
  20_business/
  30_relation/
  40_post/
  manifest/
    asset_manifest.json
    external_id_manifest.json
    validation_manifest.json
```

说明：

- `asset_manifest.json` 描述资产包版本、来源、车道、载体、依赖、计数和导入顺序。
- `external_id_manifest.json` 描述旧库来源键到 stable external id 的映射。
- `validation_manifest.json` 描述生成前、装载前、装载后校验项。

## 3. asset_manifest_version

字段：`asset_manifest_version`

当前值：

```json
"asset_manifest_version": "1.0"
```

规则：

- patch 版本用于字段补充且不破坏现有 loader。
- minor 版本用于增加可选结构。
- major 版本用于字段 rename、字段删除或语义改变。
- 后续 runner 必须拒绝未知 major 版本。

## 4. asset_manifest.json

最小结构：

```json
{
  "asset_manifest_version": "1.0",
  "asset_package_id": "partner_sc_v1",
  "generated_at": "2026-04-15T00:00:00+08:00",
  "source_snapshot": {
    "source_system": "sc",
    "source_db": "legacy_sc",
    "extract_batch_id": "partner_l4_asset_v1",
    "source_tables": ["company", "supplier"]
  },
  "lane": {
    "lane_id": "partner",
    "layer": "10_master",
    "business_priority": "core_master",
    "risk_class": "normal"
  },
  "target": {
    "model": "res.partner",
    "identity_field": "legacy_identity_key",
    "load_strategy": "upsert_by_external_id"
  },
  "assets": [
    {
      "asset_id": "partner_master_csv_v1",
      "path": "10_master/partner/partner_master_v1.csv",
      "format": "csv",
      "record_count": 0,
      "sha256": "<required-after-generation>",
      "required": true
    }
  ],
  "load_order": [
    "external_id_manifest",
    "partner_master_csv_v1"
  ],
  "dependencies": [],
  "counts": {
    "raw_rows": 0,
    "normalized_rows": 0,
    "loadable_records": 0,
    "discarded_records": 0,
    "deferred_records": 0,
    "high_risk_excluded_records": 0
  },
  "idempotency": {
    "mode": "external_id",
    "duplicate_policy": "update_existing_same_external_id",
    "conflict_policy": "block_record"
  },
  "validation_gates": [
    "external_id_unique",
    "required_fields_present",
    "dependencies_resolved",
    "no_high_risk_lane_leakage"
  ]
}
```

硬规则：

- `asset_package_id` 必须稳定，格式为 `<lane>_<source>_v<version>`。
- `lane.layer` 必须是 `00_base`、`10_master`、`20_business`、`30_relation`、`40_post` 之一。
- `target.model` 必须是新系统真实模型名或明确的 staging carrier。
- `assets[].sha256` 在资产生成后必须填充。
- `load_order` 只能引用同 manifest 中存在的 asset 或保留关键字。
- `counts.loadable_records + counts.discarded_records + counts.deferred_records + counts.high_risk_excluded_records` 必须能解释标准化后的总量。

## 5. external_id_manifest

文件：`external_id_manifest.json`

最小结构：

```json
{
  "asset_manifest_version": "1.0",
  "asset_package_id": "partner_sc_v1",
  "lane_id": "partner",
  "external_id_rule": {
    "pattern": "legacy_<lane>_<source>_<legacy_pk>",
    "source": "sc",
    "legacy_key_policy": "stable_legacy_pk_or_frozen_canonical_key"
  },
  "records": [
    {
      "external_id": "legacy_partner_sc_3308",
      "legacy_key": "3308",
      "legacy_key_type": "single_pk",
      "source_table": "company",
      "target_model": "res.partner",
      "target_lookup": {
        "field": "legacy_identity_key",
        "value": "partner:sc:3308"
      },
      "status": "loadable"
    }
  ],
  "summary": {
    "total": 0,
    "loadable": 0,
    "discarded": 0,
    "deferred": 0,
    "conflict_blocked": 0
  }
}
```

external id 规则：

- `external_id` 必须唯一。
- `external_id` 不能包含新库自增 id。
- `legacy_key` 必须来自旧库稳定键或已冻结 canonical key。
- `legacy_key_type` 允许值：`single_pk`、`composite_key`、`canonical_key`。
- `status` 允许值：`loadable`、`discarded`、`deferred`、`conflict_blocked`、`high_risk_excluded`。
- `discarded` 记录可以不进入业务资产文件，但必须进入 summary 计数或丢弃摘要。

## 6. validation_manifest.json

最小结构：

```json
{
  "asset_manifest_version": "1.0",
  "asset_package_id": "partner_sc_v1",
  "validation_gates": {
    "generate_time": [
      "source_snapshot_declared",
      "normalized_rows_counted",
      "external_id_unique",
      "required_fields_present"
    ],
    "preload": [
      "asset_files_exist",
      "asset_hashes_match",
      "dependencies_resolved",
      "target_model_available"
    ],
    "postload": [
      "target_count_matches_manifest",
      "external_id_resolves",
      "rerun_is_idempotent",
      "no_duplicate_business_identity"
    ]
  },
  "failure_policy": {
    "missing_required_field": "block_record",
    "missing_dependency": "block_record",
    "duplicate_external_id": "block_package",
    "high_risk_lane_leakage": "block_package"
  }
}
```

## 7. partner lane 样板

partner lane 是第一条资产化样板车道。

### 输入来源

| source_table | role | 已知来源 |
| --- | --- | --- |
| `company` | primary partner source | `tmp/raw/partner/company.csv` |
| `supplier` | supplier supplemental source | `tmp/raw/partner/supplier.csv` |

### 标准化事实字段

| normalized field | required | 说明 |
| --- | --- | --- |
| `legacy_partner_key` | yes | 旧库稳定主键或 canonical key |
| `partner_name` | yes | 企业名称 |
| `tax_number` | no | 税号或统一社会信用代码 |
| `phone` | no | 联系电话 |
| `email` | no | 邮箱 |
| `source_role` | yes | `company`、`supplier`、`combined` |
| `discard_reason` | conditional | 丢弃记录必须填写 |

### 目标模型字段

| target field | source | policy |
| --- | --- | --- |
| `name` | `partner_name` | required |
| `is_company` | constant `true` | required |
| `vat` | `tax_number` | optional |
| `phone` | `phone` | optional |
| `email` | `email` | optional |
| `legacy_identity_key` | `partner:<source>:<legacy_partner_key>` | required if carrier exists |

### partner lane asset package

建议包：

```text
migration_assets/
  10_master/
    partner/
      partner_master_v1.csv
      partner_discard_summary_v1.csv
  manifest/
    partner_asset_manifest_v1.json
    partner_external_id_manifest_v1.json
    partner_validation_manifest_v1.json
```

### partner lane idempotency

`idempotency` 规则：

- 首选按 `external_id` upsert。
- 若新模型已有 legacy identity carrier，则用 `legacy_identity_key` 做二次防重。
- 同一 `tax_number` 下名称冲突时，不自动合并，记录进入 `conflict_blocked`。
- 缺失非必填字段不阻断。
- 缺失 `partner_name` 或无法生成 `legacy_partner_key` 的记录丢弃。

## 8. load_order

资产包导入顺序必须显式声明。

partner 样板顺序：

```json
[
  "partner_external_id_manifest_v1",
  "partner_master_v1",
  "partner_validation_manifest_v1"
]
```

全局顺序延续上位方案：

1. `00_base`
2. `10_master/partner`
3. `10_master/project`
4. `10_master/contract_header`
5. `30_relation/project_member_neutral`
6. `20_business/receipt_core`
7. `40_post`
8. `manifest/rebuild_acceptance`

## 9. 禁止混入

本 schema 默认排除：

- payment settlement。
- accounting。
- ACL/security。
- record rules。
- module manifest/install order。
- chatter、mail activity、操作日志。

这些内容只能在独立高风险任务中扩展 schema。

## 10. 后续实现节奏

下一批可以进入：

```text
ITER-MIGRATION-PARTNER-ASSET-GENERATOR-DESIGN
```

唯一目标：

- 设计 partner asset generator 的输入、输出、字段映射和无 DB 验证命令。

不做：

- 不写新库。
- 不重构现有 partner 写库脚本。
- 不把合同、项目、收款车道混入 partner 资产生成器。
