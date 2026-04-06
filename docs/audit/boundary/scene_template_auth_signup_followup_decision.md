# SceneTemplate/AuthSignup Follow-Up Decision

## Inputs

- `docs/audit/boundary/residual_route_ownership_checkpoint.md`

## Decision

1. `scene_template` family (`/api/scenes/export`, `/api/scenes/import`)
   - continue boundary normalization in **dedicated P2 governance batch**.
   - use read-first style if possible (`export` before `import`).
   - keep write semantics delegated during transition.

2. `auth_signup` family (`/web/signup`, `/sc/auth/activate/*`)
   - keep out of current API-boundary chain.
   - require separate auth-domain task line due website/auth semantics.

## Rationale

- `scene_template` remains API-governance adjacent and fits current remediation objective.
- `auth_signup` belongs to website/auth lifecycle and should not be mixed into current runtime API ownership chain.

## Next Step

- open next batch for `scene_template` family only.
