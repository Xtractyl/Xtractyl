# /ml_backend/dom_match.py
import uuid

from utils import normalize_text_block


def extract_xpath_matches_from_dom(dom_data, answers):
    """
    dom_data: list of {"xpath", "raw", "content", "index_map"}
    answers:  list of {"question", "label", "answer"}
    """
    matches, diagnostics = [], []

    # sort by normalized content length asc (tighter nodes first)
    dom_sorted = sorted(dom_data, key=lambda el: len(el.get("content") or ""))

    for idx, ans in enumerate(answers, start=1):
        if not ans.get("answer"):
            continue

        normalized_answer = normalize_text_block(ans["answer"])

        found_match = False
        for el in dom_sorted:
            content = el.get("content") or ""
            xpath = el.get("xpath") or ""
            if not content or not xpath:
                continue

            offset_norm = content.find(normalized_answer)
            if offset_norm == -1:
                continue

            index_map = el.get("index_map") or []
            if not index_map or offset_norm + len(normalized_answer) - 1 >= len(index_map):
                diagnostics.append(
                    {"label": ans["label"], "xpath": xpath, "reason": "Index map missing/short"}
                )
                continue

            start_orig = index_map[offset_norm]
            end_orig = (
                index_map[offset_norm + len(normalized_answer) - 1] + 1
            )  # slice end exclusive

            if start_orig is None or end_orig is None or start_orig < 0 or end_orig <= start_orig:
                diagnostics.append(
                    {"label": ans["label"], "xpath": xpath, "reason": "Offset mapping failed"}
                )
                continue

            matches.append(
                {
                    "id": str(uuid.uuid4()),
                    "from_name": "label",
                    "to_name": "html",
                    "type": "labels",
                    "origin": "prediction",
                    "value": {
                        "start": xpath,
                        "end": xpath,
                        "startOffset": start_orig,
                        "endOffset": end_orig,
                        "labels": [ans["label"]],
                        "text": ans["answer"],
                    },
                }
            )
            found_match = True
            break

        if not found_match:
            diagnostics.append({"label": ans["label"], "reason": "Not found in any content block"})
    return matches, diagnostics
