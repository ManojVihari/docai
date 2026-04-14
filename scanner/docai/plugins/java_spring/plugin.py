import os
from docai.plugins.base_plugin import BasePlugin
from .extractor import SpringExtractor


class Plugin(BasePlugin):

    name = "spring"

    def __init__(self):
        self.extractor = SpringExtractor()

    def detect(self, repo_path):
        print("Running Spring detection...")

        for root, _, files in os.walk(repo_path):
            for f in files:
                if f.endswith(".java"):
                    full = os.path.join(root, f)

                    try:
                        with open(full, "r", encoding="utf-8") as file:
                            content = file.read()

                            if any(x in content for x in [
    "@RestController",
    "@Controller",
    "@RequestMapping",
    "@GetMapping",
    "@PostMapping"
]):
                                print("Detected Spring in:", full)
                                return True

                    except:
                        continue

        return False

    def extract(self, repo_path, changed_files):
        routes = []

        files_to_scan = changed_files if changed_files else []

        # 🔥 fallback to full repo if empty
        if not files_to_scan:
            for root, _, files in os.walk(repo_path):
                for f in files:
                    if f.endswith(".java"):
                        files_to_scan.append(os.path.join(root, f))
        else:
            files_to_scan = [
                os.path.join(repo_path, f) for f in files_to_scan
                if f.endswith(".java")
            ]

        for full_path in files_to_scan:
            if os.path.exists(full_path):
                routes.extend(
                    self.extractor.extract_from_file(full_path)
                )

        return routes