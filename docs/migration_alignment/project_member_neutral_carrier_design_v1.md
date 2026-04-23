# Project member neutral carrier design v1

Status: IMPLEMENTED  
Iteration: `ITER-2026-04-14-0030N`

## Carrier

Model:

```text
sc.project.member.staging
```

Purpose:

```text
Preserve legacy project-member relation facts without claiming responsibility roles.
```

## Fields

- `legacy_member_id`
- `legacy_project_id`
- `legacy_user_ref`
- `project_id`
- `user_id`
- `legacy_role_text`
- `role_fact_status`
- `import_batch`
- `evidence`
- `notes`
- `active`

## Boundary

The carrier is not `project.responsibility`.

It does not participate in:

- project responsibility role semantics;
- project or downstream record-rule visibility;
- approval / owner / reviewer logic;
- business workflow routing;
- frontend menus, actions, or views.

## Current Role Status

The 34-row safe slice is written with:

```text
role_fact_status = missing
legacy_role_text = empty
```

This is deliberate. `ITER-2026-04-14-0030RD` queried the old database directly
and did not find an authoritative role source for this project_member lane.

## Promotion Rule

Records in this carrier may only be promoted to `project.responsibility` in a
future dedicated task after one of these is true:

- a verified legacy role source is found;
- a business-approved default responsibility rule exists;
- an authority-path batch explicitly accepts record-rule and visibility impact.
