# sc_demo Replay Adaptation Matrix v1

Status: DRAFT_READY

Task: `ITER-2026-04-24-SC-DEMO-REPLAY-ADAPTATION-MATRIX-001`

## Scope

This document does not execute any replay write. It classifies the existing
`fresh_db replay` lanes and defines how they should be adapted into `sc_demo`
without creating a parallel ad-hoc importer chain.

The goal is:

- reuse the existing full historical rebuild lane design;
- keep `action = native source of truth` style discipline for migration too;
- treat `sc_demo` as a validation replay environment, not as a shortcut import
  bucket;
- produce one future one-click replay contract for deployment and local rebuild.

## Current Facts

The repository already contains a complete replay backbone:

- operation contract:
  - `docs/migration_alignment/fresh_db_operation_contract_v1.md`
- lane manifest:
  - `artifacts/migration/fresh_db_replay_manifest_v1.json`
- dry-run validator:
  - `scripts/migration/fresh_db_replay_runner_dry_run.py`

The repository also already contains carrier/staging support. The clearest
example is:

- `addons/smart_construction_core/models/support/project_member_staging.py`
  - model: `sc.project.member.staging`

This means the correct direction is not to add more isolated import scripts, but
to adapt the existing replay contract into `sc_demo`.

## Environment Positioning

`sc_demo` is the validation replay environment.

It is suitable for:

- replay payload validation;
- bounded create-only historical replay;
- carrier/staging validation;
- rollback target generation;
- repeatability checks before server deployment.

It is not suitable for:

- high-risk accounting settlement replay;
- unbounded update-mode replay;
- silently diverging from the canonical replay chain defined for
  `sc_migration_fresh`.

## Adaptation Classes

- `direct-reusable`
  - the lane semantics are already safe for `sc_demo`;
  - the current blocker is mostly hard-coded DB/path guard;
  - target model is already the intended runtime model.

- `carrier-first`
  - the lane is safe only because it lands on a carrier/staging model first;
  - promotion into runtime business facts remains explicitly out of scope.

- `fresh-db-only`
  - the lane design exists, but the current implementation is incomplete for a
    reusable `sc_demo` contract;
  - additional adapter/write implementation is still required.

- `blocked-high-risk`
  - excluded from `sc_demo` replay contract;
  - requires a separate high-risk task and explicit approval.

## Lane Matrix

| Lane | Target Model | Current Manifest Status | sc_demo Class | Decision |
| --- | --- | --- | --- | --- |
| `partner_l4_anchor_completed` | `res.partner` | `fresh_replay_executed` | `direct-reusable` | Safe create-only identity anchor lane. Needs DB/path guard generalization and `sc_demo` artifact output contract. |
| `project_anchor_completed` | `project.project` | `fresh_replay_executed` | `direct-reusable` | Safe create-only anchor lane. Needs DB/path guard generalization and `sc_demo` artifact output contract. |
| `project_member_neutral_completed` | `sc.project.member.staging` | `fresh_replay_executed` | `carrier-first` | Already uses neutral carrier model and forbids writes to `project.responsibility`. Suitable for `sc_demo` only as carrier replay. |
| `contract_header_completed_1332` | `construction.contract` | `fresh_replay_executed` | `direct-reusable` | Safe header-only create lane after partner/project prerequisites. Must stay line-free and accounting-free. |
| `contract_partner_source_12_anchor_design` | `res.partner` | `fresh_replay_executed` | `fresh-db-only` | Manifest lane exists, but document reason says no standalone reusable DB write script exists yet. Not ready for `sc_demo` replay contract. |
| `receipt_header_pending` | `payment.request` | `fresh_replay_executed` | `direct-reusable` | Safe only as draft `receive` requests with zero ledger/settlement/account.move side effects. Suitable for bounded `sc_demo` replay. |
| `payment_settlement_accounting` | `payment/settlement/accounting` | `excluded_high_risk` | `blocked-high-risk` | Must remain outside `sc_demo` replay contract. |

## Why These Classifications Hold

### 1. `partner_l4_anchor_completed`

Evidence:

- `scripts/migration/fresh_db_partner_l4_replay_write.py`
- hard guard: `env.cr.dbname != "sc_migration_fresh"`
- safe create-only identity check on:
  - `legacy_partner_source`
  - `legacy_partner_id`

Implication:

- this is not blocked by business semantics;
- it is blocked by environment hard-coding.

