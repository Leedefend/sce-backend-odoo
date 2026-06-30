# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/mnt") if Path("/mnt/artifacts").exists() else Path.cwd()
REPORT_JSON = ROOT / "artifacts" / "backend" / "ledger_reconciliation_trend.json"
REPORT_MD = ROOT / "artifacts" / "backend" / "ledger_reconciliation_trend.md"
HISTORY_JSONL = ROOT / "artifacts" / "backend" / "history" / "ledger_reconciliation_trend_samples.jsonl"
LEDGER_SNAPSHOT_PATH = ROOT / "artifacts" / "backend" / "ledger_snapshot_smoke.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _scalar(sql: str, params: tuple = ()):
    env.cr.execute(sql, params)  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def _rows(sql: str, params: tuple = ()) -> list[dict]:
    env.cr.execute(sql, params)  # noqa: F821
    columns = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def _num(value) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


def _count(value) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _state_distribution(table: str) -> list[dict]:
    return _rows(
        f"""
        SELECT COALESCE(state, '') AS state, COUNT(*)::integer AS count
          FROM {table}
         GROUP BY COALESCE(state, '')
         ORDER BY count DESC, state
        """
    )


def _last_history_sample() -> dict:
    if not HISTORY_JSONL.is_file():
        return {}
    last = ""
    for line in HISTORY_JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            last = line
    if not last:
        return {}
    try:
        payload = json.loads(last)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _delta(current: dict, previous: dict) -> dict:
    keys = [
        "payment_ledger_count",
        "payment_ledger_missing_request_count",
        "treasury_ledger_count",
        "treasury_ledger_source_less_count",
        "settlement_order_count",
        "settlement_positive_payable_count",
        "treasury_reconciliation_count",
        "treasury_reconciliation_nonzero_difference_count",
        "treasury_reconciliation_without_ledger_count",
    ]
    out = {}
    for key in keys:
        out[key] = _count(current.get(key)) - _count(previous.get(key))
    return out


def _to_markdown(payload: dict) -> str:
    observed = payload.get("observed") if isinstance(payload.get("observed"), dict) else {}
    trend = payload.get("trend") if isinstance(payload.get("trend"), dict) else {}
    lines = [
        "# Ledger Reconciliation Trend",
        "",
        f"- generated_at_utc: {payload.get('generated_at_utc', '')}",
        f"- ok: {payload.get('ok')}",
        f"- has_previous: {trend.get('has_previous', False)}",
        "",
        "## Observed",
        "",
        "| metric | value |",
        "|---|---:|",
    ]
    for key in sorted(observed.keys()):
        value = observed.get(key)
        if isinstance(value, (int, float)):
            lines.append(f"| {key} | {value} |")
    if isinstance(trend.get("delta"), dict):
        lines.extend(["", "## Delta", "", "| metric | delta |", "|---|---:|"])
        for key, value in sorted(trend["delta"].items()):
            lines.append(f"| {key} | {value} |")
    errors = payload.get("errors") if isinstance(payload.get("errors"), list) else []
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {item}" for item in errors)
    return "\n".join(lines) + "\n"


errors: list[str] = []
snapshot = _load_json(LEDGER_SNAPSHOT_PATH)
if not snapshot:
    errors.append("ledger_snapshot_smoke_missing")
elif not bool(snapshot.get("ok")):
    errors.append("ledger_snapshot_smoke_not_ok")

