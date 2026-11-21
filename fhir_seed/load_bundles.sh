#!/bin/sh
# fhir_seed/load_bundles.sh
#
# Loads the committed FHIR bundles baked into this image into the fhir
# server, but only if the server is empty (no Patient yet):
#   /bundles/synthea                 Synthea bundles   -> POST ${FHIR_BASE}
#   /bundles/document_bundle_final   document bundles  -> POST ${FHIR_BASE}/Bundle
#
# Synthea writes hospitalInformation*.json and practitionerInformation*.json
# alongside the per-patient bundles; patient bundles reference those
# Organization/Practitioner resources, so they must be loaded first or the
# reference resolution inside the transaction will fail.

set -eu

FHIR_BASE="http://${FHIR_CONTAINER_NAME:-fhir}:8080/fhir"
SYNTHEA_DIR="/bundles/synthea"
DOCUMENT_DIR="/bundles/document_bundle_final"

echo "fhir_seed: waiting for ${FHIR_BASE}/metadata to respond..."
until curl -sf "${FHIR_BASE}/metadata" > /dev/null; do
  sleep 2
done

patients=$(curl -sf "${FHIR_BASE}/Patient?_summary=count" | grep -o '"total" *: *[0-9]*' | grep -o '[0-9]*$' || true)
if [ "${patients:-0}" != "0" ]; then
  echo "fhir_seed: server already contains ${patients} Patient(s), nothing to do."
  exit 0
fi

post_bundle() {
  bundle="$1"
  url="$2"
  http_status=$(curl -s -o /tmp/fhir_seed_response.json -w "%{http_code}" \
    -X POST "$url" \
    -H "Content-Type: application/fhir+json" \
    --data-binary "@${bundle}")

  if [ "$http_status" -ge 200 ] && [ "$http_status" -lt 300 ]; then
    echo "fhir_seed: OK ($http_status) - $(basename "$bundle")"
    return 0
  else
    echo "fhir_seed: FAILED ($http_status) - $(basename "$bundle")"
    cat /tmp/fhir_seed_response.json
    return 1
  fi
}

for dir in "$SYNTHEA_DIR" "$DOCUMENT_DIR"; do
  if [ ! -d "$dir" ]; then
    echo "fhir_seed: ${dir} not found in image - check the COPY lines in docker/fhir_seed/Dockerfile."
    exit 1
  fi
done

count=0

for bundle in "$SYNTHEA_DIR"/hospitalInformation*.json "$SYNTHEA_DIR"/practitionerInformation*.json; do
  [ -e "$bundle" ] || continue
  echo "fhir_seed: loading reference bundle $(basename "$bundle")"
  post_bundle "$bundle" "$FHIR_BASE" && count=$((count + 1))
done

for bundle in "$SYNTHEA_DIR"/*.json; do
  [ -e "$bundle" ] || continue
  case "$(basename "$bundle")" in
    hospitalInformation*.json|practitionerInformation*.json) continue ;;
  esac
  echo "fhir_seed: loading patient bundle $(basename "$bundle")"
  post_bundle "$bundle" "$FHIR_BASE" && count=$((count + 1))
done

for bundle in "$DOCUMENT_DIR"/*.json; do
  [ -e "$bundle" ] || continue
  echo "fhir_seed: loading document bundle $(basename "$bundle")"
  post_bundle "$bundle" "${FHIR_BASE}/Bundle" && count=$((count + 1))
done

echo "fhir_seed: done, loaded ${count} bundle(s)."