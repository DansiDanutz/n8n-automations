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
email_main = source("ai-email-assistant/backend/main.py")
email_auth = source("ai-email-assistant/backend/services/auth_service.py")
appointment = source("appointment-booking-system/main.py")
social = source("social-media-auto-poster/main.py")
invoice = source("invoice-generator-api/main.py")
documents = source("ai-document-summarizer/main.py")
support = source("ai-customer-support-bot/main.py")
seo = source("ai-seo-content-generator/main.py")
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
appointment_env = (ROOT / "appointment-booking-system/.env.example").read_text()
appointment_requirements = (ROOT / "appointment-booking-system/requirements.txt").read_text()
appointment_docker = (ROOT / "appointment-booking-system/Dockerfile").read_text()
appointment_setup = (ROOT / "appointment-booking-system/setup.sh").read_text()
invoice_env = (ROOT / "invoice-generator-api/.env.example").read_text()
invoice_requirements = (ROOT / "invoice-generator-api/requirements.txt").read_text()
invoice_docker = (ROOT / "invoice-generator-api/Dockerfile").read_text()
invoice_setup = (ROOT / "invoice-generator-api/setup.sh").read_text()
support_env = (ROOT / "ai-customer-support-bot/.env.example").read_text()
support_requirements = (ROOT / "ai-customer-support-bot/requirements.txt").read_text()
support_docker = (ROOT / "ai-customer-support-bot/Dockerfile").read_text()
support_setup = (ROOT / "ai-customer-support-bot/setup.sh").read_text()
relay_service = source("webhook-relay-logger/backend/services/relay_service.py")
relay_auth = source("webhook-relay-logger/backend/services/auth_service.py")
relay_schemas = source("webhook-relay-logger/backend/models/schemas.py")
relay_env = (ROOT / "webhook-relay-logger/.env.example").read_text()
relay_requirements = (ROOT / "webhook-relay-logger/backend/requirements.txt").read_text()
relay_docker = (ROOT / "webhook-relay-logger/Dockerfile").read_text()
email_env = (ROOT / "ai-email-assistant/.env.example").read_text()
email_requirements = (ROOT / "ai-email-assistant/backend/requirements.txt").read_text()
email_docker = (ROOT / "ai-email-assistant/Dockerfile").read_text()
social_env = (ROOT / "social-media-auto-poster/.env.example").read_text()
social_requirements = (ROOT / "social-media-auto-poster/requirements.txt").read_text()
social_docker = (ROOT / "social-media-auto-poster/Dockerfile").read_text()
social_setup = (ROOT / "social-media-auto-poster/setup.sh").read_text()
documents_env = (ROOT / "ai-document-summarizer/.env.example").read_text()
documents_requirements = (ROOT / "ai-document-summarizer/requirements.txt").read_text()
documents_docker = (ROOT / "ai-document-summarizer/Dockerfile").read_text()
documents_setup = (ROOT / "ai-document-summarizer/setup.sh").read_text()
seo_env = (ROOT / "ai-seo-content-generator/.env.example").read_text()
seo_requirements = (ROOT / "ai-seo-content-generator/requirements.txt").read_text()
seo_docker = (ROOT / "ai-seo-content-generator/Dockerfile").read_text()

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
require(appointment, 'required_secret("ADMIN_API_KEY", 32)', "appointment service must require a strong admin key")
require(appointment, "hmac.compare_digest", "appointment admin-key checks must be timing safe")
require(appointment, "Depends(require_admin)", "appointment administrative routes must authenticate callers")
if 'allow_origins=["*"]' in appointment:
    failures.append("appointment service must not use wildcard credentialed CORS")
if '"client_name": booking["client_name"]' in appointment:
    failures.append("public appointment availability must not disclose client names")
require(appointment_env, "ADMIN_API_KEY=replace-with-at-least-32-random-characters", "appointment template must require a strong admin key")
for expected in (
    "fastapi==0.140.0",
    "uvicorn[standard]==0.51.0",
    "pydantic==2.13.4",
    "python-dotenv==1.2.2",
    "email-validator==2.3.0",
):
    require(appointment_requirements, expected, f"appointment service must pin audited dependency {expected}")
for unused in ("python-multipart", "requests"):
    if unused in appointment_requirements:
        failures.append(f"appointment service must remove unused dependency {unused}")
require(appointment_docker, "pip>=26.1.2", "appointment container must upgrade pip past PYSEC-2026-196")
require(appointment_setup, "pip>=26.1.2", "appointment setup must upgrade pip past PYSEC-2026-196")
require(invoice, 'required_secret("API_KEY", 32)', "invoice API must require a strong control-plane key")
require(invoice, 'request.url.path not in {"/", "/health"}', "invoice API must authenticate invoice routes")
require(invoice, 'request.headers.get("X-API-Key", "")', "invoice API must read X-API-Key")
require(invoice, "hmac.compare_digest", "invoice API-key checks must be timing safe")
require(invoice, "Environment(autoescape=True)", "invoice HTML must autoescape stored fields")
if 'allow_origins=["*"]' in invoice:
    failures.append("invoice API must not use wildcard credentialed CORS")
