## Penguin Species Classification — Production ML Deployment
## Arjun Aji — Data Analytics / ML Systems
# Repository: penguin-classifier-ml-deployment
# Date: 2025-08-08

# Table of Contents
# Project Overview

# Architecture Diagram & Rationale

# Getting Started — Local Setup

# Cloud Setup & Deployment (Manual)

- API Specification

- Testing

- Containerization & Image Management

- Load Testing & Performance Evaluation

- Security, Reliability & Operational Considerations

# Answers to Assignment Questions 

Troubleshooting & Known Issues

Appendices: Useful Commands & References

# Project Overview
This project demonstrates an industrially-informed ML deployment lifecycle for a Penguin species classification model (XGBoost) served via a production FastAPI microservice. The goals are to ensure reproducible model training, robust input validation, automated testing, containerized deployment to Google Cloud Run, and empirical load testing to reason about scalability, latency, and cost. The repo contains:

train.py — reproducible model training (XGBoost) and model serialization (penguin_model.json).

main.py — FastAPI application with Pydantic validation, model loading (GCS or local fallback), and /predict endpoint.

tests/ — pytest unit tests covering happy paths and edge cases; pytest-cov configuration for coverage.

Dockerfile, .dockerignore — production-oriented container build artifacts.

locustfile.py — Locust load-test scenarios to generate throughput/latency profiles.

.github/workflows/ — CI pipeline templates (build, test, lint, container build + artifact push).

DEPLOYMENT.md, LOAD_TEST_REPORT.md — process documentation and load test analysis.

This repository is intentionally structured to mirror a minimal but production-relevant MLOps pipeline: train → test → containerize → push → deploy → load-test → monitor.

Architecture Diagram & Rationale
Logical components:

Model training (local/Colab): XGBoost classifier trained on curated features from the penguins dataset.

Artifact storage: Google Cloud Storage (GCS) stores penguin_model.json. Model artifacts are immutable versioned objects.

Container registry: Google Artifact Registry stores container images.

Serving: Cloud Run serves stateless FastAPI containers behind HTTPS; autoscaling handles ephemeral traffic spikes.

Observability: Stackdriver (Cloud Monitoring & Logging) collects logs and metrics; Locust and local profiling produce load test artifacts.

Rationale (concise):
XGBoost provides a compact, performant model for tabular classification. Cloud Run provides a serverless execution model that simplifies operations (autoscaling, TLS), enabling rapid, cost-conscious experimentation and scale testing. Storing models in GCS decouples artifact management from deployments and enables versioning.

# Getting Started — Local Setup
# Requirements
Python 3.10+ (3.10.16 recommended)

Docker Desktop (latest stable)

Google Cloud SDK (gcloud) with gsutil

pip and virtualenv / .venv

Git

Quick local steps
Clone repository

git clone <repo-url>
cd penguin-classifier-ml-deployment
Create & activate venv (Windows PowerShell example)

powershell
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
Train model (optional: use Colab to run heavy compute)
```
```
python train.py
```
# outputs penguin_model.json
Run API locally

# if uvicorn not on PATH, use python -m
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8080
# visit http://localhost:8080/docs
Run unit tests and coverage
```
pytest --cov=your_app_or_root tests/
Cloud Setup & Deployment (Manual)
Create GCP resources (one-time)
Enable required APIs: Cloud Run, Artifact Registry, Cloud Storage.
```
Create GCS bucket: gsutil mb -l us-central1 gs://<your-bucket-name>

Create Artifact Registry repo (Docker format) in the same region.

Service account
Create penguin-api-sa with roles:

roles/storage.objectViewer

roles/storage.objectAdmin (if you want automated uploads from CI)

(For pushing to Artifact Registry from CI, provide roles/artifactregistry.writer or adjust IAM).

Generate sa-key.json and keep it safe. Add to .gitignore.

Build image locally and push to Artifact Registry

# Build
docker build -t penguin-api .

# Tag (example)
docker tag penguin-api us-central1-docker.pkg.dev/<PROJECT_ID>/<REPO>/penguin-api:latest

# Authenticate Docker to Artifact Registry (one-time)
gcloud auth configure-docker us-central1-docker.pkg.dev

# Push
```
docker push us-central1-docker.pkg.dev/<PROJECT_ID>/<REPO>/penguin-api:latest
Deploy to Cloud Run (console or gcloud)
```
```
gcloud run deploy penguin-api \
  --image=us-central1-docker.pkg.dev/<PROJECT_ID>/<REPO>/penguin-api:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --port=8080 \
  --memory=512Mi
