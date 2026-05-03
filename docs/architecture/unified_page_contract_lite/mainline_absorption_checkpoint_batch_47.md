# Unified Semantic Page Contract Lite - Mainline Absorption Checkpoint Batch 47

Date: 2026-05-03
Status: mainline absorbed

## 1. Boundary

Layer Target: Contract Governance / Mainline Absorption

Module:

- `addons/smart_core/core`
- `addons/smart_core/handlers`
- `frontend/apps/web/src/app/contracts`
- `frontend/apps/web/src/app/runtime`
- `frontend/apps/web/src/api`
- `frontend/apps/web/src/app/resolvers`
- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

The previous Lite governance integration branch has been absorbed into latest
`origin/main`. This checkpoint freezes that fact so later contract and mobile
work starts from the mainline baseline, not from the deleted integration branch.

## 2. Mainline Baseline

The absorbed baseline is:

```text
contractVersion: 2.0.0
runtime policy: default-off
pilot: project.project:tree
source entry: load_contract opt-in preview
default frontend path: legacy ui.contract
```

`legacy `ui.contract` remains the default path` unless the pilot is explicitly
enabled with:

```text
VITE_LITE_CONTRACT_PILOT=1
```

## 3. What Is Included

Mainline now contains:

- Lite v2.0 schema and examples
- source and patch normalizers
- Lite adapter snapshots
- `api_onchange` opt-in preview support
- `load_contract` opt-in preview support
- startup-chain negative guards
- frontend runtime negative guard
- default-off frontend pilot implementation
- browser smoke for the `project.project:tree` pilot

## 4. What Is Not Included

This checkpoint does not:

- enable Lite by default
- replace the global frontend renderer
- change `login`
- change `system.init`
- make `ui.contract` return Lite
- add mobile contract fields
- add `runtimeContract`
- add selector status
- add dependency graph
- add component registry

No mobile contract fields are introduced by this checkpoint.

## 5. Next Allowed Contract Work

The next contract governance work must start from latest `origin/main` and may
only expand the baseline through a new scoped batch.

Allowed next candidates:

- extend Lite source coverage for one additional Odoo view shape
- add one more default-off frontend pilot page
- design a minimal mobile contract extension after Lite mainline stability is
  confirmed

Not allowed in the same batch:

- mobile contract extension plus frontend mobile page rewrite
- global Lite default enablement
- frontend business semantic inference

## 6. Verification

Required static gate:

```bash
make verify.unified_page_contract.lite.mainline_absorption
```

Full Lite gate:

```bash
make verify.unified_page_contract.lite
```

Browser pilot smoke remains explicit and host-driven:

```bash
VITE_LITE_CONTRACT_PILOT=1
make verify.unified_page_contract.lite.frontend_pilot_browser.host
```

## 7. Rollback

Runtime rollback:

```text
do not set VITE_LITE_CONTRACT_PILOT=1
```

Code rollback:

```text
revert the checkpoint batch commit
```
