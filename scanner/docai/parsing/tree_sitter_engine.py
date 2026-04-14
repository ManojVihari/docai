from tree_sitter import Parser
from tree_sitter_languages import get_language


class TreeSitterEngine:

    def __init__(self, language_name: str):
        self.language = get_language(language_name)
        self.parser = Parser()
        self.parser.set_language(self.language)

    def parse(self, code: str):
        return self.parser.parse(bytes(code, "utf8"))

    def query(self, query_str: str):
        return self.language.query(query_str)