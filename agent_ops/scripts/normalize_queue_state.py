#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import dump_json, load_yaml
from run_queue import rebuild_state_from_results


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild queue state from canonical task results.")
    parser.add_argument("queue", help="Queue yaml path")
    parser.add_argument("--state", required=True, help="State json output path")
    args = parser.parse_args()

    queue_path = Path(args.queue)
    state_path = Path(args.state)
    queue = load_yaml(queue_path)
    state = rebuild_state_from_results(queue)
    dump_json(state_path, state)
    print(json.dumps(state, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
