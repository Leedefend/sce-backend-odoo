#!/usr/bin/env python3
"""Static contract guard for the FE-B04 financial workspace boundary."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend/apps/web/src"


def fail(message):
    raise SystemExit("[frontend_financial_workspace_guard] FAIL: %s" % message)


contract = (FRONTEND / "app/financialWorkspaceContract.ts").read_text(encoding="utf-8")
workspace = (FRONTEND / "components/business/FinancialRelationshipWorkspace.vue").read_text(encoding="utf-8")
dialog = (FRONTEND / "components/business/IntentConfirmationDialog.vue").read_text(encoding="utf-8")
page = (FRONTEND / "pages/ContractFormPage.vue").read_text(encoding="utf-8")
action_rows = (FRONTEND / "pages/contractForm/authoritativeBusinessActionRows.ts").read_text(encoding="utf-8")
backend = (ROOT / "addons/smart_construction_core/services/financial_workspace_contract.py").read_text(encoding="utf-8")
assembler = (ROOT / "addons/smart_core/app_config_engine/services/assemblers/page_assembler.py").read_text(encoding="utf-8")

for marker in (
    "关键事实摘要", "上下游关系", "业务明细", "审计信息",
    "formatWorkspaceMoney", "currency_risk", "data-relation-key",
):
    if marker not in workspace:
        fail("workspace is missing semantic marker %s" % marker)

for marker in ("role=\"dialog\"", "aria-modal=\"true\"", "focus", "@submit.prevent"):
    if marker not in dialog:
        fail("confirmation dialog is missing accessibility/submission guard %s" % marker)

if "value === null || value === undefined || value === ''" not in contract:
    fail("money formatter does not distinguish null from numeric zero")
if "Number.isFinite(amount)" not in contract or "Intl.NumberFormat" not in contract:
    fail("money formatter is not centralized")

for forbidden in ("model ===", "model !==", "includes(model)", "switch (model)", "switch(model)"):
    if forbidden in workspace or forbidden in contract:
        fail("frontend workspace contains a model-specific branch: %s" % forbidden)

if "FinancialRelationshipWorkspace" not in page or "IntentConfirmationDialog" not in page:
    fail("ContractFormPage does not consume the shared workspace and confirmation dialog")
if "window.confirm" in page:
    fail("legacy browser confirmation remains in ContractFormPage")
if "authoritativeMutationMethods" not in action_rows or "selectAuthoritativeBusinessActionRows" not in page:
    fail("authoritative intent actions do not suppress duplicate workflow mutations")

for marker in (
    "WORKSPACE_DECLARATIONS", "check_access_rule", "operating_metrics",
    "settlement_actual_paid_amount_map", "currency_mismatch", "projection_only",
):
    if marker not in backend:
        fail("backend projection is missing authority marker %s" % marker)
if ".sudo().search" in backend or ".sudo().browse" in backend:
    fail("business relationship projection must not bypass record access")
if '"business_workspace"' not in assembler:
    fail("generic page assembler does not carry the workspace extension")

print("[frontend_financial_workspace_guard] PASS")
