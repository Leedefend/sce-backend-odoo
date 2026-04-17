# Mail Runtime Submit Blocker Screen v1

## Purpose

After finance visibility and project funding carrier facts were corrected,
payment submit reached notification processing and failed with:

```text
Unable to send message, please configure the sender's email address.
```

This screen classifies the runtime mail facts. It does not write runtime config
or business data.

## Screen Result

Runtime mail facts in `sc_demo`:

- mail server exists: false
- SMTP user exists: false
- `mail.default.from` exists: false
- company email missing count: 1
- finance user email: empty
- finance partner email: empty

Company:

- `四川保盛建设集团有限公司`: empty email

User:

- `sc_fx_finance`: empty user email and partner email

## Classification

This is a runtime configuration blocker.

It is not:

- a project funding fact issue
- a contract/payment linkage issue
- an approval rule issue
- a frontend issue

## Next Batch

Open a dedicated runtime config batch for dev/demo:

- set a deterministic non-production sender address
- set `mail.default.from`
- set company email
- set finance user partner/email if required by submit notification
- do not configure production SMTP
- verify payment submit again with rollback-only created payment request
