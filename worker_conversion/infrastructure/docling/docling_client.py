# worker_conversion/infrastructure/docling/docling_client.py
import io

import requests
from infrastructure.errors import DoclingError
from infrastructure.interfaces.docling import DoclingClientInterface


class DoclingHttpClient(DoclingClientInterface):
    def __init__(self, base_url: str, timeout_seconds: int):
        self._base_url = base_url
        self._timeout_seconds = timeout_seconds

    def convert(self, filename: str, pdf_bytes: bytes) -> str:
        try:
            response = requests.post(
                f"{self._base_url}/convert",
                files={"file": (filename, io.BytesIO(pdf_bytes), "application/pdf")},
                data={"filename": filename},
                timeout=self._timeout_seconds,
            )
        except requests.RequestException as e:
            raise DoclingError(
                f"Could not reach Docling (client timeout after {self._timeout_seconds}s): {e}"
            ) from e

        if response.status_code == 504 and response.json().get("timeout"):
            detail = response.json().get("error", "conversion timed out")
            raise DoclingError(f"Docling timeout: {detail}")

        try:
            response.raise_for_status()
            html_content = response.json().get("html")
        except requests.RequestException as e:
            raise DoclingError(f"Docling conversion failed: {e}") from e

        if not html_content:
            raise DoclingError("Docling returned no HTML content.")

        return html_content
