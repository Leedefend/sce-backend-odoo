# History Business Usable Probe v1

Status: PASS

## Decision

`history_business_usable_ready`

## Core Counts

```json
{
  "legacy_users": 101,
  "legacy_active_users": 67,
  "legacy_user_roles": 330,
  "legacy_user_roles_projected": 315,
  "legacy_user_project_scopes_current": 20000,
  "legacy_user_project_scopes_current_with_project": 17453,
  "legacy_user_project_scopes_access_applied": 17453,
  "legacy_users_with_runtime_capability_groups": 97,
  "legacy_project_followers": 480,
  "partner_anchors": 6324,
  "project_runtime_records": 869,
  "project_records_with_owner_link": 869,
  "project_member_carrier": 23190,
  "contract_runtime_records": 9521,
  "contract_records_with_partner_link": 9521,
  "contract_summary_lines": 1441,
  "supplier_contract_runtime_records": 5301,
  "supplier_contract_line_runtime_records": 5065,
  "payment_request_runtime_records": 30187,
  "payment_request_with_project_link": 30187,
  "payment_request_with_contract_link": 14188,
  "payment_request_with_partner_link": 30187,
  "payment_request_line_runtime_records": 31883,
  "actual_outflow_runtime_records": 0,
  "legacy_actual_outflow_cash_requests": 12992,
  "legacy_receipt_cash_requests": 3652,
  "treasury_ledger_runtime_records": 18347,
  "treasury_ledger_legacy_actual_outflow": 12992,
  "treasury_ledger_legacy_receipt": 5355,
  "legacy_payment_residual_facts": 3122,
  "legacy_payment_residual_with_project": 1603,
  "payment_execution_runtime_records": 7868,
  "payment_execution_legacy_records": 7868,
  "payment_execution_legacy_with_project": 7868,
  "receipt_invoice_line_runtime_records": 4448,
  "receipt_invoice_attachment_runtime_records": 1076,
  "legacy_attachment_backfill_runtime_records": 18458,
  "legacy_file_index_rows": 178931,
  "legacy_file_index_with_path": 178931,
  "legacy_url_attachments": 19534,
  "legacy_receipt_income_facts": 7220,
  "legacy_receipt_residual_facts": 3778,
  "legacy_receipt_residual_with_project": 1894,
  "receipt_income_runtime_records": 12697,
  "receipt_income_legacy_records": 12697,
  "receipt_income_legacy_with_project": 12697,
  "legacy_expense_deposit_facts": 11167,
  "legacy_expense_reimbursement_lines": 3589,
  "legacy_expense_reimbursement_lines_with_project": 3584,
  "expense_claim_runtime_records": 38217,
  "expense_claim_legacy_records": 38217,
  "expense_claim_legacy_with_project": 38217,
  "legacy_material_category_rows": 130624,
  "legacy_material_detail_rows": 2279734,
  "legacy_material_detail_with_category": 1494612,
  "legacy_material_detail_promoted": 0,
  "product_categories_from_legacy_material": 130624,
  "material_catalog_from_legacy_material": 2279734,
  "product_templates_from_legacy_material": 0,
  "legacy_purchase_contract_facts": 49,
  "legacy_purchase_contract_with_project": 49,
  "legacy_purchase_contract_project_amount": 45,
  "legacy_purchase_contract_with_partner_text": 45,
  "general_contract_runtime_records": 45,
  "general_contract_legacy_records": 45,
  "general_contract_legacy_with_project": 45,
  "legacy_invoice_tax_facts": 5920,
  "legacy_invoice_registration_lines": 24792,
  "legacy_invoice_registration_lines_project_amount": 22098,
  "legacy_invoice_tax_project_amount": 5920,
  "invoice_registration_runtime_records": 32140,
  "invoice_registration_legacy_records": 32140,
  "invoice_registration_legacy_with_project": 32140,
  "legacy_tax_deduction_facts": 4915,
  "legacy_tax_deduction_project_amount": 4238,
  "tax_deduction_registration_runtime_records": 4915,
  "tax_deduction_registration_legacy_records": 4915,
  "tax_deduction_registration_legacy_with_project": 4915,
  "legacy_deduction_adjustment_lines": 13113,
  "legacy_deduction_adjustment_lines_with_project": 13521,
  "settlement_adjustment_runtime_records": 13521,
  "settlement_adjustment_legacy_records": 13521,
  "settlement_adjustment_legacy_with_project": 13521,
  "legacy_fund_confirmation_lines": 13141,
  "legacy_financing_loan_facts": 318,
  "legacy_financing_loan_project_amount": 318,
  "financing_loan_runtime_records": 318,
  "financing_loan_legacy_records": 318,
  "financing_loan_legacy_with_project": 318,
  "legacy_fund_daily_snapshot_facts": 496,
  "legacy_fund_daily_line_facts": 7754,
  "legacy_fund_daily_line_with_project": 7754,
  "treasury_reconciliation_runtime_records": 20060,
  "treasury_reconciliation_legacy_records": 20060,
  "treasury_reconciliation_legacy_with_project": 20060,
  "legacy_construction_diary_lines": 5687,
  "legacy_construction_diary_with_project": 5666,
  "construction_diary_runtime_records": 5665,
  "construction_diary_legacy_records": 5665,
  "construction_diary_legacy_with_project": 5665,
  "legacy_workflow_audit_facts": 79702,
  "history_todo_total": 79702,
  "history_todo_open": 79702,
  "mail_activity_total": 0,
  "mail_activity_for_history_models": 0,
  "mail_activity_assigned_legacy_users": 0,
  "mail_activity_on_payment_requests": 0,
  "mail_activity_on_contracts": 0,
  "mail_activity_on_projects": 0,
  "tier_review_total": 0,
  "tier_review_pending": null,
  "project_task_total": 0,
  "project_task_assigned": 0,
  "payment_request_state_distribution": {
    "draft": 31890
  }
}
```

