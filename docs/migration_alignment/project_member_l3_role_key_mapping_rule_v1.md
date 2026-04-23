# Project member L3 role-key mapping rule v1

Status: PASS  
Iteration: `ITER-2026-04-14-L3-ROLE-KEY-AUDIT-MAPPED-WRITE`

## Purpose

Stop guessing `project.responsibility.role_key`.

This batch audits the model field definition, legal selection values, and
current target data distribution before mapping the L3 historical member sample
to an existing legal role code.

## Mapping Rule

The frozen rule is:

```text
source_business_semantic = historical_project_member_l3_sample
target_model = project.responsibility
target_field = role_key
mapped_role_key = highest-frequency existing legal role_key in sc_demo
```

If there is no existing legal target distribution, the batch freezes an explicit
model-definition fallback:

```text
mapped_role_key = manager
mapped_role_label = 项目经理
mapping_basis = model_field_selection_fallback
```

This fallback uses an existing legal selection value and does not add or rename
any role key.

## Boundary

This batch does not modify:

- model fields;
- role selection values;
- ACL / security;
- record rules.

## Result

Legal role keys audited from `project.responsibility.role_key`:

```text
manager, cost, finance, cashier, material, safety, quality, document
```

Frozen mapping:

```text
historical_project_member_l3_sample -> manager / 项目经理
```

Write result:

- sample rows: 3
- created responsibility records: 3
- mapped role key: `manager`
- post audit matched records: 3
- rollback eligible rows: 3

Implementation note: the first write pass committed the three ORM records and
then failed while writing the rollback CSV. The recovery run detected the same
RUN_ID in the created records, reused them, and generated the final write,
audit, and rollback artifacts without duplicating records.
