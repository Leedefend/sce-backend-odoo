# Business Fact Replay Postcheck Report v1

Status: PASS

Task: `ITER-2026-05-07-BUSINESS-FACT-UPGRADE-REPLAY`

## Scope

Read-only verification for business facts replayed after project master anchors.

## Counts

```json
{
  "project.project.legacy": 810,
  "construction.contract.total": 6985,
  "construction.contract.legacy": 6985,
  "construction.contract.income_base": 1537,
  "construction.contract.expense_base": 5448,
  "construction.contract.income_wrapper": 1537,
  "construction.contract.expense_wrapper": 5448,
  "construction.contract.line": 6566,
  "sc.legacy.purchase.contract.fact": 49,
  "sc.general.contract.legacy": 45,
  "sc.invoice.registration.visible_contract_fact": 6,
  "sc.receipt.income.visible_contract_fact": 5
}
```

## Contract Split Integrity

```json
{
  "income_wrapper_missing": 0,
  "expense_wrapper_missing": 0,
  "income_wrapper_wrong_type": 0,
  "expense_wrapper_wrong_type": 0,
  "income_wrapper_duplicates": 0,
  "expense_wrapper_duplicates": 0
}
```

## Visible Business Facts

```json
{
  "visible_contracts_with_balance_surface": 20,
  "invoice_receipt_mismatch_count": 0,
  "invoice_receipt_mismatch_samples": [],
  "visible_balance_observation_count": 5,
  "visible_balance_observation_samples": [
    {
      "contract_id": 1166,
      "legacy_contract_id": "c7eeca91cf9e4c119560d13c13e82fdc",
      "legacy_document_no": "WBHTGL-20260312-001",
      "platform_unreceived": 36600.0,
      "visible_unreceived": -1299025.96
    },
    {
      "contract_id": 674,
      "legacy_contract_id": "74aa9b0db1dd4aecaf72db7d4a0a7606",
      "legacy_document_no": "WBHTGL-20260318-001",
      "platform_unreceived": 109000.0,
      "visible_unreceived": -37505999.32
    },
    {
      "contract_id": 102,
      "legacy_contract_id": "10a4a72592f04d16840882117a92c94b",
      "legacy_document_no": "WBHTGL-20260313-001",
      "platform_unreceived": 85674.0,
      "visible_unreceived": -37529325.32
    },
    {
      "contract_id": 1271,
      "legacy_contract_id": "d97f722e40614de79d23b6f299bc8e49",
      "legacy_document_no": "WBHTGL-20260326-001",
      "platform_unreceived": 24235.41,
      "visible_unreceived": 14065.93
    },
    {
      "contract_id": 319,
      "legacy_contract_id": "34322d7f3dc245d8b74e091c51a12fdf",
      "legacy_document_no": "WBHTGL-20260331-001",
      "platform_unreceived": 10169.48,
      "visible_unreceived": 0.0
    }
  ]
}
```

## Decision

`business_fact_replay_acceptance_passed`
