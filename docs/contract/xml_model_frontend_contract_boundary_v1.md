# XML, Model, and Frontend Contract Boundary

This note fixes the user-visible contract boundary for Odoo native views rendered
by the custom frontend.

## Source Priority

User-visible page facts must be resolved in this order:

1. `ir.ui.view` XML: page field order, field labels, groups, visible buttons,
   status bars, search fields, list columns.
2. Contract governance: explicit projection, pruning, and delivery policy.
3. `ir.model.fields` / `fields_get`: model type, relation, required/readonly,
   and fallback labels only.
4. Technical field name: final fallback only.

## Responsibilities

Model definitions carry data and security facts:

- field existence and type
- compute/inverse behavior
- base constraints
- access rights and record rules
- fallback labels

XML view definitions carry user-visible page facts:

- which fields are shown
- field order
- page-specific `string`
- group layout
- action/status/search/list surface

The contract layer is the only merge point. It must preserve XML page facts and
use model metadata only as structural fallback. Governance may remove native
noise or project explicit delivery policy, but it must not mask an unresolved
source-priority bug by rewriting field metadata.

The frontend renders the resolved contract. It must not infer business labels,
permissions, or field visibility from Odoo technical names.

## Guarded Case

`smart_construction_core.action_sc_runtime_user_management` is the reference
case. The XML view labels `用户名`, `启用`, `重置密码`, and `业务角色组` must win over
`res.users.fields_get()` defaults such as `登录`, `有效`, `密码`, and `用户角色`.

The guard is:

```bash
make verify.user_permission_view_contract_boundary.guard DB_NAME=<db>
```
