# Business Admin Config Center Contract Runtime Acceptance v1

## Runtime Scope
- Topic: business-admin configuration center (`sc.dictionary` with `system_param` / `role_entry` / `home_block`).
- Runtime baseline: `http://localhost:8069`, database `sc_test`.
- Role samples: `admin`, `pm`, `finance`, `outsider`.

## Capture Method
- Intended intent endpoint (`/api/v1/intent` and `/api/intent`) is unavailable in this runtime baseline (HTTP 404).
- This batch uses Odoo runtime-equivalent payload surfaces via `/web/session/authenticate` + `/web/dataset/call_kw`.
- Captured sample file: `docs/ops/business_admin_config_center_contract_runtime_samples_v1.json`.

## Payload vs Freeze Surface
- Stable model-surface fields are available (`field_count=16`) across sampled roles.
- Required config fields are present (`has_scope_fields=true`):
  - `scope_type`
  - `scope_ref`
  - `value_text`
  - `value_json`
- Access boundary evidence:
  - `admin`: full CRUD
  - `pm`: read/write/create allow, unlink deny
  - `finance`: all denied
  - `outsider`: all denied

## Consumer Alignment
- Frontend generic consumer depends on model/form carrying path and relation defaults for `sc.dictionary`.
- Runtime samples confirm required scope/value fields are supplied and rights boundary matches deny/allow expectations.
- No new frontend permission patch is required for this stage.

## Intent Parity
- Session-bootstrap is now mandatory for formal intent verification path:
  1) `/web/session/authenticate`
  2) `/api/v1/intent`
- Dedicated parity verify: `scripts/verify/native_business_admin_config_center_intent_parity_verify.py`.
- Parity output: `docs/ops/business_admin_config_center_intent_parity_v1.md`.
- Current parity verdict: `PASS` (list/form/rights/runtime equivalent checks completed).

## Delta Assessment
- Positive: role-based runtime evidence is now frozen for config-center minimum surface.
- Positive: outsider deny and finance deny are explicit in runtime samples.
- Positive: intent session-bootstrap verify establishes direct `/api/v1/intent` runtime reachability across sampled roles.

## Verdict
- Result: `PASS`.
- PASS reason: runtime-equivalent surface and direct intent-envelope surface are both captured on current baseline.
- Boundary note: deny semantics for finance/outsider remain anchored by runtime ACL evidence (`/web/dataset/call_kw`) and are not represented as HTTP deny on current `ui.contract` envelope behavior.
