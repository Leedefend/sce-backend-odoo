from .form_parser import FormViewParser


class ViewDispatcher:
    SOURCE_KIND = "legacy_view_dispatch_projection"
    SOURCE_AUTHORITIES = ("legacy_form_view_parser_projection", "ir.ui.view")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls):
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": "smart_core.view.view_dispatcher",
            "legacy_compatibility": True,
        }

    def __init__(self, env, model, view_type, view_id=None, context=None):
        self.env = env
        self.model = model
        self.view_type = view_type
        self.view_id = view_id
        self.context = context or {}

    def parse(self):
        parser_map = {
            "form": FormViewParser,
        }
            

        parser_cls = parser_map.get(self.view_type)
        if not parser_cls:
            raise ValueError(f"不支持的视图类型: {self.view_type}")

        parser = parser_cls(self.env, self.model, self.view_type, self.view_id, self.context)
        return parser.parse()
