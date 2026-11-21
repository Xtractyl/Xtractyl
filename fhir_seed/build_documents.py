#!/usr/bin/env python3
"""Build FHIR document bundles (without section texts) from Synthea output.

Usage:
    python scripts/fhir_build_documents.py fhir_seed/data/synthea \
        fhir_seed/data/document_bundle_generated [--min-kinds 3]

Per Synthea patient file, every finished inpatient encounter (class IMP) that has
at least --min-kinds of {Condition, lab Observation, MedicationRequest, Procedure}
becomes one Bundle of type "document":

  entry[0]  Composition (metadata, 7 sections, section.entry pointers, TODO texts)
  then      Patient, Encounter, the encounter's clinical resources, and everything
            they reference (Medication, further Conditions, Practitioner,
            Organization, Location), all as full copies.

Conditional references (Practitioner?identifier=...) are resolved against
hospitalInformation*.json / practitionerInformation*.json and rewritten to the
fullUrl of the copied entry. Everything is deterministic: same input, same output
(ids are derived from patient and encounter id, timestamp from the encounter end).
File name: <synthea file stem>__<encounter id>.json
"""

import argparse
import copy
import json
import re
import sys
import uuid
from pathlib import Path

XHTML = "http://www.w3.org/1999/xhtml"
COND_REF = re.compile(r"^(Practitioner|Organization|Location)\?identifier=([^|]+)\|(.+)$")
KINDS = ("Condition", "Observation", "MedicationRequest", "Procedure")
CLINICAL = ("Condition", "Observation", "MedicationRequest", "Procedure")
# Types that may be pulled in through references from the selected resources.
ALLOWED = {
    "Patient",
    "Encounter",
    "Condition",
    "Observation",
    "MedicationRequest",
    "Procedure",
    "Medication",
}
ORDER = [
    "Patient",
    "Encounter",
    "Condition",
    "Observation",
    "MedicationRequest",
    "Medication",
    "Procedure",
    "Practitioner",
    "Organization",
    "Location",
]
# (title, narrative status, resource type the section points to or None)
SECTIONS = [
    ("Reason for admission", "additional", None),
    ("Diagnoses", "additional", "Condition"),
    ("Hospital course", "additional", None),
    ("Results", "generated", "Observation"),
    ("Medications at discharge", "generated", "MedicationRequest"),
    ("Procedures", "generated", "Procedure"),
    ("Follow-up", "additional", None),
]
NS = uuid.UUID("6f1f3c0e-5b7e-4c55-9a53-4b1b6a2f0c11")  # fixed namespace for ids


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_lookup(synthea_dir):
    """(type, system, value) -> bundle entry, from the hospital/practitioner files."""
    index = {}
    for pattern in ("hospitalInformation*.json", "practitionerInformation*.json"):
        for f in sorted(synthea_dir.glob(pattern)):
            for entry in load(f).get("entry", []):
                res = entry["resource"]
                for ident in res.get("identifier", []):
                    index[(res["resourceType"], ident["system"], ident["value"])] = entry
    return index


def reference_dicts(node):
    if isinstance(node, dict):
        if isinstance(node.get("reference"), str):
            yield node
        for v in node.values():
            yield from reference_dicts(v)
    elif isinstance(node, list):
        for v in node:
            yield from reference_dicts(v)


def is_lab(res):
    return any(
        c.get("code") == "laboratory"
        for cat in res.get("category", [])
        for c in cat.get("coding", [])
    )


def div(text):
    return f"<div xmlns='{XHTML}'><p>{text}</p></div>"


def collect(enc_url, by_url, lookup):
    """Return (ordered {fullUrl: resource copy}, problems) for one encounter."""
    chosen = {}
    problems = []
    queue = [enc_url]
    for fu, res in by_url.items():
        t = res["resourceType"]
        if t in CLINICAL and res.get("encounter", {}).get("reference") == enc_url:
            if t == "Observation" and not is_lab(res):
                continue
            queue.append(fu)
    while queue:
        fu = queue.pop(0)
        if fu in chosen:
            continue
        res = copy.deepcopy(by_url[fu] if fu in by_url else lookup[fu]["resource"])
        chosen[fu] = res
        for ref in reference_dicts(res):
            value = ref["reference"]
            m = COND_REF.match(value)
            if m:
                entry = lookup.get((m.group(1), m.group(2), m.group(3)))
                if entry is None:
                    problems.append(f"unresolved {value}")
                    continue
                ref["reference"] = entry["fullUrl"]
                lookup[entry["fullUrl"]] = entry  # make it fetchable by fullUrl
                queue.append(entry["fullUrl"])
            elif value in by_url:
                if by_url[value]["resourceType"] not in ALLOWED:
                    problems.append(f"reference to {by_url[value]['resourceType']} not supported")
                else:
                    queue.append(value)
            elif value not in chosen and value not in lookup:
                problems.append(f"unresolvable reference {value}")
    return chosen, problems


