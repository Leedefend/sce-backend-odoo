#!/usr/bin/env python3
"""Replay frozen migration asset XML files into an Odoo database.

This script is executed inside ``odoo shell`` and intentionally uses ORM
creates plus ``ir.model.data`` instead of direct table inserts.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


ASSET_ROOT = Path(os.environ.get("MIGRATION_ASSET_ROOT", "/var/lib/odoo/addons/17.0/migration_assets"))
ASSET_MODULE = os.environ.get("MIGRATION_ASSET_MODULE", "migration_assets")
BATCH_SIZE = int(os.environ.get("MIGRATION_ASSET_BATCH_SIZE", "1000"))
CATALOG_PATH = ASSET_ROOT / "manifest/migration_asset_catalog_v1.json"
PROTECTED_DB_NAME = os.environ.get("PROTECTED_DB_NAME", "sc_demo")

REPLAY_CONTEXT = {
    "tracking_disable": True,
    "mail_create_nosubscribe": True,
    "mail_create_nolog": True,
    "no_reset_password": True,
    "install_mode": True,
    "sc_legacy_asset_replay_allow_contract_direction_mismatch": True,
    "sc_legacy_asset_replay_skip_payment_evidence": True,
}


class MigrationAssetReplayError(Exception):
    pass


def log(message: str) -> None:
    print(message, flush=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MigrationAssetReplayError(message)


def load_json(path: Path) -> dict:
    require(path.exists(), f"json file does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def field_value(field, text):
    if text is None:
        return False
    if field.type == "boolean":
        return str(text).strip().lower() in {"1", "true", "yes"}
    if field.type == "integer":
        value = str(text).strip()
        return int(float(value)) if value else False
    if field.type in {"float", "monetary"}:
        value = str(text).strip()
        return float(value) if value else False
    if field.type == "many2one":
        value = str(text).strip()
        return int(value) if value else False
    if field.type in {"date", "datetime", "selection"}:
        value = str(text).strip()
        return value or False
    return text


def load_xmlid_cache():
    cache = {}
    rows = env["ir.model.data"].sudo().search([("module", "=", ASSET_MODULE)])  # noqa: F821
    for row in rows:
        cache[row.name] = (row.model, row.res_id)
    return cache


def resolve_ref(ref: str, cache: dict[str, tuple[str, int]]) -> int:
    if "." in ref:
        module, name = ref.split(".", 1)
    else:
        module, name = ASSET_MODULE, ref

    if module == ASSET_MODULE and name in cache:
        return cache[name][1]

    imd = env["ir.model.data"].sudo().search(  # noqa: F821
        [("module", "=", module), ("name", "=", name)],
        limit=1,
    )
    require(bool(imd), f"unresolved_ref {ref}")
    if module == ASSET_MODULE:
        cache[name] = (imd.model, imd.res_id)
    return imd.res_id


def record_values(model_name: str, record_node, cache: dict[str, tuple[str, int]]) -> dict:
    model = env[model_name]  # noqa: F821
    values = {}
    for field_node in record_node.findall("field"):
        field_name = field_node.attrib["name"]
        require(
            field_name in model._fields,
            f"unknown_field model={model_name} field={field_name} xml_id={record_node.attrib.get('id')}",
        )
        field = model._fields[field_name]
        if "ref" in field_node.attrib:
            values[field_name] = resolve_ref(field_node.attrib["ref"], cache)
        else:
            values[field_name] = field_value(field, field_node.text)
    return values


def create_chunk(model_name: str, chunk: list[tuple[str, dict]], cache: dict[str, tuple[str, int]], counters: Counter) -> None:
    model = env[model_name].sudo().with_context(**REPLAY_CONTEXT)  # noqa: F821
    records = model.create([values for _name, values in chunk])
    imd_values = []
    for (name, _values), record in zip(chunk, records):
        cache[name] = (model_name, record.id)
        imd_values.append(
            {
                "module": ASSET_MODULE,
                "name": name,
                "model": model_name,
                "res_id": record.id,
                "noupdate": True,
            }
        )
    env["ir.model.data"].sudo().create(imd_values)  # noqa: F821
    counters["created_records"] += len(records)


def iter_xml_assets(catalog: dict):
    packages = catalog.get("packages", [])
    by_id = {package["asset_package_id"]: package for package in packages}
    for package_id in catalog.get("package_order", []):
        package = by_id[package_id]
        manifest = load_json(ASSET_ROOT / package["asset_manifest_path"])
        for asset in manifest.get("assets", []):
            if str(asset.get("path", "")).endswith(".xml"):
                yield package_id, asset["path"]


def replay_file(package_id: str, rel_path: str, cache: dict[str, tuple[str, int]], counters: Counter) -> Counter:
    xml_path = ASSET_ROOT / rel_path
    require(xml_path.exists(), f"xml asset does not exist: {xml_path}")
    records = list(ET.parse(xml_path).getroot().iter("record"))
    expected = Counter(record.attrib["model"] for record in records)
    log(f"FILE_BEGIN package={package_id} file={rel_path} records={len(records)}")

    pending: dict[str, list[tuple[str, dict]]] = {}
    skipped = 0
    for record_node in records:
        xmlid = record_node.attrib["id"]
        model_name = record_node.attrib["model"]
        if xmlid in cache:
            skipped += 1
            counters["skipped_existing_records"] += 1
            continue

        values = record_values(model_name, record_node, cache)
        pending.setdefault(model_name, []).append((xmlid, values))
        if len(pending[model_name]) >= BATCH_SIZE:
            create_chunk(model_name, pending[model_name], cache, counters)
            pending[model_name] = []
            env.cr.commit()  # noqa: F821
            log(
                "FILE_PROGRESS "
                f"file={rel_path} model={model_name} "
                f"created_total={counters['created_records']} "
                f"skipped_total={counters['skipped_existing_records']}"
            )

    for model_name, chunk in pending.items():
        if chunk:
            create_chunk(model_name, chunk, cache, counters)
    env.cr.commit()  # noqa: F821
    log(
        "FILE_DONE "
        f"package={package_id} file={rel_path} "
        f"created_total={counters['created_records']} skipped_file={skipped}"
    )
    return expected


def main() -> int:
    require(
        env.cr.dbname != PROTECTED_DB_NAME,  # noqa: F821
        f"refuse protected database for migration asset replay: {PROTECTED_DB_NAME}",
    )
    require(ASSET_ROOT.exists(), f"asset root does not exist: {ASSET_ROOT}")
    catalog = load_json(CATALOG_PATH)
    cache = load_xmlid_cache()
    counters = Counter()
    expected = Counter()

    log(
        "MIGRATION_ASSET_REPLAY_START "
        f"db={env.cr.dbname} asset_root={ASSET_ROOT} module={ASSET_MODULE} existing_xmlids={len(cache)}"  # noqa: F821
    )
    for package_id, rel_path in iter_xml_assets(catalog):
        expected.update(replay_file(package_id, rel_path, cache, counters))

    actual = Counter(
        env["ir.model.data"].sudo().search([("module", "=", ASSET_MODULE)]).mapped("model")  # noqa: F821
    )
    missing = {
        model: expected[model] - actual.get(model, 0)
        for model in expected
        if actual.get(model, 0) < expected[model]
    }
    require(not missing, f"missing_xmlid_counts={missing}")
    result = {
        "status": "PASS",
        "database": env.cr.dbname,  # noqa: F821
        "asset_root": str(ASSET_ROOT),
        "asset_module": ASSET_MODULE,
        "expected_xml_model_counts": dict(sorted(expected.items())),
        "actual_module_model_counts": dict(sorted(actual.items())),
        "created_records": counters["created_records"],
        "skipped_existing_records": counters["skipped_existing_records"],
        "db_writes": counters["created_records"],
        "odoo_shell": True,
    }
    log("MIGRATION_ASSET_REPLAY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


main()
