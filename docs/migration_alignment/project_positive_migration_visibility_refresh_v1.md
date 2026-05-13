# Project Positive Migration Visibility Refresh v1

Status: `user_approved_for_visibility_refresh`

## Decision

The project list is aligned by positive business facts instead of exact project
name equality.

Included project anchors:

- project names in the user-provided 672-name construction-contract workbook,
  except the three names the user confirmed as having no substantive business
  data;
- aliases that resolve through raw visible construction contract facts to a
  canonical `project.project`;
- same-name runtime project facts when contract names evolved;
- `周超工程（德阳二重工程项目）`, retained by user decision and mapped to
  canonical project `易静工程（德阳二重工程项目）`;
- already separated direct projects, which are exempt from this archival pass.

Excluded names:

- `2024年大邑县S216水晶(平武)-邛崃  K433+900-K434+300段道路水毁抢险救灾工程`
- `2026年春季乔木补植项目劳务分包合同`
- `旌兴·和悦雲岸1#-11#楼项目采购室外园林景观工程`

## Runtime Effect

The write flow updates only `project.project.active`:

- retained anchors are active;
- all other projects are archived and no longer visible to users by default;
- business fact tables are not modified.

## Reproducible Entry

Use the Makefile targets documented in
`docs/ops/project_positive_migration_visibility_refresh_runbook_v1.md`:

- `project.positive_migration.reconcile.probe`
- `project.positive_migration.visibility.refresh.write`

The write target is protected by `MIGRATION_REPLAY_DB_ALLOWLIST`.
