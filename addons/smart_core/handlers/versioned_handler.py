# -*- coding: utf-8 -*-


class _BaseVersionedHandler:
    VERSION = None
    SOURCE_KIND = "test_versioned_handler_projection"
    SOURCE_AUTHORITIES = ("request.path_params",)
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls):
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": "versioned_handler",
        }

    def __init__(self, context, request=None):
        self.context = context
        self.request = request

    def run(self):
        params = getattr(self.context, "path_params", {}) or {}
        model_name = params.get("model_name")
        return {
            "ok": True,
            "data": {
                "version": self.VERSION,
                "model": model_name,
            },
            "meta": {
                "source_kind": self.SOURCE_KIND,
                "source_authorities": list(self.SOURCE_AUTHORITIES),
                "source_authority": self.source_authority_contract(),
            },
        }


class VersionedDataHandlerV1(_BaseVersionedHandler):
    VERSION = "1.0.0"


class VersionedDataHandlerV2(_BaseVersionedHandler):
    VERSION = "2.0.0"


class VersionedDataHandlerV21(_BaseVersionedHandler):
    VERSION = "2.1.0"
