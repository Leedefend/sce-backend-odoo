# Project Contract Professional Split Acceptance v1

## Scope

This acceptance note records the user-facing split of project contracts into
income contracts and expense contracts while preserving the legacy-compatible
`construction.contract` fact model.

The split is intentionally implemented as professional shell models:

- `construction.contract.income` for income contracts, backed by
  `construction.contract` records with `type = 'out'`.
- `construction.contract.expense` for expense contracts, backed by
  `construction.contract` records with `type = 'in'`.

Existing migration scripts, foreign keys, settlement/payment/invoice references,
and project dashboards continue to use `construction.contract` as the canonical
fact table.

## Delivery Surface

- Income contract ledger action:
  `smart_construction_core.action_construction_contract_income`
  uses `construction.contract.income`.
- Expense contract ledger action:
  `smart_construction_core.action_construction_contract_expense`
  uses `construction.contract.expense`.
- Income contract execution action:
  `smart_construction_core.action_construction_contract_income_execution`
  uses `construction.contract.income`.
- Expense contract execution action:
  `smart_construction_core.action_construction_contract_expense_execution`
  uses `construction.contract.expense`.
- The old mixed project contract menu
  `smart_construction_core.menu_sc_construction_contract` is inactive.

## Acceptance Database

Database: `sc_partner_acceptance`

Module upgrade command:

```bash
docker exec sc-backend-odoo-partner-acceptance-odoo-1 \
  odoo -d sc_partner_acceptance -c /var/lib/odoo/odoo.conf \
  -u smart_construction_core --stop-after-init
```

Validated facts after upgrade:

| Fact | Count |
| --- | ---: |
| Base income contracts, `construction_contract.type = 'out'` | 1541 |
| Income professional wrappers, `construction_contract_income` | 1541 |
| Base expense contracts, `construction_contract.type = 'in'` | 5309 |
| Expense professional wrappers, `construction_contract_expense` | 5309 |
| Income ledger visible action records | 1532 |

The visible income ledger count keeps the established historical surface filter:

```python
['|', ('legacy_contract_id', '=', False), ('legacy_income_surface_visible', '=', True)]
```

## Guard Checks

The acceptance shell checks confirmed:

- income and expense wrapper tables match the base contract type counts;
- income/expense ledger and execution actions point to professional models;
- income/expense tree and form views load through Odoo `get_view`;
- the old mixed contract menu is inactive;
- creating through `construction.contract.income` forces `type = 'out'`;
- attempting to switch an income wrapper to `type = 'in'` raises
  `ValidationError`;
- professional entries reject a `contract_id` bound to the opposite contract
  type;
- direct creation through the base `construction.contract` still creates the
  matching professional wrapper.
- changing the base contract `type` moves the wrapper from the old professional
  table to the new one after flushing the base contract fields;
- my-work contract targets keep a valid action but do not bind the inactive
  mixed contract menu.

Transactional create and type-switch probes were rolled back and did not alter
acceptance data.
