# worker_conversion/infrastructure/callback/orchestrator_callback_client.py
import requests
from infrastructure.interfaces.callback import CallbackClientInterface
from utils.logging_utils import dev_logger, safe_logger


class OrchestratorCallbackClient(CallbackClientInterface):
    def __init__(self, callback_url: str):
        self._callback_url = callback_url

    def send(
        self,
        job_id: int,
        filename: str,
        html_key: str | None,
        success: bool,
        error: str | None = None,
        pdf_hash: str | None = None,
        html_hash: str | None = None,
    ) -> bool:
        try:
            resp = requests.post(
                self._callback_url,
                json={
                    "job_id": job_id,
                    "filename": filename,
                    "html_key": html_key or "",
                    "success": success,
                    "error": error,
                    "pdf_hash": pdf_hash or "",
                    "html_hash": html_hash or "",
                },
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("continue", True)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            safe_logger.error(
                "callback_error_response | job_id=%s | pdf_filename=%s | status=%s",
                job_id,
                filename,
                status,
            )
            if dev_logger:
                dev_logger.exception("callback_error_response_dev | error=%s", str(e))
            return False
        except requests.RequestException as e:
            safe_logger.error("callback_failed | job_id=%s | pdf_filename=%s", job_id, filename)
            if dev_logger:
                dev_logger.exception("callback_failed_dev | error=%s", str(e))
            return True  # prefer continuing job
