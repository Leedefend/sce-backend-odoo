# Page Contract Builder Modularization Plan (V1)

## Background

`addons/smart_core/core/page_contracts_builder.py` now carries multiple responsibilities (copy, section structure, semantic rules, mode inference). This plan defines a low-risk split path: stabilize first, modularize incrementally.

## Objectives

- Decouple page content definitions from assembly/orchestration logic.
- Keep existing contract output compatible.
- Enable incremental per-page recovery with lower maintenance cost.

## Phase-1 Scope

- Extract page default contract definitions (`texts`/`sections`/`page_mode`).
- Keep builder as a single entrypoint for merge and fallback.
- No change to scene registry / ACL / auth / deploy-rollback core flow.

## Proposed Structure

```text
addons/smart_core/core/page_contracts/
  __init__.py
  login_contract.py
  project_management_contract.py
  projects_list_contract.py
  risk_center_contract.py
  registry.py
```

## Responsibility Split

- `*_contract.py`: page-level default semantics (texts, sections, mode, optional hints).
- `registry.py`: registration/mapping of page contract providers.
- `page_contracts_builder.py`:
  - Load contract providers from registry.
  - Merge runtime context and fallback.
  - Preserve legacy interface and field compatibility.

## Incremental Migration Steps

1. Extract `login` first (smallest risk).
2. Add registry loading path in builder while keeping inline fallback.
3. Extract `project.management` and `projects.list` in second batch.
4. Remove duplicated inline definitions after migration stabilizes.

## Compatibility Constraints

- Do not change external call pattern of `build_page_contracts()`.
- Do not change existing `schema_version` and envelope baseline.
- Regression baseline includes:
  - `make verify.frontend.build`
  - `make verify.frontend.typecheck.strict`
  - existing contract-related verify chain.

## Risks and Mitigations

- Risk: missing key sync causes frontend fallback behavior.
  - Mitigation: key diff checklist + post-migration smoke checks.
- Risk: parallel edits create duplicate definitions.
  - Mitigation: enforce rule that new page semantics go to module files only.

## Out of Scope

- No one-shot full-page split.
- No protocol-level contract envelope redesign.
