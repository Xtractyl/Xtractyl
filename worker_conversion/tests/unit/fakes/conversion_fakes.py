# worker_conversion/tests/unit/fakes/conversion_fakes.py
from infrastructure.errors import DoclingError, StorageError
from infrastructure.interfaces.callback import CallbackClientInterface
from infrastructure.interfaces.docling import DoclingClientInterface
from infrastructure.interfaces.storage import ConversionStorageInterface


class FakeConversionStorage(ConversionStorageInterface):
    def __init__(self, objects=None, fail_get=False, fail_put=False):
        self.objects = dict(objects or {})
        self.fail_get = fail_get
        self.fail_put = fail_put
        self.put_calls = []

    def get_object(self, bucket, key):
        if self.fail_get:
            raise StorageError(f"forced get failure for {key}")
        if key not in self.objects:
            raise StorageError(f"no such object: {key}")
        return self.objects[key]

    def put_object(self, bucket, key, data, content_type):
        if self.fail_put:
            raise StorageError(f"forced put failure for {key}")
        self.objects[key] = data
        self.put_calls.append({"bucket": bucket, "key": key, "content_type": content_type})


class FakeDoclingClient(DoclingClientInterface):
    def __init__(self, html_content=None, fail=False):
        self.html_content = html_content
        self.fail = fail
        self.calls = []

    def convert(self, filename, pdf_bytes):
        self.calls.append({"filename": filename, "pdf_bytes": pdf_bytes})
        if self.fail:
            raise DoclingError("forced docling failure")
        return self.html_content


class FakeCallbackClient(CallbackClientInterface):
    def __init__(self, continue_value=True):
        self.continue_value = continue_value
        self.calls = []

    def send(self, **kwargs):
        self.calls.append(kwargs)
        return self.continue_value