### 2. `project_anchor_completed`

Evidence:

- `scripts/migration/fresh_db_project_anchor_replay_write.py`
- hard guard: `env.cr.dbname != "sc_migration_fresh"`
- safe create-only identity check on:
  - `legacy_project_id`

Implication:

- this is a direct `sc_demo` replay candidate once environment/path guards are
  parameterized.

### 3. `project_member_neutral_completed`

Evidence:

- `scripts/migration/fresh_db_project_member_neutral_replay_write.py`
- target model:
  - `sc.project.member.staging`
- forbidden runtime side effect:
  - `project.responsibility`
- visibility snapshot before/after write

Implication:

- this lane is explicitly safe because it replays into a carrier;
- therefore it should be adapted into `sc_demo` only as a carrier-first lane,
  not promoted into responsibility/runtime ownership in the same contract.

### 4. `contract_header_completed_1332`

Evidence:

- `scripts/migration/fresh_db_contract_remaining_write.py`
- header-only safe field set
- explicit post-checks:
  - no duplicate identity
  - no contract lines
  - no payment rows
  - no settlement rows
  - no accounting rows

Implication:

- this lane is suitable for `sc_demo` as a bounded header replay after anchor
  prerequisites are satisfied.

### 5. `contract_partner_source_12_anchor_design`

Evidence:

- manifest reason:
  - `no DB write script exists yet; must be implemented before fresh replay`

Implication:

- this lane must not be placed into the first `sc_demo replay contract`;
- it remains a blocker lane until its standalone replay implementation is
  completed.

### 6. `receipt_header_pending`

Evidence:

- `scripts/migration/fresh_db_receipt_core_write.py`
- bounded target:
  - `payment.request`
  - forced `type = receive`
- explicit post-checks:
  - no `payment.ledger`
  - no `sc.settlement.order`
  - no `account.move`

Implication:

- this lane is suitable for `sc_demo` replay, but only in the current bounded
  `draft receive request` mode.

### 7. `payment_settlement_accounting`

Evidence:

- manifest status:
  - `excluded_high_risk`

Implication:

- this stays outside the `sc_demo replay contract`.

## Required Adapter Work Before `sc_demo` Replay Contract

The first adaptation batch should not rewrite lane semantics. It should only
generalize execution guards and artifact plumbing.

Required changes:

1. Replace hard-coded DB guards like:
   - `env.cr.dbname == "sc_migration_fresh"`
   with an allowlisted replay environment contract such as:
   - `{"sc_migration_fresh", "sc_demo"}`

2. Replace hard-coded artifact roots like:
   - `/mnt/artifacts/...`
   with a replay artifact root contract that works for:
   - local workspace
   - dev container
   - deployment server

3. Introduce one canonical `sc_demo replay contract` document instead of
   creating additional importer scripts.

4. Keep `project_member_neutral_completed` explicitly carrier-only in the first
   `sc_demo` contract.

5. Keep `payment_settlement_accounting` excluded.

## Recommended First `sc_demo Replay Contract`

The first executable `sc_demo` replay contract should include only:

1. `partner_l4_anchor_completed`
2. `project_anchor_completed`
3. `project_member_neutral_completed`
4. `contract_header_completed_1332`
5. `receipt_header_pending`

Explicitly excluded:

1. `contract_partner_source_12_anchor_design`
2. `payment_settlement_accounting`

## Proposed Execution Order For `sc_demo`

After database/module prerequisites are satisfied:

1. replay partner anchors
2. replay project anchors
3. replay project-member neutral carrier rows
4. replay contract header rows
5. replay receipt core rows
6. refresh manifest / replay result evidence

## What Should Not Be Expanded Further

The temporary helper chain that replays only historical users into `sc_demo`
must not become the primary migration path.

Reason:

- it bypasses the full replay lane model;
- it does not express dependency order;
- it does not encode carrier-first boundaries;
- it would create a second migration architecture.

It can remain a convenience helper, but it must not replace the canonical replay
contract.

## Next Batch

The next implementation batch should be:

`Batch-Migration-sc_demo-Replay-Adapter-A`

Scope:

- parameterize `fresh_db` hard-coded guards for `sc_demo`;
- formalize artifact root contract;
- produce one executable `sc_demo replay contract` for the five allowed lanes;
- keep all high-risk and incomplete lanes excluded.
