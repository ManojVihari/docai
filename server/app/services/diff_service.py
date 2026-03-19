# services/diff_service.py

class DiffService:
    """
    Service responsible for comparing API versions
    and generating change summaries.
    """

    def compare(self, old_api: dict, new_api: dict) -> dict:
        added = []
        removed = []
        modified = []

        old_keys = set(old_api.keys())
        new_keys = set(new_api.keys())

        # Added endpoints
        for endpoint in new_keys - old_keys:
            added.append(endpoint)

        # Removed endpoints
        for endpoint in old_keys - new_keys:
            removed.append(endpoint)

        # Modified endpoints
        for endpoint in old_keys & new_keys:
            if old_api.get(endpoint) != new_api.get(endpoint):
                modified.append(endpoint)

        return {
            "added": added,
            "removed": removed,
            "modified": modified
        }

    def generate_summary(self, diff: dict) -> str:
        summary_lines = []

        for ep in diff.get("added", []):
            summary_lines.append(f"+ Added API: {ep}")

        for ep in diff.get("modified", []):
            summary_lines.append(f"~ Updated API: {ep}")

        for ep in diff.get("removed", []):
            summary_lines.append(f"- Removed API: {ep}")

        return "\n".join(summary_lines)