import ast


class ASTRouteExtractor:

    HTTP_METHODS = {"get", "post", "put", "delete", "patch"}

    def extract_routes_from_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        tree = ast.parse(source_code)

        routes = []
        router_prefix = self._extract_router_prefix(tree)

        for node in ast.walk(tree):

            if isinstance(node, ast.FunctionDef):

                route_info = self._extract_route_info(node, router_prefix, source_code)

                if route_info:
                    routes.append(route_info)

        return routes

    # ---------------------------
    # ROUTE DETECTION
    # ---------------------------
    def _extract_route_info(self, node, router_prefix, source_code):

        for decorator in node.decorator_list:

            if isinstance(decorator, ast.Call) and hasattr(decorator.func, "attr"):

                method = decorator.func.attr.lower()

                if method in self.HTTP_METHODS:

                    path = self._extract_path(decorator)
                    full_path = f"{router_prefix}{path}" if path else router_prefix

                    return {
                        "id": node.name,
                        "method": method.upper(),
                        "path": full_path,
                        "params": self._extract_parameters(node),
                        "response": self._extract_response_model(decorator),
                        "errors": self._extract_status_codes(node),
                        "dependencies": self._extract_dependencies(node),
                        "source_code": ast.get_source_segment(source_code, node)
                    }

        return None

    # ---------------------------
    # PATH
    # ---------------------------
    def _extract_path(self, decorator):
        if decorator.args:
            arg = decorator.args[0]
            if isinstance(arg, ast.Constant):
                return arg.value
        return ""

    def _extract_router_prefix(self, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call) and hasattr(node.value.func, "id"):
                    if node.value.func.id == "APIRouter":
                        for kw in node.value.keywords:
                            if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                return kw.value.value
        return ""

    # ---------------------------
    # PARAMETERS
    # ---------------------------
    def _extract_parameters(self, node):

        params = []

        args = node.args.args
        defaults = node.args.defaults

        default_offset = len(args) - len(defaults)

        for index, arg in enumerate(args):

            name = arg.arg
            annotation = self._parse_annotation(arg.annotation)

            default_value = None
            required = True

            if index >= default_offset:
                default_node = defaults[index - default_offset]
                default_value = self._parse_default(default_node)
                required = False

            param_type, location = self._infer_param_location(annotation)

            params.append({
                "name": name,
                "type": param_type,
                "in": location,
                "required": required,
                "default": default_value
            })

        return params

    def _infer_param_location(self, annotation):

        if "Path" in annotation:
            return "string", "path"
        if "Query" in annotation:
            return "string", "query"
        if "Body" in annotation:
            return "object", "body"

        return annotation or "unknown", "query"

    # ---------------------------
    # RESPONSE MODEL
    # ---------------------------
    def _extract_response_model(self, decorator):

        for kw in decorator.keywords:
            if kw.arg == "response_model":
                if isinstance(kw.value, ast.Name):
                    return {"model": kw.value.id}

        return {"model": "unknown"}

    # ---------------------------
    # DEPENDENCIES
    # ---------------------------
    def _extract_dependencies(self, node):

        deps = []

        for child in ast.walk(node):

            if isinstance(child, ast.Call):
                if hasattr(child.func, "id") and child.func.id == "Depends":
                    if child.args and isinstance(child.args[0], ast.Name):
                        deps.append(child.args[0].id)

        return deps

    # ---------------------------
    # ERRORS
    # ---------------------------
    def _extract_status_codes(self, node):

        errors = []

        for child in ast.walk(node):

            if isinstance(child, ast.Call):

                if hasattr(child.func, "id") and child.func.id == "HTTPException":

                    code = None
                    detail = None

                    for kw in child.keywords:

                        if kw.arg == "status_code" and isinstance(kw.value, ast.Constant):
                            code = kw.value.value

                        if kw.arg == "detail" and isinstance(kw.value, ast.Constant):
                            detail = kw.value.value

                    if code:
                        errors.append({
                            "code": code,
                            "detail": detail or ""
                        })

        return errors

    # ---------------------------
    # HELPERS
    # ---------------------------
    def _parse_annotation(self, annotation):

        if isinstance(annotation, ast.Name):
            return annotation.id

        if isinstance(annotation, ast.Subscript):
            return self._parse_annotation(annotation.value)

        return "unknown"

    def _parse_default(self, node):

        if isinstance(node, ast.Constant):
            return node.value

        return "complex"