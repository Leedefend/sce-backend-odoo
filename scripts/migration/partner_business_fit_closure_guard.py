#!/usr/bin/env python3
"""End-to-end no-DB closure guard for the business-fit partner lane."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


BUSINESS_RESULT = Path(
    "artifacts/migration/partner_business_aligned_rebuild_v1/"
    "fact_based_partner_rebuild_business_aligned_result_v1.json"
)
GATE_RESULT = Path(
    "artifacts/migration/partner_business_aligned_rebuild_v1/"
    "fact_based_partner_rebuild_business_aligned_gate_result_v1.json"
)
REVIEW_RESULT = Path("artifacts/migration/partner_business_aligned_rebuild_v1/partner_import_review_queue_result_v1.json")
PACKAGE_RESULT = Path("artifacts/migration/partner_business_aligned_replay_package_v1/package_build_result_v1.json")


def run(command: list[str]) -> str:
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if proc.returncode != 0:
        raise RuntimeError({"command_failed": command, "output": proc.stdout})
    return proc.stdout


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        raise RuntimeError({"missing_required_result": str(path)})
    return json.loads(path.read_text(encoding="utf-8"))


def expect_equal(errors: list[dict[str, object]], label: str, actual: object, expected: object) -> None:
    if actual != expected:
        errors.append({"check": label, "actual": actual, "expected": expected})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    result: dict[str, object]
    try:
        asset_guard = run(["python3", "scripts/migration/partner_asset_business_fit_guard.py", "--check"])
        display_guard = run(["python3", "scripts/migration/partner_display_surface_guard.py", "--check"])
        review_asset = run(["python3", "scripts/migration/partner_import_review_asset_generator.py", "--check"])
        package_build = run(["python3", "scripts/migration/partner_business_aligned_replay_package_build.py"])

        business = load_json(BUSINESS_RESULT)
        gate = load_json(GATE_RESULT)
        review = load_json(REVIEW_RESULT)
        package = load_json(PACKAGE_RESULT)
        gate_counts = gate.get("gate_action_counts") or {}
        errors: list[dict[str, object]] = []
        expect_equal(errors, "business_aligned_payload_rows", business.get("business_aligned_payload_rows"), 7792)
        expect_equal(errors, "business_rows_with_bank_account", business.get("rows_with_bank_account"), 6602)
        expect_equal(errors, "business_rows_with_tax_rate", business.get("rows_with_tax_rate"), 3741)
        expect_equal(errors, "gate_write_candidate", gate_counts.get("write_candidate"), 2123)
        expect_equal(errors, "gate_update_only_candidate", gate_counts.get("update_only_candidate"), 4225)
        expect_equal(errors, "gate_blocked_review", gate_counts.get("blocked_review"), 1444)
        expect_equal(errors, "review_status", review.get("status"), "PASS")
        expect_equal(errors, "review_rows", review.get("review_rows"), 1444)
        expect_equal(errors, "package_status", package.get("status"), "PASS")
        if int(package.get("file_count") or 0) < 29:
            errors.append({"check": "package_file_count_min", "actual": package.get("file_count"), "expected_min": 29})
        if errors:
            raise RuntimeError({"partner_business_fit_closure_guard_failed": errors})

        result = {
            "status": "PASS",
            "mode": "partner_business_fit_closure_guard",
            "business_aligned_payload_rows": business.get("business_aligned_payload_rows"),
            "gate_action_counts": gate_counts,
            "review_rows": review.get("review_rows"),
            "package_file_count": package.get("file_count"),
            "package_tarball_sha256": package.get("tarball_sha256"),
            "asset_guard": asset_guard.strip(),
            "display_guard": display_guard.strip(),
            "review_asset": review_asset.strip(),
            "package_build": package_build.strip(),
            "db_writes": 0,
        }
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0}
        print("PARTNER_BUSINESS_FIT_CLOSURE_GUARD=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("PARTNER_BUSINESS_FIT_CLOSURE_GUARD=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