```
Cloud Run returns a public HTTPS URL. Add it to DEPLOYMENT.md as CLOUD_RUN_URL.

API Specification
POST /predict
Description: Predict penguin species from four numerical features.

Request (JSON):

```
{
  "bill_length_mm": 39.1,
  "bill_depth_mm": 18.7,
  "flipper_length_mm": 181,
  "body_mass_g": 3750
}
```
Response (JSON):
```
{
  "prediction": 2
}
```
Validation: All fields required. Non-negative floats. Pydantic raises 422 for type/field errors and app returns 400 for logical domain errors.

Example curl
```
curl -X POST $CLOUD_RUN_URL/predict \
  -H "Content-Type: application/json" \
  -d '{"bill_length_mm":39.1,"bill_depth_mm":18.7,"flipper_length_mm":181,"body_mass_g":3750}'
```
Testing
Unit tests (in tests/)
Model prediction test — deterministic prediction on a known sample.

API endpoint test — 200 OK and JSON schema compliance.

Input validation tests — missing fields, invalid types (strings), out-of-range values (negative).

Edge cases — extreme numeric values, empty request body.

Run
```
pytest --cov=your_app_or_root tests/
Aim: >80% coverage; include pytest-cov report artifacts in CI.
```
Containerization & Image Management
Dockerfile considerations
```
Base image: python:3.10-slim for compact surface area.
```
requirements.txt pinned to deterministic versions for reproducible builds.

Multi-stage builds are optional for compiled dependencies, but this project keeps a single-stage minimal image to simplify Cloud Run deployment.

.dockerignore (example)
```
__pycache__/
.env
.git
tests/
*.pyc
*.md
```
Docker layer caching
Order COPY and RUN lines to maximize cache reuse: install requirements before copying the entire app to keep layer for dependency installs when code changes.

In CI, leverage build cache (or remote cache) to speed subsequent builds.

Load Testing & Performance Evaluation
locustfile.py scenarios
Baseline: 1 user, 60s

Normal: 10 users, 5 min

Stress: 50 users, 2 min

Spike: ramp 1 → 100 users in 1 minute

Local run
```
locust -f locustfile.py --host=http://localhost:8080
```
For Cloud Run:
```
Use --host=https://<cloud-run-url> and ensure load origin IPs are not blocked.
```
Record: response times (p50, p95, p99), failure rate, throughput (req/s), CPU/memory utilization.

Deliverable: LOAD_TEST_REPORT.md with scenario metrics and recommendations.

Security, Reliability & Operational Considerations
Secrets: Use Secret Manager (or set CI/CD secrets) to avoid embedding sa-key.json in repo. Do not check service account keys into Git.

Least privilege IAM: Give service accounts minimal roles required for runtime operations: Storage Object Viewer for model read; separate CI credentials for pushing images.

Container user: Avoid running as root inside container; create a non-root user in Dockerfile for runtime.

Model integrity: Verify model checksum (e.g., SHA256) at load time; use signed artifacts if strict integrity is required.

Observability: Export latency and error metrics (request histograms, error counters) to Cloud Monitoring and ensure logs contain structured JSON for ingestion.

# Answers to Assignment Questions 
# The following answers are written to demonstrate critical thinking about model theatre, deployment fragility, and production-grade mitigations. They combine technical reasoning, trade-off analysis, and prescriptive controls.

# 1. What edge cases might break your model in production that aren't in your training data?
Technical analysis:
Training data (the seaborn penguins dataset) is limited in geographic, seasonal, and measurement contexts; therefore the model is exposed to sample selection bias and covariate shift in production. Potential out-of-distribution (OOD) inputs include:

Novel species or mislabeled species — classifications for species not present in training will be arbitrarily mapped to a seen class.

Sensor/measurement drift — different calipers or measurement conventions could bias input distributions (systematic shifts in units or scale).

Unit confusion — values inadvertently provided in different units (inches vs mm; g vs kg).

Missing or partially missing features — production telemetry may omit fields or send null.

Adversarial or malformed payloads — e.g., extreme outliers (bill_length_mm = 1e6) or text injection in numeric fields.

Data type mismatch — strings or JSON types where floats expected.

Correlated feature shift — covariate relationships change (e.g., a seasonal sub-population with different mass distributions).

Mitigations:

Input validation + schema enforcement (Pydantic).

Input sanitization and normalization, including unit detection heuristics.

OOD detection mechanism (e.g., Mahalanobis distance, predictive uncertainty from an ensemble or temperature scaling, or runtime monitoring alerting when feature distributions diverge).

Canary/blue-green deployment so a subset of traffic exercises updated models.

# 2. What happens if your model file becomes corrupted?
Failure semantics:

Corruption on disk or in transit may raise parse/load exceptions (XGBoost load_model will throw). If unhandled, the service can fail during startup and return 5xx errors.

Mitigations & best practice:

Validate checksum prior to load (SHA256 or signing).

Implement fallback hierarchy: (1) load preferred model artifact from GCS; (2) if corrupted, auto-rollback to last-known-good artifact; (3) raise an operational alert and serve a graceful degraded response (e.g., cached last predictions, or return an explicit 503 with diagnostic info).

Use artifact immutability and versioning to avoid accidental overwrites.

# 3. What's a realistic load for a penguin classification service?
Analytical approach:
Define expected user model: the service is likely to be a research utility or embedded in a field-app ingestion pipeline. Realistic production loads vary by use case:

Lab/research UI: < 1 req/s

Mobile field app (moderate): 5–20 req/s during active periods

High-throughput telemetry ingestion: 50–500 req/s

Default practical baseline: For the assignment and typical university deployment, plan for ~10 req/s peak with p95 latency < 200 ms. Use this to configure autoscaling thresholds and concurrency settings.

# 4. How would you optimize if response times are too slow?
Profiling-first principle: identify the bottleneck: model inference time, cold-start container time, I/O to GCS, or CPU saturation.

Optimization strategies:

Model-level: quantize model or convert to a lighter runtime (e.g., XGBoost to Treelite or ONNX; compile to optimized inference engine).

Serving-level: preload model during container startup; avoid loading model per-request; enable model caching; increase concurrency and CPU allocation.

Container-level: increase CPU/memory; use provisioned concurrency (if supported) or keep a minimum number of warm instances.

I/O: keep model in local container filesystem instead of fetching from GCS per request; use a bootstrap step to download during image build for immutable models or during instance cold-start for dynamic models with caching.

Batching: if workflow allows, implement micro-batching for high throughput scenarios to amortize per-request overhead.

Language/Runtime: move latency-critical inference to C++/Go service or use gRPC for low-latency endpoints.

# 5. What metrics matter most for ML inference APIs?
Primary metrics:

Latency: p50/p95/p99 (ms)

Throughput: requests/sec (RPS)

Error rate: 4xx/5xx ratios

Resource utilization: CPU, memory per instance

Cold-start frequency and time-to-warm

Model-specific: prediction distribution drift metrics, input feature drift, confidence/uncertainty distributions

Observability best practice: correlate per-request latency with resource consumption and model input features to isolate root cause.

# 6. Why is Docker layer caching important for build speed? (Did you leverage it?)
Technical explanation:
Docker performs layer-by-layer builds. If earlier layers (e.g., OS packages, pip install) do not change, Docker reuses cached layers, dramatically reducing build times. Structuring Dockerfile to copy static dependency files (requirements.txt) and RUN pip install before copying application source maximizes cache reuse.

Leverage: The provided Dockerfile order installs dependencies from requirements.txt before copying application files so code changes will not invalidate the dependency installation layer.

# 7. What security risks exist with running containers as root?
Risks:

Process escaping or privilege escalation in case of container breakout exploits.

Lateral movement in multi-tenant hosts (if Docker is misconfigured).

Easier exploitation of vulnerabilities in running processes that require root permissions.

Mitigation:

Use USER directive to run as non-root in Dockerfile.

Apply read-only root filesystem where possible; drop unnecessary Linux capabilities; run with least privilege.

Use image scanning (Snyk/Trivy) and keep base images minimal.

# 8. How does cloud auto-scaling affect your load test results?
Observed effects:

Initial cold-start penalty: first request(s) after scale-up may experience higher latency. This inflates p99 on short stress tests.

Auto-scaling dampens failure under increasing load, but scaling decisions introduce transient throughput/latency dynamics.

Tests that ramp too fast can cause many cold starts and produce pessimistic latency profiles.

Testing guidance:

Include warm-up phases and ramp profiles to emulate realistic loads.

Measure scale-up latency, instance spin-up time, and steady-state throughput separately.

# 9. What would happen with 10x more traffic?
Consequences:

If CPU/memory are the bottleneck: queuing and increased latencies; potential errors if concurrent limits are exceeded.

If autoscaling is unconstrained and budget is unlimited: Cloud Run will scale up to meet demand (subject to concurrency and quota), increasing cost linearly.

If model inference is I/O-bound (e.g., remote model fetch): throughput collapse.

Mitigation:

Horizontal scale with bounded concurrency per instance.

Introduce rate limiting or admission control for graceful degradation.

Profile and optimize hot path (model inference), and implement async or batch processing pipelines for very high traffic.

# 10. How would you monitor performance in production?
Monitoring stack:

Metrics: Cloud Monitoring (latency histograms, throughput, error rates); custom metrics for model drift.

Logging: structured request logs in Cloud Logging with trace ids, input summary (no PII), and predicted class.

Tracing: distributed tracing to observe request path time (if fronted by API Gateway).

Alerting: p99 latency, error rates, cold-start frequency, and data-drift thresholds.

Canaries: deploy new models to a small % of traffic and monitor above metrics before full rollout.

# 11. How would you implement blue-green deployment?
Implementation plan:

Deploy new revision to Cloud Run with different traffic allocation (e.g., 5% new, 95% old).

Use health checks and metric-based gating (latency, errors, model output sanity checks).

If canary passes, gradually shift traffic; otherwise rollback by routing all traffic to previous revision.

Automate via CI/CD: pipeline triggers image build → push → deploy → automated smoke tests → traffic shift gating.

# 12. What would you do if deployment fails in production?
Operational playbook:

Rollback: revert traffic to last stable revision; Cloud Run allows quick traffic routing changes.

Investigate: check logs and recent commits; compare metrics against baseline.

Fix: patch code or configuration, rebuild image and redeploy as a canary.

Postmortem: record root cause, mitigation, and preventive action; update tests to catch the issue earlier.

# 13. What happens if your container uses too much memory?
Behavior:

Cloud Run will terminate the instance (OOM), triggering 5xx errors until autoscaler provisions new instances.

Excessive memory leads to instability, higher costs, and request failures.

Mitigation:

Right-size memory allocation via profiling.

Use streaming/batched inference to reduce memory per request.

Monitor memory usage and alert on sustained high usage.

Consider using smaller, specialized inference servers or model pruning to reduce memory footprint.

Troubleshooting & Known Issues
Dockerfile appears empty: ensure Dockerfile exists in project root with correct contents (no .txt suffix).

uvicorn not found: install in venv (pip install "uvicorn[standard]") or run python -m uvicorn main:app.

Windows venv pip upgrade fails (WinError 32): close Python processes, disable antivirus temporarily, or manually upgrade pip in an administrative console.

GCS permission errors: check service account scopes and GOOGLE_APPLICATION_CREDENTIALS env var.

Cold starts: set a minimum number of instances in Cloud Run (if required) or keep warmers in a scheduled job.
