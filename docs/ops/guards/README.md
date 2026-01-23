# Guards

This folder stores guard evidence outputs and usage notes.

## mail_from_guard

Goal: enforce alignment between SMTP user, `mail.default.from`, and every `res.company.email`.

Command:

```
make prod.guard.mail_from DB=sc_prod
```

Evidence:

- `docs/ops/guards/mail_from_guard.csv`
- Columns: `kind,identifier,value,match,expected`

Exit codes:

- `0` pass (all values match smtp_user)
- `2` guard fail (mismatch or missing smtp_user)
- `1` runtime error

Fix (manual only):

```
make prod.fix.mail_from DB=sc_prod
```

The fix aligns `mail.default.from` and all company emails to the default mail server `smtp_user` and prints a before/after summary.
