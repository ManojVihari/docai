import os
from docai.plugins.base_plugin import BasePlugin
from .extractor import FastAPIExtractor


class Plugin(BasePlugin):

    name = "fastapi"

    def __init__(self):
        self.extractor = FastAPIExtractor()

    def detect(self, repo_path):
        print("Running FastAPI detection...")

        for root, _, files in os.walk(repo_path):
            for f in files:
                if f.endswith(".py"):
                    full = os.path.join(root, f)

                    try:
                        with open(full, "r", encoding="utf-8") as file:
                            content = file.read().lower()

                            if "fastapi" in content:
                                print("Detected FastAPI in:", full)
                                return True

                    except Exception as e:
                        print("Error reading:", full, e)

        return False
    def extract(self, repo_path, changed_files):

        routes = []

        # ✅ fallback: if no changed files → scan all .py files
        if not changed_files:
            print("No changed files, scanning repo...")

            for root, _, files in os.walk(repo_path):

                # skip internal stuff
                if any(skip in root for skip in ["docai", "venv", "__pycache__"]):
                    continue

                for f in files:
                    if f.endswith(".py"):

                        full_path = os.path.join(root, f)

                        print("Scanning:", full_path)

                        routes.extend(
                            self.extractor.extract_from_file(full_path)
                        )
            return routes

        # ✅ normal flow (diff-based)
        for file in changed_files:

            if not file.endswith(".py"):
                continue

            full_path = os.path.join(repo_path, file)

            print("Scanning:", full_path)

            if os.path.exists(full_path):
                routes.extend(
                    self.extractor.extract_from_file(full_path)
                )

        return routes