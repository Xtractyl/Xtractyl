## Pinned Images

### Label Studio (Community)
- Release: 1.21.0
- Image: heartexlabs/label-studio
- Digest: sha256:046db042674bca7e9535b7c3a9688683405d4cbf37114cc0e3a0d5dd85de0e7a
- Note: PyPI latest seen: 1.22.0 (2025-12-19)

### Ollama
- Version: 0.12.3
- Image: ollama/ollama
- Digest: sha256:c622a7adec67cf5bd7fe1802b7e26aa583a955a54e91d132889301f50c3e0bd0
- Pinned at: 2026-01-10

### Redis (job_queue)
- Version: 7.4.6
- Image: redis
- Digest: sha256:d7432711a2a5c99c2e9dd0e006061cd274d7cb7a9e77f07ffe2ea99e21244677
- Pinned at: 2026-01-10

### PostgreSQL
- Version: 15.14 (Debian 15.14-1.pgdg13+1)
- Image: postgres
- Digest: sha256:c189d272e4fcdd1ac419adee675d30be3d389c22ee770d593f15819d22a68a0d
- Pinned at: 2026-01-10

### Orchestrator (xtractyl-orchestrator)
- Base image: python:3.10.19-slim
- Requirements (top-level): docker/orchestrator/requirements.txt
- Requirements (lock): docker/orchestrator/requirements.lock.txt
- Pinned at: 2026-01-10

### Docling
- Installed via: pip (docling==2.63.0)
- Version: 2.63.0
- Base image: python:3.10.19-slim
- Image: xtractyl-docling (custom build)
- Models: preloaded via `docling-tools models download --all`
- Requirements file: docker/docling/requirements.txt
- System dependencies: tesseract-ocr, libgl1
- Requirements (lock): docker/docling/requirements.lock.txt
- Pinned at: 2026-01-10

### ML Backend (xtractyl-ml_backend)
- Base image: mcr.microsoft.com/playwright/python:v1.55.0-jammy
- Base digest: sha256:0ff30156b1035e3bc24d92f67fb57e86bd1fef126b544f32c699ce1ae9b3b692
- Runtime: Python 3.10.12
- Playwright: 1.55.0
- Requirements file: docker/ml_backend/requirements.txt
- Requirements (lock): docker/ml_backend/requirements.lock.txt
- Pinned at: 2026-01-10

### Worker Prelabel (xtractyl-worker_prelabel)
- Base image: python:3.11.14-slim
- Runtime: Python 3.11.14
- Requirements (top-level): docker/worker/requirements.txt
- Requirements (lock): docker/worker/requirements.lock.txt
- Pinned at: 2026-01-10

### Frontend (xtractyl-frontend)
- Base image: node:20.19.5-bullseye
- Runtime: Node v20.19.5
- Package manager: npm 10.8.2
- Lockfile: frontend/package-lock.json (lockfileVersion 3)
- Install: `npm ci`
- Pinned at: 2026-01-10

## Updating pinned versions
- Change top-level requirements.txt (if needed)
- Rebuild container
- Regenerate requirements.lock.txt via `pip freeze` from the running container
- Update this file and commit together