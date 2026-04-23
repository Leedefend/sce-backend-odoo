# Migration Data Layer Policy v1

Status: PASS

Task: `ITER-2026-04-15-MIGRATION-REPLAY-MANIFEST-DATA-LAYER-POLICY`

## Principle

The migration is responsible for carrying **provable business facts** from the
legacy system into the new system. It is not responsible for completing or
inventing missing legacy data.

Old-system incompleteness is a source fact. It must be classified, discarded, or
held with evidence. It must not be patched by fabricating business truth.

## Layer Model

### L0 Identity Anchors

Purpose:

- Provide stable references for downstream facts.

Examples:

- `res.partner` legacy identity.
- `project.project.legacy_project_id`.
- user/member identity carriers.

Policy:

- Must be deterministic and idempotent.
- Missing anchors block downstream facts.
- Do not fabricate anchors to satisfy required foreign keys.

### L1 Core Business Facts

Purpose:

- Carry primary business truth.

Examples:

- project core record;
- partner core record;
- contract header;
- neutral project-member staging fact.

Policy:

- Migrate only when source evidence and target constraints agree.
- Required target fields may use technical defaults only when the default is
  already part of the new system rule.
- If old data cannot prove the fact, block or discard it.

### L2 Business Auxiliary Information

Purpose:

- Preserve useful context that is not required to operate the core fact.

Examples:

- contact names and phones;
- address;
- remarks;
- attachment references;
- legacy status text;
- source evidence notes.

Policy:

- Migrate opportunistically.
- If the new system does not require the field, leave it empty when legacy data
  is missing or dirty.
- Do not delay L1 core facts because optional L2 fields are incomplete.

### L3 Detail, Derived, And Weak Historical Facts

Purpose:

- Carry detail rows or reconstructed historical context after the header facts
  are stable.

Examples:

- contract lines;
- receipt details;
- derived workflow history;
- weak status transitions.

Policy:

- Open only after L0/L1 aggregate closure.
- Do not infer details from summary amounts unless a deterministic mapping rule
  exists.
- Derived/weak facts may be held rather than migrated.

### L4 High-Risk Financial And Authority Facts

Purpose:

- Handle facts with financial, settlement, accounting, payment, ACL, or
  authority impact.

Examples:

- payment;
- settlement;
- accounting;
- access control and record rules.

Policy:

- Always separate dedicated task contract.
- Never included in default one-click replay.
- Requires explicit high-risk authorization, dedicated verification, and
  rollback plan.

## Missing And Garbage Data Policy

- New system does not require the field: leave empty.
- Legacy deletion flag: discard ledger by default.
- Source anchor missing: hold or discard; do not synthesize anchor records.
- Ambiguous identity: hold until deterministic rule exists.
- Direction cannot be inferred: policy hold.
- Garbage data: discard with evidence.
- Financial/authority ambiguity: stop and open high-risk governance line.

## Batch Strategy

- L0 anchor lanes: grouped by distinct anchor, not dependent rows.
- L1 core facts: 500-1000 rows per low-risk create-only lane after anchors
  close.
- L2 auxiliary facts: batch update only after L1 is stable.
- L3 details: separate readiness and design before write.
- L4 high-risk: separate task line only.

## Fresh Database Replay Rule

Fresh replay must default to:

1. L0 anchors.
2. L1 core facts.
3. L2 auxiliary facts where already replay-certified.
4. L3 only after explicit readiness.
5. L4 excluded by default.

Any row that cannot satisfy its layer rule becomes evidence in the discard/hold
ledger. It must not be forced into the new database.
