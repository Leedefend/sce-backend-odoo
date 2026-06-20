#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_DATA = ROOT / "addons/smart_construction_custom/data"
SOURCE_MANIFEST = MODULE_DATA / "user_data_rebaseline_source_manifest_v1.json"
REPLAY_PREFLIGHT = MODULE_DATA / "user_data_rebaseline_replay_asset_preflight_v1.json"
BASELINE_CONTRACT = MODULE_DATA / "user_module_data_baseline_contract_v1.json"


def _load(path: Path) -> dict:
    if not path.exists():
        raise AssertionError(f"missing {path.relative_to(ROOT).as_posix()}")
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    try:
        source = _load(SOURCE_MANIFEST)
        preflight = _load(REPLAY_PREFLIGHT)
        contract = _load(BASELINE_CONTRACT)
    except Exception as exc:
        print("[user_module_data_rebaseline_contract_guard] FAIL")
        print(f"- {exc}")
        return 1

    _require(source.get("status") == "PASS", "source manifest must be PASS", failures)
    policy = source.get("policy") if isinstance(source.get("policy"), dict) else {}
    _require(
        policy.get("attachment_policy") == "link_only_until_prod_attachment_ready",
        "source manifest must keep link-only attachment policy",
        failures,
    )
    forbidden_inputs = set(policy.get("forbidden_inputs") or [])
    for forbidden in ["obsolete_20260513_release_package", "manual_development_database_residue"]:
        _require(forbidden in forbidden_inputs, f"source manifest must forbid {forbidden}", failures)

    online_sources = source.get("online_sources") if isinstance(source.get("online_sources"), dict) else {}
    scbs55 = online_sources.get("scbs55") if isinstance(online_sources.get("scbs55"), dict) else {}
    scbsly = online_sources.get("scbsly_v2") if isinstance(online_sources.get("scbsly_v2"), dict) else {}
    _require(int(scbs55.get("surface_count") or 0) == 42, "SCBS55 must lock 42 surfaces", failures)
    _require(int(scbs55.get("total_row_count") or 0) >= 140000, "SCBS55 row count is below baseline", failures)
    _require(int(scbsly.get("surface_count") or 0) == 32, "SCBSLY_V2 must lock 32 surfaces", failures)
    _require(int(scbsly.get("total_row_count") or 0) >= 76000, "SCBSLY_V2 row count is below baseline", failures)

    structured_sources = source.get("structured_db_sources")
    structured_sources = structured_sources if isinstance(structured_sources, dict) else {}
    legacy_counts = structured_sources.get("legacy_counts") if isinstance(structured_sources.get("legacy_counts"), list) else []
    _require(len(legacy_counts) >= 9, "source manifest must include core legacy MSSQL count evidence", failures)

    _require(preflight.get("status") == "PASS", "replay asset preflight must be PASS", failures)
    checks = preflight.get("checks") if isinstance(preflight.get("checks"), dict) else {}
    history_payloads = checks.get("history_payloads") if isinstance(checks.get("history_payloads"), dict) else {}
    _require(
        int(history_payloads.get("present") or 0) == 52 and int(history_payloads.get("required") or 0) == 52,
        "history replay payloads must be locked at 52/52",
        failures,
    )
    core_assets = checks.get("core_replay_assets") if isinstance(checks.get("core_replay_assets"), list) else []
    _require(
        len(core_assets) == 7 and all(item.get("exists") for item in core_assets if isinstance(item, dict)),
        "core replay assets must be locked at 7/7",
        failures,
    )
    for key, expected in [("scbs55", 42), ("scbsly_v2", 32)]:
        link_check = checks.get(f"stable_online_dump_links_{key}")
        link_check = link_check if isinstance(link_check, dict) else {}
        _require(
            int(link_check.get("entries") or 0) == expected,
            f"{key} stable online dump links must be {expected}/{expected}",
            failures,
        )
        _require(not link_check.get("broken_links"), f"{key} stable online dump links must not be broken", failures)

    _require(contract.get("version") == "user_module_data_baseline_contract.v1", "contract version mismatch", failures)
    _require(
        contract.get("status") == "READY_FOR_USER_MODULE_PACKAGING",
        "contract must be ready for user module packaging",
        failures,
    )
    attachment_policy = contract.get("attachment_policy") if isinstance(contract.get("attachment_policy"), dict) else {}
    _require(attachment_policy.get("mode") == "link_only", "contract attachment policy must be link_only", failures)
    standard = contract.get("installation_standard") if isinstance(contract.get("installation_standard"), dict) else {}
    acceptance = standard.get("fresh_database_acceptance") or []
    for required in [
        "source manifest status PASS",
        "replay asset preflight PASS",
        "SCBS55 online rows linked 42/42",
        "SCBSLY_V2 online rows linked 32/32",
        "history payloads present 52/52",
        "core replay assets present 7/7",
        "attachments remain link-only until production attachment source is prepared",
    ]:
        _require(required in acceptance, f"contract missing fresh database acceptance: {required}", failures)

    if failures:
        print("[user_module_data_rebaseline_contract_guard] FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("[user_module_data_rebaseline_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
