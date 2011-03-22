# ==================
# = Parser Mapping =
# ==================
class ParserRegistry(object):
    _registry = {}

    def register(self, obj_type, parser):
        self._registry[obj_type] = parser

    def get(self, obj_type):
        return self._registry[str(obj_type)]

    def parse(self, obj_dict):
        parser_class = self.get(obj_dict['type'])
        parser = parser_class(obj_dict)
        return parser.parse()

parser_registry = ParserRegistry()
