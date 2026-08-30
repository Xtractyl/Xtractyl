# Stage 1: generate synthetic FHIR bundles with Synthea.
# Runs only at `docker build` / `docker compose build` time — not on every
# `docker compose up` — and with a fixed seed, so the dataset is constant
# across runs (needed for drift comparisons) instead of changing every time.
FROM eclipse-temurin:17-jre AS synthea

WORKDIR /synthea

ARG FHIR_SYNTHEA_PATIENT_COUNT=25
ARG FHIR_SYNTHEA_SEED=12345

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -L -o synthea-with-dependencies.jar \
       https://github.com/synthetichealth/synthea/releases/download/v4.0.0/synthea-with-dependencies.jar

RUN java -jar synthea-with-dependencies.jar \
    -p ${FHIR_SYNTHEA_PATIENT_COUNT} \
    -s ${FHIR_SYNTHEA_SEED} \
    --exporter.fhir.use_us_core_ig=true

# Stage 2: the actual fhir_seed image — just curl + the baked-in bundles.
# No Java, no Synthea at runtime; loading the fixed dataset into `fhir` is
# all this container does.
FROM curlimages/curl@sha256:83a505ba2ba62f208ed6e410c268b7b9aa48f0f7b403c8108b9773b44199dbba

USER root
COPY --from=synthea /synthea/output/fhir /bundles
COPY fhir_seed/load_bundles.sh /load_bundles.sh
RUN chmod +x /load_bundles.sh
USER curl_user

ENTRYPOINT ["/bin/sh", "/load_bundles.sh"]