# -*- coding: utf-8 -*-
import json


PAYMENT_REQUEST_SECTIONS = [
    {"title": "办理类型"},
    {"title": "项目与往来单位"},
    {"title": "申请依据"},
    {"title": "申请金额"},
    {"title": "收款账户"},
    {"title": "付款单位"},
    {"title": "办理说明与附件"},
    {"title": "申请明细"},
    {"title": "执行与额度"},
    {"title": "往来单位默认账户"},
    {"title": "迁移来源"},
]

PAYMENT_REQUEST_FIELDS = [
    {"name": "business_category_id", "sequence": 10},
    {"name": "payment_flow_label", "sequence": 20},
    {"name": "state", "sequence": 30},
    {"name": "name", "sequence": 40},
    {"name": "project_id", "sequence": 50},
    {"name": "operation_strategy", "sequence": 60},
    {"name": "partner_id", "sequence": 70},
    {"name": "contract_id", "sequence": 80},
    {"name": "settlement_id", "sequence": 90},
    {"name": "material_settlement_id", "sequence": 100},
    {"name": "cost_category_name", "sequence": 110},
    {"name": "date_request", "sequence": 120},
    {"name": "amount", "sequence": 130},
    {"name": "amount_uppercase", "sequence": 140},
    {"name": "accepted_amount_uppercase", "sequence": 150},
    {"name": "currency_id", "sequence": 160},
    {"name": "actual_payee_unit", "sequence": 170},
    {"name": "payment_account_name", "sequence": 180},
    {"name": "payment_bank_name", "sequence": 190},
    {"name": "payment_account_no", "sequence": 200},
    {"name": "payer_unit", "sequence": 210},
    {"name": "note", "sequence": 220},
    {"name": "attachment_ids", "sequence": 230},
    {"name": "outflow_line_ids", "sequence": 300},
    {"name": "receipt_invoice_line_ids", "sequence": 310},
    {"name": "paid_amount_total", "sequence": 400},
    {"name": "unpaid_amount", "sequence": 410},
    {"name": "is_fully_paid", "sequence": 420},
    {"name": "settlement_amount_total", "sequence": 430},
    {"name": "settlement_paid_amount", "sequence": 440},
    {"name": "settlement_amount_payable", "sequence": 450},
    {"name": "settlement_remaining_amount", "sequence": 460},
    {"name": "is_overpay_risk", "sequence": 470},
    {"name": "settlement_amount_insufficient", "sequence": 480},
    {"name": "settlement_match_blocked", "sequence": 490},
    {"name": "settlement_match_warn", "sequence": 500},
    {"name": "settlement_compliance_message", "sequence": 510},
    {"name": "ledger_line_ids", "sequence": 520},
    {"name": "partner_account_name", "sequence": 600},
    {"name": "partner_bank_name", "sequence": 610},
    {"name": "partner_bank_account", "sequence": 620},
    {"name": "creator_name", "sequence": 900},
    {"name": "created_time", "sequence": 910},
    {"name": "type", "sequence": 920},
    {"name": "receipt_type", "sequence": 930},
]


def _contract_json(payload):
    return json.dumps({"view_orchestration": {"views": {"form": payload}}}, ensure_ascii=False)


def migrate(cr, version):
    sections_json = _contract_json({"sections": PAYMENT_REQUEST_SECTIONS})
    cr.execute(
        """
        UPDATE ui_business_config_contract
           SET contract_json = %s::jsonb,
               write_date = NOW()
         WHERE model = 'payment.request'
           AND name = 'payment_request_form_structure_generated_v1'
        """,
        (_contract_json({"fields": PAYMENT_REQUEST_FIELDS}),),
    )
    cr.execute(
        """
        UPDATE ui_business_config_contract
           SET contract_json = %s::jsonb,
               active = TRUE,
               status = 'published',
               write_date = NOW()
         WHERE model = 'payment.request'
           AND name = 'payment_request_form_sections_v1'
           AND company_id IS NULL
        """,
        (sections_json,),
    )
    cr.execute(
        """
        INSERT INTO ui_business_config_contract
            (name, model, view_type, priority, company_id, active, status, version_no, contract_json, create_date, write_date)
        SELECT
            'payment_request_form_sections_v1', 'payment.request', 'form', 20, NULL, TRUE, 'published', 1, %s::jsonb, NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1
              FROM ui_business_config_contract
             WHERE model = 'payment.request'
               AND name = 'payment_request_form_sections_v1'
               AND company_id IS NULL
        )
        """,
        (sections_json,),
    )
