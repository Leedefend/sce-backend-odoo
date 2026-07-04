# Business Expense Contract Subtype Evidence v1

Status: PASS

## Supplier Contract Subjects

```json
{
  "材料合同": 2409,
  "正常合同": 1779,
  "租赁合同": 423,
  "分包合同": 215,
  "劳务合同": 439,
  "其他合同": 34,
  "补充合同": 2
}
```

## Legacy Purchase / General Contract Types

```json
{
  "采购合同": 11,
  "法律咨询": 1,
  "": 1,
  "服务合同": 3,
  "其他合同": 33
}
```

## Decisions

```json
[
  {
    "key": "expense_contract_subtypes_follow_supplier_contract_subject",
    "decision": "use_supplier_subject_as_authoritative_contract_subtype",
    "reason": "Supplier contract replay carries explicit subject values from the migration asset."
  },
  {
    "key": "expense_is_not_supplier_contract_subtype",
    "decision": "keep_expense_reimbursement_and_deposit_in_expense_fact_lanes",
    "reason": "No supplier contract subject equals fee or reimbursement; expense/deposit facts already have separate carriers."
  },
  {
    "key": "subcontract_and_rental_are_contract_subtypes_when_subject_matches",
    "decision": "expose_filtered_expense_contract_views_for_subcontract_and_rental",
    "reason": "The supplier contract subject distribution includes 分包合同 and 租赁合同."
  },
  {
    "key": "pricing_method_is_not_contract_subtype",
    "decision": "keep_supplier_pricing_method_as_pricing_fact",
    "reason": "Pricing methods describe payment/pricing behavior, not contract family."
  },
  {
    "key": "legacy_purchase_general_contracts_are_separate_general_expense_contract_facts",
    "decision": "keep_legacy_purchase_general_contract_fact_lane",
    "reason": "Legacy purchase/general payload has its own contract_type distribution."
  }
]
```

## Errors

```json
[]
```

## Decision

`expense_contract_subtype_evidence_ready`
