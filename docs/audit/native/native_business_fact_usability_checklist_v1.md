# Native Business-Fact Usability Checklist v1

## Scope

This checklist targets native business-fact usability readiness only.
It excludes ACL/rule mutations and frontend orchestration changes.

## Checklist Mapping

| ID | Check Item | Verify Hook | Current Status | Notes |
|---|---|---|---|---|
| BF-01 | Seven agreed native audit artifacts exist and remain readable | `make verify.native.business_fact.static` | PASS | Guards audit baseline continuity |
| BF-02 | Native auth entry endpoint (`/api/v1/intent`) returns expected auth-gated status class | `python3 scripts/verify/native_business_fact_runtime_snapshot.py` | PASS (`401`) | Host-approved probe required for decisive evidence |
| BF-03 | Legacy auth entry endpoint (`/api/scenes/my`) returns expected auth-gated status class | `python3 scripts/verify/native_business_fact_runtime_snapshot.py` | PASS (`401`) | Confirms legacy transition path still reachable |
| BF-04 | Core business-fact model files for project/task/budget/cost/dictionary are present | `make verify.native.business_fact.static` | PASS | Static prerequisite only |
| BF-05 | Runtime probe script remains aligned to native endpoint default path | `python3 scripts/verify/scene_legacy_auth_runtime_probe.py` | PASS | Default target is `/api/v1/intent` |

## Execution Sequence (Low-Risk)

1. Run `make verify.native.business_fact.static`.
2. Run host-approved `python3 scripts/verify/native_business_fact_runtime_snapshot.py`.
3. If both pass, treat business-fact entry gate as green for next low-risk batch.

## Escalation Rule

If any future checklist item requires changing:
- `security/**`
- `record_rules/**`
- `ir.model.access.csv`
- `__manifest__.py`

then stop low-risk lane and open a dedicated high-risk gated task contract.

## Legacy Endpoint Deprecation Note
- `/api/scenes/my` is deprecated.
- Successor endpoint: `/api/v1/intent` with `intent=app.init`.
- Sunset date: `2026-04-30`.
- Deprecation header contract reference: `Deprecation`, `Sunset`, `Link`, `X-Legacy-Endpoint`.
