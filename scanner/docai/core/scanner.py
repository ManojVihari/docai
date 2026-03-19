import subprocess
import os
from docai.core.plugin_manager import PluginManager


class Scanner:

    def __init__(self):
        self.plugin_manager = PluginManager()

    def scan(self, repo_path, commit):

        changed_files = self.get_changed_files(commit)

        plugins = self.plugin_manager.load_plugins()

        for plugin in plugins:

            if plugin.detect(repo_path):

                routes = plugin.extract(repo_path, changed_files)

                return {
                    "scanner_version": "0.1",
                    "repository": os.path.basename(os.path.abspath(repo_path)),
                    "commit": commit,
                    "framework": plugin.name,
                    "routes": routes
                }

        raise Exception("No supported framework detected")


    def get_changed_files(self, commit):

        result = subprocess.check_output(
            ["git", "diff", "--name-only", f"{commit}~1", commit]
        )

        files = result.decode().splitlines()

        return [f for f in files if f.endswith(".py")]