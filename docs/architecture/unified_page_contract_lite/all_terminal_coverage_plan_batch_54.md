# Unified Semantic Page Contract Lite - All-Terminal Coverage Plan Batch 54

Date: 2026-05-03
Status: planning

## 1. Batch Boundary

Layer Target: Frontend Layer / Contract Consumer Planning

Module:

- `docs/architecture/unified_page_contract_lite`
- future `frontend` terminal contract consumer work
- future terminal verification scripts

Reason:

Lite contract governance has entered `main`. The next goal is not a separate
mobile branch of behavior. The goal is full terminal coverage: Web PC, UniApp
mini program, and Harmony H5 must consume the same Lite semantic contract with
only terminal adaptation differences.

## 2. Goal

Define the first executable plan for all-terminal coverage against Unified
Semantic Page Contract Lite.

This batch does not implement terminal runtime code. It freezes what the next
implementation batches may touch and how they will be accepted.

## 3. Scope

Allowed in this planning batch:

- define terminal coverage target for `web_pc`, `wx_mini`, and `harmony_h5`
- define frontend consumption order
- define verification gates
- define rollout and rollback rules
- identify stop conditions

Not allowed in this planning batch:

- no backend contract shape change
- no new Lite contract fields
- no `runtimeContract`
- no selector status
- no component registry
- no dependency graph
- no Web default Lite enablement
- no terminal renderer implementation
- no direct page-specific business inference in frontend

## 4. Current Baseline

Mainline already provides:

- Lite contract v2.0 schema
- `clientType` enum support for `web_pc`, `wx_mini`, `harmony_h5`
- default-off Lite frontend rollout switch
- `pilot` and `all_tree` runtime flags for Web validation
- positive, legacy fallback, and matrix browser gates for Web tree/list rollout

All terminals must consume this baseline instead of introducing parallel
terminal contracts.

## 5. Target Terminal Behavior

All terminal clients must keep the same business semantics:

- same `pageInfo.pageId`
- same `pageInfo.sceneKey`
- same `fieldCode`
- same `widgetId`
- same `actionId`
- same status semantics
- same server dispatch model
- same patch semantics: `replace` and `merge`

Terminals may differ only in rendering adaptation:

- wide multi-column layout on `web_pc`
- single-column layout
- mobile density on `wx_mini` and `harmony_h5`
- terminal component wrapper
- touch-friendly toolbar placement
- H5 or mini-program adapter limits

## 6. Implementation Plan

### Step 1 - All-Terminal Contract Baseline Probe

Operation:

- add a verification probe that requests Lite preview with `clientType=web_pc`,
  `clientType=wx_mini`, and `clientType=harmony_h5`
- compare semantic signatures across all three terminals

Modification scope:

- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Output:

- all-terminal contract baseline report
- guard target for client semantic parity

Completion criteria:

- `web_pc`, `wx_mini`, and `harmony_h5` keep stable IDs and action semantics
- only layout adaptation differs

### Step 2 - Shared Terminal Consumer Contract

Operation:

- define the shared terminal consumer contract boundary
- reuse Lite schema and store mapping rules across Web and mobile terminals
- keep non-Web renderer entries disabled by default

Modification scope:

- future terminal frontend package or app path only
- shared contract type imports if already available

Output:

- shared terminal contract consumer skeleton
- no page-specific business logic

Completion criteria:

- no direct backend response parsing from pages
- no role, permission, route, or business inference in any terminal frontend
- Web app behavior remains unchanged

### Step 3 - Web PC Regression as Coverage Anchor

Operation:

- keep `web_pc` all-tree validation as the anchor terminal
- prove existing Web rollout behavior remains unchanged while terminal work is
  added

Modification scope:

- verification only unless a regression is found

Output:

- Web PC baseline acceptance report

Completion criteria:

- `web_pc` tree/list path still passes Lite all-tree acceptance
- legacy fallback still works for non-tree views

### Step 4 - Mini Program Tree/List Pilot

Operation:

- enable one `wx_mini` tree/list pilot behind an explicit runtime flag
- use server-dispatched `actionId`
- fallback to existing legacy path if Lite preview is unavailable

Modification scope:

- mini-program frontend only
- optional mini-program smoke script

Output:

- one guarded `wx_mini` pilot path
- acceptance report

Completion criteria:

- one governed tree/list page renders rows on mini-program viewport
- action dispatch reaches server by `actionId`
- no console or page errors

### Step 5 - Harmony H5 Reuse Check

Operation:

- run the same mobile consumer path with `clientType=harmony_h5`
- verify H5 does not require a separate business contract or renderer semantics

Modification scope:

- verification only unless a platform adapter issue is found

Output:

- Harmony H5 compatibility report

Completion criteria:

- H5 consumes the same Lite contract shape
- no H5-specific business semantic branch exists

### Step 6 - All-Terminal Coverage Matrix

Operation:

- run a matrix that covers `web_pc`, `wx_mini`, and `harmony_h5`
- compare IDs, actions, status semantics, and patch operation set

Modification scope:

- verification scripts
- Makefile

Output:

- all-terminal coverage matrix report

Completion criteria:

- each terminal either passes the same semantic contract or explicitly reports
  an unsupported adapter fallback
- unsupported fallback cannot change business semantics

## 7. Verification Plan

Static gates:

```bash
make verify.unified_page_contract.lite
make verify.frontend.quick.gate
```

All-terminal contract gates to add in the next implementation batch:

```bash
make verify.unified_page_contract.lite.terminal_client_parity
make verify.unified_page_contract.lite.terminal_coverage_matrix
make verify.unified_page_contract.lite.wx_mini_pilot.host
make verify.unified_page_contract.lite.harmony_h5_pilot.host
```

Acceptance must prove:

- `web_pc`, `wx_mini`, and `harmony_h5` share one semantic contract
- `wx_mini` and `harmony_h5` do not change business semantics
- terminal frontends consume schema through store
- no page-level semantic inference exists
- Web rollout remains default-off and unaffected

## 8. Risks

Risk: terminal work becomes parallel contracts.

Control: only allow terminal adaptation differences; semantic signature guard
must fail on ID or action divergence.

Risk: a terminal renderer adds business fallback logic.

Control: frontend guard scans for role, permission, action, or route inference.

Risk: Web runtime is changed while new terminal coverage is introduced.

Control: each terminal implementation batch must keep Web acceptance gates
passing.

## 9. Rollback

Runtime rollback:

```text
do not set non-Web terminal Lite pilot rollout flags
```

Code rollback:

```text
revert the terminal implementation batch commit
```

Contract rollback:

```text
keep using the mainline Lite v2.0 schema without mobile-specific additions
```

## 10. Stop Conditions

Stop immediately if:

- any terminal requires a new business semantic field
- any terminal requires frontend permission or role inference
- any terminal needs to bypass `login -> system.init -> ui.contract`
- Web Lite rollout behavior changes
- backend contract shape becomes unstable
- verification cannot prove cross-client semantic parity