observed = {
    "payment_ledger_count": _count(_scalar("SELECT COUNT(*) FROM payment_ledger")),
    "payment_ledger_amount_sum": _num(_scalar("SELECT COALESCE(SUM(amount), 0.0) FROM payment_ledger")),
    "payment_ledger_missing_request_count": _count(_scalar("SELECT COUNT(*) FROM payment_ledger WHERE payment_request_id IS NULL")),
    "treasury_ledger_count": _count(_scalar("SELECT COUNT(*) FROM sc_treasury_ledger")),
    "treasury_ledger_amount_sum": _num(_scalar("SELECT COALESCE(SUM(amount), 0.0) FROM sc_treasury_ledger WHERE COALESCE(state, '') != 'void'")),
    "treasury_ledger_source_less_count": _count(
        _scalar(
            """
            SELECT COUNT(*)
              FROM sc_treasury_ledger
             WHERE COALESCE(source_model, '') = ''
               AND COALESCE(payment_request_id, 0) = 0
               AND COALESCE(settlement_id, 0) = 0
               AND COALESCE(state, '') != 'void'
            """
        )
    ),
    "settlement_order_count": _count(_scalar("SELECT COUNT(*) FROM sc_settlement_order")),
    "settlement_amount_total_sum": _num(_scalar("SELECT COALESCE(SUM(amount_total), 0.0) FROM sc_settlement_order WHERE active IS TRUE")),
    "settlement_amount_payable_sum": _num(_scalar("SELECT COALESCE(SUM(amount_payable), 0.0) FROM sc_settlement_order WHERE active IS TRUE")),
    "settlement_positive_payable_count": _count(_scalar("SELECT COUNT(*) FROM sc_settlement_order WHERE active IS TRUE AND COALESCE(amount_payable, 0.0) > 0.0")),
    "treasury_reconciliation_count": _count(_scalar("SELECT COUNT(*) FROM sc_treasury_reconciliation")),
    "treasury_reconciliation_nonzero_difference_count": _count(
        _scalar("SELECT COUNT(*) FROM sc_treasury_reconciliation WHERE COALESCE(system_difference, 0.0) != 0.0")
    ),
    "treasury_reconciliation_abs_difference_sum": _num(
        _scalar("SELECT COALESCE(SUM(ABS(system_difference)), 0.0) FROM sc_treasury_reconciliation")
    ),
    "treasury_reconciliation_without_ledger_count": _count(
        _scalar("SELECT COUNT(*) FROM sc_treasury_reconciliation WHERE treasury_ledger_id IS NULL")
    ),
}

if observed["payment_ledger_count"] <= 0:
    errors.append("payment_ledger_empty")
if observed["treasury_ledger_count"] <= 0:
    errors.append("treasury_ledger_empty")
if observed["settlement_order_count"] <= 0:
    errors.append("settlement_order_empty")
if observed["treasury_reconciliation_count"] <= 0:
    errors.append("treasury_reconciliation_empty")
if observed["payment_ledger_missing_request_count"] > 0:
    errors.append("payment_ledger_missing_request_count=%s" % observed["payment_ledger_missing_request_count"])

previous = _last_history_sample()
trend = {
    "has_previous": bool(previous),
    "history_path": str(HISTORY_JSONL.relative_to(ROOT)),
    "delta": _delta(observed, previous.get("observed") if isinstance(previous.get("observed"), dict) else {}),
}
payload = {
    "generated_at_utc": _utc_now(),
    "ok": not errors,
    "audit": "ledger_reconciliation_trend",
    "db": env.cr.dbname,  # noqa: F821
    "company_id": int(env.company.id),  # noqa: F821
    "observed": observed,
    "state_distribution": {
        "treasury_ledger": _state_distribution("sc_treasury_ledger"),
        "treasury_reconciliation": _state_distribution("sc_treasury_reconciliation"),
        "settlement_order": _state_distribution("sc_settlement_order"),
    },
    "snapshot": {
        "path": str(LEDGER_SNAPSHOT_PATH.relative_to(ROOT)),
        "ok": bool(snapshot.get("ok")),
    },
    "trend": trend,
    "reports": {
        "json": str(REPORT_JSON.relative_to(ROOT)),
        "md": str(REPORT_MD.relative_to(ROOT)),
    },
    "errors": errors,
}

_write(REPORT_JSON, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
_write(REPORT_MD, _to_markdown(payload))
HISTORY_JSONL.parent.mkdir(parents=True, exist_ok=True)
with HISTORY_JSONL.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps({"generated_at_utc": payload["generated_at_utc"], "observed": observed}, ensure_ascii=False, sort_keys=True) + "\n")

print(REPORT_JSON)
print(REPORT_MD)
print("[ledger_reconciliation_trend] PASS" if payload["ok"] else "[ledger_reconciliation_trend] FAIL")
if errors:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(1)
