# v1.1 Baseline Report

Date: 2026-07-12
Branch created from: `topic/productization-system-closure`
Working branch: `topic/v1.1-engineering-convergence`

## Code Baseline

- Baseline commit before convergence branch: `3ba45880d Default mobile shell sidebar to hidden`
- Productization closure validation at baseline:
  - User-visible surface coverage: `106/106`
  - Config workbench: `64/64`, `delivery_ready`, `professional_ready`
  - Business form user perspective: `20/20`
  - System user experience full browser guard: passed

## Environment Baseline To Record

The release owner must fill these before tagging the final Phase 0 baseline:

| Item | Value | Evidence |
| --- | --- | --- |
| Git tag | TBD | GitHub tag link |
| Main branch commit SHA | TBD | `git rev-parse main` |
| Odoo version | TBD | Runtime command output |
| PostgreSQL version | TBD | Runtime command output |
| Database name/version | TBD | DB metadata report |
| Installed module versions | TBD | Module inventory report |
| Frontend artifact hash | TBD | Build artifact hash |
| Image tags/digests | TBD | Registry evidence |
| Filestore location and size | TBD | Storage report |
| Known P0/P1 issues | TBD | GitHub issue links |

## Tagging Rule

Create the Phase 0 tag only after:

- Scope freeze is approved.
- GitHub milestone exists.
- Issue cleanup is complete.
- Branch protection is enabled.
- Current baseline report is filled.
