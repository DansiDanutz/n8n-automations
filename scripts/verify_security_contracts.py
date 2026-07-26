#!/usr/bin/env python3
"""Verify repository-wide security contracts for privileged services."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
failures: list[str] = []


def source(path: str) -> str:
    value = (ROOT / path).read_text()
    ast.parse(value, filename=path)
    return value


def require(value: str, expected: str, message: str) -> None:
    if expected not in value:
        failures.append(message)


cron = source("cron-job-dashboard/main.py")
limiter = source("api-rate-limiter/main.py")
purchase = source("purchase-webhook/main.py")
cron_env = (ROOT / "cron-job-dashboard/.env.example").read_text()
limiter_env = (ROOT / "api-rate-limiter/.env.example").read_text()
cron_requirements = (ROOT / "cron-job-dashboard/requirements.txt").read_text()
limiter_requirements = (ROOT / "api-rate-limiter/requirements.txt").read_text()
cron_setup = (ROOT / "cron-job-dashboard/setup.sh").read_text()
limiter_setup = (ROOT / "api-rate-limiter/setup.sh").read_text()
cron_docker = (ROOT / "cron-job-dashboard/Dockerfile").read_text()
limiter_docker = (ROOT / "api-rate-limiter/Dockerfile").read_text()
purchase_env = (ROOT / "purchase-webhook/.env.example").read_text()
purchase_requirements = (ROOT / "purchase-webhook/requirements.txt").read_text()
purchase_docker = (ROOT / "purchase-webhook/Dockerfile").read_text()

require(cron, 'required_secret("API_KEY", 32)', "cron dashboard must require a strong API key")
require(cron, 'request.url.path not in {"/", "/health"}', "cron dashboard must authenticate non-public routes")
require(cron, 'request.headers.get("X-API-Key", "")', "cron dashboard must read X-API-Key")
require(cron, "hmac.compare_digest", "cron dashboard API-key checks must be timing safe")

require(limiter, 'required_secret("ADMIN_API_KEY", 32)', "rate limiter must reject missing or weak admin keys")
require(limiter, "hmac.compare_digest", "rate limiter admin-key checks must be timing safe")
if 'os.getenv("ADMIN_API_KEY", "admin-secret-key")' in limiter:
    failures.append("rate limiter must not ship a default admin credential")
require(cron_env, "API_KEY=replace-with-at-least-32-random-characters", "cron environment template must require a strong key")
require(limiter_env, "ADMIN_API_KEY=replace-with-at-least-32-random-characters", "limiter environment template must require a strong key")
require(purchase, 'required_secret("STRIPE_WEBHOOK_SECRET", 16)', "purchase webhook must fail closed without a signing secret")
require(purchase, 'required_secret("GITHUB_TOKEN", 20)', "purchase webhook must fail closed without a GitHub token")
require(purchase, 'required_secret("MANAGEMENT_API_KEY", 32)', "purchase records must require a management key")
require(purchase, 'request.url.path.startswith("/purchases")', "purchase record routes must be authenticated")
require(purchase, "hmac.compare_digest", "purchase management-key checks must be timing safe")
require(purchase, "processed_event_ids", "purchase fulfillment must track processed Stripe events")
require(purchase, "inflight_event_ids", "purchase fulfillment must reject concurrent Stripe replays")
require(purchase_env, "MANAGEMENT_API_KEY=replace-with-at-least-32-random-characters", "purchase template must require a management key")
for expected in (
    "fastapi==0.140.0",
    "uvicorn[standard]==0.51.0",
    "stripe==15.3.1",
    "httpx==0.28.1",
    "pydantic==2.13.4",
):
    require(purchase_requirements, expected, f"purchase webhook must pin audited dependency {expected}")
if "python-multipart" in purchase_requirements:
    failures.append("purchase webhook must not include unused python-multipart")
require(purchase_docker, "pip>=26.1.2", "purchase container must upgrade pip past PYSEC-2026-196")
for name, requirements in (("cron dashboard", cron_requirements), ("rate limiter", limiter_requirements)):
    require(requirements, "fastapi==0.140.0", f"{name} must use the audited FastAPI baseline")
    require(requirements, "uvicorn[standard]==0.51.0", f"{name} must use the audited Uvicorn baseline")
    require(requirements, "pydantic==2.12.5", f"{name} must use the audited Pydantic baseline")
    require(requirements, "python-dotenv==1.2.2", f"{name} must use the audited dotenv baseline")
for name, artifact in (
    ("cron setup", cron_setup),
    ("limiter setup", limiter_setup),
    ("cron container", cron_docker),
    ("limiter container", limiter_docker),
):
    require(artifact, "pip>=26.1.2", f"{name} must upgrade pip past PYSEC-2026-196")

if failures:
    raise SystemExit("\n".join(failures))

print("Privileged service security contracts verified")
