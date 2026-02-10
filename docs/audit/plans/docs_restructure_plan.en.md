# Docs Restructure Plan v0.1 (English)

## 0. Scope and Constraints
- Scope: `docs/`, `artifacts/contract`, `artifacts/docs`, and full-repo markdown indexing.
- Capability baseline: strictly align with existing system capabilities (scene / intent / contract / guard / verify), no invented features.
- Execution constraint: prefer existing Makefile targets for validation/export (executed in this round: `contract.catalog.export`, `contract.evidence.export`, `audit.intent.surface`).
- Nature of this document: pre-change audit + restructuring plan, no large-scale migration in this round.

## 1. Documentation Audit Summary
Data source: `artifacts/docs/docs_audit_20260210_090905.json`

### 1.1 Overview
- Total markdown files: 1202
- Marked as outdated/temporary: 67
- Duplicate-title entries: 705 (many are templates/archive/third-party docs; needs layered handling)
- Missing critical links: 4

### 1.2 Key Issues (docs-first perspective)
1. Many `TEMP_*` files under `docs/ops/releases/` are mixed with formal release evidence.
2. Boundary between `docs/ops/releases/archive/temp/` and current release docs is unclear, increasing search noise.
3. Core `docs/contract/*` docs do not consistently backlink to `docs/contract/README.md` (`reason_codes.md`, `suggested_action_contract.md`, etc.).
4. Historical frontend version notes (`frontend_v0_3_notes.md` ~ `v0_7`) are mixed at the same level as current-phase docs.

### 1.3 Suspected Outdated/Temporary Files (sample)
- `docs/ops/releases/archive/temp/temp/TEMP_phase_10_batch_contract_pr_body.md`
- `docs/ops/releases/archive/temp/temp/TEMP_phase_10_pr_a_body.md`
- `docs/ops/releases/archive/temp/temp/TEMP_phase_9_8_progress.md`
- `docs/ops/releases/archive/temp/TEMP_repo_audit_summary.md`
- `docs/ops/releases/archive/temp/frontend_history/frontend_v0_3_notes.md`
- `docs/ops/releases/archive/frontend_history/frontend_v0_7_ui_notes.md`

## 2. Capability Matrix -> Document Locations

| Capability Domain | Current Source of Truth | Status | Risk |
|---|---|---|---|
| Contract | `docs/contract/README.md` `docs/contract/contract_v1.md` `docs/contract/exports/intent_catalog.json` `docs/contract/exports/scene_catalog.json` | Mostly complete | Cross-linking is weak |
| Reason Codes | `docs/contract/reason_codes.md` + `addons/smart_core/utils/reason_codes.py` | Semantics consolidated | Missing README backlink |
| Suggested Action Contract | `docs/contract/suggested_action_contract.md` + `frontend/apps/web/src/app/suggested_action/*` | Rules/guards are complete | Weak integration in top-level docs navigation |
| Release / Ops | `docs/ops/releases/*` | Rich evidence | TEMP and formal docs are mixed |
| Gate / Verify | `Makefile` (`verify.*` / `gate.*`) + `scripts/verify/*` | Execution chain is complete | Entry points are scattered across docs |
| Scene / Intent Catalogs | `docs/contract/exports/*.json` `artifacts/docs/intent_surface_report.json` | Machine-readable | No single index page |

## 3. Proposed Directory Structure (v0.1)

```text
docs/
  README.md                      # documentation home (new)
  contract/
    README.md                    # contract hub (keep, improve navigation)
    contract_v1.md
    reason_codes.md
    suggested_action_contract.md
    exports/
      intent_catalog.json
      scene_catalog.json
  ops/
    README.md                    # ops/process entry (new)
    releases/
      current/                   # current-phase evidence (new)
      archive/                   # historical archives (keep)
      templates/                 # normalized template directory (from _templates)
  audit/
    README.md                    # audit methodology (new)
    latest/                      # latest visible audit index (new index layer)
```

## 4. Directory Responsibility Boundaries
- `docs/contract/`: platform-facing contract commitments (shape, reason codes, FE/BE contract behavior).
- `docs/ops/releases/current/`: current-phase release evidence for reviewers.
- `docs/ops/releases/archive/temp/`: historical documents, not default reading path.
- `docs/audit/`: audit method/rules/latest index; machine-generated payload stays in `artifacts/`.
- `artifacts/docs/`: machine-readable outputs and one-shot audits, not long-term narrative docs.

## 5. Merge / Move / Deprecate List

### 5.1 Move (recommended)
1. `docs/ops/releases/current/phase_11_backend_closure.md` -> `docs/ops/releases/current/phase_11_backend_closure.md`
2. `docs/ops/releases/current/phase_11_1_contract_visibility.md` -> `docs/ops/releases/current/phase_11_1_contract_visibility.md`
3. `docs/ops/releases/current/phase_10_my_work_v1_evidence.md` -> `docs/ops/releases/current/phase_10_my_work_v1_evidence.md`
4. `docs/ops/releases/_templates/*` -> `docs/ops/releases/templates/*`

### 5.2 Deprecate/Archive (recommended)
1. `docs/ops/releases/TEMP_*.md`: move to `archive/temp/` or delete after reference check.
2. `docs/ops/releases/archive/temp/frontend_history/frontend_v0_3_notes.md` ~ `frontend_v0_7*.md`: move to `archive/frontend_history/`.
3. `docs/audit/node_missing_notes.md`: archive if superseded by current verification flow.

### 5.3 Link Fixes (recommended)
1. Add backlink to `docs/contract/README.md` from `docs/contract/reason_codes.md`.
2. Add backlink to `docs/contract/README.md` from `docs/contract/suggested_action_contract.md`.
3. Add a consistent “Back to contract hub” link in `docs/contract/contract_v1.md` and `docs/contract/baseline_rules.md`.

## 6. Proposed New Makefile Doc-Verification Targets (plan only)
> Not implemented in this round; planned for next PR.

1. `verify.docs.inventory`
- Output markdown inventory + classification stats to `artifacts/docs/`.

2. `verify.docs.links`
- Validate internal relative links and critical hub backlinks.

3. `verify.docs.toc`
- Validate heading structure and section consistency for contract/ops/audit docs.

4. `verify.docs.temp_guard`
- Block new `TEMP_*.md` from entering `docs/ops/releases/current/`.

5. `verify.docs.contract_sync`
- Verify version-anchor consistency between `docs/contract/*.md` and `docs/contract/exports/*.json`.

## 7. Phased Execution Plan

### Phase A (low risk, 1 PR)
- Add `docs/README.md`, `docs/ops/README.md`, `docs/audit/README.md`.
- Fix key backlinks in `docs/contract/*`.

### Phase B (medium risk, 1 PR)
- Restructure release docs into `current/`, `archive/`, `templates/`.
- Update all references.

### Phase C (gate hardening, 1 PR)
- Add docs verification scripts and Makefile targets.
- Wire `verify.docs.links + verify.docs.temp_guard` into `verify.contract.preflight` or a dedicated `verify.docs.all`.

## 8. Deliverables in This Round
- `docs/audit/plans/docs_restructure_plan.zh.md`
- `docs/audit/plans/docs_restructure_plan.en.md`
- `artifacts/docs/docs_audit_20260210_090905.json`

