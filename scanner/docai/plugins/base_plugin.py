class BasePlugin:

    name = "base"

    def detect(self, repo_path):
        raise NotImplementedError

    def extract(self, repo_path, changed_files):
        raise NotImplementedError