def build_document(patient_url, enc_url, chosen, patient_id, enc_id):
    def rank(item):
        return (ORDER.index(item[1]["resourceType"]), item[0])

    entries_sorted = sorted(chosen.items(), key=rank)
    enc = chosen[enc_url]
    participants = enc.get("participant", [])
    author = next(
        (
            p["individual"]["reference"]
            for p in participants
            if any(c.get("code") == "PPRF" for t in p.get("type", []) for c in t.get("coding", []))
            and "individual" in p
        ),
        None,
    )
    if author is None and participants and "individual" in participants[0]:
        author = participants[0]["individual"]["reference"]
    custodian = enc.get("serviceProvider", {}).get("reference")
    if not author or not custodian:
        return None, "encounter has no practitioner or serviceProvider"
    end = enc.get("period", {}).get("end")
    if not end:
        return None, "encounter has no period.end"

    comp_url = "urn:uuid:" + str(uuid.uuid5(NS, f"composition/{patient_id}/{enc_id}"))
    sections = []
    for title, status, kind in SECTIONS:
        sec = {"title": title, "text": {"status": status, "div": div("TODO")}}
        if kind:
            refs = [
                {"reference": fu}
                for fu, r in entries_sorted
                if r["resourceType"] == kind
                and (kind != "Observation" or is_lab(r))
                and r.get("encounter", {}).get("reference") == enc_url
            ]
            if refs:
                sec["entry"] = refs
        sections.append(sec)
    composition = {
        "resourceType": "Composition",
        "language": "en",
        "text": {"status": "additional", "div": div("TODO header")},
        "status": "preliminary",
        "type": {
            "coding": [
                {"system": "http://loinc.org", "code": "18842-5", "display": "Discharge summary"}
            ]
        },
        "subject": {"reference": patient_url},
        "encounter": {"reference": enc_url},
        "date": end,
        "author": [{"reference": author}],
        "title": "Discharge summary",
        "custodian": {"reference": custodian},
        "section": sections,
    }
    bundle = {
        "resourceType": "Bundle",
        "identifier": {
            "system": "urn:ietf:rfc:3986",
            "value": "urn:uuid:" + str(uuid.uuid5(NS, f"bundle/{patient_id}/{enc_id}")),
        },
        "type": "document",
        "timestamp": end,
        "entry": [{"fullUrl": comp_url, "resource": composition}]
        + [{"fullUrl": fu, "resource": r} for fu, r in entries_sorted],
    }
    return bundle, None


def process_patient_file(path, lookup, out_dir, min_kinds):
    bundle = load(path)
    by_url = {e["fullUrl"]: e["resource"] for e in bundle["entry"]}
    patient_url = next((fu for fu, r in by_url.items() if r["resourceType"] == "Patient"), None)
    if patient_url is None:
        return 0, [f"{path.name}: no Patient"]
    patient_id = by_url[patient_url]["id"]
    written, notes = 0, []
    for fu, res in by_url.items():
        if res["resourceType"] != "Encounter" or res.get("class", {}).get("code") != "IMP":
            continue
        if res.get("status") != "finished":
            continue
        present = {
            t
            for t in KINDS
            for r in by_url.values()
            if r["resourceType"] == t
            and r.get("encounter", {}).get("reference") == fu
            and (t != "Observation" or is_lab(r))
        }
        if len(present) < min_kinds:
            notes.append(f"{path.name} {res['id']}: skipped, only {sorted(present)}")
            continue
        chosen, problems = collect(fu, by_url, dict(lookup))
        if problems:
            notes.append(f"{path.name} {res['id']}: skipped, {sorted(set(problems))[:3]}")
            continue
        doc, why = build_document(patient_url, fu, chosen, patient_id, res["id"])
        if doc is None:
            notes.append(f"{path.name} {res['id']}: skipped, {why}")
            continue
        out = out_dir / f"{path.stem}__{res['id']}.json"
        out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written += 1
    return written, notes


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("synthea_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--min-kinds", type=int, default=3)
    args = ap.parse_args(argv[1:])
    lookup = build_lookup(args.synthea_dir)
    if not lookup:
        print("no hospitalInformation*/practitionerInformation* files found", file=sys.stderr)
        return 1
    args.out_dir.mkdir(parents=True, exist_ok=True)
    skip = ("hospitalInformation", "practitionerInformation")
    files = [f for f in sorted(args.synthea_dir.glob("*.json")) if not f.name.startswith(skip)]
    total, notes = 0, []
    for f in files:
        n, ns = process_patient_file(f, lookup, args.out_dir, args.min_kinds)
        total += n
        notes += ns
    for line in notes:
        print(line, file=sys.stderr)
    print(f"{len(files)} patient file(s), {total} document bundle(s) written to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
