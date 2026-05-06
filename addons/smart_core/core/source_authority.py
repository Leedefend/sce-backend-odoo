# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Iterable

NO_BUSINESS_FACT_AUTHORITY = True


def build_source_authority_contract(
    *,
    kind: str,
    authorities: Iterable[str],
    runtime_carrier: str | None = None,
    projection_only: bool = True,
    rebuildable: bool | None = True,
    no_business_fact_authority: bool = NO_BUSINESS_FACT_AUTHORITY,
    **extra: Any,
) -> dict[str, Any]:
    contract: dict[str, Any] = {
        "kind": kind,
        "authorities": list(authorities),
        "projection_only": projection_only,
        "no_business_fact_authority": no_business_fact_authority,
    }
    if rebuildable is not None:
        contract["rebuildable"] = rebuildable
    if runtime_carrier:
        contract["runtime_carrier"] = runtime_carrier
    contract.update({key: value for key, value in extra.items() if value is not None})
    return contract
