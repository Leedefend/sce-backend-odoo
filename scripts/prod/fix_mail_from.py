import sys
import traceback


def _safe_str(value):
    return (value or "").strip()


def main():
    if "env" not in globals():
        print("ERROR: Odoo env not found. Run via odoo shell.", file=sys.stderr)
        raise SystemExit(1)

    mail_server_model = env["ir.mail_server"].sudo()
    if hasattr(mail_server_model, "_get_default_mail_server"):
        mail_server = mail_server_model._get_default_mail_server()
    else:
        mail_server = mail_server_model.search([("active", "=", True)], order="sequence,id", limit=1)
        if not mail_server:
            mail_server = mail_server_model.search([], order="sequence,id", limit=1)
    smtp_user = _safe_str(mail_server.smtp_user) if mail_server else ""
    if not smtp_user:
        print("ERROR: default mail server or smtp_user is missing.", file=sys.stderr)
        raise SystemExit(1)

    icp = env["ir.config_parameter"].sudo()
    companies = env["res.company"].sudo().search([])

    before_icp = _safe_str(icp.get_param("mail.default.from"))
    before_companies = {c.id: _safe_str(c.email) for c in companies}

    icp.set_param("mail.default.from", smtp_user)
    if companies:
        companies.write({"email": smtp_user})

    env.cr.commit()

    after_icp = _safe_str(icp.get_param("mail.default.from"))
    after_companies = {c.id: _safe_str(c.email) for c in companies}

    print("FIX: mail_from aligned to smtp_user")
    print(f"smtp_user={smtp_user}")
    print(f"mail.default.from: {before_icp} -> {after_icp}")
    for company in companies:
        before = before_companies.get(company.id, "")
        after = after_companies.get(company.id, "")
        print(f"company {company.id} {company.name}: {before} -> {after}")

    raise SystemExit(0)


try:
    main()
except SystemExit:
    raise
except Exception:
    print("ERROR: fix_mail_from crashed", file=sys.stderr)
    traceback.print_exc()
    raise SystemExit(1)
