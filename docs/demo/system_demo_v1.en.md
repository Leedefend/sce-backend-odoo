# SCEMS v1.0 System Demo Script

## 1. Demo Goal
Show the v1 core business loop in 10–15 minutes:

`Login -> My Work -> Project Ledger -> Project Management Dashboard -> Contract/Cost/Finance -> Risk`

## 2. Pre-demo Setup
- Environment: `dev` or `test`
- Database: seeded demo data (recommended `sc_demo`)
- Demo accounts: `sc_fx_pm` / `sc_fx_finance` / `sc_fx_executive`

## 3. Demo Steps

### Step 1 Login
- Login as project manager.
- Show homepage and main navigation.

### Step 2 Open "My Work"
- Open `my_work.workspace`.
- Show todo list, my projects, quick entries, risk summary.

### Step 3 Open "Project Ledger"
- Open `projects.ledger`.
- Run filter/search to locate a target project.

### Step 4 Open "Project Management Dashboard"
- Navigate from ledger to `project.management`.
- Show all 7 dashboard blocks:
  - Header
  - Metrics
  - Progress
  - Contract
  - Cost
  - Finance
  - Risk

### Step 5 Show business workspaces
- Demonstrate:
  - `contracts.workspace`
  - `cost.analysis`
  - `finance.workspace`

### Step 6 Show risk and role differences
- Switch to management-view account and show read-only perspective.
- Explain deny/degrade behavior for unauthorized capabilities.

## 4. Demo Acceptance Criteria
- Pages open without blocking errors.
- Core path can be completed end-to-end.
- Role differences align with permission design.