## User Feedback Formal Field Coverage

```json
{
  "sc.settlement.order": {
    "model_exists": true,
    "fields": {
      "title": {
        "exists": true,
        "searchable": true,
        "filled_records": 37
      },
      "document_date": {
        "exists": true,
        "searchable": true,
        "filled_records": 37
      },
      "settlement_unit_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 37
      },
      "submitted_amount": {
        "exists": true,
        "searchable": true,
        "filled_records": 37
      },
      "approved_amount": {
        "exists": true,
        "searchable": true,
        "filled_records": 37
      },
      "requested_fund_amount": {
        "exists": true,
        "searchable": true,
        "filled_records": 37
      },
      "engineering_address": {
        "exists": true,
        "searchable": true,
        "filled_records": 37
      },
      "deduction_amount": {
        "exists": true,
        "searchable": false,
        "filled_records": null
      },
      "unpaid_amount": {
        "exists": true,
        "searchable": true,
        "filled_records": 37
      },
      "settlement_description": {
        "exists": true,
        "searchable": true,
        "filled_records": 37
      },
      "attachment_count": {
        "exists": true,
        "searchable": false,
        "filled_records": null
      }
    }
  },
  "sc.material.rfq": {
    "model_exists": true,
    "fields": {
      "contact_name": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "contact_phone": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "source_material_plan_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "selected_supplier_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "note": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      }
    }
  },
  "sc.material.rfq.line": {
    "model_exists": true,
    "fields": {
      "source_material_plan_line_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "supplier_contact_name": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "supplier_contact_phone": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "quote_status": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      }
    }
  },
  "purchase.order": {
    "model_exists": true,
    "fields": {
      "project_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "plan_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "source_material_rfq_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      }
    }
  },
  "purchase.order.line": {
    "model_exists": true,
    "fields": {
      "project_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "plan_line_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "source_material_rfq_line_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      }
    }
  },
  "sc.material.acceptance.line": {
    "model_exists": true,
    "fields": {
      "purchase_request_line_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "purchase_order_line_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "planned_qty": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "issue_note": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      }
    }
  },
  "sc.material.inbound.line": {
    "model_exists": true,
    "fields": {
      "acceptance_line_id": {
        "exists": true,
        "searchable": true,
        "filled_records": 0
      },
      "unit_price": {
        "exists": true,
        "searchable": true,
        "filled_records": 19
      },
      "amount": {
        "exists": true,
        "searchable": true,
        "filled_records": 19
      },
      "note": {
        "exists": true,
        "searchable": true,
        "filled_records": 19
      }
    }
  }
}
```

