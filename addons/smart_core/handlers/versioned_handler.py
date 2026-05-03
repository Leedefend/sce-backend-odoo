# -*- coding: utf-8 -*-


class _BaseVersionedHandler:
    VERSION = None
    SOURCE_KIND = "test_versioned_handler_projection"
    SOURCE_AUTHORITIES = ("request.path_params",)

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
            },
        }


class VersionedDataHandlerV1(_BaseVersionedHandler):
    VERSION = "1.0.0"


class VersionedDataHandlerV2(_BaseVersionedHandler):
    VERSION = "2.0.0"


class VersionedDataHandlerV21(_BaseVersionedHandler):
    VERSION = "2.1.0"
