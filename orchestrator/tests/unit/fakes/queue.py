# /orchestrator/tests/unit/fakes/queue.py
from infrastructure.interfaces.queue import ConversionQueueInterface, PrelabelQueueInterface


class FakeConversionQueue(ConversionQueueInterface):
    def __init__(self):
        self.pushed = []

    def push_conversion_job(self, job_id, project, pdf_keys):
        self.pushed.append({"job_id": job_id, "project": project, "pdf_keys": pdf_keys})


class FakePrelabelQueue(PrelabelQueueInterface):
    def __init__(self):
        self.pushed = []

    def push_prelabel_job(self, payload):
        self.pushed.append(payload)
