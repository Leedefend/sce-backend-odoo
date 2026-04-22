# Agent Instructions (Iteration-Driven Mode)

---

## 0. Core Principle

This repository uses a **controlled continuous iteration model**.

The agent MUST:
- Execute tasks one iteration at a time
- Produce verifiable output for each iteration
- Stop automatically when risk or uncertainty is detected

---

## 1. Task-Driven Execution (MANDATORY)

Before any coding:

1. A valid task contract MUST exist under:
   agent_ops/tasks/*.yaml

2. The agent MUST:
   - Load the task contract
   - Read and obey `docs/architecture/execution_baseline_v1.md`
   - Respect allowed / forbidden paths
   - Follow change rules
   - Execute acceptance commands

❌ If no task contract → STOP

### 1.1 Low-Cost Iteration Mode (MANDATORY For Governance Tasks)

For governance, audit, and classification tasks, the agent MUST default to a
low-cost staged execution mode.

Hard rules:

- Complex tasks MUST plan before implementation.
- A single task may execute only one stage at a time.
- Governance tasks SHOULD be split into `scan`, `screen`, and `verify`.
- `scan` may only find candidates and MUST NOT conclude.
- `screen` may only classify scan output and MUST NOT rescan the repository.
- `verify` may only run declared checks and MUST NOT introduce new reasoning.
- Repo-wide scans are forbidden in low-cost mode.
- Template prompts under `agent_ops/templates/prompts/` take priority over ad
  hoc long prompts.
- Cross-stage reasoning is forbidden in low-cost mode.
- Each subtask should run in a new session with short context.
- Low-risk tasks MAY use bounded role-parallel execution only when the task
  contract explicitly declares it.
- Role-parallel execution must keep a single stage, disjoint write scope, and a
  new session per role.
- `executor`, `auditor`, and `reporter` may run in parallel only inside the
  same declared low-risk stage; they must not reopen repository scans or add
  cross-stage reasoning.
- If role boundaries or write boundaries become unclear, the batch MUST fall
  back to single-agent sequential execution.
- Subagents are allowed only when parallel execution is clearly required.
- Default execution should remain single-agent, staged, and short-context.

Low-cost mode should use:

- `docs/ops/codex_low_cost_iteration_policy_v1.md`
- `agent_ops/templates/task_low_cost.yaml`
- `agent_ops/templates/prompts/lead_scan.txt`
- `agent_ops/templates/prompts/lead_screen.txt`
- `agent_ops/templates/prompts/lead_verify.txt`

### 1.2 Lifecycle Usability Battlefield Rule (MANDATORY)

For system usability analysis and enhancement rounds, scheduling MUST treat
backend semantics as the primary battlefield.

Hard rules:

- Usability gaps must be diagnosed against backend-provided semantics first.
- Frontend must stay as a generic semantic consumer and interaction renderer.
- Frontend must NOT branch on concrete business models to patch usability gaps.
- If current backend semantics cannot support required usability behavior, the
  scheduler MUST open a backend semantic-supply task line.
- Frontend-only batches in usability rounds are allowed only when they consume
  existing generic semantics and do not introduce model-specific assumptions.
- Any proposed frontend model-special-case for usability is a stop signal and
  must be redirected to backend semantic correction.

### 1.3 Backend Sub-Layer Decision Gate (MANDATORY)

When lifecycle usability work is on backend battlefield, the scheduler MUST
decide the backend change layer before implementation:

- `business-fact layer`:
  - use when missing data is business truth (state, rule result, ownership,
    amount, permission fact, workflow fact).
- `scene-orchestration layer`:
  - use when missing data is semantic organization for consumption (next-step
    hints, lifecycle labels, entry guidance envelope, scene-ready grouping).

Hard rules:

- The decision must be explicit in task `architecture.reason`.
- Scene/orchestration layer must not fabricate business facts.
- Business-fact layer must not emit frontend-specific view structure.
- If uncertainty exists, scheduler must run a `screen` task first and stop
  direct implementation.

Stop rules:

- Implementing orchestration semantics that depend on missing business truth.
- Implementing business fact changes to patch pure presentation semantics.
- Any frontend special-case proposed before backend sub-layer decision is made.

---

## 2. Iteration Loop (Agent Loop)

Each iteration MUST follow:

1. Plan
   - Identify Layer Target / Module / Reason

2. Implement
   - Only modify allowed paths

3. Verify
   - Run all required `make verify.*` commands

4. Report
   - Generate iteration report:
     - changed files
     - verification result
     - risk summary
     - next suggestion

5. Decide
   - PASS → continue next task
   - PASS_WITH_RISK → STOP
   - FAIL → STOP

---

## 3. Mandatory Preflight (Before Any Edit)

Always run:

- `pwd`
- `git rev-parse --show-toplevel`
- `git branch --show-current`
- `git status --short`

---

## 4. Execution Policy

- Must follow:
  - `docs/ops/codex_execution_allowlist.md`
  - `docs/ops/codex_workspace_execution_rules.md`

- Allowed branches:
  - feat/*
  - feature/*
  - codex/*
  - experiment/*

- Forbidden:
  - main / master / release/* direct modification

### 4.1 Full Authorization Inside Allowed Branches

When all of the following are true:

- current branch matches `feat/*`, `feature/*`, `codex/*`, or `experiment/*`
- a valid task contract exists and is active
- the next step stays inside the active task allowlist and repo execution rules
- no stop condition from Section 6 is triggered

the agent MUST treat low-risk execution authorization as already granted for the
full implementation / verification / report loop of that task.

This means the agent SHOULD NOT pause for redundant confirmation before:

- creating the next low-risk task in the same active objective
- applying low-risk repo changes inside allowed paths
- running required validation and verification commands
- continuing from one PASS batch to the next PASS-eligible batch

This rule does NOT authorize:

- forbidden-path edits
- destructive git operations
- bypassing host/tool approvals enforced outside the repository
- work outside the active task scope
- ignoring stop conditions or failed verification

---

## 5. Architecture Guard (MANDATORY)

Before coding:

- Read:
  - `ARCHITECTURE_GUARD.md`
  - `docs/architecture/ai_development_guard.md`

Must declare:

- Layer Target
- Module
- Module Ownership
- Kernel or Scenario
- Reason

Must also follow:

- `docs/architecture/execution_baseline_v1.md`
- `docs/architecture/platform_kernel_boundary_freeze_v1.md`
- `agent_ops/policies/architecture_reference_policy.yaml`

---

## 6. Risk & Stop Conditions (CRITICAL)

The agent MUST STOP immediately if:

1. Any forbidden path is modified
2. Any of the following files are touched:
   - security/**
   - record_rules/**
   - ir.model.access.csv
   - *payment*
   - *settlement*
   - *account*
   - __manifest__.py
3. Any `make verify.*` fails
4. Contract structure changes (field rename/remove)
5. Diff exceeds safe size threshold
6. Task cannot be completed with certainty
7. Planned kernel alignment would absorb industry-specific semantics

### 6.1 Narrow Exception For Dedicated Permission-Governance Batches

The generic stop condition for `security/**` remains the default and MUST still
trigger an immediate stop in ordinary batches.

Exception:

The agent MAY implement controlled `security/**` changes only when all of the
following are simultaneously true:

- an active task contract explicitly declares a dedicated
  `permission-governance` or equivalent high-risk authority-path objective
- the task allowlist explicitly includes the exact `security/**` paths being
  changed
- the user has explicitly authorized proceeding with that high-risk batch
- the planned changes are additive and scoped to the approved authority-path
  objective
- `record_rules/**`, `ir.model.access.csv`, `__manifest__.py`, and financial
  domains remain outside scope unless separately authorized by a new task line

When this exception is used:

- the batch MUST be treated as high-risk
- verification and reporting MUST be completed in the same batch
- if uncertainty remains about implied groups, ACL impact, or platform-level
  authority leakage, the agent MUST stop immediately

### 6.2 Narrow Exception For Dedicated Post Master-Data ACL Batches

The generic stop condition for `ir.model.access.csv` remains the default and
MUST still trigger an immediate stop in ordinary batches.

Exception:

The agent MAY implement controlled `ir.model.access.csv` changes only when all
of the following are simultaneously true:

- an active task contract explicitly declares a dedicated platform master-data
  objective for the customer/workbook `岗位` carrier
- the task allowlist explicitly includes the exact
  `addons/smart_enterprise_base/security/ir.model.access.csv` path
- the user has explicitly authorized proceeding with that high-risk batch
- the planned changes are additive and scoped to the new post master-data model
  plus its user-carrier relation
- `record_rules/**`, `__manifest__.py`, and financial domains remain outside
  scope unless separately authorized by a new task line

When this exception is used:

- the batch MUST be treated as high-risk
- verification and reporting MUST be completed in the same batch
- if uncertainty remains about model ownership, access scope, or platform-level
  leakage, the agent MUST stop immediately

### 6.3 Narrow Exception For Dedicated Enterprise-Maintenance Ownership ACL Batches

The generic stop condition for `ir.model.access.csv` remains the default and
MUST still trigger an immediate stop in ordinary batches.

Exception:

The agent MAY implement controlled `ir.model.access.csv` changes only when all
of the following are simultaneously true:

- an active task contract explicitly declares a dedicated customer-delivery
  ownership objective for enterprise maintenance
- the task allowlist explicitly includes the exact
  `addons/smart_enterprise_base/security/ir.model.access.csv` path
- the user has explicitly authorized proceeding with that high-risk batch
- the planned changes are additive and scoped only to enterprise company,
  department, and post maintenance ownership
- `res.users` ownership, `record_rules/**`, `__manifest__.py`, and financial
  domains remain outside scope unless separately authorized by a new task line

When this exception is used:

- the batch MUST be treated as high-risk
- verification and reporting MUST be completed in the same batch
- if uncertainty remains about authority inheritance, ACL scope, or
  platform-admin leakage, the agent MUST stop immediately

### 6.4 Narrow Exception For Dedicated Enterprise User-Maintenance Ownership ACL Batches

The generic stop condition for `ir.model.access.csv` remains the default and
MUST still trigger an immediate stop in ordinary batches.

Exception:

The agent MAY implement controlled `ir.model.access.csv` changes only when all
of the following are simultaneously true:

- an active task contract explicitly declares a dedicated customer-delivery
  ownership objective for enterprise user maintenance
- the task allowlist explicitly includes the exact
  `addons/smart_enterprise_base/security/ir.model.access.csv` path
- the user has explicitly authorized proceeding with that high-risk batch
- the planned changes are additive and scoped only to enterprise user
  maintenance ownership via the existing business-admin authority path
- record rules, manifest changes, financial domains, and platform governance
  fields remain outside scope unless separately authorized by a new task line

When this exception is used:

- the batch MUST be treated as high-risk
- verification and reporting MUST be completed in the same batch
- if uncertainty remains about `res.users` exposure, ACL scope, or
  platform-admin leakage, the agent MUST stop immediately

### 6.5 Narrow Exception For Dedicated Bootstrap Module Migration Batches

The generic stop condition for `__manifest__.py` remains the default and MUST
still trigger an immediate stop in ordinary batches.

Exception:

The agent MAY implement controlled `__manifest__.py` changes only when all of
the following are simultaneously true:

- an active task contract explicitly declares a dedicated taxonomy-migration or
  equivalent high-risk objective for
  `smart_construction_bootstrap -> smart_platform_bootstrap`
- the task allowlist explicitly includes the exact manifest paths and any
  directly related bootstrap reference files being changed
- the user has explicitly authorized proceeding with that high-risk batch
- the planned changes are additive and scoped only to:
  - creating the new neutral bootstrap module
  - preserving `smart_construction_bootstrap` as a compatibility shim
  - migrating bootstrap dependency/install/verify/doc references in the frozen
    transition order
- `security/**`, `record_rules/**`, `ir.model.access.csv`, and financial
  domains remain outside scope unless separately authorized by a new task line

When this exception is used:

- the batch MUST be treated as high-risk
- verification and reporting MUST be completed in the same batch
- if uncertainty remains about dependency direction, upgrade/install safety, or
  compatibility-shim removal conditions, the agent MUST stop immediately

### 6.6 Narrow Exception For Dedicated Fresh-Runtime Install-Order Recovery ACL Batches

The generic stop conditions for `security/**` and `ir.model.access.csv` remain
the default and MUST still trigger an immediate stop in ordinary batches.

Exception:

The agent MAY implement controlled `security/**` and `ir.model.access.csv`
changes only when all of the following are simultaneously true:

- an active task contract explicitly declares a dedicated fresh-runtime or
  install-order recovery objective
- the task allowlist explicitly includes the exact
  `addons/smart_enterprise_base/security/ir.model.access.csv`,
  `addons/smart_enterprise_base/views/menu_enterprise_base.xml`,
  `addons/smart_construction_core/security/ir.model.access.csv`, and
  `addons/smart_construction_core/security/action_groups_patch.xml` paths
- the user has explicitly authorized proceeding with that high-risk batch
- the planned changes only remove pre-core references from
  `smart_enterprise_base` and re-apply the equivalent business-full grants from
  `smart_construction_core` after its groups exist
- `record_rules/**`, `__manifest__.py`, frontend paths, and financial domains
  remain outside scope unless separately authorized by a new task line

When this exception is used:

- the batch MUST be treated as high-risk
- verification and reporting MUST be completed in the same batch
- if uncertainty remains about final authority ownership, install order, or
  platform-admin leakage, the agent MUST stop immediately

### 6.7 Narrow Exception For Dedicated Customer Seed Materialization Batches

The generic stop condition for `__manifest__.py` remains the default and MUST
still trigger an immediate stop in ordinary batches.

Exception:

The agent MAY implement controlled `__manifest__.py` and module data-load
changes only when all of the following are simultaneously true:

- an active task contract explicitly declares a dedicated customer bootstrap or
  install-time seed materialization objective
- the task allowlist explicitly includes the exact
  `addons/smart_construction_custom/__manifest__.py`,
  `addons/smart_construction_custom/data/**`, and any directly related
  customer-module documentation paths being changed
- the user has explicitly authorized proceeding with that high-risk batch
- the planned changes are additive and scoped only to turning customer runtime
  bootstrap facts into install-time module data for reproducible fresh installs
- `security/**`, `record_rules/**`, `ir.model.access.csv`, frontend paths, and
  financial domains remain outside scope unless separately authorized by a new
  task line

When this exception is used:

- the batch MUST be treated as high-risk
- verification and reporting MUST be completed in the same batch
- if uncertainty remains about install order, duplicate ownership, or customer
  seed reproducibility, the agent MUST stop immediately

### 6.8 Narrow Exception For Dedicated Payment-Settlement Orchestration Boundary-Recovery Batches

The generic stop conditions for `*payment*` and `*settlement*` remain the
default and MUST still trigger an immediate stop in ordinary batches.

Exception:

The agent MAY implement controlled `*payment*` and `*settlement*` related file
changes only when all of the following are simultaneously true:

- an active task contract explicitly declares a dedicated
  orchestration-boundary recovery objective for payment/settlement slices
- the task allowlist explicitly includes the exact target paths (for example
  `addons/smart_core/orchestration/payment_slice_contract_orchestrator.py` and
  `addons/smart_core/orchestration/settlement_slice_contract_orchestrator.py`)
- the user has explicitly authorized proceeding with that high-risk batch
- the planned changes are additive and scoped only to dependency-ownership
  migration (protocol adapter / extension-provider wiring), without changing
  payment or settlement business/financial semantics
- `security/**`, `record_rules/**`, `ir.model.access.csv`, `__manifest__.py`,
  and accounting/financial rule semantics remain outside scope unless
  separately authorized by a new task line

When this exception is used:

- the batch MUST be treated as high-risk
- verification and reporting MUST be completed in the same batch
- if uncertainty remains about financial semantics, authority leakage, or
  runtime safety, the agent MUST stop immediately

### 6.10 Narrow Exception For Dedicated Smart Core Capability-Registry Startup-Warmup Batches

The generic stop condition for `__manifest__.py` remains the default and MUST
still trigger an immediate stop in ordinary batches.

Exception:

The agent MAY implement controlled `__manifest__.py` changes only when all of
the following are simultaneously true:

- an active task contract explicitly declares a dedicated startup-warmup
  objective for `smart_core` capability-registry materialization
- the task allowlist explicitly includes the exact
  `addons/smart_core/__manifest__.py` path plus only the directly related
  warmup hook/runtime files needed to seed the existing capability-registry
  artifact
- the user has explicitly authorized proceeding with that high-risk batch
- the planned changes are additive and scoped only to:
  - adding the minimal startup hook declaration for `smart_core`
  - wiring one bounded warmup path that seeds the existing capability-registry
    artifact before ordinary `system.init` traffic
  - restarting runtime and verifying the first real request no longer uses
    fallback build
- `security/**`, `record_rules/**`, `ir.model.access.csv`, frontend paths,
  persistence redesign, payment/settlement/account domains, and unrelated
  manifest or dependency changes remain outside scope unless separately
  authorized by a new task line

When this exception is used:

- the batch MUST be treated as high-risk
- verification and reporting MUST be completed in the same batch
- if uncertainty remains about module lifecycle safety, startup ownership, or
  scope expansion beyond bounded warmup behavior, the agent MUST stop
  immediately

### 6.11 Narrow Exception For Dedicated Payment-Entry Provider-Handoff Batches

The generic stop condition for `*payment*` remains the default and MUST still
trigger an immediate stop in ordinary batches.

Exception:

The agent MAY implement controlled `*payment*` path changes only when all of
the following are simultaneously true:

- an active task contract explicitly declares a dedicated payment-entry
  provider-handoff objective
- the task allowlist explicitly includes only these exact implementation paths:
  - `addons/smart_construction_scene/providers/payment_entry_workbench_provider.py`
  - `addons/smart_construction_scene/tests/test_action_only_scene_semantic_supply.py`
- the task allowlist may additionally include only payment-entry-specific
  task/doc/log governance paths needed for the same batch
- the user has explicitly authorized proceeding with that high-risk batch
- the planned changes are additive and scoped only to:
  - exposing `delivery_handoff_v1` from the payment-entry scene provider
  - updating the semantic-supply unittest assertions for that provider handoff
  - synchronizing the matching task/doc/log artifacts
- `payment_approval`, `addons/smart_construction_core/**`, security,
  record-rule, manifest, settlement, account, runtime-contract, and payment
  business-rule changes remain outside scope unless separately authorized by a
  new task line

When this exception is used:

- the batch MUST be treated as high-risk
- verification and reporting MUST be completed in the same batch
- if uncertainty remains about provider-only scope, implied deep payment-path
  changes, or business-semantic leakage beyond the handoff surface, the agent
  MUST stop immediately

### 6.9 Narrow Exception For Dedicated No-Contract Payment Business-Continuity Batches

The generic stop condition for `*payment*` remains the default and MUST still
trigger an immediate stop in ordinary batches.

Exception:

The agent MAY implement controlled no-contract payment business-continuity
changes only when all of the following are simultaneously true:

- an active task contract explicitly declares a dedicated no-contract payment
  business-continuity objective
- the task allowlist explicitly includes only these exact payment paths:
  - `addons/smart_construction_core/models/core/payment_request.py`
  - `addons/smart_construction_core/handlers/payment_request_available_actions.py`
- the user has explicitly authorized proceeding with that high-risk batch
- the planned changes are scoped only to allowing `payment.request` submit
  without `contract_id` when no `settlement_id` is selected for daily or
  non-contract outflows
- selected-contract checks, canceled-contract checks, selected-settlement
  consistency checks, settlement amount checks, funding gates, attachment
  checks, project lifecycle checks, data-validator checks, tier-validation,
  audit/evidence behavior, ACLs, accounting, ledgers, manifests, and frontend
  behavior remain outside scope unless separately authorized by a new task line
- the implementation keeps `payment.request.available_actions` prechecks
  consistent with `payment.request.action_submit`

When this exception is used:

- the batch MUST be treated as high-risk
- verification and reporting MUST be completed in the same batch
- verification MUST include rollback-only no-contract submit, selected-contract
  submit, selected-settlement consistency, and imported business continuity
  checks
- if uncertainty remains about financial semantics, settlement semantics,
  approval safety, or account/ledger impact, the agent MUST stop immediately

---

## 7. Allowed Change Rules

- Prefer additive changes only
- Do NOT modify:
  - core business facts
  - financial semantics
  - ACL / record rules

---

## 8. Reporting Requirement

Each iteration MUST produce:

- Summary of change
- Verification result
- Risk analysis
- Rollback suggestion
- Next iteration suggestion

### 8.1 Continuous Iteration Reporting Semantics

When the repository is already in continuous-iteration mode and no stop condition
has been triggered, iteration reporting MUST be phrased as a progress checkpoint,
not as an end-of-work close-out.

The agent MUST NOT use reporting that implies:

- the work has paused
- the batch chain has ended
- the next step requires renewed confirmation

unless a real stop condition has been triggered.

If the current batch is `PASS` and the next batch is still eligible, the report
MUST make it clear that execution is continuing.

### 8.2 Terminal Close-Out Is Reserved For Real Stop Conditions

In continuous-iteration mode, a terminal close-out message is only valid when at
least one of the following is true:

- a real stop condition from Section 6 has been triggered
- the user has explicitly redirected or paused the active objective
- the active task line has been fully completed and no eligible next batch remains

Otherwise, the agent MUST remain in working-mode progress reporting and continue
execution instead of signaling a terminal end state.

### 8.3 Working-Mode Checkpoints Are The Default During Active Chains

During an active continuous-iteration chain, ordinary `PASS` checkpoints MUST be
communicated as in-flight working-mode progress updates, not as summary-style
close-out messages.

If the next eligible batch is already known and no stop condition exists, the
agent MUST prefer ongoing progress reporting over checkpoint summaries that feel
like a turn has ended.

### 8.4 Non-Blocking Commentary Must Not Create Waiting State

During continuous iteration, non-blocking questions, judgments, or diagnostic
statements MUST NOT move the agent into a waiting state by default.

If the information needed for the next step can be derived from repository rules,
existing context, or the active task chain, the agent MUST continue immediately
instead of waiting for another user prompt.

Only genuinely blocking questions may create a waiting state.

### 8.5 Questions Do Not Suspend The Active Loop

In continuous iteration, a question or midstream judgment does not suspend the
active execution loop by itself.

If the agent emits a question for clarity, but the answer is not strictly
required to choose the next low-risk, rule-compliant step, the agent MUST:

- treat the question as non-blocking commentary
- derive the next action from the active objective, task chain, and repo rules
- continue implementation / verification / reporting without waiting

The agent MUST NOT convert its own non-blocking question into an implicit pause.

### 8.6 Non-Blocking Wait Timeout Must Auto-Recover

If the agent ever drifts into a non-blocking wait state during continuous
iteration, that wait MUST be treated as invalid once it exceeds 5 seconds.

After 5 seconds, the agent MUST automatically trigger one recovery action:

- re-check the active task chain and repo execution rules
- resolve the next eligible low-risk step
- resume implementation / verification / reporting without waiting for another
  user prompt

This auto-recovery rule applies only when no real stop condition has been
triggered.

### 8.7 The Next Execution Opportunity Is The Recovery Trigger

If the agent cannot literally emit output during the invalid wait interval, the
next available execution opportunity MUST be treated as the timeout recovery
trigger.

This means that on the next user message, tool step, or execution checkpoint
after such a timeout, the agent MUST behave as if recovery has already fired and
continue immediately.

The agent MUST NOT spend that next execution opportunity on explanation-only
commentary before restarting execution.

### 8.8 Resume-First Behavior Is Mandatory

After a timeout recovery trigger, the first action MUST be one of the following:

- create or activate the next valid low-risk task contract
- run the required preflight / validation for that task
- start the concrete implementation step for that task

Pure explanation, justification, or retrospective analysis may follow, but they
MUST NOT replace the resume-first action.

### 8.9 User-Visible Reply Mode Must Stay Non-Terminal

While a continuous-iteration chain is still active and no real stop condition
has been triggered, user-visible replies MUST stay in working-mode progress
form.

The agent MUST NOT use a terminal-style final close-out as an ordinary checkpoint
while execution is continuing.

Terminal user-visible close-out is reserved for:

- real stop conditions
- explicit user pause / redirect
- genuine completion of the active task line

### 8.10 Active Chains Must Use Working-Mode Update Channel

While a continuous-iteration chain is active, ordinary user-visible updates MUST
use the working-mode progress channel rather than a terminal close-out channel.

This rule applies to every non-stop-condition checkpoint, including:

- PASS checkpoints
- timeout-recovery checkpoints
- midstream governance corrections
- in-progress product iteration updates

The agent MUST treat terminal close-out channel selection as unavailable until a
real stop condition or genuine completion exists.

### 8.11 Role-Split Operating Model Is Mandatory

During continuous iteration, the agent MUST conceptually operate in three
sequential roles, even if one agent performs all three:

- `executor`: starts and advances the next eligible low-risk batch
- `reporter`: emits working-mode progress updates about that active batch
- `stop-guard`: decides whether a real stop condition exists

The execution order is fixed:

1. `stop-guard` checks whether a real stop condition is active
2. if no stop condition exists, `executor` must continue the next eligible batch
3. only then may `reporter` emit the user-visible working-mode update

`reporter` MUST NOT override `executor`, and terminal close-out authority is
reserved to `stop-guard`.

### 8.12 User Stop-Callout Must Trigger Immediate Recovery

If the user explicitly says that the agent has stopped, paused, or failed to
continue during an active continuous-iteration chain, that message itself MUST
be treated as an immediate recovery trigger.

On that turn:

- `stop-guard` checks whether a real stop condition exists
- if none exists, `executor` MUST start a concrete next batch immediately
- only after that may `reporter` explain what failed in the previous behavior

The agent MUST NOT answer a stop-callout with explanation-only commentary.

---

## 9. Continuous Iteration Mode

The agent MAY continue automatically ONLY IF:

- Last iteration result = PASS
- No risk triggered
- Next task is low-risk

Otherwise → STOP

### 9.1 Default Continue Rule

When the repository is already in continuous-iteration mode, the agent MUST treat
"continue automatically" as the default behavior rather than waiting for another
explicit user confirmation after each PASS batch.

This default applies only when all of the following remain true:

- the current batch result is `PASS`
- no stop condition from Section 6 is triggered
- the next batch stays within a clearly declared low-risk scope
- the next batch still follows the active product or governance objective

The agent MUST NOT pause only to ask whether it should continue if the above
conditions are satisfied.

The agent MUST ALSO avoid presenting a normal `PASS` checkpoint as if it were a
terminal summary. In continuous-iteration mode, wording that sounds like a
finished stop point is prohibited unless a real stop condition exists.

### 9.2 Self-Directed Next-Step Resolution Is Mandatory

When a continuous-iteration batch has passed and no stop condition has fired,
the agent MUST resolve the next executable low-risk step by consulting, in this
order:

1. the active task objective and acceptance rules
2. repository execution rules and architecture guards
3. the current changed-state / verification state
4. the latest completed-step and next-step entry in the delivery context log

If these sources are sufficient to determine the next step, the agent MUST
continue automatically and MUST NOT wait for another user prompt.

### 9.3 Five-Second Recovery Trigger

During continuous iteration, if no real stop condition exists and the agent has
entered an invalid non-blocking wait for more than 5 seconds, the agent MUST
immediately:

1. re-anchor on the active task objective
2. consult the execution rules and latest delivery-log `next_step`
3. launch the next eligible low-risk batch

The agent MUST treat this recovery trigger as mandatory behavior, not as an
optional best practice.

### 9.4 Recovery Must Start The Next Batch Before Analysis

When timeout recovery fires, the agent MUST launch the next eligible low-risk
batch before using the turn to explain why the recovery was necessary.

If the next batch can be determined from:

- the active objective
- the task chain
- execution rules
- the latest delivery-log `next_step`

then the agent MUST start that batch first and only then provide progress
commentary.

### 9.5 Visible Progress Updates Must Match Internal Execution State

If internal execution is continuing under the continuous-iteration rules, the
visible reply mode MUST also communicate an in-progress state.

The agent MUST NOT let visible communication imply a stop when the internal
policy requires continued execution.

### 9.6 Stop-Guard Owns Terminal Authority

Within the role-split operating model, only `stop-guard` may authorize a
terminal close-out.

If `executor` still has an eligible low-risk batch and `stop-guard` has not
detected a real stop condition, `reporter` MUST stay in working-mode progress
updates and MUST NOT emit a terminal end-state.

### 9.7 Stop-Callout Turn Must Begin With Execution

When the user reports that the agent has effectively stopped during continuous
iteration, the recovery turn MUST begin with a concrete execution action such as:

- creating the next governance/product batch
- validating the active recovery task
- launching the next low-risk implementation step

Analysis or apology may follow, but only after execution has restarted.
session close-out counts as an execution pause and must be avoided.

### 9.2 Stop Rules Still Override Continuous Iteration

Continuous iteration improves execution efficiency, but it never overrides:

- forbidden path boundaries
- acceptance and verification failures
- contract uncertainty
- risk escalation
- architecture guard failures

If any stop condition is triggered, the agent MUST stop immediately even inside
continuous-iteration mode.

---

## 10. Priority Strategy

Always prioritize:

1. User-visible outcome
2. Read-only extension
3. Verification completeness
4. Execution baseline compliance

Avoid:

- premature architecture abstraction
- cross-module refactor
- schema change
- automatic migration of industry semantics into platform kernel

---
