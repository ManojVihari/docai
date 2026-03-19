import os
import re


class MarkdownWriter:

    def __init__(self, base_path="docs"):
            self.base_path = base_path
    
    def write(self, repository: str, api_name: str, version: int, content: str):

        """
        Writes documentation as:
        docs/<repo>/<api_name>/v<version>.md
        """

        repo_path = os.path.join(self.base_path, repository)
        api_path = os.path.join(repo_path, api_name)

        os.makedirs(api_path, exist_ok=True)

        file_path = os.path.join(api_path, f"v{version}.md")

        with open(file_path, "w") as f:
            f.write(content)

        print(f"[DOC WRITTEN] {file_path}")

    def write_or_replace(self, new_content: str):
        print(f"Writing documentation for API. Extracting API name...")
        """
        Replaces existing API section if present.
        Otherwise appends.
        """

        api_name = self._extract_api_name(new_content)

        if not api_name:
            print("Could not extract API name. Appending instead.")
            self._append(new_content)
            return

        if not os.path.exists(self.file_path):
            self._append(new_content)
            return

        with open(self.file_path, "r") as f:
            existing_content = f.read()

        pattern = rf"# API: {re.escape(api_name)}.*?(?=\n# API:|\Z)"
        updated_content, count = re.subn(
            pattern,
            new_content.strip(),
            existing_content,
            flags=re.DOTALL
        )

        if count == 0:
            # API section not found, append
            updated_content = existing_content + "\n\n" + new_content

        with open(self.file_path, "w") as f:
            f.write(updated_content)

    def _append(self, content):
        with open(self.file_path, "a") as f:
            f.write("\n\n")
            f.write(content)

    def _extract_api_name(self, markdown_text):
        match = re.search(r"# API:\s*(.+)", markdown_text)
        if match:
            return match.group(1).strip()
        return None
