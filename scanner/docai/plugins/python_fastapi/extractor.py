from tree_sitter import Parser, Language, Query, QueryCursor
from tree_sitter_python import language as python_language
import os
import re


class FastAPIExtractor:

    def __init__(self):
        self.parser = Parser()
        self.language = Language(python_language())
        self.parser.language = self.language

        self.query = Query(self.language, """
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
        """)

    # ============================
    # MAIN ENTRY (SINGLE FILE)
    # ============================

    def extract_from_file(self, file_path):
        with open(file_path, "rb") as f:
            code = f.read()

        tree = self.parser.parse(code)
        cursor = QueryCursor(self.query)
        captures = cursor.captures(tree.root_node)

        normalized = self._normalize_captures(captures)
        routes_map = {}

        for node, capture_name in normalized:

            parent = self._get_parent(node, "decorated_definition")
            if not parent:
                continue

            key = (parent.start_byte, parent.end_byte)

            if key not in routes_map:
                routes_map[key] = {}

            text = self._get_text(node, code)

            if capture_name == "method":
                routes_map[key]["method"] = text.upper()

            elif capture_name == "path":
                routes_map[key]["path"] = text.strip('"')

            elif capture_name == "func_name":

                route = routes_map[key]
                route["function"] = text

                func_node = next(
                    (c for c in parent.children if c.type == "function_definition"),
                    None
                )

                # 🔥 CORE SIGNALS
                route["params"] = self.extract_params(func_node, code)
                route["errors"] = self.extract_errors(func_node, code)
                route["calls"] = self.extract_calls(func_node, code)
                route["control_flow"] = self.extract_control_flow(func_node, code)
                route["data_flow"] = self.extract_data_flow(func_node, code)
                route["variable_flow"] = self.extract_variable_flow(func_node, code)

                # 🔥 DERIVED
                route["service_calls"] = self.extract_service_calls(route["calls"])
                route["call_graph"] = self.build_call_graph(
                    route["function"], route["calls"]
                )

        return list(routes_map.values())

    # ============================
    # 🔥 NEW: REPOSITORY PROCESSING
    # ============================

    def process_repository(self, repo_path, changed_files):

        # 1. full graph
        graph = self.build_full_graph(repo_path)

        # 2. changed functions
        changed_funcs = self.find_changed_functions(repo_path, changed_files)

        # 3. all routes
        all_routes = self.extract_all_routes(repo_path)

        # 4. impacted routes
        impacted = []

        for route in all_routes:
            func = route.get("function")

            if func in changed_funcs:
                route["impact"] = self.expand_impact(func, graph)
                impacted.append(route)

        return impacted

    # ============================
    # GRAPH BUILDING
    # ============================

    def build_full_graph(self, repo_path):

        graph = {}

        for root, _, files in os.walk(repo_path):
            for f in files:

                if not f.endswith(".py"):
                    continue

                full = os.path.join(root, f)

                try:
                    routes = self.extract_from_file(full)

                    for r in routes:
                        func = r.get("function")
                        calls = r.get("calls", [])

                        graph[func] = [
                            self.extract_call_name(c)
                            for c in calls
                        ]

                except:
                    continue

        return graph

    # ============================
    # CHANGED FUNCTION DETECTION
    # ============================

    def find_changed_functions(self, repo_path, changed_files):

        changed = set()

        for file in changed_files:

            if not file.endswith(".py"):
                continue

            full = os.path.join(repo_path, file)

            if not os.path.exists(full):
                continue

            try:
                routes = self.extract_from_file(full)

                for r in routes:
                    if "function" in r:
                        changed.add(r["function"])

            except:
                continue

        return changed

    # ============================
    # ROUTE COLLECTION
    # ============================

    def extract_all_routes(self, repo_path):

        routes = []

        for root, _, files in os.walk(repo_path):
            for f in files:

                if not f.endswith(".py"):
                    continue

                full = os.path.join(root, f)

                try:
                    routes.extend(self.extract_from_file(full))
                except:
                    continue

        return routes

    # ============================
    # IMPACT EXPANSION
    # ============================

    def expand_impact(self, func, graph, visited=None):

        if visited is None:
            visited = set()

        if func in visited:
            return []

        visited.add(func)

        impact = []

        for call in graph.get(func, []):

            if call in visited:
                continue

            impact.append(call)

            deeper = self.expand_impact(call, graph, visited)
            impact.extend(deeper)

        return list(set(impact))

    # ============================
    # HELPERS
    # ============================

    def _normalize_captures(self, captures):
        normalized = []

        if isinstance(captures, dict):
            for name, nodes in captures.items():
                for node in nodes:
                    normalized.append((node, name))
        else:
            for item in captures:
                if hasattr(item[0], "start_byte"):
                    normalized.append((item[0], item[1]))
                else:
                    normalized.append((item[1], item[0]))

        return normalized

    def _get_parent(self, node, target_type):
        while node and node.type != target_type:
            node = node.parent
        return node

    def _get_text(self, node, code):
        return code[node.start_byte:node.end_byte].decode()

    # ============================
    # EXTRACTION METHODS (UNCHANGED)
    # ============================

    def extract_params(self, func_node, code):
        params = []

        params_node = next(
            (c for c in func_node.children if c.type == "parameters"),
            None
        )

        if not params_node:
            return []

        for node in params_node.children:

            if node.type in ["(", ")", ","]:
                continue

            text = self._get_text(node, code).strip()

            param = {
                "name": "",
                "type": "unknown",
                "required": True,
                "default": None
            }

            if ":" in text and "=" in text:
                name_part, rest = text.split(":", 1)
                type_part, default_part = rest.split("=", 1)

                param["name"] = name_part.strip()
                param["type"] = type_part.strip()
                param["default"] = default_part.strip()
                param["required"] = False

            elif ":" in text:
                name_part, type_part = text.split(":", 1)

                param["name"] = name_part.strip()
                param["type"] = type_part.strip()

            elif "=" in text:
                name_part, default_part = text.split("=", 1)

                param["name"] = name_part.strip()
                param["default"] = default_part.strip()
                param["required"] = False

            else:
                param["name"] = text.strip()

            params.append(param)

        return params

    def extract_errors(self, func_node, code):
        errors = []
        stack = [func_node]

        while stack:
            node = stack.pop()
            text = self._get_text(node, code)

            match = re.search(r"status_code\s*=\s*(\d+)", text)
            if "HTTPException" in text and match:
                errors.append(int(match.group(1)))

            stack.extend(node.children)

        return list(set(errors))

    def extract_calls(self, func_node, code):
        calls = []
        stack = [func_node]

        IGNORE = ["HTTPException", "ValueError"]

        while stack:
            node = stack.pop()

            if node.type == "call":
                text = self._get_text(node, code)

                if any(i in text for i in IGNORE):
                    stack.extend(node.children)
                    continue

                calls.append(text)

            stack.extend(node.children)

        return list(set(calls))

    def extract_control_flow(self, func_node, code):
        flows = []
        stack = [func_node]

        while stack:
            node = stack.pop()

            if node.type == "if_statement":
                text = self._get_text(node, code)

                if "validate_email" in text:
                    flows.append("email validation")
                elif "validate_role" in text:
                    flows.append("role validation")
                elif "isinstance" in text:
                    flows.append("type validation")
                elif "name.strip()" in text:
                    flows.append("name validation")
                else:
                    flows.append("conditional logic")

            stack.extend(node.children)

        return list(set(flows))

    def extract_data_flow(self, func_node, code):
        flow = {"transforms": [], "outputs": []}
        stack = [func_node]

        while stack:
            node = stack.pop()

            if node.type == "call":
                text = self._get_text(node, code)

                if any(x in text for x in [".lower()", ".strip()"]):
                    flow["transforms"].append(text)

            elif node.type == "return_statement":
                flow["outputs"].append(self._get_text(node, code))

            stack.extend(node.children)

        flow["transforms"] = list(set(flow["transforms"]))
        flow["outputs"] = list(set(flow["outputs"]))

        return flow

    def extract_variable_flow(self, func_node, code):
        flow = {}
        stack = [func_node]

        while stack:
            node = stack.pop()

            if node.type == "assignment":
                text = self._get_text(node, code)

                parts = text.split("=")
                if len(parts) == 2:
                    flow[parts[0].strip()] = parts[1].strip()

            stack.extend(node.children)

        return flow

    def extract_service_calls(self, calls):
        service_calls = []

        for call in calls:
            name = self.extract_call_name(call)

            if name.startswith("validate"):
                continue

            if name in ["lower", "strip", "str", "isinstance"]:
                continue

            service_calls.append(name)

        return list(set(service_calls))

    def extract_call_name(self, call_text):
        name = call_text.split("(")[0].strip()

        if "." in name:
            name = name.split(".")[-1]

        return name

    def build_call_graph(self, func_name, calls):
        IGNORE = {"lower", "strip", "str", "isinstance"}

        graph = {func_name: []}

        for call in calls:
            name = self.extract_call_name(call)

            if name in IGNORE:
                continue

            graph[func_name].append(name)

        return graph