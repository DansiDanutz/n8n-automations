import os
import subprocess
import sys
from pathlib import Path

import pytest

import main
from api.database import SessionLocal
from api.models import Assistant, Conversation
from main import create_talk_token, required_secret


BOOTSTRAP_HEADERS = {"X-Bootstrap-Key": "test-bootstrap-key-that-is-at-least-32-characters"}


def create_tenant(client, suffix="one"):
    response = client.post(
        "/api/tenants",
        headers=BOOTSTRAP_HEADERS,
        json={"name": f"Tenant {suffix}", "email": f"{suffix}@example.com"},
    )
    assert response.status_code == 200
    return {"X-API-Key": response.json()["api_key"]}


def create_assistant(client, tenant_headers, name="Support"):
    response = client.post("/api/assistants", headers=tenant_headers, json={"name": name})
    assert response.status_code == 200
    return response.json()


def test_tenant_bootstrap_requires_operator_key(client):
    response = client.post("/api/tenants", json={"name": "Anonymous", "email": "anon@example.com"})
    assert response.status_code == 401


def test_public_talk_requires_signed_assistant_token(client):
    tenant = create_tenant(client, "signed")
    assistant = create_assistant(client, tenant)
    response = client.post(f"/api/talk/{assistant['slug']}/text", json={"message": "hello"})
    assert response.status_code == 401


def test_text_talk_accepts_valid_token_without_network(client, monkeypatch):
    tenant = create_tenant(client, "valid")
    assistant = create_assistant(client, tenant)

    async def fake_llm(messages, model):
        return {"text": "safe reply", "tokens": 2, "latency_ms": 1}

    monkeypatch.setattr(main, "llm_respond", fake_llm)
    response = client.post(
        f"/api/talk/{assistant['slug']}/text",
        headers={"X-Talk-Token": create_talk_token(assistant["slug"])},
        json={"message": "hello"},
    )
    assert response.status_code == 200
    assert response.json()["response"] == "safe reply"


def test_conversation_cannot_cross_assistant_boundary(client, monkeypatch):
    tenant = create_tenant(client, "scope")
    first = create_assistant(client, tenant, "First")
    second = create_assistant(client, tenant, "Second")
    with SessionLocal() as db:
        first_model = db.query(Assistant).filter(Assistant.slug == first["slug"]).one()
        conversation = Conversation(assistant_id=first_model.id)
        db.add(conversation)
        db.commit()
        conversation_id = str(conversation.id)

    async def fake_llm(messages, model):
        return {"text": "isolated", "tokens": 1, "latency_ms": 1}

    monkeypatch.setattr(main, "llm_respond", fake_llm)
    response = client.post(
        f"/api/talk/{second['slug']}/text",
        headers={"X-Talk-Token": create_talk_token(second["slug"])},
        json={"message": "hello", "conversation_id": conversation_id},
    )
    assert response.status_code == 200
    assert response.json()["conversation_id"] != conversation_id


def test_talk_page_escapes_assistant_content(client):
    tenant = create_tenant(client, "xss")
    assistant = create_assistant(client, tenant, '<img src=x onerror="alert(1)">')
    response = client.get(f"/talk/{assistant['slug']}")
    assert response.status_code == 200
    assert '<img src=x onerror="alert(1)">' not in response.text
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in response.text
    assert "document.createTextNode(text)" in response.text

    tenant_two = create_tenant(client, "script-close")
    script_assistant = create_assistant(client, tenant_two, "</script><script>alert(1)</script>")
    script_page = client.get(f"/talk/{script_assistant['slug']}")
    assert "</script><script>alert(1)</script>" not in script_page.text
    assert "\\u003c/script\\u003e" in script_page.text


def test_audio_upload_is_bounded_before_provider_call(client):
    tenant = create_tenant(client, "audio")
    assistant = create_assistant(client, tenant)
    response = client.post(
        f"/api/talk/{assistant['slug']}/voice",
        headers={"X-Talk-Token": create_talk_token(assistant["slug"])},
        files={"audio": ("large.webm", b"x" * (main.MAX_AUDIO_BYTES + 1), "audio/webm")},
    )
    assert response.status_code == 413


def test_prompt_input_is_bounded(client):
    tenant = create_tenant(client, "bounds")
    assistant = create_assistant(client, tenant)
    response = client.post(
        f"/api/talk/{assistant['slug']}/text",
        headers={"X-Talk-Token": create_talk_token(assistant["slug"])},
        json={"message": "x" * 4001},
    )
    assert response.status_code == 422


def test_public_talk_is_rate_limited_before_provider_calls(client, monkeypatch):
    tenant = create_tenant(client, "rate")
    assistant = create_assistant(client, tenant)
    main._talk_requests.clear()
    monkeypatch.setattr(main, "TALK_RATE_LIMIT", 2)

    async def fake_llm(messages, model):
        return {"text": "reply", "tokens": 1, "latency_ms": 1}

    monkeypatch.setattr(main, "llm_respond", fake_llm)
    headers = {"X-Talk-Token": create_talk_token(assistant["slug"])}
    assert client.post(f"/api/talk/{assistant['slug']}/text", headers=headers, json={"message": "one"}).status_code == 200
    assert client.post(f"/api/talk/{assistant['slug']}/text", headers=headers, json={"message": "two"}).status_code == 200
    assert client.post(f"/api/talk/{assistant['slug']}/text", headers=headers, json={"message": "three"}).status_code == 429


def test_cors_preflight_uses_configured_origin(client):
    response = client.options(
        "/api/tenants",
        headers={"Origin": "https://voice.example", "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://voice.example"


def test_required_secret_rejects_placeholder(monkeypatch):
    monkeypatch.setenv("VOICE_PLACEHOLDER", "replace-with-at-least-32-random-characters")
    with pytest.raises(RuntimeError, match="VOICE_PLACEHOLDER"):
        required_secret("VOICE_PLACEHOLDER", 32)


@pytest.mark.parametrize("missing", ["BOOTSTRAP_API_KEY", "SECRET_KEY", "ELEVENLABS_API_KEY"])
def test_service_fails_closed_without_required_secret(missing):
    env = os.environ.copy()
    env.pop(missing, None)
    result = subprocess.run(
        [sys.executable, "-c", "import main"],
        cwd=Path(__file__).parents[1],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert missing in result.stderr


def test_service_fails_closed_without_llm_provider():
    env = os.environ.copy()
    env.pop("OPENAI_API_KEY", None)
    env.pop("DEEPSEEK_API_KEY", None)
    result = subprocess.run(
        [sys.executable, "-c", "import main"],
        cwd=Path(__file__).parents[1],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "At least one LLM provider key must be configured" in result.stderr
