#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

HANDLER_ROOT = Path("addons/smart_core/handlers")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def audit_handler_output_styles() -> dict:
    handlers = sorted(HANDLER_ROOT.rglob("*.py"))
    summary = {
        "total_handlers": 0,
        "objectized_handlers": 0,
        "legacy_status_returns": 0,
        "legacy_ok_returns": 0,
        "err_helper_returns": 0,
        "objectized_files": [],
        "legacy_files": [],
    }

    for path in handlers:
        text = _read_text(path)
        rel = str(path)
        summary["total_handlers"] += 1

        has_object = "IntentExecutionResult" in text
        status_count = text.count('return {"status"')
        ok_count = text.count('return {"ok"')
        err_count = text.count("return self._err(") + text.count("return self.err(")

        if has_object:
            summary["objectized_handlers"] += 1
            summary["objectized_files"].append(rel)

        legacy_count = status_count + ok_count + err_count
        if legacy_count > 0:
            summary["legacy_files"].append(
                {
                    "file": rel,
                    "status_returns": status_count,
                    "ok_returns": ok_count,
                    "err_returns": err_count,
                }
            )

        summary["legacy_status_returns"] += status_count
        summary["legacy_ok_returns"] += ok_count
        summary["err_helper_returns"] += err_count

    summary["migration_gauge"] = {
        "objectized_ratio": (
            round(summary["objectized_handlers"] / summary["total_handlers"], 4)
            if summary["total_handlers"]
            else 0.0
        ),
        "objectized_handlers": summary["objectized_handlers"],
        "total_handlers": summary["total_handlers"],
    }

    candidate_rows = []
    for item in summary["legacy_files"]:
        status_returns = int(item.get("status_returns") or 0)
        ok_returns = int(item.get("ok_returns") or 0)
        err_returns = int(item.get("err_returns") or 0)
        score = ok_returns * 3 - status_returns * 2 - err_returns
        candidate_rows.append(
            {
                "file": item.get("file"),
                "candidate_rank": score,
                "status_returns": status_returns,
                "ok_returns": ok_returns,
                "err_returns": err_returns,
            }
        )

    summary["next_candidates"] = sorted(candidate_rows, key=lambda row: row["candidate_rank"], reverse=True)[:8]

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit smart_core handler output styles.")
    parser.add_argument("--json", action="store_true", help="print machine-readable json")
    args = parser.parse_args()

    payload = audit_handler_output_styles()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("handler_output_style_audit")
        print(f"  total_handlers: {payload['total_handlers']}")
        print(f"  objectized_handlers: {payload['objectized_handlers']}")
        print(f"  objectized_ratio: {payload['migration_gauge']['objectized_ratio']}")
        print(f"  legacy_status_returns: {payload['legacy_status_returns']}")
        print(f"  legacy_ok_returns: {payload['legacy_ok_returns']}")
        print(f"  err_helper_returns: {payload['err_helper_returns']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
