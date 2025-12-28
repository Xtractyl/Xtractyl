# /ml_backend/dom_match.py
import json
import logging
import uuid

from utils import normalize_text_block


def extract_xpath_matches_from_dom(dom_data, answers):
    """
    dom_data: list of {"xpath", "raw", "content", "index_map"}
    answers:  list of {"question", "label", "answer"}
    """
    matches, diagnostics = [], []

    logging.debug(
        "🔎 Starting DOM matching: %d DOM blocks, %d answers", len(dom_data), len(answers)
    )

    # sort by normalized content length asc (tighter nodes first)
    dom_sorted = sorted(dom_data, key=lambda el: len(el.get("content") or ""))

    for idx, ans in enumerate(answers, start=1):
        if not ans.get("answer"):
            continue

        normalized_answer = normalize_text_block(ans["answer"])
        logging.debug(
            "🧩 [%d] Label=%s | normalized_answer=%r (len=%d)",
            idx,
            ans["label"],
            normalized_answer,
            len(normalized_answer),
        )

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
                logging.debug(
                    "❌ [%d] Index map missing/short | xpath=%s | offset_norm=%d | ans_len=%d | map_len=%d",
                    idx,
                    xpath,
                    offset_norm,
                    len(normalized_answer),
                    len(index_map),
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
                logging.debug(
                    "❌ [%d] Offset mapping failed | xpath=%s | offset_norm=%d | start_orig=%s | end_orig=%s",
                    idx,
                    xpath,
                    offset_norm,
                    start_orig,
                    end_orig,
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
            logging.debug(
                "✅ [%d] Match | xpath=%s | start_orig=%d | end_orig=%d | norm_offset=%d",
                idx,
                xpath,
                start_orig,
                end_orig,
                offset_norm,
            )
            found_match = True
            break

        if not found_match:
            diagnostics.append({"label": ans["label"], "reason": "Not found in any content block"})
            logging.debug(
                "🔍 [%d] No match for label=%s | normalized_answer=%r",
                idx,
                ans["label"],
                normalized_answer,
            )

    logging.info("🧾 Match summary: %d matches, %d diagnostics", len(matches), len(diagnostics))
    if diagnostics:
        logging.debug("🧪 Diagnostics: %s", json.dumps(diagnostics, ensure_ascii=False))
    return matches, diagnostics
