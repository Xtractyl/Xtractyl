# orchestrator/infrastructure/storage/minio_storage.py
from datetime import timedelta

from domain.errors import ExternalServiceError
from infrastructure.interfaces.storage import StorageInterface
from minio import Minio
from minio.deleteobjects import DeleteObject
from minio.error import S3Error


class MinioStorage(StorageInterface):
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        presign_expiry_seconds: int,
    ):
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        self._bucket = bucket
        self._expiry = presign_expiry_seconds

    def ensure_bucket(self) -> None:
        try:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
        except S3Error as e:
            raise ExternalServiceError(
                code="MINIO_UNAVAILABLE",
                message="Could not connect to MinIO.",
            ) from e

    def presigned_put(self, key: str) -> str:
        try:
            # Returns a presigned URL string valid for self._expiry seconds
            return self._client.presigned_put_object(
                self._bucket, key, expires=timedelta(seconds=self._expiry)
            )
        except S3Error as e:
            raise ExternalServiceError(
                code="MINIO_PRESIGN_FAILED",
                message=f"Could not generate presigned URL for {key}.",
            ) from e

    def get_object(self, key: str) -> str:
        try:
            response = self._client.get_object(self._bucket, key)
            return response.read().decode("utf-8")
        except S3Error as e:
            raise ExternalServiceError(
                code="MINIO_GET_FAILED",
                message=f"Could not read object {key} from MinIO.",
            ) from e

    def delete_prefix(self, prefix: str) -> None:
        try:
            objects = self._client.list_objects(self._bucket, prefix=f"{prefix}/", recursive=True)
            to_delete = [DeleteObject(obj.object_name) for obj in objects]
            if not to_delete:
                return
            errors = list(self._client.remove_objects(self._bucket, to_delete))
            if errors:
                raise ExternalServiceError(
                    code="MINIO_DELETE_FAILED",
                    message=f"Failed to delete some objects under {prefix}.",
                )
        except S3Error as e:
            raise ExternalServiceError(
                code="MINIO_DELETE_FAILED",
                message=f"Could not delete objects under {prefix}.",
            ) from e
