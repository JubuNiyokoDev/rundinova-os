# Build a RundiNova app release on an already approved, self-hosted image.
# This path updates only the local app code and assets; it never resolves
# Frappe, ERPNext, HRMS, or CRM branches from upstream.
ARG RUNDINOVA_BASE_IMAGE=rundinova/erpnext:16.37.7
FROM ${RUNDINOVA_BASE_IMAGE}
ARG RUNDINOVA_BASE_IMAGE
ARG RUNDINOVA_BASE_IMAGE_ID

USER frappe
WORKDIR /home/frappe/frappe-bench

COPY --chown=frappe:frappe apps/rundinova_tech /tmp/rundinova_tech-source
COPY images/rundinova/capture-release-metadata.py /opt/capture-release-metadata.py

RUN rm -rf apps/rundinova_tech && \
	mv /tmp/rundinova_tech-source apps/rundinova_tech && \
	env/bin/pip install --no-deps --quiet -e apps/rundinova_tech && \
    bench build --app rundinova_tech && \
    if [ ! -L assets/rundinova_tech ]; then \
      mkdir -p assets/rundinova_tech && \
      cp -a apps/rundinova_tech/rundinova_tech/public/. assets/rundinova_tech/; \
    fi && \
    test -f assets/rundinova_tech/js/workspace_sidebar.js && \
    test -f assets/rundinova_tech/js/rundinova_branding.js && \
    test -f assets/rundinova_tech/css/rundinova_desk.css && \
    test -f assets/rundinova_tech/images/rundinova-favicon.svg && \
    test -f assets/rundinova_tech/images/rundinova-logo.png && \
    python3 /opt/capture-release-metadata.py overlay \
      --bench-dir /home/frappe/frappe-bench \
      --output /home/frappe/frappe-bench/release-metadata.json \
      --base-image "${RUNDINOVA_BASE_IMAGE}" \
      --base-image-id "${RUNDINOVA_BASE_IMAGE_ID}"
