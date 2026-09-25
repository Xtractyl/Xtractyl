# worker_conversion/tests/unit/test_domain.py
import hashlib

import pytest
from contracts import ConversionJobPayload
from domain import convert_file, handle_job
from infrastructure.errors import DoclingError, StorageError

from tests.unit.fakes.conversion_fakes import (
    FakeCallbackClient,
    FakeConversionStorage,
    FakeDoclingClient,
)

# --- convert_file ---


def test_convert_file_success_returns_key_and_hashes():
    pdf_bytes = b"fake pdf content"
    storage = FakeConversionStorage(objects={"proj/pdfs/a.pdf": pdf_bytes})
    docling = FakeDoclingClient(html_content="<html>converted</html>")

    html_key, pdf_hash, html_hash = convert_file(1, "proj/pdfs/a.pdf", storage, docling)

    assert html_key == "proj/htmls/a.html"
    assert pdf_hash == hashlib.sha256(pdf_bytes).hexdigest()
    assert html_hash == hashlib.sha256(b"<html>converted</html>").hexdigest()
    assert storage.put_calls == [
        {"bucket": "xtractyl", "key": "proj/htmls/a.html", "content_type": "text/html"}
    ]


def test_convert_file_raises_storage_error_when_pdf_read_fails():
    storage = FakeConversionStorage(fail_get=True)
    docling = FakeDoclingClient(html_content="<html>x</html>")

    with pytest.raises(StorageError):
        convert_file(1, "proj/pdfs/a.pdf", storage, docling)

    assert docling.calls == []


def test_convert_file_raises_docling_error_when_conversion_fails():
    storage = FakeConversionStorage(objects={"proj/pdfs/a.pdf": b"content"})
    docling = FakeDoclingClient(fail=True)

    with pytest.raises(DoclingError):
        convert_file(1, "proj/pdfs/a.pdf", storage, docling)

    assert storage.put_calls == []


def test_convert_file_raises_storage_error_when_html_write_fails():
    storage = FakeConversionStorage(objects={"proj/pdfs/a.pdf": b"content"}, fail_put=True)
    docling = FakeDoclingClient(html_content="<html>x</html>")

    with pytest.raises(StorageError):
        convert_file(1, "proj/pdfs/a.pdf", storage, docling)


# --- handle_job ---


def test_handle_job_sends_success_callback_for_each_file():
    storage = FakeConversionStorage(objects={"proj/pdfs/a.pdf": b"content"})
    docling = FakeDoclingClient(html_content="<html>ok</html>")
    callback = FakeCallbackClient(continue_value=True)
    job = ConversionJobPayload(job_id=1, project="proj", pdf_keys=["proj/pdfs/a.pdf"])

    handle_job(job, storage, docling, callback)

    assert len(callback.calls) == 1
    call = callback.calls[0]
    assert call["success"] is True
    assert call["error"] is None
    assert call["html_key"] == "proj/htmls/a.html"


def test_handle_job_sends_failure_callback_and_stops_when_told_to():
    storage = FakeConversionStorage(objects={})
    docling = FakeDoclingClient(html_content="<html>ok</html>")
    callback = FakeCallbackClient(continue_value=False)
    job = ConversionJobPayload(
        job_id=1, project="proj", pdf_keys=["proj/pdfs/a.pdf", "proj/pdfs/b.pdf"]
    )

    handle_job(job, storage, docling, callback)

    assert len(callback.calls) == 1
    call = callback.calls[0]
    assert call["success"] is False
    assert "no such object" in call["error"]
    assert call["html_key"] is None


def test_handle_job_continues_to_next_file_when_callback_allows():
    storage = FakeConversionStorage(
        objects={"proj/pdfs/a.pdf": b"content-a", "proj/pdfs/b.pdf": b"content-b"}
    )
    docling = FakeDoclingClient(html_content="<html>ok</html>")
    callback = FakeCallbackClient(continue_value=True)
    job = ConversionJobPayload(
        job_id=1, project="proj", pdf_keys=["proj/pdfs/a.pdf", "proj/pdfs/b.pdf"]
    )

    handle_job(job, storage, docling, callback)

    assert len(callback.calls) == 2
    assert all(call["success"] is True for call in callback.calls)
