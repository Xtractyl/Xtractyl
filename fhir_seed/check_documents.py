#!/usr/bin/env python3
"""Validate hand-finished FHIR document bundles before they are committed.

Usage: python fhir_seed/check_documents.py fhir_seed/data/document_bundle_final

Checks per file: valid JSON, Bundle.type == document, entry[0] is a Composition,
every section.text.div is well-formed XML with the XHTML namespace and has
non-whitespace text, no TODO placeholder is left, fullUrls are unique and every
reference inside the bundle resolves to a fullUrl. Exit code 1 on any finding.
Not a replacement for the official FHIR validator.
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

XHTML_NS = "http://www.w3.org/1999/xhtml"


def walk_refs(node):
    if isinstance(node, dict):
        ref = node.get("reference")
        if isinstance(ref, str):
            yield ref
        for v in node.values():
            yield from walk_refs(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_refs(v)


def check_div(div, where, problems):
    try:
        root = ET.fromstring(div)
    except ET.ParseError as e:
        problems.append(f"{where}: div is not well-formed XML ({e})")
        return
    if root.tag != f"{{{XHTML_NS}}}div":
        problems.append(f"{where}: root must be <div xmlns='{XHTML_NS}'>")
    text = "".join(root.itertext())
    if not text.strip():
        problems.append(f"{where}: div has no text content")
    if "TODO" in text:
        problems.append(f"{where}: TODO placeholder still present")


def check_file(path):
    problems = []
    try:
        bundle = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [f"not valid JSON ({e})"]
    if bundle.get("resourceType") != "Bundle" or bundle.get("type") != "document":
        problems.append("not a Bundle of type document")
        return problems
    entries = bundle.get("entry") or []
    if not entries or entries[0].get("resource", {}).get("resourceType") != "Composition":
        problems.append("entry[0] is not a Composition")
        return problems
    urls = [e.get("fullUrl") for e in entries]
    if None in urls or len(set(urls)) != len(urls):
        problems.append("fullUrl missing or not unique")
    known = {u for u in urls if u}
    for e in entries:
        for ref in walk_refs(e.get("resource", {})):
            if ref not in known:
                problems.append(f"reference not resolvable inside bundle: {ref}")
    comp = entries[0]["resource"]
    narr = comp.get("text", {}).get("div")
    if narr:
        check_div(narr, "Composition.text", problems)
    for i, sec in enumerate(comp.get("section") or []):
        div = sec.get("text", {}).get("div")
        where = f"section[{i}] '{sec.get('title', '?')}'"
        if div is None:
            if not sec.get("entry"):
                problems.append(f"{where}: no text.div and no entry")
        else:
            check_div(div, where, problems)
    return problems


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    files = sorted(Path(argv[1]).glob("*.json"))
    if not files:
        print(f"no *.json files in {argv[1]}")
        return 1
    bad = 0
    for f in files:
        probs = check_file(f)
        for p in probs:
            print(f"{f.name}: {p}")
        bad += bool(probs)
    print(f"{len(files)} file(s) checked, {bad} with findings")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
