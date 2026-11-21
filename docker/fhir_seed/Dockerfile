# stage 1: synthea FHIR data generating stage.
FROM eclipse-temurin:17-jre AS synthea

WORKDIR /synthea

ARG FHIR_SYNTHEA_PATIENT_COUNT
ARG FHIR_SYNTHEA_SEED

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && curl -L -o synthea-with-dependencies.jar \
       https://github.com/synthetichealth/synthea/releases/download/v4.0.0/synthea-with-dependencies.jar

RUN java -jar synthea-with-dependencies.jar \
    -p ${FHIR_SYNTHEA_PATIENT_COUNT} \
    -s ${FHIR_SYNTHEA_SEED} \
    --exporter.fhir.use_us_core_ig=true


# stage 2: started with 'make fhir-synthea-regen' starts stage 1 
# (due to --from dependency) copies stage 1 build and (see Makefile)
# copies data to fhir_seed/data/document_bundle_generated
FROM scratch AS synthea_export
COPY --from=synthea /synthea/output/fhir /


# stage 3 can only run after
# 1. completing stage 1 and 2
# 2. running 'make fhir-generate' to create 
# raw document bundles in /fhir_seed/data/document_bundle_final
# 3. adding section.text.div manually to finalize document bundles


# stage 3: started with 'docker compose up --build fhir_seed'
# copies patient bundles and document bundles on fhir server (if the server is empty)

FROM curlimages/curl@sha256:83a505ba2ba62f208ed6e410c268b7b9aa48f0f7b403c8108b9773b44199dbba

USER root
COPY fhir_seed/data/synthea /bundles/synthea
COPY fhir_seed/data/document_bundle_final /bundles/document_bundle_final
COPY fhir_seed/load_bundles.sh /load_bundles.sh
RUN chmod +x /load_bundles.sh
USER curl_user

ENTRYPOINT ["/bin/sh", "/load_bundles.sh"]