#!/usr/bin/env python3
"""Static architecture guard for FE-B05's authoritative work workspace."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "addons/smart_construction_core/services/payment_request_work_item_service.py"
COMPONENT = ROOT / "frontend/apps/web/src/components/business/MyWorkApprovalWorkspace.vue"
FORM = ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue"
CONTRACT = ROOT / "addons/smart_construction_core/services/financial_workspace_contract.py"


def require(text: str, needles: list[str], label: str) -> None:
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"[FAIL] {label}: missing {missing}")


def main() -> int:
    service = SERVICE.read_text(encoding="utf-8")
    component = COMPONENT.read_text(encoding="utf-8")
    form = FORM.read_text(encoding="utf-8")
    contract = CONTRACT.read_text(encoding="utf-8")
    if ".sudo(" in service:
        raise SystemExit("[FAIL] payment work projection must not use sudo")
    require(
        service,
        [
            '"todo": "待我处理"',
            '"initiated": "我发起的"',
            "check_access_rights(\"read\"",
            "record.check_access_rule(\"read\")",
            "actor_matches_required_role",
            'return [("company_id", "=", self._active_company_id())]',
        ],
        "payment work projection",
    )
    handler = (ROOT / "addons/smart_construction_core/handlers/my_work_summary.py").read_text(encoding="utf-8")
    require(handler, ['if bool(params.get("product_workspace")):', '"items": []'], "network-safe product workspace branch")
    require(
        component,
        [
            "item.business_type",
            "item.record.label",
            "item.state.label",
            "item.project?.label",
            "item.company?.label",
            "formatMoney(item)",
            "executePaymentRequestAction",
            "dialogRef.value?.showModal()",
            "emit('refresh')",
        ],
        "My Work product component",
    )
    require(
        contract,
        [
            '"key": "create_payment_request"',
            "check_access_rights(\"create\"",
            'has_group("smart_construction_core.group_sc_cap_finance_user")',
            '"default_settlement_id"',
        ],
        "settlement form entry contract",
    )
    if "model === 'payment.request'" in form or 'model === "payment.request"' in form:
        raise SystemExit("[FAIL] generic form contains a payment-request title/render special case")
    print("[OK] FE-B05 authoritative work/form/approval guard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
