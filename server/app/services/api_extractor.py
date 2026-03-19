import re


class APIExtractor:

    ROUTE_PATTERN = r"@(app|router)\.(get|post|put|delete)\(\"(.*?)\"\)"
    FUNCTION_PATTERN = r"def\s+(\w+)\("

    def extract_routes(self, diff_text):
        route_match = re.search(self.ROUTE_PATTERN, diff_text)
        function_match = re.search(self.FUNCTION_PATTERN, diff_text)

        if not route_match or not function_match:
            return None

        method = route_match.group(2).upper()
        path = route_match.group(3)
        function_name = function_match.group(1)

        return {
            "method": method,
            "path": path,
            "function_name": function_name,
            "api_id": function_name  # 🔥 identity based on function
        }
