# Batch B File-Level Change List v1

## Scope Intent

Transition system from “structure-valid” to “runtime-valid and business-usable” with audit-driven, file-level execution.

## Phase 1 — Runtime Recovery (P0)

### Target Files

- `scripts/verify/scene_legacy_auth_smoke.py`
- `scripts/verify/scene_legacy_auth_smoke_semantic_verify.py`
- `Makefile` (short verify targets only)

### Actions

1. Keep unreachable as strict FAIL by default.
2. Keep fallback only behind explicit env switch.
3. Ensure semantic smoke target is callable via make.

### Gate Commands

- `python3 agent_ops/scripts/validate_task.py <task.yaml>`
- `make verify.scene.legacy_auth.smoke.semantic`
- `make verify.scene.legacy_contract.guard`

### Stop Conditions

- Any fallback behavior drifting to implicit PASS.
- Any runtime unreachable case not failing in strict mode.

---

## Phase 2 — Business Foundation Closure (P1)

### 2.1 Permission Minimal Convergence

#### Target Files

- `addons/smart_construction_core/security/ir.model.access.csv`
- `addons/smart_construction_core/security/sc_record_rules.xml`

#### Actions

1. Deduplicate `project.budget` ACL overlap.
2. Add minimal rules for:
   - `project.project` member visibility
   - `project.task` member/assignee visibility
   - `project.budget` project-member visibility
   - `project.cost.ledger` project-member visibility

#### Gate Commands

- `python3 agent_ops/scripts/validate_task.py <task.yaml>`
- `make verify.scene.legacy_auth.smoke.semantic`
- `make verify.scene.legacy_contract.guard`

#### Stop Conditions

- ACL/rule scope expands beyond minimal closure.
- Financial/business semantics changed.

### 2.2 Master Data Seed Minimalization

#### Target Files

- `addons/smart_construction_custom/__manifest__.py`
- `addons/smart_construction_custom/data/customer_project_dictionary_seed.xml`

#### Actions

1. Add install-time non-transactional dictionary seed.
2. Keep seed domain limited to baseline dictionaries.

#### Gate Commands

- `python3 agent_ops/scripts/validate_task.py <task.yaml>`
- `make verify.test_seed_dependency.guard`

#### Stop Conditions

- Seed includes payment/settlement/accounting transactions.
- Manifest dependency direction is changed.

### 2.3 Menu/Action/View Runtime Evidence

#### Target Files

- `docs/audit/native/native_post_install_business_entry_smoke_evidence_v1.md`

#### Actions

1. Collect static entry action evidence for critical business entry points.
2. Record short-chain verify outputs.

#### Gate Commands

- `make verify.scene.legacy_contract.guard`
- `make verify.test_seed_dependency.guard`

---

## Phase 3 — Business Closure Delivery (P2/Delivery)

### Target Files (Evidence & Planning)

- `docs/audit/native/native_foundation_acceptance_summary_v1.md`
- `docs/audit/native/native_next_stage_roadmap_v1.md`

### Actions

1. Consolidate closure status across project/task/cost/payment/settlement flow readiness.
2. Publish next-stage targeted regression checklist.

### Gate Commands

- `python3 agent_ops/scripts/validate_task.py <task.yaml>`

### Stop Conditions

- Any unresolved P0/P1 is marked as complete.
- Any high-risk lane is executed without dedicated contract.

---

## Fixed Debug Order (Mandatory)

`角色 -> 能力组 -> ACL -> record rule`

---

## Execution Rhythm

1. One task contract per batch.
2. One batch one objective.
3. Validate before closeout.
4. Report changed files / verify / risk / rollback / next step.
