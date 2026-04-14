from tree_sitter import Parser, Language, Query, QueryCursor
from tree_sitter_python import language as python_language

# ---- Setup parser ----
parser = Parser()
PY_LANGUAGE = Language(python_language())
parser.language = PY_LANGUAGE

# ---- Code ----
code = b"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/hello")
def hello():
    return 1
"""

tree = parser.parse(code)

# ---- Query (FIXED) ----
query_text = """
(
  (decorated_definition
    (decorator
      (call
        function: (attribute
          attribute: (identifier) @method
        )
        arguments: (argument_list
          (string) @path
        )
      )
    )
    (function_definition
      name: (identifier) @func_name
    )
  )
)
"""

query = Query(PY_LANGUAGE, query_text)
cursor = QueryCursor(query)

# ---- Extract ----
captures = cursor.captures(tree.root_node)

routes = []
temp = {}

# ---- NORMALIZE captures ----
normalized = []

if isinstance(captures, dict):
    # case: { "method": [nodes], ... }
    for name, nodes in captures.items():
        for node in nodes:
            normalized.append((node, name))
else:
    # case: list of tuples
    for item in captures:
        if hasattr(item[0], "start_byte"):
            normalized.append((item[0], item[1]))
        else:
            normalized.append((item[1], item[0]))

# ---- PROCESS normalized data ----
for node, capture_name in normalized:

    text = code[node.start_byte:node.end_byte].decode()

    if capture_name == "method":
        temp["method"] = text.upper()

    elif capture_name == "path":
        temp["path"] = text.strip('"')

    elif capture_name == "func_name":
        temp["function"] = text

        routes.append(temp.copy())
        temp = {}

print(routes)