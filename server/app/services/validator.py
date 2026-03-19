class APIDocValidator:

    REQUIRED_SECTIONS = [
        "# API:",
        "## Overview",
        "## Endpoint",
        "## Authentication",
        "## Request",
        "### Headers",
        "### Path Parameters",
        "### Query Parameters",
        "### Request Body",
        "## Response",
        "### Success Response",
        "### Error Responses",
        "## Business Logic",
        "## Dependencies",
        "## Change Impact",
    ]

    def validate(self, markdown_text: str) -> bool:
        """
        Validates that generated documentation follows
        the strict API documentation contract.
        """

        if not markdown_text or not isinstance(markdown_text, str):
            return False

        for section in self.REQUIRED_SECTIONS:
            if section not in markdown_text:
                print(f"Validation failed: Missing section -> {section}")
                return False

        return True