require(invoice_env, "API_KEY=replace-with-at-least-32-random-characters", "invoice template must require a strong API key")
for expected in (
    "fastapi==0.140.0",
    "uvicorn[standard]==0.51.0",
    "pydantic==2.13.4",
    "jinja2==3.1.6",
    "reportlab==5.0.0",
):
    require(invoice_requirements, expected, f"invoice API must pin audited dependency {expected}")
for unused in ("python-multipart", "sqlite3", "weasyprint"):
    if unused in invoice_requirements:
        failures.append(f"invoice API must remove unused dependency {unused}")
require(invoice_docker, "pip>=26.1.2", "invoice container must upgrade pip past PYSEC-2026-196")
require(invoice_setup, "pip>=26.1.2", "invoice setup must upgrade pip past PYSEC-2026-196")
require(support, 'required_secret("API_KEY", 32)', "support bot must require a strong API key")
require(support, 'request.url.path not in {"/", "/health"}', "support bot must authenticate support routes")
require(support, 'request.headers.get("X-API-Key", "")', "support bot must read X-API-Key")
require(support, "hmac.compare_digest", "support API-key checks must be timing safe")
if 'allow_origins=["*"]' in support:
    failures.append("support bot must not use wildcard credentialed CORS")
require(support_env, "API_KEY=replace-with-at-least-32-random-characters", "support template must require a strong API key")
for expected in (
    "fastapi==0.140.0",
    "uvicorn[standard]==0.51.0",
    "openai==2.48.0",
    "pydantic==2.13.4",
):
    require(support_requirements, expected, f"support bot must pin audited dependency {expected}")
for unused in ("python-multipart", "sqlite3"):
    if unused in support_requirements:
        failures.append(f"support bot must remove unused dependency {unused}")
require(support_docker, "pip>=26.1.2", "support container must upgrade pip past PYSEC-2026-196")
require(support_setup, "pip>=26.1.2", "support setup must upgrade pip past PYSEC-2026-196")
require(relay_auth, 'required_secret("JWT_SECRET_KEY", 32)', "webhook relay must reject missing or weak JWT secrets")
if "webhook-relay-secret-change-in-production" in relay_auth:
    failures.append("webhook relay must not ship a forgeable JWT secret")
require(relay_service, "validate_public_target_url", "webhook relay must validate outbound destinations")
require(relay_service, "address.is_global", "webhook relay must reject non-public and ambiguous DNS answers")
require(relay_service, "loop.getaddrinfo", "webhook relay must resolve every target before delivery")
require(relay_service, "allow_redirects=False", "webhook relay must not follow redirects")
require(relay_service, "SENSITIVE_RELAY_HEADERS", "webhook relay must strip credentials and hop-by-hop headers")
require(relay_env, "JWT_SECRET_KEY=replace-with-at-least-32-random-characters", "webhook relay template must require a strong JWT secret")
require(email_auth, 'required_secret("JWT_SECRET_KEY", 32)', "email assistant must require a strong JWT secret")
require(email_main, 'required_secret("WEBHOOK_SECRET", 32)', "email assistant must require a strong webhook secret")
require(email_main, "hmac.compare_digest", "email webhook authentication must be timing safe")
require(email_main, "Depends(verify_webhook_secret)", "email webhook routes must authenticate callers")
if "demopass123" in email_auth:
    failures.append("email assistant must not ship a demo password")
for expected in (
    "fastapi==0.140.0",
    "uvicorn[standard]==0.51.0",
    "pydantic==2.13.4",
    "python-multipart==0.0.32",
    "aiohttp==3.14.3",
    "PyJWT==2.13.0",
    "pwdlib[argon2]==0.3.0",
):
    require(relay_requirements, expected, f"webhook relay must pin audited dependency {expected}")
for unused in ("celery", "python-jose", "passlib", "redis", "jinja2", "asyncio"):
    if unused in relay_requirements:
        failures.append(f"webhook relay must not include unused dependency {unused}")
require(relay_docker, "pip>=26.1.2", "webhook relay container must upgrade pip past PYSEC-2026-196")
require(relay_docker, '"backend.main:app"', "webhook relay container must import the backend as a package")
require(relay_schemas, '@field_validator("path", mode="before")', "webhook relay path validation must use the supported Pydantic API")
for expected in (
    "fastapi==0.140.0",
    "uvicorn[standard]==0.51.0",
    "pydantic==2.13.4",
    "PyJWT==2.13.0",
    "pwdlib[argon2]==0.3.0",
):
    require(email_requirements, expected, f"email assistant must pin audited dependency {expected}")
