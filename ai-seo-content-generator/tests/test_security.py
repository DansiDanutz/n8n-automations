import os
import subprocess
import sys
from pathlib import Path

import pytest

from main import required_secret


API_HEADERS = {"X-API-Key": "test-seo-api-key-that-is-at-least-32-characters"}


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/generate/blog-post", {"topic": "SEO", "target_keywords": ["SEO"]}),
        ("post", "/generate/meta-description", {"page_title": "SEO", "main_keywords": ["SEO"], "page_content_summary": "Summary"}),
        ("post", "/analyze/keywords", {"primary_keyword": "SEO", "industry": "software"}),
        ("post", "/analyze/competitors", {"competitor_urls": ["https://example.com"], "target_keywords": ["SEO"]}),
        ("get", "/stats", None),
    ],
)
def test_private_routes_reject_anonymous_requests(client, method, path, payload):
    response = client.request(method, path, json=payload)
    assert response.status_code == 401


def test_health_remains_public(client):
    assert client.get("/health").status_code == 200


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/generate/blog-post", {"topic": "", "target_keywords": ["SEO"]}),
        ("/generate/blog-post", {"topic": "SEO", "target_keywords": ["SEO"], "word_count": 4001}),
        ("/generate/meta-description", {"page_title": "SEO", "main_keywords": [], "page_content_summary": "Summary"}),
        ("/analyze/keywords", {"primary_keyword": "x" * 201, "industry": "software"}),
        ("/analyze/competitors", {"competitor_urls": [], "target_keywords": ["SEO"]}),
    ],
)
def test_prompt_inputs_are_bounded(client, path, payload):
    assert client.post(path, headers=API_HEADERS, json=payload).status_code == 422


def test_cors_preflight_allows_configured_origin_without_api_key(client):
    response = client.options(
        "/stats",
        headers={
            "Origin": "https://seo.example",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-API-Key",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://seo.example"


def test_required_secret_fails_closed(monkeypatch):
    monkeypatch.delenv("MISSING_SEO_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="MISSING_SEO_SECRET"):
        required_secret("MISSING_SEO_SECRET", 32)


def test_required_secret_rejects_documented_placeholder(monkeypatch):
    monkeypatch.setenv("PLACEHOLDER_SEO_SECRET", "replace-with-at-least-32-random-characters")
    with pytest.raises(RuntimeError, match="PLACEHOLDER_SEO_SECRET"):
        required_secret("PLACEHOLDER_SEO_SECRET", 32)


def test_service_fails_closed_without_api_key():
    env = os.environ.copy()
    env.pop("API_KEY", None)
    result = subprocess.run(
        [sys.executable, "-c", "import main"],
        cwd=Path(__file__).parents[1],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "API_KEY" in result.stderr


def test_service_fails_closed_without_provider_key():
    env = os.environ.copy()
    env["API_KEY"] = "test-seo-api-key-that-is-at-least-32-characters"
    env.pop("OPENROUTER_API_KEY", None)
    env.pop("OPENAI_API_KEY", None)
    result = subprocess.run(
        [sys.executable, "-c", "import main"],
        cwd=Path(__file__).parents[1],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "At least one AI provider key must be configured" in result.stderr
