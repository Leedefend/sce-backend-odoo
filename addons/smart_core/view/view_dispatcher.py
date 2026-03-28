from .native_view_parser_registry import get_parser_class, normalize_view_type


class ViewDispatcher:
    def __init__(self, env, model, view_type, view_id=None, context=None):
        self.env = env
        self.model = model
        self.view_type = view_type
        self.view_id = view_id
        self.context = context or {}

    def parse(self):
        parser_cls = get_parser_class(self.view_type)
        if not parser_cls:
            raise ValueError(f"不支持的视图类型: {normalize_view_type(self.view_type)}")

        parser = parser_cls(self.env, self.model, self.view_type, self.view_id, self.context)
        return parser.parse()
