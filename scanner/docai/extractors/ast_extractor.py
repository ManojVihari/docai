import ast


class ASTRouteExtractor:

    def extract_routes_from_file(self, file_path):
        with open(file_path, "r") as f:
            source_code = f.read()

        tree = ast.parse(source_code)

        routes = []

        for node in ast.walk(tree):

            if isinstance(node, ast.FunctionDef):

                for decorator in node.decorator_list:

                    if isinstance(decorator, ast.Call):
                        if hasattr(decorator.func, "attr"):

                            method = decorator.func.attr.upper()

                            if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:

                                path = None
                                if decorator.args:
                                    arg = decorator.args[0]
                                    if isinstance(arg, ast.Constant):
                                        path = arg.value

                                parameters = self._extract_parameters(node)
                                status_codes = self._extract_status_codes(node)

                                routes.append({
                                    "function_name": node.name,
                                    "method": method,
                                    "path": path,
                                    "parameters": parameters,
                                    "status_codes": status_codes,
                                    "source_code": ast.get_source_segment(source_code, node)
                                })

        return routes

    def _extract_parameters(self, node):

        params = []

        args = node.args.args
        defaults = node.args.defaults

        # Align defaults with args
        default_offset = len(args) - len(defaults)

        for index, arg in enumerate(args):

            param_name = arg.arg
            param_type = self._get_annotation(arg.annotation) if arg.annotation else "unknown"

            default_value = None
            required = True

            if index >= default_offset:
                default_node = defaults[index - default_offset]

                if isinstance(default_node, ast.Constant):
                    default_value = default_node.value
                else:
                    default_value = "complex"

                required = False

            params.append({
                "name": param_name,
                "type": param_type,
                "required": required,
                "default": default_value
            })

        return params


    def _get_annotation(self, annotation):
        if isinstance(annotation, ast.Name):
            return annotation.id
        return "unknown"

    def _extract_status_codes(self, node):

        errors = []

        for child in ast.walk(node):

            if isinstance(child, ast.Call):

                if hasattr(child.func, "id") and child.func.id == "HTTPException":

                    status_code = None
                    detail = None

                    for keyword in child.keywords:

                        if keyword.arg == "status_code":
                            if isinstance(keyword.value, ast.Constant):
                                status_code = keyword.value.value

                        if keyword.arg == "detail":
                            if isinstance(keyword.value, ast.Constant):
                                detail = keyword.value.value

                    if status_code:
                        errors.append({
                            "code": status_code,
                            "detail": detail or "No detail provided"
                        })

        return errors
