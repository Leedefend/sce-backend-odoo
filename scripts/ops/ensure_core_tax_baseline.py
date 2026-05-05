"""Ensure core tax baseline before historical data replay."""

from odoo.addons.smart_construction_core.hooks import ensure_core_taxes


ensure_core_taxes(env)  # noqa: F821

Tax = env["account.tax"].sudo().with_context(active_test=False)  # noqa: F821
required = [
    ("销项VAT 9%", 9.0, "sale"),
    ("进项VAT 13%", 13.0, "purchase"),
]
missing = []
for name, amount, type_tax_use in required:
    tax = Tax.search(
        [
            ("company_id", "=", env.company.id),  # noqa: F821
            ("name", "=", name),
            ("amount", "=", amount),
            ("amount_type", "=", "percent"),
            ("type_tax_use", "=", type_tax_use),
        ],
        limit=1,
    )
    if not tax:
        missing.append({"name": name, "amount": amount, "type_tax_use": type_tax_use})
    elif not tax.active:
        tax.active = True

if missing:
    raise RuntimeError({"missing_core_tax_baseline": missing})

env.cr.commit()  # noqa: F821
print(
    {
        "status": "PASS",
        "mode": "ensure_core_tax_baseline",
        "database": env.cr.dbname,  # noqa: F821
        "required": len(required),
    }
)
