# v1.0 Iteration Round 1 Minimum Regression Report

## 1. Scope

Executed required commands:

1. `make verify.frontend.build`
2. `make verify.frontend.typecheck.strict`
3. `make verify.project.dashboard.contract`
4. `make verify.phase_next.evidence.bundle`

Release-grade demo seed closure commands (new fixed items):

5. `make demo.load.release DB_NAME=sc_demo`
6. `make verify.demo.release.seed DB_NAME=sc_demo`

## 2. Results

- `make verify.frontend.build`: PASS
- `make verify.frontend.typecheck.strict`: PASS
- `make verify.project.dashboard.contract`: PASS
- `make verify.phase_next.evidence.bundle`: PASS (final re-check passed)
- `make demo.load.release DB_NAME=sc_demo`: PASS (release seed load succeeded)
- `make verify.demo.release.seed DB_NAME=sc_demo`: PASS (release seed acceptance passed)

Historical failure output (closed by re-check):

- `[role_capability_floor_prod_like] FAIL`
- `admin session setup failed: <urlopen error timed out>`

Historical re-run once had the same result.

Final re-check result (2026-07-05):

- `make verify.phase_next.evidence.bundle`: PASS
- `make verify.release.round1.final_closeout.guard`: PASS
- `make verify.release.master_stage.final_closeout.guard`: PASS

## 3. Impact Assessment

- Product-expression changes do not break frontend build/typecheck/dashboard contract verification.
- The historical evidence-bundle failure is closed by final re-check and is no longer a release blocker.

## 4. Recommendation

1. Keep `verify.phase_next.evidence.bundle` in the pre-release minimum regression set.
2. Keep `verify.release.round1.final_closeout.guard` and `verify.release.master_stage.final_closeout.guard` in the document/evidence closeout gates.
3. Treat later environment timeouts as runtime-environment incidents without reopening this product-expression closeout.

## 5. Release Demo Seed Acceptance (Fixed Section)

- Goal: ensure demo data is a repeatable + verifiable release baseline.
- Load command: `make demo.load.release DB_NAME=sc_demo`
- Verify command: `make verify.demo.release.seed DB_NAME=sc_demo`
- Minimum pass criteria:
  - showroom project coverage is present;
  - `project_id=20` has non-empty contract/cost/finance data;
  - release role users (including `svc_e2e_smoke`) are present.
