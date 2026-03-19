from git import Repo
import os


class DiffAnalyzer:

    def __init__(self, repo_path="sample_repo"):
        self.repo_path = repo_path
        self.repo = Repo(repo_path)

    def get_changed_python_files(self):
        diff_output = self.repo.git.diff("HEAD~1..HEAD", name_only=True)
        files = diff_output.split("\n")
        return [f for f in files if f.endswith(".py")]

    def get_file_diff(self, file_path):
        return self.repo.git.diff("HEAD~1..HEAD", file_path)
    