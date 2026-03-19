from app.services.db import SessionLocal, APIVersion
import os
import json

class VersionService:

    def __init__(self, base_path="database"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _get_file(self, repository, api_name):

        repo_dir = os.path.join(self.base_path, repository)
        os.makedirs(repo_dir, exist_ok=True)

        return os.path.join(repo_dir, f"{api_name}.json")

    def get_versions(self, repository, api_name):

        file_path = self._get_file(repository, api_name)

        if not os.path.exists(file_path):
            return []

        with open(file_path, "r") as f:
            return json.load(f)

    def get_latest(self, repository, api_name):

        versions = self.get_versions(repository, api_name)

        if not versions:
            return None

        return versions[-1]

    def should_create_version(self, repository, api_name, signature):

        latest = self.get_latest(repository, api_name)

        if not latest:
            return True, 1

        if latest["signature"] == signature:
            return False, latest["version"]

        return True, latest["version"] + 1


    def save_version(self, repository, api_name, version, signature, commit_hash, content):

        file_path = self._get_file(repository, api_name)

        versions = self.get_versions(repository, api_name)

        new_entry = {
            "version": version,
            "signature": signature,
            "commit_hash": commit_hash,
            "content": content
        }

        versions.append(new_entry)

        with open(file_path, "w") as f:
            json.dump(versions, f, indent=2)

        print(f"[NEW VERSION] {api_name} v{version}")

    # ---------------------------------------
    # Save New Version
    # ---------------------------------------
    # def save_version(self, api_name, commit_hash, content):
    #     print(f"Saving version for API: {api_name}, Commit: {commit_hash}")
    #     db = SessionLocal()

    #     try:
    #         latest = (
    #             db.query(APIVersion)
    #             .filter(APIVersion.api_name == api_name)
    #             .order_by(APIVersion.version.desc())
    #             .first()
    #         )

    #         next_version = 1 if not latest else latest.version + 1

    #         new_version = APIVersion(
    #             api_name=api_name,
    #             version=next_version,
    #             commit_hash=commit_hash,
    #             content=content,
    #             status="draft"
    #         )

    #         db.add(new_version)
    #         db.commit()

    #     finally:
    #         db.close()

    # ---------------------------------------
    # Get All Versions for API
    # ---------------------------------------
    # def get_versions(self, api_name):

    #     db = SessionLocal()

    #     try:
    #         versions = (
    #             db.query(APIVersion)
    #             .filter(APIVersion.api_name == api_name)
    #             .order_by(APIVersion.version.desc())
    #             .all()
    #         )
    #         return versions

    #     finally:
    #         db.close()

    # ---------------------------------------
    # Get All Unique API Names
    # ---------------------------------------
    def get_all_api_names(self):

        db = SessionLocal()

        try:
            results = db.query(APIVersion.api_name).distinct().all()
            return [r[0] for r in results]

        finally:
            db.close()

    # ---------------------------------------
    # Approve Version
    # ---------------------------------------
    def approve_version(self, api_name, version):

        db = SessionLocal()

        try:
            record = (
                db.query(APIVersion)
                .filter(
                    APIVersion.api_name == api_name,
                    APIVersion.version == version
                )
                .first()
            )

            if record:
                record.status = "approved"
                db.commit()

        finally:
            db.close()
