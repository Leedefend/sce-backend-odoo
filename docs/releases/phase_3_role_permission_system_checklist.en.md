# SCEMS v1.0 Phase 3: Role and Permission System Checklist

## 1. Goal
Build a complete V1 role-permission loop so users only see, access, and operate what they are authorized for.

## 2. Role Scope (V1)
- Project Manager
- Project Member
- Contract Admin
- Finance Collaborator
- Management Viewer
- System Administrator

## 3. Required Items

### A. Model ACL
- [x] Role-specific ACL for key models is defined and traceable
- [x] Minimum permission set is complete for `project.project`, `construction.contract`, `project.cost`, `payment.request`
- [x] No inconsistent ACL patterns (e.g., write without read)

### B. Record Rules
- [x] Project members only access assigned/authorized project records
- [x] Finance collaborators can access fund-related data without cross-domain write overreach
- [x] Management viewer is strictly read-only

### C. Capability and Block Visibility
- [x] Core capabilities are controlled via role matrix
- [x] 7 blocks in `project.management` support role-based visible/readonly behavior
- [x] Unauthorized capabilities are denied/degraded in contract output

### D. Scene and Route Permissions
- [x] Main navigation scene visibility matches role policy
- [x] Unauthorized scene access returns structured reason codes (no blank page)
- [x] Deep-link access follows the same permission policy

### E. Demo Accounts and Evidence
- [x] Prod-like fixture accounts are available and login-ready
- [x] Role matrix verification report is reproducible
- [x] Key permission evidence artifacts are archivable

## 4. Suggested Verification Commands
- `make verify.role.capability_floor.prod_like`
- `make verify.role.capability_floor.prod_like.schema.guard`
- `make verify.role.management_viewer.readonly.guard`
- `make verify.role.project_member.unification.guard`
- `make verify.role.system_admin.minimum_permission_audit.guard`
- `make verify.role.acl.minimum_set.guard`
- `make verify.relation.access_policy.consistency.audit`
- `make verify.portal.role_scene_navigation_guard`
- `make verify.scene.contract.shape`
- `make verify.project.dashboard.role_runtime.guard`
- `make verify.scene.permission_reasoncode_deeplink.guard`
- `make verify.project.form.contract.surface.guard`
- `make verify.phase_next.evidence.bundle`

## 5. Deliverables
- Role-permission matrix doc (suggested: `docs/releases/role_permission_matrix_v1.en.md`)
- Phase 3 report (suggested: `artifacts/release/phase3_role_permission_system.md`)
- Key verify artifacts (role/capability/contract)

## 6. Exit Criteria
- All checklist items complete
- Core role paths pass verification (PM, Finance, Management Viewer)
- Execution board Phase 3 is updated to `DONE`