for unused in ("passlib", "python-jose", "numpy", "scikit-learn", "spacy"):
    if unused in email_requirements:
        failures.append(f"email assistant must remove unused dependency {unused}")
require(email_env, "WEBHOOK_SECRET=replace-with-at-least-32-random-characters", "email template must require a strong webhook secret")
require(email_docker, "pip>=26.1.2", "email container must upgrade pip past PYSEC-2026-196")
require(social, 'required_secret("API_KEY", 32)', "social poster must require a strong control-plane key")
require(social, 'request.url.path not in {"/", "/health"}', "social poster must authenticate non-health routes")
require(social, 'request.headers.get("X-API-Key", "")', "social poster must read X-API-Key")
require(social, "hmac.compare_digest", "social poster API-key checks must be timing safe")
if 'allow_origins=["*"]' in social:
    failures.append("social poster must not use wildcard credentialed CORS")
require(social_env, "API_KEY=replace-with-at-least-32-random-characters", "social poster template must require a strong API key")
for expected in (
    "fastapi==0.140.0",
    "uvicorn[standard]==0.51.0",
    "pydantic==2.13.4",
    "apscheduler==3.11.2",
    "tweepy==4.16.0",
    "sqlalchemy==2.0.51",
):
    require(social_requirements, expected, f"social poster must pin audited dependency {expected}")
for unused in ("python-multipart", "sqlite3"):
    if unused in social_requirements:
        failures.append(f"social poster must remove unused dependency {unused}")
require(social_docker, "pip>=26.1.2", "social poster container must upgrade pip past PYSEC-2026-196")
require(social_setup, "pip>=26.1.2", "social poster setup must upgrade pip past PYSEC-2026-196")
require(documents, 'required_secret("API_KEY", 32)', "document summarizer must require a strong API key")
require(documents, 'request.url.path not in {"/", "/health"}', "document summarizer must authenticate document routes")
require(documents, 'request.headers.get("X-API-Key", "")', "document summarizer must read X-API-Key")
require(documents, "hmac.compare_digest", "document API-key checks must be timing safe")
require(documents, 'save_path = Path(UPLOAD_DIR) / f"{doc_id}{ext}"', "document uploads must use server-generated paths")
require(documents, "hashlib.sha256(content).hexdigest()", "document deduplication must use a collision-resistant hash")
if "INSERT OR IGNORE INTO documents" in documents:
    failures.append("document uploads must not silently overwrite duplicate storage paths")
if 'file.filename}' in documents:
    failures.append("document uploads must not place client filenames in storage paths")
if 'allow_origins=["*"]' in documents:
    failures.append("document summarizer must not use wildcard CORS")
require(documents_env, "API_KEY=replace-with-at-least-32-random-characters", "document template must require a strong API key")
for expected in (
    "fastapi==0.140.0",
    "uvicorn[standard]==0.51.0",
    "pydantic==2.13.4",
    "python-dotenv==1.2.2",
    "openai==2.48.0",
    "python-multipart==0.0.32",
    "pypdf==6.14.2",
    "python-docx==1.2.0",
):
    require(documents_requirements, expected, f"document summarizer must pin audited dependency {expected}")
require(documents_docker, "pip>=26.1.2", "document container must upgrade pip past PYSEC-2026-196")
require(documents_setup, "pip>=26.1.2", "document setup must upgrade pip past PYSEC-2026-196")
require(seo, 'required_secret("API_KEY", 32)', "SEO generator must require a strong API key")
require(seo, 'request.url.path != "/health"', "SEO generator must authenticate non-health routes")
require(seo, 'request.headers.get("X-API-Key", "")', "SEO generator must read X-API-Key")
require(seo, "hmac.compare_digest", "SEO API-key checks must be timing safe")
require(seo, "At least one AI provider key must be configured", "SEO generator must fail closed without an AI provider")
require(seo, "ClientTimeout(total=60)", "SEO upstream calls must have a total timeout")
if 'allow_origins=["*"]' in seo:
    failures.append("SEO generator must not use wildcard credentialed CORS")
require(seo_env, "API_KEY=replace-with-at-least-32-random-characters", "SEO template must require a strong API key")
for expected in (
    "fastapi==0.140.0",
    "uvicorn[standard]==0.51.0",
    "aiohttp==3.14.3",
    "pydantic==2.13.4",
    "python-dotenv==1.2.2",
):
    require(seo_requirements, expected, f"SEO generator must pin audited dependency {expected}")
for unused in ("python-multipart", "requests", "beautifulsoup4", "lxml"):
    if unused in seo_requirements:
        failures.append(f"SEO generator must remove unused dependency {unused}")
require(seo_docker, "pip>=26.1.2", "SEO container must upgrade pip past PYSEC-2026-196")
require(seo_docker, "urllib.request", "SEO container health check must use an available client")
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
