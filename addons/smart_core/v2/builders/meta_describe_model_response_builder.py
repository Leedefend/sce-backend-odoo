from __future__ import annotations

from ..contracts.results import MetaDescribeModelResultV2


class MetaDescribeModelResponseBuilderV2:
    def build(self, result: MetaDescribeModelResultV2) -> dict:
        fields = result.fields if isinstance(result.fields, dict) else {}
        return {
            "intent": str(result.intent or "meta.describe_model"),
            "model": str(result.model or ""),
            "display_name": str(result.display_name or ""),
            "fields": fields,
            "capabilities": {
                "can_read": bool(result.can_read),
                "can_write": bool(result.can_write),
            },
            "source": str(result.source or "v2-shadow"),
            "version": str(result.version or "v2"),
            "schema_validated": bool(result.schema_validated),
            "phase": str(result.phase or "boundary_closure"),
        }


def build_meta_describe_model_response(result: MetaDescribeModelResultV2) -> dict:
    return MetaDescribeModelResponseBuilderV2().build(result)
