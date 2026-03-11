# SCEMS v1.0 Release Gap Analysis

## 1. Purpose
Identify critical gaps between current system status and the SCEMS v1.0 launch bar, then define executable closure actions.

## 2. Launch Criteria Baseline

### 2.1 Target Criteria
- Deployable
- Demo-ready
- Trainable
- Usable in real operations

### 2.2 Core Business Path
- Login
- My Work
- Project Ledger
- Project Management Console
- Contract/Cost/Fund review
- Risk identification

## 3. Current State vs Gaps

### A. Product and Scene
- Current: core scene and delivery-policy foundation exists
- Gap: `project.management` 7-block semantics need tighter business-data alignment

### B. Services and Capabilities
- Current: contract/scene orchestration is relatively mature
- Gap: aggregation services (e.g. `ProjectDashboardService`) need stable interfaces and metric definitions

### C. Roles and Permissions
- Current: prod-like role verification baseline exists
- Gap: V1 role matrix and block visibility rules need explicit configuration inventory

### D. Verification System
- Current: verification chain includes `phase_next.evidence.bundle` and scene governance
- Gap: missing V1-focused aggregated gates (dashboard/route/permission)

### E. Deployment and Operations
- Current: Makefile and container foundation exist
- Gap: missing V1 delivery-grade deployment and rollback playbooks

### F. Demo and Acceptance
- Current: partial demo/release documentation exists
- Gap: missing dedicated v1 demo script and user acceptance checklist

## 4. Priority Levels

### P0 (Launch Blocking)
- Scope freeze and change-control mechanism
- 7-block console semantics + data loop closure
- Role/permission matrix implementation
- Deployment guide/demo script/acceptance checklist completion

### P1 (Launch Strengthening)
- V1 verification entry aggregation and reporting
- Standardized training/demo templates

### P2 (Post-launch Optimization)
- Metrics expansion
- Scene personalization and UX optimization

## 5. Closure Plan (Aligned to Phases)
- Phase 0: scope freeze + asset inventory + gap analysis
- Phase 1: navigation convergence and delivery-policy lock
- Phase 2: core scenario closure (4 key scenarios)
- Phase 3: role/permission system
- Phase 4: frontend stability
- Phase 5: verification and deployment readiness
- Phase 6: pilot run and v1.0 launch

## 6. Exit Criteria (Definition of Done)
- All in-scope capabilities pass release-level verification
- Core business path reproducible under prod-like roles
- Release documentation complete and reviewed
- Launch demo executable by non-engineering staff using script only

