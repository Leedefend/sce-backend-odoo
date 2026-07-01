# -*- coding: utf-8 -*-
import json


PAYMENT_EXECUTION_REQUIRED_FIELDS = [
    "business_category_id",
    "payment_request_id",
    "project_id",
    "partner_id",
    "paid_amount",
    "receipt_account_name",
    "receipt_account_no",
    "payment_account_name",
    "payment_account_no",
]

PAYMENT_EXECUTION_SECTIONS = [
    {"title": "办理类型"},
    {"title": "付款依据"},
    {"title": "付款金额"},
    {"title": "收款账户"},
    {"title": "付款账户"},
    {"title": "办理说明"},
    {"title": "公司-承包人资金责任"},
    {"title": "来源与系统追溯"},
]

PAYMENT_EXECUTION_FIELDS = [
    {"name": "business_category_id", "sequence": 10},
    {"name": "execution_flow_label", "sequence": 20},
    {"name": "state", "sequence": 30},
    {"name": "name", "sequence": 40},
    {"name": "payment_request_id", "sequence": 50},
    {"name": "project_id", "sequence": 60},
    {"name": "operation_strategy", "sequence": 70},
    {"name": "partner_id", "sequence": 80},
    {"name": "contract_id", "sequence": 90},
    {"name": "date_payment", "sequence": 100},
    {"name": "paid_amount", "sequence": 110},
    {"name": "planned_amount", "sequence": 120},
    {"name": "invoice_amount", "sequence": 130},
    {"name": "currency_id", "sequence": 140},
    {"name": "receipt_account_name", "sequence": 150},
    {"name": "receipt_bank_name", "sequence": 160},
    {"name": "receipt_account_no", "sequence": 170},
    {"name": "payment_account_name", "sequence": 180},
    {"name": "payment_bank_name", "sequence": 190},
    {"name": "payment_account_no", "sequence": 200},
    {"name": "bank_account", "sequence": 210},
    {"name": "payment_method", "sequence": 220},
    {"name": "handler_name", "sequence": 230},
    {"name": "document_no", "sequence": 240},
    {"name": "note", "sequence": 250},
    {"name": "attachment_ids", "sequence": 260},
    {"name": "company_contractor_responsibility_state", "sequence": 300},
    {"name": "company_contractor_arrival_unprocessed_amount", "sequence": 310},
    {"name": "company_contractor_arrival_over_processed_amount", "sequence": 320},
    {"name": "company_contractor_self_funding_balance", "sequence": 330},
    {"name": "company_contractor_responsibility_notice", "sequence": 340},
    {"name": "payment_family", "sequence": 900},
    {"name": "source_kind", "sequence": 910},
    {"name": "push_result", "sequence": 920},
    {"name": "kingdee_document_no", "sequence": 930},
    {"name": "creator_name", "sequence": 940},
    {"name": "created_time", "sequence": 950},
]


def _contract_json(payload):
    return json.dumps({"view_orchestration": {"views": {"form": payload}}}, ensure_ascii=False)


def migrate(cr, version):
    required_fields_json = json.dumps(PAYMENT_EXECUTION_REQUIRED_FIELDS, ensure_ascii=False)
    defaults = {
        "finance.payment.execution.partner": {
            "source_kind": "actual_outflow",
            "payment_family": "往来单位付款",
        },
        "finance.payment.execution.company": {
            "source_kind": "actual_outflow",
            "payment_family": "公司财务支出",
        },
    }
    for code, default_values in defaults.items():
        cr.execute(
            """
            UPDATE sc_business_category
               SET default_values_json = %s,
                   required_fields_json = %s,
                   write_date = NOW()
             WHERE code = %s
            """,
            (json.dumps(default_values, ensure_ascii=False), required_fields_json, code),
        )

    cr.execute(
        """
        UPDATE ui_business_config_contract
           SET contract_json = %s::jsonb,
               write_date = NOW()
         WHERE model = 'sc.payment.execution'
           AND name = 'sc_payment_execution_form_sections_v1'
        """,
        (_contract_json({"sections": PAYMENT_EXECUTION_SECTIONS}),),
    )
    cr.execute(
        """
        UPDATE ui_business_config_contract
           SET contract_json = %s::jsonb,
               write_date = NOW()
         WHERE model = 'sc.payment.execution'
           AND name = 'sc_payment_execution_form_structure_generated_v1'
        """,
        (_contract_json({"fields": PAYMENT_EXECUTION_FIELDS}),),
    )
