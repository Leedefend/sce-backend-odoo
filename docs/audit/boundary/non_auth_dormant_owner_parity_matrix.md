# Non-Auth Dormant Owner Parity Matrix (ITER-2026-04-05-1052)

## Matrix

| Legacy Dormant Surface (smart_construction_core) | Route(s) | Active Owner Counterpart (smart_core) | Parity | Note |
| --- | --- | --- | --- | --- |
| `execute_controller.py` | `/api/execute_button` | `platform_execute_api.py` | PASS | same route signature present |
| `frontend_api.py` | `/api/menu/tree`, `/api/user_menus` | `platform_menu_api.py` | PASS | both routes present |
| `portal_execute_button_controller.py` | `/api/contract/portal_execute_button`, `/api/portal/execute_button` | `platform_portal_execute_api.py` | PASS | contract+execute pair present |
| `ui_contract_controller.py` | `/api/ui/contract` | `platform_ui_contract_api.py` | PASS | both keep legacy-disabled behavior |

## Conclusion

- all four dormant non-auth legacy surfaces have active smart_core owner parity.
- cleanup implementation can proceed as low-risk non-functional hygiene (file/import cleanup), subject to bounded scope.

## Suggested Next Batch

- open cleanup implement task to remove or archive dormant non-auth legacy controller surfaces in `smart_construction_core` without touching behavior contracts.
