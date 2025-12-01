from .form_parser import FormViewParser


class ViewDispatcher:
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
