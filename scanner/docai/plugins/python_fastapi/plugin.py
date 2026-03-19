import os
from docai.extractors.ast_extractor import ASTRouteExtractor


class Plugin:

    name = "fastapi"

    def __init__(self):
        self.extractor = ASTRouteExtractor()

    def detect(self, repo_path):

        for root, _, files in os.walk(repo_path):

            for file in files:

                if not file.endswith(".py"):
                    continue

                path = os.path.join(root, file)

                try:

                    with open(path, "r", encoding="utf-8") as f:

                        if "fastapi" in f.read().lower():
                            return True

                except Exception:
                    continue

        return False


    def extract(self, repo_path, changed_files):

        routes = []

        for file in changed_files:

            full_path = os.path.join(repo_path, file)

            if not os.path.exists(full_path):
                continue

            extracted = self.extractor.extract_routes_from_file(full_path)

            routes.extend(extracted)

        return routes