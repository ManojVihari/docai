class MarkdownBuilder:

    def build(self, route_data, llm_sections):
        print(f"Building markdown for route: {route_data.function_name}")

        md = f"# API: {route_data.function_name}\n\n"

        # Overview (from LLM)
        md += "## Overview\n"
        md += llm_sections["overview"] + "\n\n"

        # Endpoint
        md += "## Endpoint\n"
        md += f"- Method: {route_data.method}\n"
        md += f"- Path: {route_data.path}\n\n"

        # Request Body (only if parameters exist)
        if route_data.parameters:
            md += "## Request\n\n"
            md += "### Request Body\n"
            md += "| Field | Type | Required | Default |\n"
            md += "| --- | --- | --- | --- |\n"

            for param in route_data.parameters:

                required_text = "Yes" if param.required else "No"
                default_text = param.default if param.default is not None else "-"

                md += f"| {param.name} | {param.type} | {required_text} | {default_text} |\n"

            md += "\n"


        # Response Section (only if status codes exist)
        if route_data.status_codes:
            md += "## Response\n\n"
            md += "### Error Responses\n"
            md += "| Code | Meaning |\n"
            md += "| --- | --- |\n"

            for error in route_data.status_codes:
                md += f"| {error.code} | {error.detail} |\n"

            md += "\n"

        # Business Logic
        md += "## Business Logic\n"
        md += llm_sections["business_logic"] + "\n\n"

        # Change Impact
        md += "## Change Impact\n"
        md += llm_sections["change_impact"] + "\n"

        return md