## Promotion Gaps

```json
{
  "runtime_list_form_missing": [],
  "project_member_owner_promotion_gap": false,
  "contract_partner_runtime_gap": false,
  "payment_request_runtime_link_gap": false,
  "workflow_audit_without_actionable_runtime": false,
  "no_actionable_todo_surface": false,
  "payment_request_no_pending_runtime_states": false,
  "payment_receipt_execution_surface_gap": false,
  "attachment_custody_surface_gap": false,
  "invoice_tax_runtime_surface_gap": false,
  "tax_deduction_runtime_surface_gap": false,
  "receipt_income_runtime_surface_gap": false,
  "payment_execution_runtime_surface_gap": false,
  "settlement_adjustment_runtime_surface_gap": false,
  "treasury_reconciliation_surface_gap": false,
  "financing_loan_runtime_surface_gap": false,
  "expense_deposit_runtime_surface_gap": false,
  "expense_claim_runtime_surface_gap": false,
  "material_catalog_runtime_surface_gap": false,
  "material_category_projection_gap": false,
  "material_catalog_projection_gap": false,
  "construction_diary_runtime_surface_gap": false,
  "purchase_contract_runtime_surface_gap": false,
  "general_contract_runtime_surface_gap": false,
  "legacy_user_access_runtime_gap": false,
  "active_legacy_business_menu_exposures": []
}
```

## Sample Runtime Records

```json
{
  "project_project_id": 1,
  "construction_contract_id": 1,
  "payment_request_id": 1,
  "payment_request_line_id": 1,
  "receipt_invoice_line_id": 1,
  "receipt_invoice_attachment_id": 991,
  "legacy_file_index_id": 1,
  "legacy_invoice_registration_line_id": 1,
  "invoice_registration_id": 1,
  "legacy_tax_deduction_fact_id": 1,
  "tax_deduction_registration_id": 1,
  "receipt_income_id": 1,
  "payment_execution_id": 1,
  "legacy_expense_deposit_fact_id": 1,
  "legacy_expense_reimbursement_line_id": 1,
  "expense_claim_id": 1,
  "legacy_material_detail_id": 1,
  "legacy_purchase_contract_fact_id": 1,
  "general_contract_id": 2,
  "legacy_deduction_adjustment_line_id": 1,
  "settlement_adjustment_id": 1,
  "legacy_fund_confirmation_line_id": 1,
  "legacy_financing_loan_fact_id": 1,
  "financing_loan_id": 1,
  "legacy_fund_daily_snapshot_fact_id": 1,
  "legacy_fund_daily_line_id": 1,
  "treasury_reconciliation_id": 1,
  "construction_diary_id": 1,
  "treasury_ledger_id": 1,
  "legacy_workflow_audit_id": 1,
  "history_todo_id": 1,
  "mail_activity_id": null,
  "tier_review_id": null
}
```

## Notes

- This probe is read-only and does not mutate runtime business objects.
- It evaluates whether replayed historical facts have crossed from carrier-only evidence to user-visible runtime surfaces.
- A non-ready result means promotion work is still required before claiming user business continuity.
