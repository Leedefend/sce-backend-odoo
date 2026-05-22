# Browser Acceptance

## Runtime

- Frontend: `http://127.0.0.1:5174`
- Backend: `http://127.0.0.1:18081`
- Database: `sc_demo`
- Login: `wutao`
- Project list entry: `/a/506?menu_id=379&action_id=506`

## Results

- Form relation many2many multi-select: PASS
  - Artifact: `artifacts/form-many2many-multi-select/20260521T205253/summary.json`
  - Covered add two relation tags, save, reload/read, remove, and cleanup restore.
- List group clear acceptance: PASS
  - Artifact: `artifacts/list-group-clear-acceptance/20260521T205921/summary.json`
  - Covered menu group, custom group, group facet clear, URL state cleanup, and flat list restoration.
- Full list search/group usability script: NOT USED FOR FINAL ACCEPTANCE
  - Artifact: `artifacts/list-search-group-usability/20260521T205255/summary.json`
  - It was stopped after the long-running favorite-filter tail scenario. The focused group-clear acceptance script is the acceptance evidence for group/search route behavior.

## Gates

- `python3 scripts/verify/frontend_page_contract_orchestration_consumption_guard.py`: PASS
- `python3 scripts/verify/frontend_contract_runtime_guard.py`: PASS
- `pnpm run typecheck`: PASS
- `pnpm run build`: PASS
