# /orchestrator/tests/unit/fakes/storage.py
from infrastructure.interfaces.storage import StorageInterface


class FakeStorage(StorageInterface):
    def __init__(self):
        self.bucket_ensured = False
        self.deleted_prefixes = []

    def ensure_bucket(self):
        self.bucket_ensured = True

    def presigned_put(self, key):
        return f"https://fake-minio/{key}"

    def get_object(self, key):
        raise NotImplementedError("not needed by conversion domain tests yet")

    def delete_prefix(self, prefix):
        self.deleted_prefixes.append(prefix)

    def list_top_level_prefixes(self):
        raise NotImplementedError("not needed by conversion domain tests yet")
