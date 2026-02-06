# Release R0 Launch Package Baseline

## Official launch package

- Package key: `sc-project-execution-core`
- Display name: `智能施工 · 项目执行管理（基础版）`
- Default channel: `stable`

## Included launch scenes

- `projects.list` (default first-visit success path)
- `projects.ledger`
- `projects.intake` (optional entry)

## First-login success path

`login -> /s/projects.list`

## Workbench policy

- Workbench is fallback only for exceptional navigation states.
- Directory menus must resolve to the first reachable child action/scene before fallback.
