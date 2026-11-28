#!/usr/bin/env python3
"""Build DocumentReference transaction bundles for the PDFs in the seed data.

Usage: python fhir_seed/build_pdf_references.py \
    fhir_seed/data/synthea fhir_seed/data/pdf fhir_seed/data/documentreference

But we use it from the Makefile: make fhir-pdf-refs
    
Each PDF <name>.pdf (have to be put into fhir_seed/data/pdf see
formatting requirements for PDF names below) gets one bundle <name>.json 
with a DocumentReference whose attachment points to Binary/pdf-<name> 
(uploaded by load_bundles.sh) and whose subject is a patient from the Synthea files.
Patients and PDFs are sorted by file name and paired round-robin 
(PDF 1 -> patient 1, ..., then from the start again). Existing bundles 
in the output folder are never overwritten.

PDF names: lowercase letters, digits and hyphens only (max 50 characters).
"""

import json
import re
import sys
import uuid
from pathlib import Path

NAMESPACE = uuid.UUID("6f1f3c0e-5b7e-4c55-9a53-4b1b6a2f0c11")
SYNTHEA_SYSTEM = "https://github.com/synthetichealth/synthea"
PDF_SYSTEM = "https://xtractyl.example/fhir-seed/pdf"
PDF_NAME = re.compile(r"^[a-z0-9-]{1,50}$")
PATIENT_FILE = re.compile(r"_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.json$")
INFO_PREFIXES = ("hospitalInformation", "practitionerInformation")


def list_patients(synthea_dir):
    patients = []
    for f in sorted(synthea_dir.glob("*.json")):
        if f.name.startswith(INFO_PREFIXES):
            continue
        m = PATIENT_FILE.search(f.name)
        if not m:
            raise SystemExit(f"cannot read patient UUID from file name: {f.name}")
        patients.append((f.name, m.group(1)))
    return patients


def build_bundle(stem, patient_uuid):
    binary_id = f"pdf-{stem}"
    docref = {
        "resourceType": "DocumentReference",
        "identifier": [{"system": PDF_SYSTEM, "value": stem}],
        "status": "current",
        "description": stem,
        "subject": {"reference": f"Patient?identifier={SYNTHEA_SYSTEM}|{patient_uuid}"},
        "content": [
            {
                "attachment": {
                    "contentType": "application/pdf",
                    "url": f"Binary/{binary_id}",
                    "title": f"{stem}.pdf",
                }
            }
        ],
    }
    return {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "fullUrl": f"urn:uuid:{uuid.uuid5(NAMESPACE, 'docref/' + stem)}",
                "resource": docref,
                "request": {
                    "method": "POST",
                    "url": "DocumentReference",
                    "ifNoneExist": f"identifier={PDF_SYSTEM}|{stem}",
                },
            }
        ],
    }


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    synthea_dir, pdf_dir, out_dir = (Path(a) for a in argv[1:])
    patients = list_patients(synthea_dir)
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not patients:
        print(f"no patient files in {synthea_dir}")
        return 1
    if not pdfs:
        print(f"no *.pdf files in {pdf_dir}")
        return 1
    bad = [p.name for p in pdfs if not PDF_NAME.match(p.stem)]
    if bad:
        print("PDF names must match [a-z0-9-]{1,50}: " + ", ".join(bad))
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    for i, pdf in enumerate(pdfs):
        patient_file, patient_uuid = patients[i % len(patients)]
        target = out_dir / f"{pdf.stem}.json"
        if target.exists():
            print(f"kept    {target.name} (exists)")
            continue
        bundle = build_bundle(pdf.stem, patient_uuid)
        target.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"written {target.name} -> {patient_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
