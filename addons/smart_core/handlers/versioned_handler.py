# -*- coding: utf-8 -*-


class _BaseVersionedHandler:
    VERSION = None

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
            "meta": {},
        }


class VersionedDataHandlerV1(_BaseVersionedHandler):
    VERSION = "1.0.0"


class VersionedDataHandlerV2(_BaseVersionedHandler):
    VERSION = "2.0.0"


class VersionedDataHandlerV21(_BaseVersionedHandler):
    VERSION = "2.1.0"
