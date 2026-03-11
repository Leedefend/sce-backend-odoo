# SCEMS v1.0 Role Permission Matrix

## 1. Objective
Define the V1 role-permission baseline across ACL, record rules, capabilities, and block visibility.

## 2. Role Mapping (Business Role -> Current Validation Role)

| Business Role (V1) | Current Validation Role (prod-like) | Notes |
|---|---|---|
| Project Manager | `pm` (`sc_fx_pm`) | covered |
| Project Member | `project_member` (`sc_fx_project_member`) | unified; `material_user/cost_user` kept for compatibility |
| Contract Admin | `contract_admin` (`sc_fx_contract_admin`) | covered |
| Finance Collaborator | `finance` (`sc_fx_finance`) | covered |
| Management Viewer | `executive` (`sc_fx_executive`) | covered (should remain read-mostly) |
| System Administrator | `admin` (non prod-like fixture) | provided by built-in system admin role |

## 3. Baseline by Permission Dimension

### 3.1 Model ACL
- `project.project`: project roles have read access; PM has required write actions.
- `construction.contract`: contract/PM/executive have read; contract role has operation privileges.
- `project.cost`: cost-domain access is role-controlled.
- `payment.request`: finance and management roles have read; finance has workflow operations.

### 3.2 Record Rules
- Project members: scoped to authorized project data.
- Finance collaborators: scoped to finance domain, no cross-domain write overreach.
- Management viewer: read-only first.

### 3.3 Capability / Block Visibility
- `system.init` capability output must match role baseline.
- `project.management` 7 blocks support role-based visible/readonly behavior.
- Unauthorized capabilities must fail gracefully (deny/degrade), never blank-fail.

## 4. Current Validation Snapshot (from role_capability_floor_prod_like)

| Role | capability_count | journey(system.init/ui.contract) | Status |
|---|---:|---|---|
| `pm` | 25 | PASS / PASS | PASS |
| `executive` | 42 | PASS / PASS | PASS |
| `finance` | 37 | PASS / PASS | PASS |
| `contract_admin` | 42 | PASS / PASS | PASS |
| `project_member` | 25 | PASS / PASS | PASS |
| `material_user` | 25 | PASS / PASS | PASS |
| `cost_user` | 25 | PASS / PASS | PASS |

## 5. Pending Improvements
- Add explicit read-only verification for management viewer.
- Extend management-viewer read-only checks from contract-level to runtime write-intent probes.
