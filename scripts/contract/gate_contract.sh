#!/usr/bin/env bash
set -euo pipefail

CASES_FILE=${CASES_FILE:-docs/contract/cases.yml}
DB_NAME=${DB:-${DB_NAME:-}}
REF_DIR=${REF_DIR:-docs/contract/snapshots}
TMP_DIR=${TMP_DIR:-tmp/contract_snapshots_run}
IGNORE_KEYS=${IGNORE_KEYS:-trace_id,exported_at,generated_at,done_at,server_time,create_date,write_date,__last_update,create_uid,write_uid,version,request_id,last_updated_at}
BOOTSTRAP=${BOOTSTRAP:-0}
BOOTSTRAP_PASS=${BOOTSTRAP_PASS:-0}
IGNORE_NULL_TOP_LEVEL_ERROR=${IGNORE_NULL_TOP_LEVEL_ERROR:-1}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --bootstrap)
      BOOTSTRAP=1
      ;;
    --bootstrap-pass)
      BOOTSTRAP_PASS=1
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: gate_contract.sh [--bootstrap] [--bootstrap-pass]

  --bootstrap       Copy missing baselines into REF_DIR.
  --bootstrap-pass  Exit 0 when bootstrapping missing baselines.
USAGE
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 2
      ;;
  esac
  shift
done

if [ -z "$DB_NAME" ]; then
  echo "DB not set; use DB=your_db" >&2
  exit 2
fi

rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

OUTDIR="$TMP_DIR" CASES_FILE="$CASES_FILE" DB="$DB_NAME" CONTRACT_CONFIG="${CONTRACT_CONFIG:-}" ODOO_CONF="${ODOO_CONF:-}" scripts/contract/export_all.sh

IGNORE_KEYS="$IGNORE_KEYS" REF_DIR="$REF_DIR" TMP_DIR="$TMP_DIR" BOOTSTRAP="$BOOTSTRAP" BOOTSTRAP_PASS="$BOOTSTRAP_PASS" IGNORE_NULL_TOP_LEVEL_ERROR="$IGNORE_NULL_TOP_LEVEL_ERROR" python3 - <<'PY'
import difflib
import json
import os
import shutil
import sys


def _read_trace_id(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("trace_id")
    except Exception:
        return "unknown"


def _strip_keys(obj, ignore_keys, depth=0, parent_key=""):
    if isinstance(obj, dict):
        cleaned = {
            k: _strip_keys(v, ignore_keys, depth + 1, k)
            for k, v in obj.items()
            if k not in ignore_keys
        }
        if (
            os.environ.get("IGNORE_NULL_TOP_LEVEL_ERROR", "1") == "1"
            and depth == 0
            and "error" in cleaned
            and cleaned.get("error") is None
        ):
            cleaned.pop("error", None)
        return cleaned
    if isinstance(obj, list):
        normalized = [_strip_keys(v, ignore_keys, depth + 1, parent_key) for v in obj]
        # Normalize domain atoms like: [field, "in"|"not in", [values...]]
        # where scalar value order is non-semantic.
        if (
            len(normalized) >= 3
            and isinstance(normalized[1], str)
            and normalized[1] in ("in", "not in")
            and isinstance(normalized[2], list)
            and all(isinstance(v, (str, int, float, bool)) for v in normalized[2])
        ):
            normalized[2] = sorted(normalized[2], key=lambda v: str(v))
        # Normalize known set-like scalar lists whose order is non-semantic.
        if parent_key in ("groups_xmlids",) and all(isinstance(v, (str, int, float, bool)) for v in normalized):
            normalized = sorted(normalized, key=lambda v: str(v))
        return normalized
    return obj


def _shapeize(obj):
    if isinstance(obj, dict):
        return {k: _shapeize(v) for k, v in sorted(obj.items(), key=lambda kv: kv[0])}
    if isinstance(obj, list):
        if not obj:
            return []
        shaped = [_shapeize(v) for v in obj]
        uniq = []
        seen = set()
        for item in shaped:
            sig = json.dumps(item, ensure_ascii=False, sort_keys=True)
            if sig in seen:
                continue
            seen.add(sig)
            uniq.append(item)
        uniq.sort(key=lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True))
        return uniq
    if isinstance(obj, bool):
        return "bool"
    if isinstance(obj, int):
        return "int"
    if isinstance(obj, float):
        return "float"
    if isinstance(obj, str):
        return "str"
    if obj is None:
        return "null"
    return type(obj).__name__


cases_file = os.environ.get("CASES_FILE", "docs/contract/cases.yml")
ref_dir = os.environ.get("REF_DIR", "docs/contract/snapshots")
tmp_dir = os.environ.get("TMP_DIR", "tmp/contract_snapshots_run")
ignore_keys = [k.strip() for k in os.environ.get("IGNORE_KEYS", "").split(",") if k.strip()]
bootstrap = os.environ.get("BOOTSTRAP", "0") == "1"
bootstrap_pass = os.environ.get("BOOTSTRAP_PASS", "0") == "1"

with open(cases_file, "r", encoding="utf-8") as f:
    cases = json.loads(f.read())

report = []
failures = 0
missing = 0

for case in cases:
    name = case.get("case")
    compare_mode = str(case.get("compare_mode") or "strict").strip().lower()
    ref_path = os.path.join(ref_dir, f"{name}.json")
    cur_path = os.path.join(tmp_dir, f"{name}.json")

    if not os.path.exists(cur_path):
        report.append(("FAIL", name, "snapshot not generated"))
        failures += 1
        continue
    if not os.path.exists(ref_path):
        trace_id = _read_trace_id(cur_path)
        report.append(("MISSING_BASELINE", name, f"trace_id={trace_id}"))
        missing += 1
        if bootstrap:
            os.makedirs(ref_dir, exist_ok=True)
            shutil.copy2(cur_path, ref_path)
        continue

    with open(ref_path, "r", encoding="utf-8") as f:
        ref_data = json.load(f)
    with open(cur_path, "r", encoding="utf-8") as f:
        cur_data = json.load(f)

    ref_norm = _strip_keys(ref_data, ignore_keys)
    cur_norm = _strip_keys(cur_data, ignore_keys)
    if compare_mode == "shape":
        ref_norm = _shapeize(ref_norm)
        cur_norm = _shapeize(cur_norm)

    ref_text = json.dumps(ref_norm, ensure_ascii=False, sort_keys=True, indent=2).splitlines()
    cur_text = json.dumps(cur_norm, ensure_ascii=False, sort_keys=True, indent=2).splitlines()

    if ref_text == cur_text:
        report.append(("PASS", name, ""))
        continue

    trace_id = _read_trace_id(cur_path)
    report.append(("FAIL", name, f"diff trace_id={trace_id}"))
    diff = difflib.unified_diff(ref_text, cur_text, fromfile=ref_path, tofile=cur_path, lineterm="")
    for line in diff:
        print(line)
    failures += 1

for status, name, detail in report:
    msg = f"{status} {name}"
    if detail:
        msg += f" ({detail})"
    print(msg)

if failures:
    sys.exit(2)
if missing and not bootstrap:
    sys.exit(2)
if missing and bootstrap and not bootstrap_pass:
    sys.exit(2)
PY
