# worker_conversion/infrastructure/storage/minio_storage.py
import io

from infrastructure.errors import StorageError
from infrastructure.interfaces.storage import ConversionStorageInterface
from minio import Minio
from minio.error import S3Error


class MinioConversionStorage(ConversionStorageInterface):
    def __init__(self, client: Minio):
        self._client = client

    def get_object(self, bucket: str, key: str) -> bytes:
        try:
            response = self._client.get_object(bucket, key)
            return response.read()
        except S3Error as e:
            raise StorageError(f"Could not read object {key}: {e}") from e

    def put_object(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        try:
            self._client.put_object(
                bucket, key, io.BytesIO(data), length=len(data), content_type=content_type
            )
        except S3Error as e:
            raise StorageError(f"Could not write object {key}: {e}") from e
