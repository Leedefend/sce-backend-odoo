# Unified Page Contract v2+ DataContract Batch-E

Date: 2026-05-01
Status: Batch-E implementation note

## Layer Target

Contract Governance / DataContract Consolidation

## Module

- `addons/smart_core/core/unified_page_contract_v2_data.py`
- `docs/architecture/unified_page_contract_v2/fixtures/data_contract_source.json`
- `docs/architecture/unified_page_contract_v2/snapshots/data_contract_snapshot_v1.json`
- `scripts/verify/unified_page_contract_v2_data_guard.py`
- `docs/architecture/unified_page_contract_v2/unified_page_contract_v2.schema.json`
- `Makefile`

## Reason

Existing renderable data can come from record payloads, list rows, relation rows, dict/options, tree data, and datasource metadata. v2+ requires these sources to be normalized into one `DataContract` so frontend runtimes do not infer data meaning from ad hoc response shapes.

## Source Mapping

| Source | v2+ output |
| --- | --- |
| `mainData` / `main_data` / `record` / `values` / `formData` | `mainData` |
| `tableRows` / `rows` / `list_rows` / `table_rows` / `records` | `tableRows` |
| `relationRows` / `relation_rows` / `line_patches` | `relationRows` |
| `treeData` / `tree_data` | `treeData` |
| `ganttData` / `gantt_data` | `ganttData` |
| `dictData` / `dict_data` / `options` | `dictData` |
| `pagination` | `pagination` |
| `dataSource` / `data_source` / `data_sources` | `dataSource` |
| `dataMeta` / `data_meta` | `dataMeta` |

## DataSource Boundary

`dataSource` contains metadata only:

- query/provider identity
- cache policy
- consistency hint
- subscription flag

It must not contain:

- SQL
- raw domains
- permissions
- ACL / record rules
- sudo hints
- business execution rules

## Schema Change

`treeData` and `ganttData` are added as optional `DataContract` extension slots. They are not required in the canonical examples, so current form/list/tree/nested examples remain compatible.

## Upgrade Assessment

No Odoo model field, view, security, data XML, cron, or manifest dependency is added.

Result:

- `-u smart_core`: not required for this batch.
- service restart: not required for static validation; required only if a live Odoo worker must import the new module without process reload.

## Verification

Primary restricted target:

```bash
make verify.unified_page_contract.v2
```

Data-only target:

```bash
make verify.unified_page_contract.v2.data
```

## Rollback

Revert:

- `addons/smart_core/core/unified_page_contract_v2_data.py`
- `scripts/verify/unified_page_contract_v2_data_guard.py`
- `docs/architecture/unified_page_contract_v2/fixtures/data_contract_source.json`
- `docs/architecture/unified_page_contract_v2/snapshots/data_contract_snapshot_v1.json`
- schema optional `treeData/ganttData` extension
- `Makefile` data target changes

No database rollback is required.
