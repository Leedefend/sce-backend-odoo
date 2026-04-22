# auth_signup Migration Touch List (ITER-2026-04-05-1037)

## Purpose

- provide implementation-prep touch list for ownership migration.
- keep execution bounded and reversible per batch.

## Candidate Touch Points (File-Level)

| area | file | role in flow | migration concern | batch suggestion |
| --- | --- | --- | --- | --- |
| controller entry | `addons/smart_construction_core/controllers/auth_signup.py` | route + signup/activation policy | source owner handoff or delegation shim | Implement-1 |
| controller export | `addons/smart_construction_core/controllers/__init__.py` | controller registration | avoid duplicate registration during transition | Implement-1 |
| login entry UI | `addons/smart_construction_core/views/web_login_views.xml` | signup link exposure | preserve `/web/signup` compatibility anchor | Verify-1 |
| signup templates | `addons/smart_construction_core/views/signup_templates.xml` | auth_signup template override | ensure template inheritance remains valid | Verify-1 |
| anti-abuse model | `addons/smart_construction_core/models/support/signup_throttle.py` | rate-limit storage/check | owner relocation may require import path updates | Implement-2 |
| default seeding | `addons/smart_construction_core/hooks.py` (`_ensure_signup_defaults`) | `sc.signup.*` defaults | avoid config key drift during handoff | Implement-2 |

## Non-Negotiable Compatibility Anchors

1. `/web/signup` must remain reachable.
2. `/sc/auth/activate/<string:token>` must remain valid.
3. `sc.signup.*` keys must keep effective behavior.
4. login page signup entry must remain functional.

## Proposed Batch Split

### Implement-1 (route owner handoff)
- focus: controller ownership/delegation only.
- change set target: `auth_signup.py`, controller `__init__.py`.
- stop if any ACL/security/manifest dependency appears.

### Implement-2 (policy dependency alignment)
- focus: throttle model + defaults seed ownership alignment.
- change set target: `signup_throttle.py`, `hooks.py` (bounded section only).
- stop if migration implies ACL or install-order manifest changes.

### Verify-1 (compatibility verification)
- focus: web login entry + signup template + activation callback flow.
- evidence output: compatibility checklist with rollback command list.

## Rollback Anchors

- `git restore addons/smart_construction_core/controllers/auth_signup.py`
- `git restore addons/smart_construction_core/controllers/__init__.py`
- `git restore addons/smart_construction_core/models/support/signup_throttle.py`
- `git restore addons/smart_construction_core/hooks.py`
- `git restore addons/smart_construction_core/views/web_login_views.xml`
- `git restore addons/smart_construction_core/views/signup_templates.xml`

## Stop Conditions For Implement Entry

- any required change to `security/**`, `record_rules/**`, `ir.model.access.csv`, `__manifest__.py`.
- any inability to preserve route compatibility anchors.
- any uncertainty on single-source ownership after cutover.
