# /ml_backend/perf_collector.py
from __future__ import annotations

import statistics
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Dict, List, Optional


@dataclass
class PerfEvent:
    name: str
    ms: float
    tags: Dict[str, Any]


class PerfCollector:
    def __init__(self) -> None:
        self._events: List[PerfEvent] = []
        self._task_ctx: Optional[str] = None  # e.g. LS task_id / filename

    @contextmanager
    def task(self, task_id: str):
        prev = self._task_ctx
        self._task_ctx = task_id
        try:
            yield
        finally:
            self._task_ctx = prev

    @contextmanager
    def measure(self, name: str, **tags: Any):
        if self._task_ctx is not None and "task_id" not in tags:
            tags["task_id"] = self._task_ctx

        t0 = perf_counter()
        try:
            yield tags
        finally:
            t1 = perf_counter()
            self._events.append(
                PerfEvent(
                    name=name,
                    ms=(t1 - t0) * 1000.0,
                    tags=dict(tags),
                )
            )

    def to_dict(self, include_events: bool = False) -> Dict[str, Any]:
        def events(prefix: str) -> List[PerfEvent]:
            return [e for e in self._events if e.name.startswith(prefix)]

        llm = events("llm.")
        dom = events("dom.")

        task_ms_dom_extract = sum(e.ms for e in dom if e.name == "dom.extract")
        task_ms_dom_match = sum(e.ms for e in dom if e.name == "dom.match")
        dom_ms = task_ms_dom_extract + task_ms_dom_match

        task_ms_llm_total = sum(e.ms for e in llm)
        task_ms_total = sum(e.ms for e in self._events)

        llm_calls = [e.ms for e in llm if e.name == "llm.call"]
        avg_call_ms = statistics.mean(llm_calls) if llm_calls else 0.0
        median_call_ms = statistics.median(llm_calls) if llm_calls else 0.0

        timeouts = sum(1 for e in llm if e.name == "llm.call" and e.tags.get("status") == "timeout")

        out = {
            "request": {
                "task_ms_total": task_ms_total,
                "task_ms_llm_total": task_ms_llm_total,
                "dom_ms": dom_ms,
                "task_ms_dom_extract": task_ms_dom_extract,
                "task_ms_dom_match": task_ms_dom_match,
                "n_llm_calls": sum(1 for e in llm if e.name == "llm.call"),
                "n_timeouts": timeouts,
                "avg_llm_call_ms": avg_call_ms,
                "median_llm_call_ms": median_call_ms,
            }
        }

        if include_events:
            out["events"] = [{"name": e.name, "ms": e.ms, "tags": e.tags} for e in self._events]

        return out
