#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME is required}"
PROTECTED_DB_NAME="${PROTECTED_DB_NAME:-sc_demo}"

if [[ "$DB_NAME" == "$PROTECTED_DB_NAME" ]]; then
  echo "[customer.fresh_init.finalize] REFUSE protected database: DB_NAME=$DB_NAME" >&2
  echo "[customer.fresh_init.finalize] Use a temporary database for fresh rebuild validation." >&2
  exit 2
fi

echo "[customer.fresh_init.finalize] db=${DB_NAME}"

compose_dev run --rm -T \
  --entrypoint /usr/bin/odoo odoo \
  shell \
  --config="$ODOO_CONF" \
  -d "$DB_NAME" \
  --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,"$ADDONS_EXTERNAL_MOUNT" <<'PY'
company_name = "四川保盛建设集团有限公司"
policy = env["sc.security.policy"].sudo()
policy.bootstrap_customer_company_departments()

company = env.ref("base.main_company", raise_if_not_found=False)
currency = env.ref("base.CNY", raise_if_not_found=False)
if not company:
    raise RuntimeError("base.main_company is missing after customer initialization")
if not currency:
    raise RuntimeError("base.CNY is missing after customer initialization")
if not currency.active:
    currency.sudo().write({"active": True})
if company.name != company_name:
    company.sudo().write({"name": company_name, "active": True})
if company.currency_id != currency:
    if "account.move.line" in env.registry and env["account.move.line"].sudo().search_count([]):
        raise RuntimeError("refuse to switch company currency after journal items exist")
    company.sudo().write({"currency_id": currency.id})

duplicates = env["res.company"].sudo().search([
    ("name", "=", company_name),
    ("active", "=", True),
])
if len(duplicates) != 1 or duplicates != company:
    raise RuntimeError("customer company baseline is not unique after finalization")

users = env["res.users"].sudo().search([
    ("login", "in", [
        "wutao",
        "yangdesheng",
        "zhangwencui",
        "lijianfeng",
        "yelingyue",
        "lidexue",
        "chenshuai",
    ]),
])
for user in users:
    values = {}
    if user.company_id != company:
        values["company_id"] = company.id
    if user.company_ids != company:
        values["company_ids"] = [(6, 0, [company.id])]
    if values:
        user.with_context(no_reset_password=True).sudo().write(values)

env.cr.commit()

from odoo.addons.smart_construction_custom.hooks import ensure_customer_default_taxes

ensure_customer_default_taxes(env)
env.cr.commit()
tax_sale = env.ref("smart_construction_seed.tax_sale_9", raise_if_not_found=False)
tax_purchase = env.ref("smart_construction_seed.tax_purchase_13", raise_if_not_found=False)
if not tax_sale or not tax_purchase:
    raise RuntimeError("customer default tax XMLIDs are missing after finalization")

print(
    "[customer.fresh_init.finalize] PASS company=%s currency=%s users=%s tax_sale=%s tax_purchase=%s"
    % (company.id, company.currency_id.name, len(users), tax_sale.id, tax_purchase.id)
)
PY
