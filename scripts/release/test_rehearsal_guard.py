#!/usr/bin/env python3
import os
from contextlib import contextmanager

from rehearsal_guard import validate


@contextmanager
def environ(**values):
    old = os.environ.copy()
    os.environ.update(values)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old)


def rejected(db, **environment):
    with environ(SC_ENVIRONMENT=environment.get("SC_ENVIRONMENT", "release_rehearsal"), SC_ALLOW_DEMO_DATA=environment.get("SC_ALLOW_DEMO_DATA", "0")):
        try:
            validate(db)
        except ValueError:
            return
    raise AssertionError(f"unsafe database was accepted: {db!r}")


for unsafe in ("", "postgres", "sc_demo", "sc_frontend_acceptance", "sc_prod", "sc_prod_sim", "customer_production"):
    rejected(unsafe)
rejected("sc_release_rehearsal", SC_ENVIRONMENT="production")
rejected("sc_release_rehearsal", SC_ALLOW_DEMO_DATA="1")
with environ(SC_ENVIRONMENT="release_rehearsal", SC_ALLOW_DEMO_DATA="0"):
    for safe in ("sc_release_rehearsal", "sc_release_rehearsal_restored", "sc_release_rehearsal_rollback"):
        assert validate(safe) == safe
print("[test.rehearsal.guard] PASS safe=3 rejected=9")
