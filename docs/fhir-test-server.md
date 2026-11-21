# Local FHIR test server

One container sets this up automatically on `docker compose up`:

**`fhir_seed`** loads a fixed, reproducible set of synthetic FHIR data into
the `fhir` server, but only if `fhir` is empty (no `Patient` yet). The data
is **committed to the repository** under `fhir_seed/data/` and copied into
the image at build time (`docker/fhir_seed/Dockerfile`, final stage), so the
dataset stays constant across `docker compose up` runs. This matters for
drift comparisons, which need the same underlying data across evaluation
runs. Nothing is generated at container start.

| Folder (`fhir_seed/data/`) | Content | In git |
|---|---|---|
| `synthea/` | Raw bundles from [Synthea](https://github.com/synthetichealth/synthea) (`v4.0.0`, fixed seed, `--exporter.fhir.use_us_core_ig=true`), **reduced to the patients that a document bundle was built from** plus `hospitalInformation*.json` / `practitionerInformation*.json` | yes |
| `document_bundle_generated/` | Document bundles built from `synthea/`, section texts still `TODO` | no (git-ignored, regenerable) |
| `document_bundle_final/` | The same bundles with the section texts written by hand | yes |

`fhir_seed` loads in this order:

1. `hospitalInformation*.json` and `practitionerInformation*.json` from
   `synthea/` (patient bundles reference these Organization/Practitioner
   resources),
2. the per-patient Synthea bundles from `synthea/` (`POST /fhir`),
3. the document bundles from `document_bundle_final/` (`POST /fhir/Bundle`).

`fhir` itself has no persistent volume — its data lives only in the running
container, so a full `docker compose down && up` always starts from an empty
server, and `fhir_seed` loads the committed data into it again. If `fhir`
already contains patients, `fhir_seed` does nothing.

After `docker compose up`, the server is reachable at
`http://localhost:${FHIR_PORT:-8090}/fhir` (e.g.
`GET /fhir/DocumentReference`, `GET /fhir/Patient`, `GET /fhir/Bundle`).

API documentation (endpoints/schemas, not the stored data itself):
`http://localhost:${FHIR_PORT:-8090}/fhir/swagger-ui/`. Use its "Try it
out" on a `GET` operation, or `curl`/the URLs above, to see the actual
stored resources.

## Maintaining the test data

Only needed when the committed data should change; the results are
committed, so normal users never run these. All targets are in the `Makefile`.

1. `make fhir-synthea-regen` generates raw Synthea bundles into
   `fhir_seed/data/synthea/`. It needs Docker only (no local Java) and builds
   only the Synthea stage of the `fhir_seed` Dockerfile. Patient count and
   seed can be overridden: `make fhir-synthea-regen FHIR_SYNTHEA_PATIENT_COUNT=50`.
   If `synthea/` already contains bundles, the target refuses to replace
   them, because the document bundles were built from that set. Replace it
   on purpose with `make fhir-synthea-regen FORCE=1`.
2. `make fhir-generate` builds one document bundle (Arztbrief / discharge
   summary) per suitable inpatient encounter into
   `document_bundle_generated/` and copies only **new** files to
   `document_bundle_final/`. Files already in `document_bundle_final/` are
   never overwritten, so hand-written texts survive a re-run. File names are
   `<synthea file name>__<encounter id>.json`, which makes each document
   traceable to its Synthea source.
3. `make fhir-synthea-prune` reduces `synthea/` to what is needed. Only a
   small share of the generated patients has a suitable inpatient encounter
   (22 of about 336 in the first run, 247 MB instead of 1.2 GB). The target
   removes every patient file from `synthea/` that no bundle in
   `document_bundle_generated/` was built from and keeps the
   `hospitalInformation*.json` and `practitionerInformation*.json` files.
   Run it after `make fhir-generate`; it refuses to run when
   `document_bundle_generated/` is empty. It deletes files, the full set
   comes back with `make fhir-synthea-regen FORCE=1`. Running
   `make fhir-generate` again on the reduced set must produce the same
   document bundles.
4. Write the section texts directly into `document_bundle_final/*.json`
   (`Composition.section[].text.div`, XHTML narrative).
5. `make fhir-check` validates `document_bundle_final/`: valid JSON, Bundle
   of type `document`, Composition first, unique `fullUrl`s, every reference
   resolvable inside the bundle, well-formed XHTML in every text `div`, no
   `TODO` left. It is not a replacement for the official FHIR validator.
6. Commit `synthea/` and `document_bundle_final/`.

To see the result locally, recreate the stack so `fhir` starts empty and
`fhir_seed` is rebuilt with the new data:

```bash
docker compose down
docker compose up -d --build fhir_seed
```

(`up --build` only forces a rebuild of `fhir_seed`, everything else is a
cache hit. Without `down`, `fhir` keeps its old data and `fhir_seed` does
nothing.)

## Document bundles

The bundles in `document_bundle_final/` are FHIR `Bundle`s of type
`document`: `entry[0]` is a `Composition` (LOINC 18842-5, discharge
summary) with sections (reason for admission, diagnoses, hospital course,
results, medications at discharge, procedures, follow-up). The section texts
are XHTML in `section.text.div`. The bundle is self-contained: it holds full
copies of Patient, Encounter, Conditions, lab Observations,
MedicationRequests (with their Medications), Procedures, Practitioner,
Organization and Location, and all references inside resolve to `fullUrl`s
of the same bundle. They are meant for the XPath/DOM ingestion path, like
the HTML derived from PDFs by Docling.

The underlying clinical data is synthetic Synthea data and can be medically
implausible (e.g. an adult kidney transplant in a children's hospital); the
letter texts follow the data, not clinical reality.

## Where the free text actually is

`DocumentReference.content[0].attachment.data` (Synthea data) is
base64-encoded and holds the clinical note text:

```bash
curl -s "http://localhost:8090/fhir/DocumentReference?_count=1" | python3 -c "
import json, sys, base64
entry = json.load(sys.stdin)['entry'][0]['resource']
print(base64.b64decode(entry['content'][0]['attachment']['data']).decode('utf-8'))
"
```

Plain-structured text (markdown-style headings like `# Chief Complaint`,
not HTML/XML) — this is a candidate for the planned character-offset text
ingestion path, not the XPath/DOM path used for Docling-derived HTML and
the document bundles above.

`DiagnosticReport` without US Core enabled only covers structured lab
panels (no free text); the `conclusion` field is absent on those.